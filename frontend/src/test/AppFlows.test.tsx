import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'
import type { Evidence } from '../types'

const apiMocks = vi.hoisted(() => ({
  createEvidence: vi.fn(),
  deleteEvidence: vi.fn(),
  getApiBaseUrl: vi.fn(),
  getEvidence: vi.fn(),
  listEvidence: vi.fn(),
  presignUpload: vi.fn(),
  uploadFile: vi.fn(),
}))

vi.mock('../api/evidenceApi', () => ({
  ...apiMocks,
  EvidenceApiError: class EvidenceApiError extends Error {
    readonly status: number

    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
}))

const record: Evidence = {
  id: 'record-1',
  title: 'Professional milestone',
  description: 'A meaningful result',
  tags: ['milestone'],
  fileName: 'milestone.pdf',
  contentType: 'application/pdf',
  assetKey: 'record-1.pdf',
  createdAt: '2025-01-10T12:00:00Z',
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getApiBaseUrl.mockReturnValue('https://api.example.com')
  apiMocks.listEvidence.mockResolvedValue({ items: [] })
})

describe('App evidence flows', () => {
  it('shows loading followed by the empty state', async () => {
    let resolveList!: (value: { items: Evidence[] }) => void
    apiMocks.listEvidence.mockReturnValue(
      new Promise((resolve) => {
        resolveList = resolve
      }),
    )

    render(<App />)
    expect(screen.getByRole('status')).toHaveTextContent('Opening your library')

    resolveList({ items: [] })
    expect(await screen.findByText('Your library is ready')).toBeInTheDocument()
  })

  it('shows a visible failure state', async () => {
    apiMocks.listEvidence.mockRejectedValue(new Error('offline'))

    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'ProofStack could not connect to the library',
    )
  })

  it('requests a fresh detail response before downloading', async () => {
    const user = userEvent.setup()
    apiMocks.listEvidence.mockResolvedValue({ items: [record] })
    apiMocks.getEvidence.mockResolvedValue({
      ...record,
      assetUrl: 'https://example.invalid/asset',
    })
    let downloadedUrl = ''
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function captureDownload(this: HTMLAnchorElement) {
        downloadedUrl = this.href
      })
    render(<App />)
    await screen.findByText(record.title)

    await user.click(screen.getByRole('button', { name: `Download ${record.title}` }))

    await waitFor(() => expect(apiMocks.getEvidence).toHaveBeenCalledWith(record.id))
    expect(downloadedUrl).toBe('https://example.invalid/asset')
    expect(anchorClick).toHaveBeenCalledOnce()
  })

  it('deletes only after visible confirmation', async () => {
    const user = userEvent.setup()
    apiMocks.listEvidence.mockResolvedValue({ items: [record] })
    apiMocks.deleteEvidence.mockResolvedValue(undefined)
    render(<App />)
    await screen.findByText(record.title)

    await user.click(screen.getByRole('button', { name: `Delete ${record.title}` }))
    expect(apiMocks.deleteEvidence).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Confirm' }))

    await waitFor(() => expect(apiMocks.deleteEvidence).toHaveBeenCalledWith(record.id))
    expect(screen.getByRole('status')).toHaveTextContent('Evidence removed')
    expect(screen.queryByText(record.title)).not.toBeInTheDocument()
  })

  it('creates metadata only after the direct upload succeeds', async () => {
    const user = userEvent.setup()
    apiMocks.presignUpload.mockResolvedValue({
      uploadUrl: 'https://example.invalid/upload',
      assetKey: 'record-1.pdf',
      expiresIn: 300,
    })
    apiMocks.uploadFile.mockResolvedValue(undefined)
    apiMocks.createEvidence.mockResolvedValue(record)
    render(<App />)
    await screen.findByText('Your library is ready')

    await user.type(screen.getByRole('textbox', { name: 'Title' }), record.title)
    await user.upload(
      screen.getByLabelText('File'),
      new File(['evidence'], record.fileName, { type: record.contentType }),
    )
    await user.click(screen.getByRole('button', { name: 'Preserve evidence' }))

    await waitFor(() => expect(apiMocks.createEvidence).toHaveBeenCalledOnce())
    expect(apiMocks.presignUpload).toHaveBeenCalledWith({
      fileName: record.fileName,
      contentType: record.contentType,
    })
    expect(apiMocks.uploadFile.mock.invocationCallOrder[0]).toBeLessThan(
      apiMocks.createEvidence.mock.invocationCallOrder[0],
    )
    expect(apiMocks.createEvidence).toHaveBeenCalledWith({
      title: record.title,
      description: undefined,
      tags: [],
      fileName: record.fileName,
      contentType: record.contentType,
      assetKey: 'record-1.pdf',
    })
    expect(screen.getByRole('status')).toHaveTextContent('Evidence preserved')
  })

  it('does not create metadata when the direct upload fails', async () => {
    const user = userEvent.setup()
    apiMocks.presignUpload.mockResolvedValue({
      uploadUrl: 'https://example.invalid/upload',
      assetKey: 'record-1.pdf',
      expiresIn: 300,
    })
    apiMocks.uploadFile.mockRejectedValue(new Error('upload failed'))
    render(<App />)
    await screen.findByText('Your library is ready')

    await user.type(screen.getByRole('textbox', { name: 'Title' }), record.title)
    await user.upload(
      screen.getByLabelText('File'),
      new File(['evidence'], record.fileName, { type: record.contentType }),
    )
    await user.click(screen.getByRole('button', { name: 'Preserve evidence' }))

    await waitFor(() => expect(apiMocks.uploadFile).toHaveBeenCalledOnce())
    expect(apiMocks.createEvidence).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(
      'ProofStack could not connect to the library',
    )
  })
})

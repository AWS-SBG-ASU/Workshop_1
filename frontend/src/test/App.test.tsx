import { render, screen } from '@testing-library/react'
import App from '../App'

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

describe('App', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    apiMocks.getApiBaseUrl.mockReturnValue('https://api.example.com')
    apiMocks.listEvidence.mockResolvedValue({ items: [] })
  })

  it('renders the initial library experience', async () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: /keep the proof/i })).toBeInTheDocument()
    expect(screen.getByRole('form', { name: /add evidence/i })).toBeInTheDocument()
    expect(await screen.findByText('Your library is ready')).toBeInTheDocument()
    expect(apiMocks.listEvidence).toHaveBeenCalledOnce()
  })

  it('shows setup guidance when the API base URL is missing', () => {
    apiMocks.getApiBaseUrl.mockReturnValue(null)

    render(<App />)

    expect(
      screen.getByRole('heading', { name: /connect your personal evidence library/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('VITE_API_BASE_URL')).toBeInTheDocument()
    expect(screen.queryByRole('form', { name: /add evidence/i })).not.toBeInTheDocument()
    expect(apiMocks.listEvidence).not.toHaveBeenCalled()
  })
})

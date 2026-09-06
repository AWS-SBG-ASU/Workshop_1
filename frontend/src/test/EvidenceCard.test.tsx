import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EvidenceCard } from '../components/EvidenceCard'
import type { Evidence } from '../types'

const evidence: Evidence = {
  id: 'record-1',
  title: 'Professional milestone',
  tags: ['milestone'],
  fileName: 'milestone.pdf',
  contentType: 'application/pdf',
  assetKey: 'record-1.pdf',
  createdAt: '2025-01-10T12:00:00Z',
}

describe('EvidenceCard', () => {
  it('asks for confirmation before deleting a record and its file', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    render(
      <EvidenceCard
        evidence={evidence}
        onDownload={vi.fn()}
        onDelete={onDelete}
      />,
    )

    await user.click(screen.getByRole('button', { name: /delete professional milestone/i }))

    expect(screen.getByText('Remove record and file?')).toBeInTheDocument()
    expect(onDelete).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(onDelete).toHaveBeenCalledWith('record-1')
  })

  it('allows deletion to be cancelled', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    render(
      <EvidenceCard
        evidence={evidence}
        onDownload={vi.fn()}
        onDelete={onDelete}
      />,
    )

    await user.click(screen.getByRole('button', { name: /delete professional milestone/i }))
    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onDelete).not.toHaveBeenCalled()
    expect(screen.queryByText('Remove record and file?')).not.toBeInTheDocument()
  })
})

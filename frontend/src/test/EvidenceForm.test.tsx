import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EvidenceForm } from '../components/EvidenceForm'

describe('EvidenceForm', () => {
  it('has accessible fields and reports required values', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EvidenceForm onSubmit={onSubmit} />)

    expect(screen.getByRole('textbox', { name: 'Title' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /notes/i })).toBeInTheDocument()
    expect(screen.getByLabelText('File')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /preserve evidence/i }))

    expect(screen.getByText('Add a title for this record.')).toBeInTheDocument()
    expect(screen.getByText('Choose a file to preserve.')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Title' })).toHaveAttribute(
      'aria-invalid',
      'true',
    )
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits valid form values', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<EvidenceForm onSubmit={onSubmit} />)

    await user.type(screen.getByRole('textbox', { name: 'Title' }), 'Project outcome')
    await user.type(screen.getByRole('textbox', { name: /tags/i }), 'result, report')
    await user.upload(
      screen.getByLabelText('File'),
      new File(['content'], 'outcome.pdf', { type: 'application/pdf' }),
    )
    await user.click(screen.getByRole('button', { name: /preserve evidence/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Project outcome',
        tags: ['result', 'report'],
        file: expect.any(File),
      }),
    )
  })
})

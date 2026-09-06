import { useId, useRef, useState, type FormEvent } from 'react'
import type { EvidenceFormValues } from '../types'

interface EvidenceFormProps {
  onSubmit: (
    values: EvidenceFormValues,
  ) => boolean | void | Promise<boolean | void>
  isSubmitting?: boolean
}

interface FormErrors {
  title?: string
  file?: string
}

export function EvidenceForm({
  onSubmit,
  isSubmitting = false,
}: EvidenceFormProps) {
  const titleId = useId()
  const descriptionId = useId()
  const tagsId = useId()
  const fileId = useId()
  const formRef = useRef<HTMLFormElement>(null)
  const [errors, setErrors] = useState<FormErrors>({})

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const title = String(data.get('title') ?? '').trim()
    const fileInput = event.currentTarget.elements.namedItem('file')
    const selectedFile =
      fileInput instanceof HTMLInputElement ? fileInput.files?.[0] : undefined
    const file = selectedFile && selectedFile.size > 0 ? selectedFile : null
    const nextErrors: FormErrors = {}

    if (!title) nextErrors.title = 'Add a title for this record.'
    if (!file) nextErrors.file = 'Choose a file to preserve.'

    setErrors(nextErrors)
    if (!title || !file) {
      const fieldName = !title ? 'title' : 'file'
      const invalidField = event.currentTarget.elements.namedItem(fieldName)
      if (invalidField instanceof HTMLElement) invalidField.focus()
      return
    }

    const wasSaved = await onSubmit({
      title,
      description: String(data.get('description') ?? '').trim(),
      tags: String(data.get('tags') ?? '')
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
      file,
    })

    if (wasSaved !== false) {
      formRef.current?.reset()
      setErrors({})
    }
  }

  return (
    <form
      className="evidence-form"
      ref={formRef}
      onSubmit={handleSubmit}
      noValidate
      aria-label="Add evidence"
    >
      <div className="form-heading">
        <div>
          <p className="eyebrow">New record</p>
          <h2>Add to your library</h2>
        </div>
        <span className="step-badge">Private by design</span>
      </div>

      <div className="field">
        <label htmlFor={titleId}>Title</label>
        <input
          id={titleId}
          name="title"
          type="text"
          autoComplete="off"
          placeholder="What does this record show?"
          aria-invalid={Boolean(errors.title)}
          aria-describedby={errors.title ? `${titleId}-error` : undefined}
          disabled={isSubmitting}
        />
        {errors.title && (
          <p className="field-error" id={`${titleId}-error`}>
            {errors.title}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor={descriptionId}>Notes <span>Optional</span></label>
        <textarea
          id={descriptionId}
          name="description"
          rows={3}
          placeholder="Add context that will help you find this later."
          disabled={isSubmitting}
        />
      </div>

      <div className="field">
        <label htmlFor={tagsId}>Tags <span>Optional</span></label>
        <input
          id={tagsId}
          name="tags"
          type="text"
          placeholder="work, certification, milestone"
          aria-describedby={`${tagsId}-hint`}
          disabled={isSubmitting}
        />
        <p className="field-hint" id={`${tagsId}-hint`}>Separate tags with commas.</p>
      </div>

      <div className="field">
        <label htmlFor={fileId}>File</label>
        <input
          className="file-input"
          id={fileId}
          name="file"
          type="file"
          aria-invalid={Boolean(errors.file)}
          aria-describedby={errors.file ? `${fileId}-error` : `${fileId}-hint`}
          disabled={isSubmitting}
        />
        {errors.file ? (
          <p className="field-error" id={`${fileId}-error`}>{errors.file}</p>
        ) : (
          <p className="field-hint" id={`${fileId}-hint`}>Choose a document or image.</p>
        )}
      </div>

      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Preserving…' : 'Preserve evidence'}
      </button>
    </form>
  )
}

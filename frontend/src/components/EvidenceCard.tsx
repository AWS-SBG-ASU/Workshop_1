import { useState } from 'react'
import type { Evidence } from '../types'

interface EvidenceCardProps {
  evidence: Evidence
  onDownload: (id: string) => void
  onDelete: (id: string) => void
  isDownloading?: boolean
  isDeleting?: boolean
}

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      }).format(date)
}

export function EvidenceCard({
  evidence,
  onDownload,
  onDelete,
  isDownloading = false,
  isDeleting = false,
}: EvidenceCardProps) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)

  function confirmDelete() {
    setIsConfirmingDelete(false)
    onDelete(evidence.id)
  }

  return (
    <article className="evidence-card">
      <div className="card-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M7 3.75h7l4 4V20.25H7V3.75Z" />
          <path d="M14 3.75v4h4M9.75 12h5.5M9.75 15.5h4" />
        </svg>
      </div>
      <div className="card-content">
        <div className="card-meta">
          <time dateTime={evidence.createdAt}>{formatDate(evidence.createdAt)}</time>
          <span aria-hidden="true">·</span>
          <span>{evidence.fileName}</span>
        </div>
        <h3>{evidence.title}</h3>
        {evidence.description && <p>{evidence.description}</p>}
        {evidence.tags.length > 0 && (
          <ul className="tag-list" aria-label="Tags">
            {evidence.tags.map((tag) => <li key={tag}>{tag}</li>)}
          </ul>
        )}
      </div>
      <div className="card-actions">
        <button
          className="text-button"
          type="button"
          onClick={() => onDownload(evidence.id)}
          disabled={isDownloading}
          aria-label={`Download ${evidence.title}`}
        >
          {isDownloading ? 'Preparing…' : 'Download'}
        </button>
        {isConfirmingDelete ? (
          <div className="delete-confirm" role="group" aria-label={`Confirm deletion of ${evidence.title}`}>
            <span>Remove record and file?</span>
            <button className="text-button danger" type="button" onClick={confirmDelete}>Confirm</button>
            <button className="text-button" type="button" onClick={() => setIsConfirmingDelete(false)}>Cancel</button>
          </div>
        ) : (
          <button
            className="text-button danger"
            type="button"
            onClick={() => setIsConfirmingDelete(true)}
            disabled={isDeleting}
            aria-label={`Delete ${evidence.title}`}
          >
            {isDeleting ? 'Deleting…' : 'Delete'}
          </button>
        )}
      </div>
    </article>
  )
}

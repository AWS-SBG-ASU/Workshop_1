import type { Evidence } from '../types'
import { EvidenceCard } from './EvidenceCard'
import { EmptyState } from './States'

interface EvidenceListProps {
  items: Evidence[]
  hasQuery: boolean
  deletingId?: string | null
  downloadingId?: string | null
  onDownload: (id: string) => void
  onDelete: (id: string) => void
}

export function EvidenceList({
  items,
  hasQuery,
  deletingId,
  downloadingId,
  onDownload,
  onDelete,
}: EvidenceListProps) {
  if (items.length === 0) {
    return <EmptyState isSearchResult={hasQuery} />
  }

  return (
    <div className="evidence-list" aria-label="Evidence library">
      {items.map((item) => (
        <EvidenceCard
          key={item.id}
          evidence={item}
          onDownload={onDownload}
          onDelete={onDelete}
          isDownloading={downloadingId === item.id}
          isDeleting={deletingId === item.id}
        />
      ))}
    </div>
  )
}

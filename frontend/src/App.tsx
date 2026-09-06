import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createEvidence,
  deleteEvidence,
  EvidenceApiError,
  getApiBaseUrl,
  getEvidence,
  listEvidence,
  presignUpload,
  uploadFile,
} from './api/evidenceApi'
import { EvidenceForm } from './components/EvidenceForm'
import { EvidenceList } from './components/EvidenceList'
import { Search } from './components/Search'
import {
  ConfigurationState,
  ErrorState,
  LoadingState,
} from './components/States'
import type { Evidence, EvidenceFormValues } from './types'
import { filterEvidence } from './utils/search'

function getErrorMessage(error: unknown): string {
  if (error instanceof EvidenceApiError) {
    if (error.status === 404) return 'That evidence record could not be found.'
    if (error.status >= 500) {
      return 'A service needed by ProofStack is unavailable. Please try again shortly.'
    }
    return error.message
  }

  return 'ProofStack could not connect to the library. Check your connection and try again.'
}

export default function App() {
  const isConfigured = Boolean(getApiBaseUrl())
  const [items, setItems] = useState<Evidence[]>([])
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(isConfigured)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const loadEvidence = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await listEvidence()
      setItems(response.items)
    } catch (loadError) {
      setError(getErrorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isConfigured) void loadEvidence()
  }, [isConfigured, loadEvidence])

  const visibleItems = useMemo(
    () => filterEvidence(items, query),
    [items, query],
  )

  async function handleCreate(values: EvidenceFormValues) {
    setIsSubmitting(true)
    setError(null)
    setNotice(null)
    try {
      const contentType = values.file.type || 'application/octet-stream'
      const upload = await presignUpload({
        fileName: values.file.name,
        contentType,
      })
      await uploadFile(upload, values.file)
      const created = await createEvidence({
        title: values.title,
        description: values.description || undefined,
        tags: values.tags,
        fileName: values.file.name,
        contentType,
        assetKey: upload.assetKey,
      })
      setItems((current) => [created, ...current])
      setNotice('Evidence preserved in your library.')
      return true
    } catch (createError) {
      setError(getErrorMessage(createError))
      return false
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDownload(id: string) {
    setDownloadingId(id)
    setError(null)
    setNotice(null)
    try {
      const detail = await getEvidence(id)
      const link = document.createElement('a')
      link.href = detail.assetUrl
      link.target = '_blank'
      link.rel = 'noreferrer'
      link.click()
    } catch (downloadError) {
      setError(getErrorMessage(downloadError))
    } finally {
      setDownloadingId(null)
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id)
    setError(null)
    setNotice(null)
    try {
      await deleteEvidence(id)
      setItems((current) => current.filter((item) => item.id !== id))
      setNotice('Evidence removed from your library.')
    } catch (deleteError) {
      setError(getErrorMessage(deleteError))
    } finally {
      setDeletingId(null)
    }
  }

  if (!isConfigured) return <ConfigurationState />

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="./" aria-label="ProofStack home">
          <span className="brand-mark" aria-hidden="true">PS</span>
          <span>
            <strong>ProofStack</strong>
            <small>Personal evidence library</small>
          </span>
        </a>
        <div className="privacy-note">
          <span className="status-dot" aria-hidden="true" />
          Your records, in one place
        </div>
      </header>

      <main>
        <section className="hero" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">Your personal archive</p>
            <h1 id="page-title">Keep the proof.<br />Find it when it counts.</h1>
            <p className="hero-copy">
              Preserve documents, milestones, and supporting records in a library built for recall.
            </p>
          </div>
          <div className="hero-stat" aria-label={`${items.length} records preserved`}>
            <strong>{items.length.toString().padStart(2, '0')}</strong>
            <span>records preserved</span>
          </div>
        </section>

        <div className="workspace-grid">
          <aside>
            <EvidenceForm onSubmit={handleCreate} isSubmitting={isSubmitting} />
          </aside>

          <section className="library-section" aria-labelledby="library-title">
            <div className="library-heading">
              <div>
                <p className="eyebrow">Browse and retrieve</p>
                <h2 id="library-title">Evidence library</h2>
              </div>
            </div>

            {!isLoading && !error && (
              <Search
                value={query}
                onChange={setQuery}
                resultCount={visibleItems.length}
              />
            )}

            {notice && <p className="notice" role="status">{notice}</p>}
            {error && !isLoading && <ErrorState message={error} onRetry={loadEvidence} />}
            {isLoading ? (
              <LoadingState />
            ) : !error ? (
              <EvidenceList
                items={visibleItems}
                hasQuery={Boolean(query.trim())}
                deletingId={deletingId}
                downloadingId={downloadingId}
                onDownload={handleDownload}
                onDelete={handleDelete}
              />
            ) : null}
          </section>
        </div>
      </main>

      <footer>
        <span>ProofStack</span>
        <p>Evidence, organized for the moments that matter.</p>
      </footer>
    </div>
  )
}

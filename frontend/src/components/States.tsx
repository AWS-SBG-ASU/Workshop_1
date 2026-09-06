interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function LoadingState() {
  return (
    <div className="state-card" role="status">
      <span className="spinner" aria-hidden="true" />
      <div>
        <h3>Opening your library</h3>
        <p>Gathering your evidence records…</p>
      </div>
    </div>
  )
}

export function EmptyState({ isSearchResult = false }: { isSearchResult?: boolean }) {
  return (
    <div className="state-card empty-state">
      <span className="state-mark" aria-hidden="true">{isSearchResult ? '0' : '+'}</span>
      <div>
        <h3>{isSearchResult ? 'No matching evidence' : 'Your library is ready'}</h3>
        <p>
          {isSearchResult
            ? 'Try a different title, tag, or file name.'
            : 'Add your first record to start building a useful personal archive.'}
        </p>
      </div>
    </div>
  )
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="state-card error-state" role="alert">
      <span className="state-mark" aria-hidden="true">!</span>
      <div>
        <h3>Your library could not be loaded</h3>
        <p>{message}</p>
        {onRetry && <button className="text-button" type="button" onClick={onRetry}>Try again</button>}
      </div>
    </div>
  )
}

export function ConfigurationState() {
  return (
    <main className="configuration-shell">
      <section className="configuration-card" aria-labelledby="configuration-title">
        <div className="brand-mark" aria-hidden="true">PS</div>
        <p className="eyebrow">One setup step remains</p>
        <h1 id="configuration-title">Connect your personal evidence library</h1>
        <p>
          Add your API base URL to begin preserving and finding the records that matter to you.
        </p>
        <div className="config-instruction">
          <span>Environment variable</span>
          <code>VITE_API_BASE_URL</code>
        </div>
        <p className="config-note">
          Copy <code>.env.example</code> to <code>.env.local</code>, then replace the example value.
        </p>
      </section>
    </main>
  )
}

interface SearchProps {
  value: string
  onChange: (value: string) => void
  resultCount: number
}

export function Search({ value, onChange, resultCount }: SearchProps) {
  return (
    <div className="search-block">
      <label className="search-field" htmlFor="evidence-search">
        <span className="sr-only">Search your evidence</span>
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="m21 21-4.35-4.35m2.35-5.15a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z" />
        </svg>
        <input
          id="evidence-search"
          type="search"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Search titles, tags, or files"
        />
      </label>
      <p className="result-count" aria-live="polite">
        {resultCount} {resultCount === 1 ? 'record' : 'records'}
      </p>
    </div>
  )
}

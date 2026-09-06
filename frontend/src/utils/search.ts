import type { Evidence } from '../types'

function searchableText(item: Evidence): string {
  return [
    item.title,
    item.description ?? '',
    item.fileName,
    ...item.tags,
  ]
    .join(' ')
    .toLocaleLowerCase()
}

export function filterEvidence(items: Evidence[], query: string): Evidence[] {
  const terms = query
    .trim()
    .toLocaleLowerCase()
    .split(/\s+/)
    .filter(Boolean)

  if (terms.length === 0) return items

  return items.filter((item) => {
    const value = searchableText(item)
    return terms.every((term) => value.includes(term))
  })
}

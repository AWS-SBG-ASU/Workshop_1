import type { Evidence } from '../types'
import { filterEvidence } from '../utils/search'

const records: Evidence[] = [
  {
    id: 'one',
    title: 'Cloud architecture certificate',
    description: 'Completed assessment',
    tags: ['certification', 'cloud'],
    fileName: 'certificate.pdf',
    contentType: 'application/pdf',
    assetKey: 'one.pdf',
    createdAt: '2025-01-10T12:00:00Z',
  },
  {
    id: 'two',
    title: 'Quarterly impact summary',
    tags: ['work', 'results'],
    fileName: 'impact.png',
    contentType: 'image/png',
    assetKey: 'two.png',
    createdAt: '2025-02-10T12:00:00Z',
  },
]

describe('filterEvidence', () => {
  it('returns every record for blank search text', () => {
    expect(filterEvidence(records, '   ')).toEqual(records)
  })

  it('matches case-insensitively across titles, tags, descriptions, and files', () => {
    expect(filterEvidence(records, 'CLOUD certificate')).toEqual([records[0]])
    expect(filterEvidence(records, 'completed')).toEqual([records[0]])
    expect(filterEvidence(records, 'impact.png')).toEqual([records[1]])
  })

  it('requires every search term to match the same record', () => {
    expect(filterEvidence(records, 'quarterly results')).toEqual([records[1]])
    expect(filterEvidence(records, 'cloud results')).toEqual([])
  })
})

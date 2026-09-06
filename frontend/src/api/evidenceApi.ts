import type {
  ApiErrorResponse,
  CreateEvidenceRequest,
  Evidence,
  EvidenceDetailResponse,
  EvidenceError,
  ListEvidenceResponse,
  PresignUploadRequest,
  PresignUploadResponse,
} from '../types'

export class EvidenceApiError extends Error {
  readonly status: number
  readonly code?: string

  constructor(status: number, payload: EvidenceError) {
    super(payload.message)
    this.name = 'EvidenceApiError'
    this.status = status
    this.code = payload.code
  }
}

export function getApiBaseUrl(): string | null {
  const value = import.meta.env.VITE_API_BASE_URL?.trim()
  return value ? value.replace(/\/+$/, '') : null
}

function requireApiBaseUrl(): string {
  const baseUrl = getApiBaseUrl()
  if (!baseUrl) {
    throw new EvidenceApiError(0, {
      code: 'API_NOT_CONFIGURED',
      message: 'VITE_API_BASE_URL is not configured.',
    })
  }
  return baseUrl
}

function normalizeErrorPayload(
  value: unknown,
  fallbackMessage: string,
): EvidenceError {
  if (!value || typeof value !== 'object') return { message: fallbackMessage }

  const envelope = value as Partial<ApiErrorResponse>
  const candidate = envelope.error
  if (!candidate || typeof candidate !== 'object') {
    return { message: fallbackMessage }
  }

  return {
    message:
      typeof candidate.message === 'string'
        ? candidate.message
        : fallbackMessage,
    code: typeof candidate.code === 'string' ? candidate.code : undefined,
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Accept', 'application/json')
  if (init?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(`${requireApiBaseUrl()}${path}`, {
      ...init,
      headers,
    })
  } catch {
    throw new EvidenceApiError(0, {
      code: 'NETWORK_ERROR',
      message: 'The API could not be reached.',
    })
  }

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}.`
    let payload: EvidenceError = { message: fallbackMessage }

    try {
      const value: unknown = await response.json()
      payload = normalizeErrorPayload(value, fallbackMessage)
    } catch {
      // Keep the status-based fallback when an error response has no JSON body.
    }

    throw new EvidenceApiError(response.status, payload)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function presignUpload(
  payload: PresignUploadRequest,
): Promise<PresignUploadResponse> {
  return request('/uploads/presign', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function uploadFile(
  upload: PresignUploadResponse,
  file: File,
): Promise<void> {
  const response = await fetch(upload.uploadUrl, {
    method: 'PUT',
    body: file,
    headers: upload.headers ?? { 'Content-Type': file.type },
  })

  if (!response.ok) {
    throw new EvidenceApiError(response.status, {
      code: 'UPLOAD_FAILED',
      message: 'The file could not be uploaded.',
    })
  }
}

export function createEvidence(
  payload: CreateEvidenceRequest,
): Promise<Evidence> {
  return request('/evidence', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listEvidence(): Promise<ListEvidenceResponse> {
  return request('/evidence')
}

export function getEvidence(id: string): Promise<EvidenceDetailResponse> {
  return request(`/evidence/${encodeURIComponent(id)}`)
}

export function deleteEvidence(id: string): Promise<void> {
  return request(`/evidence/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export interface Evidence {
  id: string
  title: string
  description?: string
  tags: string[]
  fileName: string
  contentType: string
  assetKey: string
  assetUrl?: string
  createdAt: string
  updatedAt?: string
}

export interface PresignUploadRequest {
  fileName: string
  contentType: string
}

export interface PresignUploadResponse {
  uploadUrl: string
  assetKey: string
  expiresIn: number
  headers?: Record<string, string>
}

export interface CreateEvidenceRequest {
  title: string
  description?: string
  tags: string[]
  fileName: string
  contentType: string
  assetKey: string
}

export interface ListEvidenceResponse {
  items: Evidence[]
}

export interface EvidenceDetailResponse extends Evidence {
  assetUrl: string
}

export interface ApiErrorResponse {
  error: {
    code: string
    message: string
  }
}

export interface EvidenceError {
  code?: string
  message: string
}

export interface EvidenceFormValues {
  title: string
  description: string
  tags: string[]
  file: File
}

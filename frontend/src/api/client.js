import axios from 'axios'

const client = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
})

// Response interceptor for unified error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.error('[Argus API Error] Timeout exceeded')
      error.isTimeout = true
      error.message = 'Scan is still running... this may take a few minutes for large targets'
    } else if (error.response) {
      console.error('[Argus API Error]', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('[Argus API Error] No response received:', error.request)
    } else {
      console.error('[Argus API Error] Request setup failed:', error.message)
    }
    return Promise.reject(error)
  }
)

/**
 * Unwrap the standard API envelope: { success, data, error }
 */
const unwrap = (response) => response.data?.data ?? response.data

/**
 * Create a new scan for the given domain.
 * POST /api/scan
 * @param {string} domain
 */
export async function createScan(domain) {
  const res = await client.post('/api/scan', { domain })
  return unwrap(res)
}

/**
 * Fetch the full scan object by ID.
 * GET /api/scan/{id}
 * @param {string} id
 */
export async function getScan(id) {
  const res = await client.get(`/api/scan/${id}`)
  return unwrap(res)
}

/**
 * List all scans (most recent first).
 * GET /api/scans
 */
export async function listScans() {
  const res = await client.get('/api/scans')
  return unwrap(res)
}

/**
 * Delete a scan by ID.
 * DELETE /api/scan/{id}
 * @param {string} id
 */
export async function deleteScan(id) {
  const res = await client.delete(`/api/scan/${id}`)
  return unwrap(res)
}

/**
 * Export a scan as a JSON blob download.
 * GET /api/scan/{id}/export
 * @param {string} id
 */
export async function exportScan(id) {
  const res = await client.get(`/api/scan/${id}/export`)
  const data = res.data?.data ?? res.data
  const jsonStr = JSON.stringify(data, null, 2)
  return new Blob([jsonStr], { type: 'application/json' })
}

/**
 * Trigger AI summary regeneration.
 * POST /api/scan/{id}/regenerate-summary
 * @param {string} id
 */
export async function regenerateSummary(id) {
  const res = await client.post(`/api/scan/${id}/regenerate-summary`)
  return unwrap(res)
}

/**
 * Download the PDF report for a scan.
 * GET /api/scan/{id}/report/pdf
 * @param {string} id
 * @param {string} domain  — used for the filename
 */
export async function downloadPdfReport(id, domain) {
  const res = await client.get(`/api/scan/${id}/report/pdf`, {
    responseType: 'blob',
    timeout: 120000,
  })
  return res.data // raw Blob
}

export default client

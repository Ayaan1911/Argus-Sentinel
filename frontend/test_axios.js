import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('[Argus API Error]', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('[Argus API Error] No response received:', error.request)
    } else {
      console.error('[Argus API Error] Request setup failed:', error.message)
    }
    return Promise.reject(error)
  }
)

const unwrap = (response) => response.data?.data ?? response.data

async function listScans() {
  const res = await client.get('/api/scans')
  return unwrap(res)
}

async function run() {
  console.log('Fetching...')
  try {
    const data = await listScans()
    console.log('Result:', data)
    console.log('IsArray?', Array.isArray(data))
  } catch (err) {
    console.error('Caught error:', err)
  }
}

run()

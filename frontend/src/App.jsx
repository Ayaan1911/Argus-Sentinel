import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...')
  const [isOnline, setIsOnline] = useState(false)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setApiStatus('API Online')
          setIsOnline(true)
        }
      })
      .catch(() => {
        setApiStatus('API Offline')
        setIsOnline(false)
      })
  }, [])

  return (
    <div style={{ backgroundColor: '#0a0f1a', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
      <h1 style={{ color: 'white', fontSize: '3rem', margin: '0 0 10px 0' }}>Argus Sentinel</h1>
      <p style={{ color: 'gray', fontSize: '1.2rem', marginBottom: '30px' }}>AI-Powered Cybersecurity Reasoning Engine</p>
      
      <div style={{
        padding: '8px 16px',
        borderRadius: '20px',
        backgroundColor: isOnline ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
        color: isOnline ? '#22c55e' : '#ef4444',
        fontWeight: 'bold'
      }}>
        {apiStatus}
      </div>
    </div>
  )
}

export default App

import { useState } from 'react'
import './App.css'

type HealthStatus = 'idle' | 'checking' | 'healthy' | 'error'

export default function App() {
  const [status, setStatus] = useState<HealthStatus>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  async function checkHealth() {
    setStatus('checking')
    setErrorMsg('')
    try {
      // Proxied by Vite dev server → http://localhost:8000/health
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus(data.status === 'healthy' ? 'healthy' : 'error')
    } catch (err) {
      setStatus('error')
      setErrorMsg(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  const statusColour: Record<HealthStatus, string> = {
    idle: '#888',
    checking: '#d4a017',
    healthy: '#22c55e',
    error: '#ef4444',
  }

  const statusLabel: Record<HealthStatus, string> = {
    idle: 'Not checked yet',
    checking: 'Checking…',
    healthy: '✅ Backend is healthy',
    error: `❌ Error${errorMsg ? ': ' + errorMsg : ''}`,
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 520, margin: '80px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: 8 }}>🏠 RoomGenius AI</h1>
      <p style={{ color: '#555', marginBottom: 32 }}>
        AI-powered room layout assistant — Day 1 MVP
      </p>

      <section style={{ border: '1px solid #e5e7eb', borderRadius: 12, padding: 24, marginBottom: 24 }}>
        <h2 style={{ marginTop: 0 }}>Backend Connection</h2>
        <p style={{ color: statusColour[status], fontWeight: 600, minHeight: 24 }}>
          {statusLabel[status]}
        </p>
        <button
          id="health-check-btn"
          onClick={checkHealth}
          disabled={status === 'checking'}
          style={{
            padding: '10px 24px',
            borderRadius: 8,
            border: 'none',
            background: '#3b82f6',
            color: '#fff',
            fontSize: '1rem',
            cursor: status === 'checking' ? 'not-allowed' : 'pointer',
            opacity: status === 'checking' ? 0.6 : 1,
          }}
        >
          {status === 'checking' ? 'Checking…' : 'Check Backend Health'}
        </button>
      </section>

      <section style={{ border: '1px solid #e5e7eb', borderRadius: 12, padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>Room Input (coming next)</h2>
        <p style={{ color: '#888' }}>Room dimensions and furniture form will be added here.</p>
      </section>
    </main>
  )
}

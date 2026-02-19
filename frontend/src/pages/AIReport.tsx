import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { api } from '../api'

export default function AIReport() {
  const [report, setReport] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'sum' | 'max_per_lab'>('max_per_lab')
  const [includeSoftware, setIncludeSoftware] = useState(true)
  const [studentsFactor, setStudentsFactor] = useState(1.0)

  const generate = () => {
    setLoading(true)
    setError(null)
    setReport(null)
    api.aiReport({ mode, include_software: includeSoftware, students_factor: studentsFactor })
      .then((r) => setReport(r.report))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  return (
    <>
      <h1 style={{ marginTop: 0 }}>AI-пояснительная записка</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
        Генерация текста по обеспеченности через Ollama (локальная модель). Убедитесь, что сервис ollama запущен и модель загружена.
      </p>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Параметры</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            Режим расчёта:
            <select className="input" value={mode} onChange={(e) => setMode(e.target.value as 'sum' | 'max_per_lab')} style={{ width: 'auto' }}>
              <option value="sum">sum</option>
              <option value="max_per_lab">max_per_lab</option>
            </select>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={includeSoftware} onChange={(e) => setIncludeSoftware(e.target.checked)} />
            Включить данные по ПО
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            Коэффициент контингента (students_factor): 
            <input
              type="number"
              className="input"
              min={0.5}
              max={3}
              step={0.1}
              value={studentsFactor}
              onChange={(e) => setStudentsFactor(parseFloat(e.target.value) || 1)}
              style={{ width: 80 }}
            />
          </label>
          <button className="btn btn-primary" onClick={generate} disabled={loading} style={{ alignSelf: 'flex-start' }}>
            {loading ? 'Генерация…' : 'Сформировать записку'}
          </button>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {report && (
        <div className="card report-markdown">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>
      )}
    </>
  )
}

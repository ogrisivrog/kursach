import { useEffect, useState } from 'react'
import { api } from '../api'

const LIMIT = 100

export default function Inventory() {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.inventory>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [item, setItem] = useState('')
  const [location, setLocation] = useState('')
  const [offset, setOffset] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importMsg, setImportMsg] = useState<string | null>(null)

  const load = () => {
    setError(null)
    api.inventory({ item: item || undefined, location: location || undefined, limit: LIMIT, offset })
      .then(setData)
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load(); }, [offset])
  const onFilter = (e: React.FormEvent) => { e.preventDefault(); setOffset(0); load(); }

  const doImport = async () => {
    if (!file) return
    setImporting(true)
    setImportMsg(null)
    try {
      const r = await api.importInventory(file)
      setImportMsg(`Импортировано: ${JSON.stringify(r)}`)
      setFile(null)
      load()
    } catch (e) {
      setImportMsg(`Ошибка: ${(e as Error).message}`)
    } finally {
      setImporting(false)
    }
  }

  return (
    <>
      <h1 style={{ marginTop: 0 }}>Инвентарь</h1>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Импорт CSV</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Формат: item_name, location, qty_available
        </p>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button className="btn btn-primary" onClick={doImport} disabled={!file || importing}>
            {importing ? 'Загрузка…' : 'Импорт'}
          </button>
          {importMsg && <span style={{ fontSize: '0.9rem' }}>{importMsg}</span>}
        </div>
      </div>
      <form onSubmit={onFilter} style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <input className="input" placeholder="Позиция (фильтр)" value={item} onChange={(e) => setItem(e.target.value)} />
        <input className="input" placeholder="Локация (фильтр)" value={location} onChange={(e) => setLocation(e.target.value)} />
        <button type="submit" className="btn">Применить</button>
      </form>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <p style={{ color: 'var(--text-muted)' }}>Всего: {data.total}. Показано: {data.rows.length}.</p>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Позиция</th>
                  <th>Локация</th>
                  <th>Кол-во</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.item_name}</td>
                    <td>{r.location}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.qty_available}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <button className="btn" onClick={() => setOffset((o) => Math.max(0, o - LIMIT))} disabled={offset === 0}>
              Назад
            </button>
            <button className="btn" onClick={() => setOffset((o) => o + LIMIT)} disabled={data.rows.length < LIMIT}>
              Вперёд
            </button>
          </div>
        </>
      )}
    </>
  )
}

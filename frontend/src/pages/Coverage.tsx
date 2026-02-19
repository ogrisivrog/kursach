import { useEffect, useState } from 'react'
import { api } from '../api'

type Mode = 'sum' | 'max_per_lab'

export default function Coverage() {
  const [equipment, setEquipment] = useState<Awaited<ReturnType<typeof api.coverage>> | null>(null)
  const [software, setSoftware] = useState<Awaited<ReturnType<typeof api.softwareCoverage>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [onlyDeficit, setOnlyDeficit] = useState(true)
  const [mode, setMode] = useState<Mode>('max_per_lab')

  const load = () => {
    setError(null)
    api.coverage({ only_deficit: onlyDeficit, mode }).then(setEquipment).catch((e) => setError(e.message))
    api.softwareCoverage({ only_deficit: onlyDeficit, mode }).then(setSoftware).catch(() => setSoftware(null))
  }

  useEffect(() => { load(); }, [onlyDeficit, mode])

  return (
    <>
      <h1 style={{ marginTop: 0 }}>Покрытие</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>
        Сравнение наличия с требованиями. Режим: <strong>sum</strong> — сумма по дисциплинам; <strong>max_per_lab</strong> — по каждой лаборатории берётся максимум, затем сумма.
      </p>
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={onlyDeficit} onChange={(e) => setOnlyDeficit(e.target.checked)} />
          Только дефицит
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          Режим:
          <select className="input" value={mode} onChange={(e) => setMode(e.target.value as Mode)} style={{ width: 'auto' }}>
            <option value="sum">sum</option>
            <option value="max_per_lab">max_per_lab</option>
          </select>
        </label>
        <button className="btn" onClick={load}>Обновить</button>
      </div>
      {error && <div className="error">{error}</div>}
      {equipment && (
        <>
          <h2>Оборудование</h2>
          <div style={{ overflowX: 'auto', marginBottom: 32 }}>
            <table>
              <thead>
                <tr>
                  <th>Позиция</th>
                  <th>Требуется</th>
                  <th>В наличии</th>
                  <th>Дефицит</th>
                </tr>
              </thead>
              <tbody>
                {equipment.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.item_name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.qty_required}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.qty_available}</td>
                    <td>
                      {r.deficit > 0 ? <span className="badge badge-danger">{r.deficit}</span> : <span className="badge badge-success">0</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {software && software.rows.length > 0 && (
        <>
          <h2>ПО (лицензии)</h2>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>ПО</th>
                  <th>Требуется мест</th>
                  <th>В наличии</th>
                  <th>Дефицит</th>
                </tr>
              </thead>
              <tbody>
                {software.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.software_name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.seats_required}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.seats_available}</td>
                    <td>
                      {r.deficit > 0 ? <span className="badge badge-danger">{r.deficit}</span> : <span className="badge badge-success">0</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}

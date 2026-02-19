import { api } from '../api'
import { useState } from 'react'

export default function Reports() {
  const [mode, setMode] = useState<'sum' | 'max_per_lab'>('max_per_lab')
  const [onlyDeficit, setOnlyDeficit] = useState(true)

  const equipmentUrl = api.reportProcurementCsv({ mode, only_deficit: onlyDeficit })
  const softwareUrl = api.reportSoftwareCsv({ mode, only_deficit: onlyDeficit })

  return (
    <>
      <h1 style={{ marginTop: 0 }}>Отчёты</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
        Скачать CSV для закупок (оборудование) и покрытия ПО.
      </p>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Параметры</h3>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            Режим:
            <select className="input" value={mode} onChange={(e) => setMode(e.target.value as 'sum' | 'max_per_lab')} style={{ width: 'auto' }}>
              <option value="sum">sum</option>
              <option value="max_per_lab">max_per_lab</option>
            </select>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={onlyDeficit} onChange={(e) => setOnlyDeficit(e.target.checked)} />
            Только дефицит
          </label>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <a href={equipmentUrl} download="procurement_plan.csv" className="btn btn-primary">
          Скачать отчёт по оборудованию (CSV)
        </a>
        <a href={softwareUrl} download="software_coverage.csv" className="btn btn-primary">
          Скачать отчёт по ПО (CSV)
        </a>
      </div>
    </>
  )
}

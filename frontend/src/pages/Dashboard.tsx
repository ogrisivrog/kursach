import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof api.stats>> | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.stats()
      .then(setStats)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="error">Ошибка: {error}. Проверьте, что бэкенд запущен на порту 8000.</div>
  if (!stats) return <div className="loading">Загрузка…</div>

  const cards = [
    { title: 'Позиций (номенклатура)', value: stats.items, to: '/inventory' },
    { title: 'Локаций', value: stats.locations, to: '/inventory' },
    { title: 'Записей инвентаря', value: stats.inventory_rows, to: '/inventory' },
    { title: 'Всего единиц (инвентарь)', value: stats.qty_sum, to: '/inventory' },
    { title: 'Записей требований', value: stats.requirements_rows, to: '/requirements' },
    { title: 'Всего единиц (требуется)', value: stats.requirements_sum, to: '/requirements' },
  ]

  return (
    <>
      <h1 style={{ marginTop: 0 }}>Дашборд</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
        Сводка по данным МТО. Импорт и отчёты — в соответствующих разделах.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
        {cards.map((c) => (
          <Link key={c.title} to={c.to} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="card" style={{ cursor: 'pointer' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 4 }}>{c.title}</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{c.value}</div>
            </div>
          </Link>
        ))}
      </div>
    </>
  )
}

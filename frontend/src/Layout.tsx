import { NavLink } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Дашборд' },
  { to: '/inventory', label: 'Инвентарь' },
  { to: '/requirements', label: 'Требования' },
  { to: '/coverage', label: 'Покрытие' },
  { to: '/reports', label: 'Отчёты' },
  { to: '/ai-report', label: 'AI-записка' },
]

export default function Layout({ children }: { children?: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: 220,
          borderRight: '1px solid var(--border)',
          padding: '20px 0',
          background: 'var(--bg-card)',
        }}
      >
        <div style={{ padding: '0 16px 16px', borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
          <h1 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>МТО</h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Материально-техническое обеспечение
          </p>
        </div>
        <nav>
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                display: 'block',
                padding: '10px 20px',
                color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                textDecoration: 'none',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                marginLeft: -3,
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: 24, overflow: 'auto' }}>
        {children}
      </main>
    </div>
  )
}

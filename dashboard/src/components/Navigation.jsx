import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'

export default function Navigation() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (e) => {
    if (e.key === 'Enter' && query.trim()) {
      navigate(`/symbol/${query.trim().toUpperCase()}`)
      setQuery('')
    }
  }

  return (
    <nav className="nav">
      <Link to="/" className="nav-logo">
        <div className="nav-logo-icon" />
        <span>Nasdaq AI Predictor</span>
      </Link>

      <ul className="nav-links">
        <li>
          <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
            Dashboard
          </NavLink>
        </li>
      </ul>

      <div className="nav-search">
        <div className="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            className="search-input"
            type="text"
            placeholder="Tìm mã cổ phiếu (Enter ↵)"
            value={query}
            onChange={e => setQuery(e.target.value.toUpperCase())}
            onKeyDown={handleSearch}
          />
        </div>
      </div>
    </nav>
  )
}

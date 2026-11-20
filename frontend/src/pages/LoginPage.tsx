import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../services/api'
import type { AuthStatus, User } from '../services/api'
import { errorMessage } from '../hooks/useToast'
import { btnGold, card, inputStyle, labelStyle } from '../styles/shared'

export default function LoginPage({ status, onSignedIn }: { status: AuthStatus; onSignedIn: (u: User) => void }) {
  const setup = status.setup_required
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    const call = setup
      ? api.auth.setup({ email, name, password, setup_token: token || undefined })
      : api.auth.login(email, password)
    call
      .then(onSignedIn)
      .catch((err) => setError(errorMessage(err, 'Could not sign in.')))
      .finally(() => setBusy(false))
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
      backgroundColor: 'var(--primary)',
      backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
      backgroundSize: '48px 48px',
    }}>
      <form onSubmit={submit} style={{ ...card, width: '100%', maxWidth: 400, padding: '36px 34px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 2, marginBottom: 4 }}>
            <span style={{ fontFamily: 'var(--fd)', fontSize: 26, fontWeight: 300, color: 'var(--link)' }}>O</span>
            <em style={{ fontFamily: 'var(--fd)', fontSize: 26, fontWeight: 300, color: 'var(--gold)' }}>PB</em>
            <span style={{ fontFamily: 'var(--fb)', fontSize: 9, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--mid)', marginLeft: 10 }}>RivalSense</span>
          </div>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 24, fontWeight: 300, color: 'var(--dark)', margin: '8px 0 4px' }}>
            {setup ? 'Create the first admin' : 'Sign in'}
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', margin: 0, lineHeight: 1.5 }}>
            {setup
              ? 'No accounts exist yet. This admin can then invite the rest of the team from Settings.'
              : 'Use the account an admin created for you.'}
          </p>
        </div>

        {setup && !status.setup_allowed ? (
          <p role="alert" style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--status-red)', lineHeight: 1.5, margin: 0 }}>
            The first admin can only be created on the server itself — run{' '}
            <code>python scripts/create_user.py you@company.com "Your Name" --role admin</code>{' '}
            or set <code>RIVALSENSE_SETUP_TOKEN</code>.
          </p>
        ) : (
          <>
            {setup && (
              <label style={labelStyle}>
                Name
                <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} required maxLength={80} autoComplete="name" />
              </label>
            )}
            <label style={labelStyle}>
              Email
              <input style={inputStyle} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" autoFocus />
            </label>
            <label style={labelStyle}>
              Password
              <input
                style={inputStyle} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                minLength={setup ? status.min_password : undefined} autoComplete={setup ? 'new-password' : 'current-password'}
              />
              {setup && <span style={{ fontSize: 11, color: 'var(--mid)', textTransform: 'none', letterSpacing: 0 }}>At least {status.min_password} characters.</span>}
            </label>
            {setup && status.setup_token_required && (
              <label style={labelStyle}>
                Setup token
                <input style={inputStyle} value={token} onChange={(e) => setToken(e.target.value)} required autoComplete="off" />
              </label>
            )}
            {error && <p role="alert" style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--status-red)', margin: 0 }}>{error}</p>}
            <button type="submit" style={{ ...btnGold, opacity: busy ? 0.6 : 1 }} disabled={busy}>
              {busy ? 'Please wait…' : setup ? 'Create admin and sign in' : 'Sign in'}
            </button>
          </>
        )}
      </form>
    </div>
  )
}

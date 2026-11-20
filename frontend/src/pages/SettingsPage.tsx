import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../services/api'
import type { CompetitorSettings, Role, SettingsData, User } from '../services/api'
import Eyebrow from '../components/Eyebrow'
import Spinner from '../components/Spinner'
import Toast from '../components/Toast'
import { refreshCompetitors } from '../components/CompetitorSelect'
import { errorMessage, useToast } from '../hooks/useToast'
import { btnGhost, btnGold, btnNavy, card, heroStyle, inputStyle, labelStyle, thStyle } from '../styles/shared'

const PROVIDERS = ['', 'greenhouse', 'lever', 'ashby', 'workday']

interface Draft {
  name: string
  g2_slug: string
  trustpilot_slug: string
  reddit_keywords: string
  pricing_urls: string
  provider: string
  board: string
  app_store_id: string
  capterra_url: string
}

const EMPTY: Draft = {
  name: '', g2_slug: '', trustpilot_slug: '', reddit_keywords: '', pricing_urls: '',
  provider: '', board: '', app_store_id: '', capterra_url: '',
}

function toDraft(c: CompetitorSettings): Draft {
  return {
    name: c.name,
    g2_slug: c.g2_slug ?? '',
    trustpilot_slug: c.trustpilot_slug ?? '',
    reddit_keywords: (c.reddit_keywords ?? []).join(', '),
    pricing_urls: (c.pricing_urls ?? []).join('\n'),
    provider: c.careers?.provider ?? '',
    board: c.careers?.board ?? '',
    app_store_id: c.app_store_id ? String(c.app_store_id) : '',
    capterra_url: c.capterra_url ?? '',
  }
}

function fromDraft(d: Draft): CompetitorSettings {
  return {
    name: d.name.trim(),
    g2_slug: d.g2_slug.trim(),
    trustpilot_slug: d.trustpilot_slug.trim(),
    reddit_keywords: d.reddit_keywords.split(',').map((k) => k.trim()).filter(Boolean),
    pricing_urls: d.pricing_urls.split('\n').map((u) => u.trim()).filter(Boolean),
    ...(d.provider ? { careers: { provider: d.provider, board: d.board.trim() } } : {}),
    ...(d.app_store_id.trim() ? { app_store_id: Number(d.app_store_id) } : {}),
    ...(d.capterra_url.trim() ? { capterra_url: d.capterra_url.trim() } : {}),
  }
}

function CompetitorForm({ initial, original, onSaved, onCancel, onError }: {
  initial: Draft; original: string | null
  onSaved: () => void; onCancel: () => void; onError: (m: string) => void
}) {
  const [d, setD] = useState<Draft>(initial)
  const [busy, setBusy] = useState(false)
  const set = (k: keyof Draft) => (e: { target: { value: string } }) => setD({ ...d, [k]: e.target.value })

  function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    const body = fromDraft(d)
    const call = original ? api.settings.updateCompetitor(original, body) : api.settings.addCompetitor(body)
    call.then(onSaved).catch((err) => onError(errorMessage(err, 'Could not save.'))).finally(() => setBusy(false))
  }

  const field = (label: string, key: keyof Draft, hint?: string, props: Record<string, unknown> = {}) => (
    <label style={labelStyle}>
      {label}
      <input style={inputStyle} value={d[key]} onChange={set(key)} {...props} />
      {hint && <span style={{ fontSize: 11, color: 'var(--mid)', textTransform: 'none', letterSpacing: 0 }}>{hint}</span>}
    </label>
  )

  return (
    <form onSubmit={submit} style={{ ...card, padding: '22px 26px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, borderLeft: '3px solid var(--gold)' }}>
      {field('Name', 'name', original ? 'Renaming does not move data already stored under the old name.' : undefined, { required: true, maxLength: 60 })}
      {field('Reddit keywords', 'reddit_keywords', 'Comma-separated, e.g. salesforce, sfdc', { required: true })}
      {field('G2 slug', 'g2_slug', 'g2.com/products/<slug>/reviews')}
      {field('Trustpilot domain', 'trustpilot_slug', 'trustpilot.com/review/<domain>')}
      <label style={labelStyle}>
        Pricing pages
        <textarea style={{ ...inputStyle, minHeight: 64, resize: 'vertical' }} value={d.pricing_urls} onChange={set('pricing_urls')} />
        <span style={{ fontSize: 11, color: 'var(--mid)', textTransform: 'none', letterSpacing: 0 }}>One https:// URL per line.</span>
      </label>
      <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: 10 }}>
        <label style={labelStyle}>
          Job board
          <select style={inputStyle} value={d.provider} onChange={set('provider')}>
            {PROVIDERS.map((p) => <option key={p} value={p}>{p || 'none'}</option>)}
          </select>
        </label>
        {field('Board', 'board', d.provider === 'workday' ? 'Career-site URL' : 'Board token from the URL', { disabled: !d.provider })}
      </div>
      {field('App Store id', 'app_store_id', 'Number in apps.apple.com/…/id<number>', { inputMode: 'numeric', pattern: '\\d*' })}
      {field('Capterra reviews URL', 'capterra_url')}
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
        <button type="submit" style={btnGold} disabled={busy}>{busy ? 'Saving…' : original ? 'Save changes' : 'Add competitor'}</button>
        <button type="button" style={btnGhost} onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

function UsersSection({ me, onError, onDone }: { me: User; onError: (m: string) => void; onDone: (m: string) => void }) {
  const [users, setUsers] = useState<User[] | null>(null)
  const [form, setForm] = useState({ email: '', name: '', password: '', role: 'member' as Role })
  const load = useCallback(() => api.auth.users().then(setUsers).catch((e) => onError(errorMessage(e, 'Could not load users.'))), [onError])
  useEffect(() => { load() }, [load])

  function add(e: FormEvent) {
    e.preventDefault()
    api.auth.createUser(form)
      .then((u) => { onDone(`Account created for ${u.email}. Share the password with them securely.`); setForm({ email: '', name: '', password: '', role: 'member' }); load() })
      .catch((err) => onError(errorMessage(err, 'Could not create the account.')))
  }
  function setRole(u: User, role: Role) {
    api.auth.updateUser(u.id, { role }).then(load).catch((err) => onError(errorMessage(err, 'Could not change the role.')))
  }
  function resetPassword(u: User) {
    const password = window.prompt(`New password for ${u.email} (signs them out everywhere):`)
    if (!password) return
    api.auth.updateUser(u.id, { password }).then(() => onDone(`Password changed for ${u.email}.`))
      .catch((err) => onError(errorMessage(err, 'Could not change the password.')))
  }
  function remove(u: User) {
    if (!window.confirm(`Delete the account of ${u.email}?`)) return
    api.auth.deleteUser(u.id).then(load).catch((err) => onError(errorMessage(err, 'Could not delete the account.')))
  }

  return (
    <section>
      <Eyebrow>Team</Eyebrow>
      <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: '0 0 16px' }}>Users</h2>
      {!users ? <Spinner /> : (
        <div style={{ ...card, overflow: 'hidden', marginBottom: 16 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ backgroundColor: 'var(--primary)' }}>
              <th style={thStyle}>Name</th><th style={thStyle}>Email</th><th style={thStyle}>Role</th><th style={thStyle}>Last sign-in</th><th style={thStyle} />
            </tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderTop: '1px solid var(--primary-10)' }}>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }}>{u.name}{u.id === me.id && ' (you)'}</td>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 13, color: 'var(--dark)' }}>{u.email}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <select style={{ ...inputStyle, width: 'auto' }} value={u.role} disabled={u.id === me.id}
                            onChange={(e) => setRole(u, e.target.value as Role)} aria-label={`Role of ${u.email}`}>
                      <option value="member">member</option><option value="admin">admin</option>
                    </select>
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }}>{u.last_login?.slice(0, 16).replace('T', ' ') ?? 'never'}</td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <button style={btnGhost} onClick={() => resetPassword(u)}>Reset password</button>{' '}
                    {u.id !== me.id && <button style={{ ...btnGhost, color: 'var(--status-red)' }} onClick={() => remove(u)}>Delete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <form onSubmit={add} style={{ ...card, padding: '18px 22px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12, alignItems: 'end' }}>
        <label style={labelStyle}>Name<input style={inputStyle} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required maxLength={80} /></label>
        <label style={labelStyle}>Email<input style={inputStyle} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
        <label style={labelStyle}>Initial password<input style={inputStyle} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={10} autoComplete="new-password" /></label>
        <label style={labelStyle}>Role
          <select style={inputStyle} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
            <option value="member">member</option><option value="admin">admin</option>
          </select>
        </label>
        <button type="submit" style={btnNavy}>Add user</button>
      </form>
    </section>
  )
}

export default function SettingsPage({ user }: { user: User | null }) {
  const [data, setData] = useState<SettingsData | null>(null)
  const [editing, setEditing] = useState<string | 'new' | null>(null)
  const [features, setFeatures] = useState('')
  const { toast, showToast } = useToast()
  const isAdmin = user?.role === 'admin'
  const onError = useCallback((m: string) => showToast(m, 'error'), [showToast])
  const onDone = useCallback((m: string) => showToast(m, 'success'), [showToast])

  const load = useCallback(() => api.settings.get().then((s) => { setData(s); setFeatures(s.own_features.join('\n')) })
    .catch((e) => onError(errorMessage(e, 'Could not load settings.'))), [onError])
  useEffect(() => { load() }, [load])

  function saved(message: string) {
    setEditing(null)
    refreshCompetitors()
    onDone(message)
    load()
  }

  function remove(name: string) {
    if (!window.confirm(`Remove ${name}? Data already collected for it stays in the database.`)) return
    api.settings.deleteCompetitor(name).then(() => saved(`${name} removed.`)).catch((e) => onError(errorMessage(e, 'Could not remove.')))
  }

  function saveFeatures() {
    api.settings.setFeatures(features.split('\n')).then((r) => { setFeatures(r.own_features.join('\n')); onDone('Your features were saved.') })
      .catch((e) => onError(errorMessage(e, 'Could not save features.')))
  }

  return (
    <div>
      <div style={heroStyle}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto' }}>
          <Eyebrow light>Settings</Eyebrow>
          <h1 style={{ fontFamily: 'var(--fd)', fontSize: 36, fontWeight: 300, color: '#fff', margin: '0 0 6px' }}>
            Competitors &amp; <em style={{ fontStyle: 'italic', color: 'var(--gold-light)' }}>team</em>
          </h1>
          <p style={{ fontFamily: 'var(--fb)', fontSize: 13, color: 'rgba(255,255,255,0.45)', maxWidth: 600 }}>
            Who you track, which of your features to highlight, and who can sign in.
            {!isAdmin && ' Only admins can change these settings.'}
          </p>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--light)', minHeight: '60vh' }}>
        <div style={{ maxWidth: 'var(--max-width-dashboard)', margin: '0 auto', padding: '44px 48px', display: 'flex', flexDirection: 'column', gap: 36 }}>
          {toast && <Toast message={toast.msg} type={toast.type} />}
          {!data ? <Spinner /> : (
            <>
              <section>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12, marginBottom: 16 }}>
                  <div>
                    <Eyebrow>Tracking</Eyebrow>
                    <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: 0 }}>Competitors</h2>
                  </div>
                  {isAdmin && editing === null && <button style={btnGold} onClick={() => setEditing('new')}>Add competitor</button>}
                </div>
                {editing === 'new' && (
                  <div style={{ marginBottom: 16 }}>
                    <CompetitorForm initial={EMPTY} original={null} onSaved={() => saved('Competitor added. Run ingestion to collect its data.')} onCancel={() => setEditing(null)} onError={onError} />
                  </div>
                )}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {data.competitors.map((c) => editing === c.name ? (
                    <CompetitorForm key={c.name} initial={toDraft(c)} original={c.name} onSaved={() => saved(`${c.name} saved.`)} onCancel={() => setEditing(null)} onError={onError} />
                  ) : (
                    <div key={c.name} style={{ ...card, padding: '16px 22px', display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                      <div>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 14, fontWeight: 600, color: 'var(--link)' }}>{c.name}</div>
                        <div style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', marginTop: 4 }}>
                          {[c.g2_slug && `G2 ${c.g2_slug}`, c.trustpilot_slug && `Trustpilot ${c.trustpilot_slug}`,
                            `Reddit: ${c.reddit_keywords.join(', ')}`, c.pricing_urls?.length && `${c.pricing_urls.length} pricing page(s)`,
                            c.careers && `${c.careers.provider} jobs`, c.app_store_id && 'App Store', c.capterra_url && 'Capterra']
                            .filter(Boolean).join(' · ')}
                        </div>
                      </div>
                      {isAdmin && editing === null && (
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button style={btnGhost} onClick={() => setEditing(c.name)}>Edit</button>
                          <button style={{ ...btnGhost, color: 'var(--status-red)' }} onClick={() => remove(c.name)}>Remove</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <Eyebrow>Your product</Eyebrow>
                <h2 style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 300, color: 'var(--dark)', margin: '0 0 6px' }}>Own features</h2>
                <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)', margin: '0 0 12px' }}>
                  Feature requests in competitor reviews that match these are flagged as your advantage (Wish Miner, Battlecards). One per line.
                </p>
                <div style={{ ...card, padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <textarea style={{ ...inputStyle, minHeight: 160, resize: 'vertical' }} value={features}
                            onChange={(e) => setFeatures(e.target.value)} readOnly={!isAdmin} aria-label="Own features, one per line" />
                  {isAdmin && <div><button style={btnNavy} onClick={saveFeatures}>Save features</button></div>}
                </div>
              </section>

              {isAdmin && user && user.id !== 0 && <UsersSection me={user} onError={onError} onDone={onDone} />}
              {isAdmin && user?.id === 0 && (
                <p style={{ fontFamily: 'var(--fb)', fontSize: 12, color: 'var(--mid)' }}>
                  Sign-in is turned off (AUTH_DISABLED=true), so there are no user accounts to manage.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

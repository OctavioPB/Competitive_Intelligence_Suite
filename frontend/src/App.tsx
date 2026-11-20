import { useCallback, useEffect, useState } from 'react'
import Nav from './components/Nav'
import Footer from './components/Footer'
import DataSourceBanner from './components/DataSourceBanner'
import { useTheme } from './hooks/useTheme'
import HomePage from './pages/HomePage'
import PainPointRadarPage from './pages/PainPointRadarPage'
import SentimentTimelinePage from './pages/SentimentTimelinePage'
import FeatureWishMinerPage from './pages/FeatureWishMinerPage'
import BattlecardPage from './pages/BattlecardPage'
import TriggerAlertsPage from './pages/TriggerAlertsPage'
import HotProspectPage from './pages/HotProspectPage'
import InfoPage from './pages/InfoPage'
import ChurnIntelligencePage from './pages/ChurnIntelligencePage'
import DigestPage from './pages/DigestPage'
import OutreachComposerPage from './pages/OutreachComposerPage'
import MarketSignalsPage from './pages/MarketSignalsPage'
import ChangesPage from './pages/ChangesPage'
import ComparePage from './pages/ComparePage'
import AskPage from './pages/AskPage'
import WinLossPage from './pages/WinLossPage'
import SettingsPage from './pages/SettingsPage'
import LoginPage from './pages/LoginPage'
import Spinner from './components/Spinner'
import { api, UNAUTHORIZED_EVENT } from './services/api'
import type { AuthStatus, User } from './services/api'

export type Page =
  | 'home'
  | 'pain-radar'
  | 'sentiment'
  | 'wish-miner'
  | 'battlecard'
  | 'alerts'
  | 'prospects'
  | 'info'
  | 'churn'
  | 'digest'
  | 'outreach'
  | 'signals'
  | 'changes'
  | 'compare'
  | 'ask'
  | 'winloss'
  | 'settings'

function renderPage(page: Page, onNavigate: (p: Page) => void, user: User | null) {
  switch (page) {
    case 'home':
      return <HomePage onNavigate={onNavigate} />
    case 'pain-radar':
      return <PainPointRadarPage />
    case 'sentiment':
      return <SentimentTimelinePage />
    case 'wish-miner':
      return <FeatureWishMinerPage />
    case 'battlecard':
      return <BattlecardPage />
    case 'alerts':
      return <TriggerAlertsPage />
    case 'prospects':
      return <HotProspectPage onNavigate={onNavigate} />
    case 'info':
      return <InfoPage />
    case 'churn':
      return <ChurnIntelligencePage />
    case 'digest':
      return <DigestPage />
    case 'outreach':
      return <OutreachComposerPage />
    case 'signals':
      return <MarketSignalsPage />
    case 'changes':
      return <ChangesPage />
    case 'compare':
      return <ComparePage onNavigate={onNavigate} />
    case 'ask':
      return <AskPage />
    case 'winloss':
      return <WinLossPage />
    case 'settings':
      return <SettingsPage user={user} />
  }
}

export default function App() {
  const [page, setPage] = useState<Page>('home')
  const { theme, toggleTheme } = useTheme()
  const [auth, setAuth] = useState<AuthStatus | null>(null)
  const [authError, setAuthError] = useState(false)

  const checkSession = useCallback(() => {
    api.auth.status().then((s) => { setAuth(s); setAuthError(false) }).catch(() => setAuthError(true))
  }, [])
  useEffect(() => { checkSession() }, [checkSession])

  // Any 401 (session expired, signed out elsewhere) returns to the sign-in screen.
  useEffect(() => {
    const onUnauthorized = () => setAuth((a) => (a && a.auth_enabled ? { ...a, user: null } : a))
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [])

  function handleSignOut() {
    api.auth.logout().finally(() => { setPage('home'); checkSession() })
  }

  if (authError) {
    return (
      <div style={{ padding: 48, fontFamily: 'var(--fb)', color: 'var(--dark)' }}>
        Cannot reach the RivalSense API. Is the backend running?{' '}
        <button onClick={checkSession} style={{ marginLeft: 8 }}>Retry</button>
      </div>
    )
  }
  if (!auth) {
    return <div style={{ padding: 48 }}><Spinner /></div>
  }
  if (auth.auth_enabled && !auth.user) {
    return <LoginPage status={auth} onSignedIn={(user) => setAuth({ ...auth, user, setup_required: false })} />
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Nav
        currentPage={page}
        onNavigate={setPage}
        theme={theme}
        onToggleTheme={toggleTheme}
        user={auth.user}
        authEnabled={auth.auth_enabled}
        onSignOut={handleSignOut}
      />
      <DataSourceBanner />
      <main style={{ flex: 1 }}>
        {renderPage(page, setPage, auth.user)}
      </main>
      <Footer />
    </div>
  )
}

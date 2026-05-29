import { useState } from 'react'
import Nav from './components/Nav'
import Footer from './components/Footer'
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

function renderPage(page: Page, onNavigate: (p: Page) => void) {
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
  }
}

export default function App() {
  const [page, setPage] = useState<Page>('home')
  const { theme, toggleTheme } = useTheme()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Nav
        currentPage={page}
        onNavigate={setPage}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <main style={{ flex: 1 }}>
        {renderPage(page, setPage)}
      </main>
      <Footer />
    </div>
  )
}

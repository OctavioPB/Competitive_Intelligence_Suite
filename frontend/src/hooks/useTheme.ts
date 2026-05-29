import { useState, useEffect } from 'react'

type Theme = 'light' | 'dark'

function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem('rivalsense-theme') as Theme | null
  return stored === 'dark' ? 'dark' : 'light'
}

export function useTheme(): { theme: Theme; toggleTheme: () => void } {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    applyTheme(theme)
    localStorage.setItem('rivalsense-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return { theme, toggleTheme }
}

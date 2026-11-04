import { useEffect, useLayoutEffect, useState } from 'react'
import { AccessibilityContext } from './accessibility-context.js'
import { PREFERENCES_KEY, applyPreferences, normalizePreferences, readPreferences } from './accessibility.js'

export default function AccessibilityProvider({ children }) {
  const [preferences, setPreferences] = useState(() => readPreferences())
  const [saveError, setSaveError] = useState(false)
  useLayoutEffect(() => { applyPreferences(document.documentElement, preferences) }, [preferences])
  useEffect(() => {
    const sync = event => { if (event.key === PREFERENCES_KEY || event.key === null) setPreferences(readPreferences()) }
    window.addEventListener('storage', sync)
    return () => window.removeEventListener('storage', sync)
  }, [])
  function update(change) {
    const next = normalizePreferences({ ...preferences, ...change })
    setPreferences(next)
    try { localStorage.setItem(PREFERENCES_KEY, JSON.stringify(next)); setSaveError(false) }
    catch { setSaveError(true) }
  }
  return <AccessibilityContext.Provider value={{ preferences, update, saveError }}>{children}</AccessibilityContext.Provider>
}


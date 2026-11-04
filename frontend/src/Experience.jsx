import { useEffect, useState } from 'react'
import App from './App.jsx'
import Landing from './Landing.jsx'
import AccessibilityProvider from './AccessibilityProvider.jsx'
import AccessibilityWidget from './AccessibilityWidget.jsx'
import './brand.css'
import './accessibility.css'

export default function Experience() {
  const [hash, setHash] = useState(location.hash)
  const isAdmin = hash === '#login' || hash === '#gestao'
  useEffect(() => {
    const change = () => setHash(location.hash)
    window.addEventListener('hashchange', change)
    return () => window.removeEventListener('hashchange', change)
  }, [])
  useEffect(() => { if (isAdmin) window.scrollTo(0, 0) }, [isAdmin])
  return <AccessibilityProvider>{isAdmin ? <>
    <div className="return-bar"><a className="history-button" href="#topo">← Nossa História</a><span>Baby Belo Ateliê</span></div>
    <App />
  </> : <Landing />}<AccessibilityWidget /></AccessibilityProvider>
}


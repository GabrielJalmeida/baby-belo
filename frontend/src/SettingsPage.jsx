import AccessibilityControls from './AccessibilityControls.jsx'

export default function SettingsPage() {
  return <section className="data-panel accessibility-panel" aria-labelledby="accessibility-title">
    <span className="eyebrow">ACESSIBILIDADE</span>
    <h2 id="accessibility-title">Do seu jeito, com mais conforto.</h2>
    <p>Estas preferências valem para todas as telas e ficam salvas neste navegador.</p>
    <AccessibilityControls />
  </section>
}

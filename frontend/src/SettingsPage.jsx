import { useContext } from 'react'
import { AccessibilityContext } from './accessibility-context.js'
import { defaultPreferences } from './accessibility.js'

export default function SettingsPage() {
  const { preferences, update, saveError } = useContext(AccessibilityContext)
  return <section className="data-panel accessibility-panel" aria-labelledby="accessibility-title">
    <span className="eyebrow">ACESSIBILIDADE</span>
    <h2 id="accessibility-title">Do seu jeito, com mais conforto.</h2>
    <p>Estas preferências valem para todas as telas e ficam salvas neste navegador.</p>
    <div className="preference-list">
      <label className="preference-row"><span><strong>Modo noturno</strong><small>Cores suaves e fundo escuro para ambientes com pouca luz.</small></span><input type="checkbox" role="switch" checked={preferences.dark} onChange={event => update({ dark: event.target.checked })}/></label>
      <label className="preference-row"><span><strong>Tamanho da fonte</strong><small>Aumente os textos para facilitar a leitura.</small></span><select aria-label="Tamanho da fonte" value={preferences.fontSize} onChange={event => update({ fontSize: event.target.value })}><option value="normal">Normal</option><option value="large">Maior</option><option value="larger">Muito maior</option></select></label>
      <label className="preference-row"><span><strong>Alto contraste</strong><small>Realce textos, bordas e botões.</small></span><input type="checkbox" role="switch" checked={preferences.contrast} onChange={event => update({ contrast: event.target.checked })}/></label>
      <label className="preference-row"><span><strong>Sublinhar links</strong><small>Identifique os links com mais facilidade.</small></span><input type="checkbox" role="switch" checked={preferences.underline} onChange={event => update({ underline: event.target.checked })}/></label>
    </div>
    <p className="preference-status" role="status">{saveError ? 'As preferências estão aplicadas, mas o navegador bloqueou o salvamento. Elas serão perdidas ao fechar a página.' : 'Preferências salvas automaticamente.'}</p>
    <button className="button-secondary" type="button" onClick={() => update(defaultPreferences)}>Restaurar aparência padrão</button>
  </section>
}


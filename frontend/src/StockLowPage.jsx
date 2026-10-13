import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import './StockLowPage.css'

function formatQuantity(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 4 }).format(number)
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" strokeWidth="1.7" />
      <path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

function WarningIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 22 20H2L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M12 9v5m0 3h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

export default function StockLowPage({ companyId, onLogout, onNavigateProducts, onNavigateMovements }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadLowStock() {
      try {
        const result = await api.lowStockAll(companyId)
        if (cancelled) return
        setItems(Array.isArray(result) ? result : [])
        setError('')
      } catch (loadError) {
        if (cancelled) return
        if (loadError instanceof ApiError && loadError.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setError(loadError.message || 'Não foi possível carregar os itens com estoque baixo.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadLowStock()
    return () => { cancelled = true }
  }, [companyId, onLogout, reloadKey])

  const filteredItems = useMemo(() => {
    const query = search.trim().toLocaleLowerCase('pt-BR')
    if (!query) return items
    return items.filter((item) => (
      (item.item_nome ?? '').toLocaleLowerCase('pt-BR').includes(query)
      || (item.unidade_nome ?? '').toLocaleLowerCase('pt-BR').includes(query)
      || (item.unidade_simbolo ?? '').toLocaleLowerCase('pt-BR').includes(query)
      || String(item.item_id).includes(query)
    ))
  }, [items, search])

  function retry() {
    setLoading(true)
    setError('')
    setReloadKey((value) => value + 1)
  }

  return (
    <section className="stock-low-page" aria-labelledby="stock-low-title">
      <div className="stock-low-summary-row">
        <div className="stock-low-summary" role="status" aria-live="polite">
          <span className="stock-low-summary-icon"><WarningIcon /></span>
          <div>
            <strong>{loading ? 'Consultando estoque…' : `${items.length} ${items.length === 1 ? 'item precisa' : 'itens precisam'} de atenção`}</strong>
            <p>Itens retornados pela consulta oficial de estoque baixo da API.</p>
          </div>
        </div>
        <div className="stock-low-actions">
          <button className="button-secondary" type="button" onClick={retry} disabled={loading}>
            Atualizar lista
          </button>
          <button className="button-primary" type="button" onClick={onNavigateMovements}>
            Registrar movimentação
          </button>
        </div>
      </div>

      <div className="stock-low-toolbar">
        <label className="stock-low-search">
          <SearchIcon />
          <span className="sr-only">Buscar item com estoque baixo</span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por produto, unidade ou ID…"
          />
          {search && (
            <button type="button" onClick={() => setSearch('')} aria-label="Limpar busca">×</button>
          )}
        </label>
        <span className="stock-low-count">{filteredItems.length} {filteredItems.length === 1 ? 'resultado' : 'resultados'}</span>
      </div>

      {error && (
        <div className="stock-low-feedback" role="alert">
          <div><strong>Não foi possível carregar o estoque baixo.</strong><p>{error}</p></div>
          <button className="button-secondary" type="button" onClick={retry}>Tentar novamente</button>
        </div>
      )}

      {loading && !error && (
        <div className="stock-low-state" aria-label="Carregando estoque baixo">
          <span className="stock-low-spinner" />
          <strong>Consultando os saldos</strong>
          <p>Estamos buscando todos os resultados disponíveis da empresa ativa.</p>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="stock-low-state">
          <span className="stock-low-state-icon"><WarningIcon /></span>
          <strong>Nenhum item abaixo do mínimo</strong>
          <p>O estoque baixo está vazio. Quando um saldo atingir a regra de mínimo definida no cadastro, o item aparecerá aqui.</p>
          <button className="button-secondary" type="button" onClick={onNavigateProducts}>Consultar produtos</button>
        </div>
      )}

      {!loading && !error && items.length > 0 && filteredItems.length === 0 && (
        <div className="stock-low-state compact">
          <strong>Nenhum resultado para essa busca</strong>
          <p>Tente outro nome, símbolo de unidade ou ID.</p>
          <button className="button-secondary" type="button" onClick={() => setSearch('')}>Limpar busca</button>
        </div>
      )}

      {!loading && !error && filteredItems.length > 0 && (
        <div className="stock-low-table-wrap">
          <table className="stock-low-table">
            <thead>
              <tr><th>Produto</th><th>Saldo atual</th><th>Estoque mínimo</th><th>Diferença para o mínimo</th><th>Status</th></tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const current = Number(item.saldo_atual)
                const minimum = Number(item.estoque_minimo)
                const deficit = Number.isFinite(current) && Number.isFinite(minimum) ? Math.max(0, minimum - current) : null
                const unit = item.unidade_simbolo || item.unidade_nome || 'unid.'
                return (
                  <tr key={item.item_id}>
                    <td>
                      <div className="stock-low-product">
                        <span className="stock-low-product-symbol">{(item.item_nome || 'P').trim().charAt(0).toUpperCase()}</span>
                        <span><strong>{item.item_nome}</strong><small>Item #{item.item_id} · {item.unidade_nome || 'Unidade não informada'}</small></span>
                      </div>
                    </td>
                    <td className="stock-low-number"><strong>{formatQuantity(item.saldo_atual)}</strong><small>{unit}</small></td>
                    <td className="stock-low-number">{formatQuantity(item.estoque_minimo)}<small>{unit}</small></td>
                    <td className="stock-low-number stock-low-deficit">{deficit === null ? '—' : formatQuantity(deficit)}<small>{unit}</small></td>
                    <td><span className="stock-low-badge"><span />Estoque baixo</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="stock-low-note">O saldo é calculado e validado pelo backend. Para repor ou corrigir quantidades, registre uma movimentação; não edite o saldo diretamente.</p>
    </section>
  )
}

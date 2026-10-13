import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import './InventoryPage.css'

function formatQuantity(value) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 4 }).format(number)
}

function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

function parseQuantity(value) {
  const normalized = String(value ?? '').trim().replace(/\s/g, '').replace(',', '.')
  if (!normalized || !/^(?:\d+\.?\d*|\.\d+)$/.test(normalized)) return null
  const number = Number(normalized)
  return Number.isFinite(number) ? number : null
}

function statusLabel(status) {
  if (status === 'ABERTO') return 'Em andamento'
  if (status === 'CONCLUIDO') return 'Concluído'
  if (status === 'CANCELADO') return 'Cancelado'
  return status || 'Desconhecido'
}

function statusClass(status) {
  if (status === 'ABERTO') return 'inventory-status-open'
  if (status === 'CONCLUIDO') return 'inventory-status-done'
  return 'inventory-status-cancelled'
}

function EmptyPanel({ title, description }) {
  return (
    <div className="inventory-empty">
      <span className="inventory-empty-mark" aria-hidden="true">↗</span>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
}

export default function InventoriesPage({ companyId, onLogout, canWrite = true }) {
  const [inventories, setInventories] = useState([])
  const [items, setItems] = useState([])
  const [units, setUnits] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState(null)
  const [countDraft, setCountDraft] = useState({})
  const [observation, setObservation] = useState('')
  const [initialLoading, setInitialLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [detailError, setDetailError] = useState('')
  const [actionError, setActionError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [creating, setCreating] = useState(false)
  const [savingItemId, setSavingItemId] = useState(null)
  const [busyAction, setBusyAction] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadLists() {
      setInitialLoading(true)
      setLoadError('')
      try {
        const [inventoryRows, itemRows, unitRows] = await Promise.all([
          api.inventories(companyId),
          api.items(companyId),
          api.units(companyId),
        ])
        if (cancelled) return
        const safeInventories = Array.isArray(inventoryRows) ? inventoryRows : []
        setInventories(safeInventories)
        setItems(Array.isArray(itemRows) ? itemRows : [])
        setUnits(Array.isArray(unitRows) ? unitRows : [])
        setSelectedId((current) => {
          if (current && safeInventories.some((row) => String(row.id) === current)) return current
          const preferred = safeInventories.find((row) => row.status === 'ABERTO') ?? safeInventories[0]
          return preferred ? String(preferred.id) : ''
        })
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setLoadError(error.message || 'Não foi possível carregar os inventários.')
      } finally {
        if (!cancelled) setInitialLoading(false)
      }
    }

    void loadLists()
    return () => { cancelled = true }
  }, [companyId, onLogout, reloadKey])

  useEffect(() => {
    let cancelled = false
    if (!selectedId) return undefined

    async function loadDetail() {
      setDetailLoading(true)
      setDetailError('')
      try {
        // O detalhe retorna o snapshot inteiro, mesmo quando possui mais de 50 itens.
        const result = await api.inventoryDetail(companyId, Number(selectedId))
        if (cancelled) return
        setDetail(result)
        const drafts = {}
        for (const row of result.itens ?? []) {
          drafts[row.item_id] = row.quantidade_contada === null || row.quantidade_contada === undefined
            ? ''
            : String(row.quantidade_contada).replace('.', ',')
        }
        setCountDraft(drafts)
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setDetailError(error.message || 'Não foi possível abrir este inventário.')
        setDetail(null)
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    }

    void loadDetail()
    return () => { cancelled = true }
  }, [companyId, selectedId, onLogout])

  // Não exibe o detalhe anterior enquanto outra seleção está carregando.
  const selectedDetail = selectedId && String(detail?.id) === selectedId ? detail : null
  const selectedDetailError = selectedId ? detailError : ''
  const itemById = useMemo(() => new Map(items.map((item) => [item.id, item])), [items])
  const unitById = useMemo(() => new Map(units.map((unit) => [unit.id, unit])), [units])
  const openInventory = inventories.find((item) => item.status === 'ABERTO')
  const inventoryRows = selectedDetail?.itens ?? []
  const uncountedCount = inventoryRows.filter((row) => row.quantidade_contada === null || row.quantidade_contada === undefined).length
  const countedCount = inventoryRows.length - uncountedCount
  const progress = inventoryRows.length ? Math.round((countedCount / inventoryRows.length) * 100) : 0
  const isOpen = selectedDetail?.status === 'ABERTO'

  async function createInventory(event) {
    event.preventDefault()
    if (creating || !canWrite || !items.length) return
    setCreating(true)
    setActionError('')
    setFeedback('')
    try {
      const created = await api.createInventory(companyId, { observacao: observation.trim() || null })
      setObservation('')
      setSelectedId(String(created.id))
      setFeedback(`Inventário #${created.id} aberto.`)
      setReloadKey((value) => value + 1)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setActionError(error.message || 'Não foi possível abrir o inventário.')
    } finally {
      setCreating(false)
    }
  }

  async function saveCount(row) {
    if (!canWrite || !selectedDetail || !isOpen || savingItemId !== null) return
    setActionError('')
    setFeedback('')
    const raw = countDraft[row.item_id] ?? ''
    const quantity = parseQuantity(raw)
    if (quantity === null || quantity < 0) {
      setActionError('Informe uma quantidade válida, igual ou maior que zero.')
      return
    }
    const item = itemById.get(row.item_id)
    const unit = item ? unitById.get(item.unidade_id) : null
    if (unit && !unit.permite_decimal && !Number.isInteger(quantity)) {
      setActionError(`A unidade ${unit.nome} não permite quantidade fracionária.`)
      return
    }

    setSavingItemId(row.item_id)
    try {
      const updated = await api.recordInventoryCount(companyId, selectedDetail.id, row.item_id, quantity)
      setDetail((previous) => previous && String(previous.id) === String(selectedDetail.id) ? {
        ...previous,
        itens: (previous.itens ?? []).map((current) => current.item_id === row.item_id ? updated : current),
      } : previous)
      setCountDraft((previous) => ({ ...previous, [row.item_id]: String(quantity).replace('.', ',') }))
      setFeedback(`Contagem salva para ${item?.nome || `item #${row.item_id}`}.`)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setActionError(error.message || 'Não foi possível salvar a contagem. Confira a conexão antes de tentar novamente.')
    } finally {
      setSavingItemId(null)
    }
  }

  async function runInventoryAction(action) {
    if (!canWrite || !selectedDetail || busyAction || selectedDetail.status !== 'ABERTO') return
    if (action === 'complete' && uncountedCount > 0) {
      setActionError('Registre a contagem de todos os itens antes de concluir o inventário.')
      return
    }
    const confirmation = action === 'complete'
      ? `Concluir o inventário #${selectedDetail.id}? As diferenças encontradas poderão gerar ajustes de estoque.`
      : `Cancelar o inventário #${selectedDetail.id}? Esta ação não poderá ser desfeita.`
    if (!window.confirm(confirmation)) return

    setBusyAction(action)
    setActionError('')
    setFeedback('')
    try {
      const updated = action === 'complete'
        ? await api.completeInventory(companyId, selectedDetail.id)
        : await api.cancelInventory(companyId, selectedDetail.id)
      setDetail((previous) => previous && String(previous.id) === String(updated.id) ? { ...previous, ...updated } : previous)
      setInventories((previous) => previous.map((row) => row.id === updated.id ? { ...row, ...updated } : row))
      setFeedback(action === 'complete' ? 'Inventário concluído com sucesso.' : 'Inventário cancelado.')
      setReloadKey((value) => value + 1)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setActionError(error.message || 'Não foi possível concluir a operação.')
    } finally {
      setBusyAction('')
    }
  }

  function retry() {
    setLoadError('')
    setReloadKey((value) => value + 1)
  }

  return (
    <div className="inventory-page">
      {loadError && (
        <div className="inventory-alert inventory-alert-error" role="alert">
          <div><strong>Não foi possível carregar os dados.</strong><p>{loadError}</p></div>
          <button type="button" className="inventory-button inventory-button-secondary" onClick={retry}>Tentar novamente</button>
        </div>
      )}
      {actionError && <div className="inventory-alert inventory-alert-error" role="alert"><p>{actionError}</p><button type="button" className="inventory-alert-dismiss" aria-label="Fechar aviso" onClick={() => setActionError('')}>×</button></div>}
      {feedback && <div className="inventory-alert inventory-alert-success" role="status"><p>{feedback}</p><button type="button" className="inventory-alert-dismiss" aria-label="Fechar aviso" onClick={() => setFeedback('')}>×</button></div>}

      <section className="inventory-create-panel">
        <div className="inventory-section-title">
          <div><span className="inventory-section-kicker">CONTAGEM FÍSICA</span><h2>Acompanhe os inventários</h2><p>Compare a quantidade real com o saldo registrado sem editar o saldo diretamente.</p></div>
          {openInventory && <span className="inventory-open-note">Há um inventário aberto</span>}
        </div>
        <form className="inventory-create-form" onSubmit={createInventory}>
          <label className="inventory-field inventory-observation-field">
            <span>Observação do novo inventário <small>Opcional</small></span>
            <input value={observation} onChange={(event) => setObservation(event.target.value)} maxLength={5000} placeholder="Ex.: contagem mensal do depósito" disabled={!canWrite || creating || Boolean(openInventory)} />
          </label>
          <button className="inventory-button inventory-button-primary" type="submit" disabled={!canWrite || creating || initialLoading || !items.length || Boolean(openInventory)}>
            {creating ? 'Abrindo...' : 'Abrir inventário'}
          </button>
        </form>
        {!canWrite && <p className="inventory-inline-note">Seu perfil permite consultar inventários, mas não criar ou alterar contagens.</p>}
        {!initialLoading && items.length === 0 && <p className="inventory-inline-note">Cadastre pelo menos um item ativo antes de abrir um inventário.</p>}
        {openInventory && <p className="inventory-inline-note">A empresa pode ter somente um inventário aberto por vez. Continue a contagem no inventário selecionado abaixo.</p>}
      </section>

      <section className="inventory-layout">
        <div className="inventory-list-panel">
          <div className="inventory-panel-heading"><div><h2>Histórico de inventários</h2><p>{inventories.length} registro{inventories.length === 1 ? '' : 's'}</p></div><button type="button" className="inventory-icon-button" onClick={retry} disabled={initialLoading} aria-label="Atualizar lista" title="Atualizar lista">↻</button></div>
          {initialLoading ? (
            <div className="inventory-skeleton" aria-label="Carregando inventários"><span /><span /><span /></div>
          ) : inventories.length === 0 ? (
            <EmptyPanel title="Nenhum inventário ainda" description="Abra um inventário para iniciar a contagem física dos itens ativos." />
          ) : (
            <div className="inventory-list" role="list" aria-label="Inventários da empresa">
              {inventories.map((row) => (
                <button type="button" role="listitem" key={row.id} className={`inventory-list-card ${String(row.id) === selectedId ? 'is-selected' : ''}`} onClick={() => { setSelectedId(String(row.id)); setActionError(''); setFeedback('') }} aria-current={String(row.id) === selectedId ? 'true' : undefined}>
                  <span className="inventory-card-number">#{row.id}</span>
                  <span className="inventory-card-main"><strong>{row.observacao?.trim() || `Inventário #${row.id}`}</strong><small>Aberto em {formatDateTime(row.iniciado_em)}</small></span>
                  <span className={`inventory-status ${statusClass(row.status)}`}>{statusLabel(row.status)}</span>
                </button>
              ))}
            </div>
          )}
          <p className="inventory-list-note">O histórico é preservado após a conclusão ou o cancelamento.</p>
        </div>

        <div className="inventory-detail-panel">
          {detailLoading ? (
            <div className="inventory-detail-loading"><span /><span /><span /><span /></div>
          ) : selectedDetailError ? (
            <div className="inventory-detail-error" role="alert"><strong>Não foi possível abrir o inventário.</strong><p>{selectedDetailError}</p><button type="button" className="inventory-button inventory-button-secondary" onClick={retry}>Atualizar dados</button></div>
          ) : !selectedDetail ? (
            <EmptyPanel title="Selecione um inventário" description="Escolha um registro do histórico para consultar a contagem e as diferenças." />
          ) : (
            <>
              <div className="inventory-detail-heading">
                <div><span className="inventory-section-kicker">DETALHE DO INVENTÁRIO</span><h2>Inventário #{selectedDetail.id}</h2><p>Iniciado em {formatDateTime(selectedDetail.iniciado_em)}</p></div>
                <span className={`inventory-status ${statusClass(selectedDetail.status)}`}>{statusLabel(selectedDetail.status)}</span>
              </div>
              {selectedDetail.observacao && <p className="inventory-detail-observation">{selectedDetail.observacao}</p>}
              <div className="inventory-progress-block">
                <div className="inventory-progress-label"><span>Progresso da contagem</span><strong>{countedCount} de {inventoryRows.length} itens · {progress}%</strong></div>
                <div className="inventory-progress-track" role="progressbar" aria-label="Progresso da contagem" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><span style={{ width: `${progress}%` }} /></div>
              </div>

              {inventoryRows.length === 0 ? (
                <EmptyPanel title="Este inventário não possui itens" description="Não há itens no snapshot retornado pela API." />
              ) : (
                <div className="inventory-table-wrap">
                  <table className="inventory-table">
                    <thead><tr><th>Item</th><th>Saldo do sistema</th><th>Contagem física</th><th>Diferença</th><th /></tr></thead>
                    <tbody>
                      {inventoryRows.map((row) => {
                        const item = itemById.get(row.item_id)
                        const unit = item ? unitById.get(item.unidade_id) : null
                        const counted = row.quantidade_contada !== null && row.quantidade_contada !== undefined
                        const saving = savingItemId === row.item_id
                        return (
                          <tr key={row.item_id}>
                            <td><div className="inventory-item-name"><strong>{item?.nome || `Item #${row.item_id}`}</strong><small>{unit?.nome || 'Unidade não disponível'}{unit?.simbolo ? ` · ${unit.simbolo}` : ''}</small></div></td>
                            <td className="inventory-number">{formatQuantity(row.saldo_sistema)}</td>
                            <td>
                              <label className="inventory-count-control"><span className="sr-only">Quantidade contada para {item?.nome || `item ${row.item_id}`}</span><input type="text" inputMode="decimal" value={countDraft[row.item_id] ?? ''} onChange={(event) => setCountDraft((previous) => ({ ...previous, [row.item_id]: event.target.value }))} placeholder="Contar" disabled={!canWrite || !isOpen || saving || savingItemId !== null} aria-label={`Quantidade contada para ${item?.nome || `item ${row.item_id}`}`} /></label>
                            </td>
                            <td className={`inventory-number ${counted && Number(row.diferenca) < 0 ? 'inventory-difference-negative' : counted && Number(row.diferenca) > 0 ? 'inventory-difference-positive' : ''}`}>{counted ? formatQuantity(row.diferenca) : '—'}</td>
                            <td className="inventory-save-cell">{isOpen && canWrite ? <button type="button" className="inventory-save-button" onClick={() => saveCount(row)} disabled={savingItemId !== null || busyAction !== '' || countDraft[row.item_id] === undefined || countDraft[row.item_id] === ''}>{saving ? 'Salvando…' : counted ? 'Atualizar' : 'Salvar'}</button> : <span className={`inventory-counted-tag ${counted ? 'is-counted' : ''}`}>{counted ? 'Contado' : 'Sem contagem'}</span>}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="inventory-detail-footer">
                <div className="inventory-footer-copy">{isOpen ? uncountedCount ? `Faltam ${uncountedCount} item(ns) para concluir.` : 'Todas as contagens foram registradas.' : selectedDetail.status === 'CONCLUIDO' ? `Concluído em ${formatDateTime(selectedDetail.concluido_em)}.` : `Cancelado em ${formatDateTime(selectedDetail.cancelado_em)}.`}</div>
                {isOpen && canWrite && <div className="inventory-footer-actions"><button type="button" className="inventory-button inventory-button-secondary" onClick={() => runInventoryAction('cancel')} disabled={Boolean(busyAction) || savingItemId !== null}>{busyAction === 'cancel' ? 'Cancelando…' : 'Cancelar inventário'}</button><button type="button" className="inventory-button inventory-button-primary" onClick={() => runInventoryAction('complete')} disabled={Boolean(busyAction) || savingItemId !== null || uncountedCount > 0 || inventoryRows.length === 0}>{busyAction === 'complete' ? 'Concluindo…' : 'Concluir inventário'}</button></div>}
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import './MovementPage.css'

const HISTORY_PAGE_SIZE = 50

const MOVEMENT_TYPES = [
  {
    value: 'ENTRADA',
    label: 'Entrada',
    badge: 'movement-in',
    explanation: 'Adiciona a quantidade informada ao saldo do produto.',
  },
  {
    value: 'SAIDA',
    label: 'Saída',
    badge: 'movement-out',
    explanation: 'Retira a quantidade informada. O saldo não pode ficar negativo.',
  },
  {
    value: 'AJUSTE_ENTRADA',
    label: 'Ajuste de entrada',
    badge: 'movement-adjust-in',
    explanation: 'Registra um acréscimo de quantidade para ajustar o saldo.',
  },
  {
    value: 'AJUSTE_SAIDA',
    label: 'Ajuste de saída',
    badge: 'movement-adjust-out',
    explanation: 'Registra uma redução de quantidade para ajustar o saldo.',
  },
]

function formatQuantity(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 4 }).format(number)
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

function movementType(value) {
  return MOVEMENT_TYPES.find((item) => item.value === value) ?? {
    label: value,
    badge: 'movement-neutral',
  }
}

function isOutgoing(type) {
  return type === 'SAIDA' || type === 'AJUSTE_SAIDA'
}

function EmptyHistory({ loading, error, hasItem }) {
  if (loading) {
    return (
      <div className="movement-history-empty" role="status">
        Carregando histórico...
      </div>
    )
  }
  if (error) {
    return (
      <div className="movement-history-empty movement-history-error" role="alert">
        {error}
      </div>
    )
  }
  if (!hasItem) {
    return (
      <div className="movement-history-empty">
        Cadastre um produto para registrar movimentações.
      </div>
    )
  }
  return (
    <div className="movement-history-empty">
      <span className="movement-empty-icon" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="11" stroke="currentColor" strokeWidth="1.5" />
          <path d="M16 9v7l5 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
      <strong>Nenhuma movimentação registrada</strong>
      <p>Quando você registrar uma entrada, saída ou ajuste, ela aparecerá aqui.</p>
    </div>
  )
}

export default function MovementsPage({ companyId, onLogout, onNavigateProducts }) {
  const [items, setItems] = useState([])
  const [units, setUnits] = useState([])
  const [balances, setBalances] = useState([])
  const [loadingCatalog, setLoadingCatalog] = useState(true)
  const [catalogError, setCatalogError] = useState('')
  const [selectedItemId, setSelectedItemId] = useState('')

  const [currentBalance, setCurrentBalance] = useState(null)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [historyOffset, setHistoryOffset] = useState(0)
  const [hasMoreHistory, setHasMoreHistory] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [draft, setDraft] = useState({
    tipo: 'ENTRADA',
    quantidade: '',
    motivo: '',
    observacao: '',
  })

  useEffect(() => {
    let cancelled = false

    async function loadCatalog() {
      setLoadingCatalog(true)
      setCatalogError('')

      try {
        const [itemList, unitList, balanceList] = await Promise.all([
          api.items(companyId),
          api.units(companyId),
          api.stockBalancesAll(companyId),
        ])

        if (cancelled) return

        setItems(itemList)
        setUnits(unitList)
        setBalances(balanceList)
        setSelectedItemId((current) => (
          itemList.some((item) => String(item.id) === current)
            ? current
            : String(itemList[0]?.id ?? '')
        ))
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setCatalogError(error.message)
      } finally {
        if (!cancelled) setLoadingCatalog(false)
      }
    }

    void loadCatalog()
    return () => { cancelled = true }
  }, [companyId, onLogout, reloadKey])

  useEffect(() => {
    let cancelled = false

    async function loadSelectedItem() {
      if (!selectedItemId) {
        setCurrentBalance(null)
        setHistory([])
        setHistoryError('')
        setHistoryLoading(false)
        setHistoryOffset(0)
        setHasMoreHistory(false)
        return
      }

      setHistoryLoading(true)
      setHistoryError('')

      try {
        const [movements, balance] = await Promise.all([
          api.itemMovements(companyId, Number(selectedItemId), HISTORY_PAGE_SIZE, 0),
          api.itemBalance(companyId, Number(selectedItemId)),
        ])

        if (cancelled) return
        setHistory(movements)
        setHistoryOffset(movements.length)
        setHasMoreHistory(movements.length === HISTORY_PAGE_SIZE)
        setCurrentBalance(balance.saldo_atual)
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setHistoryError(error.message)
        setHistory([])
        setCurrentBalance(null)
      } finally {
        if (!cancelled) setHistoryLoading(false)
      }
    }

    void loadSelectedItem()
    return () => { cancelled = true }
  }, [companyId, selectedItemId, reloadKey, onLogout])

  const unitById = useMemo(
    () => new Map(units.map((unit) => [Number(unit.id), unit])),
    [units],
  )

  const balanceByItemId = useMemo(
    () => new Map(balances.map((balance) => [Number(balance.item_id), balance])),
    [balances],
  )

  const selectedItem = items.find((item) => String(item.id) === selectedItemId)
  const selectedUnit = selectedItem
    ? unitById.get(Number(selectedItem.unidade_id))
    : null
  const selectedBalanceRow = selectedItem
    ? balanceByItemId.get(Number(selectedItem.id))
    : null
  const lowBalance = selectedBalanceRow
    ? Number(selectedBalanceRow.saldo_atual) < Number(selectedBalanceRow.estoque_minimo)
    : false

  const selectedType = movementType(draft.tipo)

  function updateDraft(field, value) {
    setDraft((previous) => ({ ...previous, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setFeedback('')

    if (!selectedItem) {
      setFormError('Cadastre ou selecione um produto antes de registrar uma movimentação.')
      return
    }

    const quantityText = draft.quantidade.trim().replace(',', '.')
    if (!/^\d+(?:\.\d{1,4})?$/.test(quantityText)) {
      setFormError('Informe uma quantidade maior que zero, com no máximo quatro casas decimais.')
      return
    }

    const quantity = Number(quantityText)
    if (!Number.isFinite(quantity) || quantity <= 0 || quantity >= 100000000000000) {
      setFormError('A quantidade deve ser positiva e estar dentro do limite permitido.')
      return
    }

    if (selectedUnit && !selectedUnit.permite_decimal && !Number.isInteger(quantity)) {
      setFormError('A unidade deste produto aceita apenas quantidades inteiras.')
      return
    }

    if (draft.motivo.trim().length > 255) {
      setFormError('O motivo pode ter no máximo 255 caracteres.')
      return
    }

    if (draft.observacao.trim().length > 5000) {
      setFormError('A observação pode ter no máximo 5.000 caracteres.')
      return
    }

    const payload = {
      item_id: Number(selectedItemId),
      tipo: draft.tipo,
      quantidade: quantityText,
      motivo: draft.motivo.trim() || null,
      observacao: draft.observacao.trim() || null,
    }

    setSaving(true)
    try {
      await api.createMovement(companyId, payload)
      setFeedback(`${selectedType.label} registrada para “${selectedItem.nome}”.`)
      setDraft((previous) => ({
        ...previous,
        quantidade: '',
        motivo: '',
        observacao: '',
      }))
      setReloadKey((value) => value + 1)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setFormError(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function loadMoreHistory() {
    if (!selectedItemId || loadingMore) return
    setLoadingMore(true)
    setHistoryError('')

    try {
      const nextPage = await api.itemMovements(
        companyId,
        Number(selectedItemId),
        HISTORY_PAGE_SIZE,
        historyOffset,
      )
      setHistory((previous) => [...previous, ...nextPage])
      setHistoryOffset((previous) => previous + nextPage.length)
      setHasMoreHistory(nextPage.length === HISTORY_PAGE_SIZE)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setHistoryError(error.message)
    } finally {
      setLoadingMore(false)
    }
  }

  function retryCatalog() {
    setLoadingCatalog(true)
    setCatalogError('')
    setReloadKey((value) => value + 1)
  }

  return (
    <section className="movement-page">
      {feedback && (
        <div className="record-feedback success" role="status">
          <span aria-hidden="true">✓</span>
          {feedback}
          <button
            type="button"
            className="feedback-dismiss"
            onClick={() => setFeedback('')}
            aria-label="Dispensar mensagem"
          >×</button>
        </div>
      )}

      {catalogError && (
        <div className="record-feedback error" role="alert">
          <span>{catalogError}</span>
          <button type="button" className="text-button" onClick={retryCatalog}>
            Tentar novamente
          </button>
        </div>
      )}

      <div className="movement-layout">
        <form className="movement-form-panel" onSubmit={handleSubmit}>
          <div className="movement-panel-heading">
            <div className="movement-panel-icon">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <span className="eyebrow">OPERAÇÃO DE ESTOQUE</span>
              <h2>Registrar movimentação</h2>
              <p>Selecione um produto, defina a operação e informe a quantidade.</p>
            </div>
          </div>

          {formError && <div className="record-feedback error" role="alert">{formError}</div>}

          {items.length === 0 && !loadingCatalog && !catalogError && (
            <div className="record-feedback notice" role="status">
              Não há produtos ativos nesta empresa. Cadastre um produto primeiro.
              <button type="button" className="text-button" onClick={onNavigateProducts}>
                Ir para produtos
              </button>
            </div>
          )}

          <div className="movement-form-fields">
            <div className="form-field">
              <label htmlFor="movement-item">Produto *</label>
              <select
                id="movement-item"
                className="record-field-select"
                value={selectedItemId}
                onChange={(event) => {
                  setSelectedItemId(event.target.value)
                  setFormError('')
                }}
                disabled={loadingCatalog || items.length === 0 || saving}
                required
              >
                <option value="">Selecione um produto</option>
                {items.map((item) => {
                  const unit = unitById.get(Number(item.unidade_id))
                  return (
                    <option value={item.id} key={item.id}>
                      {item.nome} · {unit?.simbolo || unit?.nome || `unidade #${item.unidade_id}`}
                    </option>
                  )
                })}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="movement-type">Tipo de operação *</label>
              <select
                id="movement-type"
                className="record-field-select"
                value={draft.tipo}
                onChange={(event) => updateDraft('tipo', event.target.value)}
                disabled={saving}
              >
                {MOVEMENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
              <small className="field-help">{selectedType.explanation}</small>
            </div>

            <div className="form-field">
              <label htmlFor="movement-quantity">Quantidade *</label>
              <div className="movement-quantity-field">
                <input
                  id="movement-quantity"
                  type="text"
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder={selectedUnit && !selectedUnit.permite_decimal ? 'Ex.: 12' : 'Ex.: 12 ou 2,5'}
                  value={draft.quantidade}
                  onChange={(event) => updateDraft('quantidade', event.target.value)}
                  maxLength={20}
                  disabled={!selectedItem || saving}
                  required
                />
                <span>{selectedUnit?.simbolo || selectedUnit?.nome || 'unidade'}</span>
              </div>
              <small className="field-help">
                {selectedUnit && !selectedUnit.permite_decimal
                  ? 'Esta unidade aceita somente números inteiros.'
                  : 'Use ponto ou vírgula decimal, com até quatro casas.'}
              </small>
            </div>

            <div className="form-field">
              <label htmlFor="movement-reason">Motivo</label>
              <input
                id="movement-reason"
                value={draft.motivo}
                onChange={(event) => updateDraft('motivo', event.target.value)}
                maxLength={255}
                placeholder="Ex.: compra, venda, perda, correção"
                disabled={!selectedItem || saving}
              />
              <small className="field-help">Opcional · até 255 caracteres</small>
            </div>

            <div className="form-field">
              <label htmlFor="movement-observation">Observação</label>
              <textarea
                id="movement-observation"
                value={draft.observacao}
                onChange={(event) => updateDraft('observacao', event.target.value)}
                maxLength={5000}
                rows={3}
                placeholder="Informações adicionais (opcional)"
                disabled={!selectedItem || saving}
              />
              <small className="field-help">{draft.observacao.length}/5000 caracteres</small>
            </div>
          </div>

          <div className="movement-form-note">
            <span aria-hidden="true">i</span>
            <p>
              O registro é permanente no histórico. Saídas que deixariam o saldo negativo
              e operações bloqueadas por inventário aberto serão recusadas pelo sistema.
            </p>
          </div>

          <div className="movement-form-footer">
            <button
              type="submit"
              className="button-primary"
              disabled={saving || loadingCatalog || !selectedItem}
            >
              {saving ? 'Registrando...' : `Registrar ${selectedType.label.toLocaleLowerCase('pt-BR')}`}
              {!saving && (
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M5 12h14m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
              {saving && <span className="button-spinner" aria-hidden="true" />}
            </button>
          </div>
        </form>

        <aside className="movement-side-column">
          <section className="movement-balance-card">
            <span className="eyebrow">SALDO DO PRODUTO</span>
            {selectedItem ? (
              <>
                <h2>{selectedItem.nome}</h2>
                <div className="movement-balance-value">
                  {currentBalance === null ? '—' : formatQuantity(currentBalance)}
                  <span>{selectedUnit?.simbolo || selectedUnit?.nome || ''}</span>
                </div>
                <div className="movement-balance-divider" />
                <div className="movement-balance-meta">
                  <span>Estoque mínimo</span>
                  <strong>{formatQuantity(selectedItem.estoque_minimo)} {selectedUnit?.simbolo || ''}</strong>
                </div>
                <div className="movement-balance-status">
                  <span className={lowBalance ? 'movement-status-dot is-warning' : 'movement-status-dot'} />
                  {lowBalance ? 'Saldo abaixo do mínimo' : 'Consulte o saldo atualizado após cada operação'}
                </div>
              </>
            ) : (
              <p className="movement-no-selection">
                Selecione um produto para consultar seu saldo e histórico.
              </p>
            )}
          </section>

          <section className="movement-guidance-card">
            <span className="eyebrow">COMO O SALDO MUDA</span>
            <div className="movement-guidance-row">
              <span className="movement-guidance-symbol positive">+</span>
              <span><strong>Entrada</strong><small>Soma quantidade ao saldo</small></span>
            </div>
            <div className="movement-guidance-row">
              <span className="movement-guidance-symbol negative">−</span>
              <span><strong>Saída</strong><small>Subtrai quantidade do saldo</small></span>
            </div>
            <p>O saldo oficial é calculado pelo backend a partir das movimentações registradas.</p>
          </section>
        </aside>
      </div>

      <section className="movement-history-panel">
        <div className="movement-history-heading">
          <div>
            <span className="eyebrow">REGISTROS DO PRODUTO</span>
            <h2>Histórico de movimentações</h2>
            <p>
              {selectedItem
                ? `Movimentações mais recentes de ${selectedItem.nome}.`
                : 'Selecione um produto para consultar o histórico.'}
            </p>
          </div>
          {selectedItem && (
            <span className="movement-history-count">
              {history.length} {history.length === 1 ? 'registro carregado' : 'registros carregados'}
            </span>
          )}
        </div>

        {historyError && (
          <div className="record-feedback error movement-history-error-banner" role="alert">
            {historyError}
          </div>
        )}

        {historyLoading || history.length === 0 ? (
          <EmptyHistory
            loading={historyLoading}
            error={historyError}
            hasItem={Boolean(selectedItem)}
          />
        ) : (
          <>
            <div className="records-table-scroll">
              <table className="records-table movement-history-table">
                <thead>
                  <tr>
                    <th>Data e hora</th>
                    <th>Operação</th>
                    <th className="records-number-column">Quantidade</th>
                    <th>Motivo</th>
                    <th>Observação</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((movement) => {
                    const type = movementType(movement.tipo)
                    const outgoing = isOutgoing(movement.tipo)
                    return (
                      <tr key={movement.id}>
                        <td>{formatDate(movement.ocorrida_em)}</td>
                        <td><span className={`movement-type-chip ${type.badge}`}>{type.label}</span></td>
                        <td className={`records-number-column ${outgoing ? 'quantity-out' : 'quantity-in'}`}>
                          <strong>{outgoing ? '−' : '+'}{formatQuantity(movement.quantidade)}</strong>
                        </td>
                        <td>{movement.motivo || '—'}</td>
                        <td className="movement-observation-cell">{movement.observacao || '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {hasMoreHistory && (
              <div className="movement-load-more">
                <button
                  type="button"
                  className="button-secondary"
                  onClick={loadMoreHistory}
                  disabled={loadingMore}
                >
                  {loadingMore ? 'Carregando...' : 'Carregar movimentações anteriores'}
                </button>
              </div>
            )}
          </>
        )}
      </section>

      <p className="records-page-note">
        Esta tela consulta o histórico por produto, conforme a API atual. O sistema não permite
        excluir movimentações por esta interface.
      </p>
    </section>
  )
}

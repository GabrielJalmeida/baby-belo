import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import './ProductDetails.css'

const HISTORY_PAGE_SIZE = 20

const MOVEMENT_LABELS = {
  ENTRADA: 'Entrada',
  SAIDA: 'Saída',
  AJUSTE_ENTRADA: 'Ajuste de entrada',
  AJUSTE_SAIDA: 'Ajuste de saída',
}

const quantityFormatter = new Intl.NumberFormat('pt-BR', {
  maximumFractionDigits: 4,
})

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})

function formatQuantity(value) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  return Number.isFinite(number) ? quantityFormatter.format(number) : '—'
}

function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(`${value}T00:00:00Z`)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(date)
}

function customValueColumn(record) {
  return [
    'valor_texto',
    'valor_inteiro',
    'valor_decimal',
    'valor_monetario',
    'valor_booleano',
    'valor_data',
    'opcao_id',
  ].find((key) => record[key] !== null && record[key] !== undefined) ?? null
}

function formatCustomValue(record, optionById) {
  const column = customValueColumn(record)
  if (!column) return '—'

  if (column === 'opcao_id') {
    return optionById.get(Number(record.opcao_id)) ?? `Opção #${record.opcao_id}`
  }
  if (column === 'valor_booleano') return record.valor_booleano ? 'Sim' : 'Não'
  if (column === 'valor_data') return formatDate(record.valor_data)
  if (column === 'valor_monetario') {
    const number = Number(record.valor_monetario)
    return Number.isFinite(number) ? currencyFormatter.format(number) : '—'
  }
  if (column === 'valor_inteiro' || column === 'valor_decimal') {
    return formatQuantity(record[column])
  }
  return String(record[column])
}

function isUnauthorized(error) {
  return error instanceof ApiError && error.status === 401
}

export default function ProductDetails({
  item,
  unit,
  balance: initialBalance,
  companyId,
  onClose,
  onEdit,
  onLogout,
  canWrite = true,
}) {
  const [balance, setBalance] = useState(initialBalance?.saldo_atual ?? null)
  const [balanceLoading, setBalanceLoading] = useState(!initialBalance)
  const [balanceError, setBalanceError] = useState('')
  const [movements, setMovements] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyLoadingMore, setHistoryLoadingMore] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [hasMoreMovements, setHasMoreMovements] = useState(false)
  const [customValues, setCustomValues] = useState([])
  const [customFields, setCustomFields] = useState([])
  const [customOptions, setCustomOptions] = useState({})
  const [customCategoryName, setCustomCategoryName] = useState('')
  const [customCategoryId, setCustomCategoryId] = useState(null)
  const [customLoading, setCustomLoading] = useState(true)
  const [customError, setCustomError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadBalance() {
      try {
        const result = await api.itemBalance(companyId, item.id)
        if (!cancelled) {
          setBalance(result.saldo_atual)
          setBalanceError('')
        }
      } catch (error) {
        if (cancelled) return
        if (isUnauthorized(error)) onLogout('Sua sessão expirou. Entre novamente.')
        setBalanceError(error.message || 'Não foi possível consultar o saldo.')
      } finally {
        if (!cancelled) setBalanceLoading(false)
      }
    }

    async function loadHistory() {
      try {
        const result = await api.itemMovements(companyId, item.id, HISTORY_PAGE_SIZE, 0)
        if (!cancelled) {
          setMovements(result)
          setHasMoreMovements(result.length === HISTORY_PAGE_SIZE)
          setHistoryError('')
        }
      } catch (error) {
        if (cancelled) return
        if (isUnauthorized(error)) onLogout('Sua sessão expirou. Entre novamente.')
        setHistoryError(error.message || 'Não foi possível carregar o histórico.')
      } finally {
        if (!cancelled) setHistoryLoading(false)
      }
    }

    async function loadCustomData() {
      try {
        const associationRequest = api.itemCategory(companyId, item.id).catch((error) => {
          if (error instanceof ApiError && error.status === 404) return null
          throw error
        })
        const [association, values] = await Promise.all([
          associationRequest,
          api.itemCustomValues(companyId, item.id),
        ])
        if (cancelled) return

        setCustomValues(values)
        const categoryId = association?.categoria_id ?? null
        setCustomCategoryId(categoryId)
        if (!categoryId) {
          setCustomCategoryName('')
          setCustomFields([])
          setCustomOptions({})
          return
        }

        const [categories, fields] = await Promise.all([
          api.customCategories(companyId).catch((error) => {
            if (isUnauthorized(error)) throw error
            return []
          }),
          api.customFields(companyId, categoryId),
        ])
        if (cancelled) return

        const category = categories.find((entry) => Number(entry.id) === Number(categoryId))
        setCustomCategoryName(category?.nome ?? `Categoria #${categoryId}`)
        setCustomFields(fields)

        const optionEntries = await Promise.all(
          fields
            .filter((field) => field.tipo_dado === 'LISTA')
            .map(async (field) => {
              try {
                return [String(field.id), await api.customOptions(companyId, field.id)]
              } catch (error) {
                if (error instanceof ApiError && error.status === 404) {
                  return [String(field.id), []]
                }
                throw error
              }
            }),
        )
        if (!cancelled) setCustomOptions(Object.fromEntries(optionEntries))
      } catch (error) {
        if (cancelled) return
        if (isUnauthorized(error)) onLogout('Sua sessão expirou. Entre novamente.')
        setCustomError(error.message || 'Não foi possível carregar os campos personalizados.')
      } finally {
        if (!cancelled) setCustomLoading(false)
      }
    }

    void loadBalance()
    void loadHistory()
    void loadCustomData()

    return () => {
      cancelled = true
    }
  }, [companyId, item.id, onLogout])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const fieldById = useMemo(
    () => new Map(customFields.map((field) => [Number(field.id), field])),
    [customFields],
  )

  const optionById = useMemo(() => {
    const entries = Object.values(customOptions).flat()
    return new Map(entries.map((option) => [Number(option.id), option.valor]))
  }, [customOptions])

  async function loadMoreMovements() {
    setHistoryLoadingMore(true)
    setHistoryError('')
    try {
      const nextPage = await api.itemMovements(
        companyId,
        item.id,
        HISTORY_PAGE_SIZE,
        movements.length,
      )
      setMovements((current) => [...current, ...nextPage])
      setHasMoreMovements(nextPage.length === HISTORY_PAGE_SIZE)
    } catch (error) {
      if (isUnauthorized(error)) onLogout('Sua sessão expirou. Entre novamente.')
      setHistoryError(error.message || 'Não foi possível carregar mais movimentações.')
    } finally {
      setHistoryLoadingMore(false)
    }
  }

  async function retryHistory() {
    setHistoryLoading(true)
    setHistoryError('')
    try {
      const result = await api.itemMovements(companyId, item.id, HISTORY_PAGE_SIZE, 0)
      setMovements(result)
      setHasMoreMovements(result.length === HISTORY_PAGE_SIZE)
    } catch (error) {
      if (isUnauthorized(error)) onLogout('Sua sessão expirou. Entre novamente.')
      setHistoryError(error.message || 'Não foi possível carregar o histórico.')
    } finally {
      setHistoryLoading(false)
    }
  }

  const minimum = Number(item.estoque_minimo ?? 0)
  const currentBalance = balance === null || balance === undefined ? null : Number(balance)
  const stockIsLow = currentBalance !== null && Number.isFinite(currentBalance) && currentBalance <= minimum

  return (
    <div
      className="product-detail-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="product-detail-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-detail-title"
      >
        <header className="product-detail-header">
          <div className="product-detail-heading-copy">
            <span className="eyebrow">CATÁLOGO · DETALHES</span>
            <h2 id="product-detail-title">{item.nome}</h2>
            <p>Produto #{item.id} · Consulte cadastro, saldo e histórico sem alterar o estoque.</p>
          </div>
          <button type="button" className="product-detail-close" onClick={onClose} aria-label="Fechar detalhes">
            ×
          </button>
        </header>

        <div className="product-detail-summary">
          <article className="product-detail-stat product-detail-stat-primary">
            <span>Saldo atual</span>
            <strong>{balanceLoading && balance === null ? 'Carregando…' : formatQuantity(balance)}</strong>
            <small>{unit?.simbolo || unit?.nome || 'Unidade cadastrada'}</small>
          </article>
          <article className="product-detail-stat">
            <span>Estoque mínimo</span>
            <strong>{formatQuantity(item.estoque_minimo)}</strong>
            <small>Limite de atenção</small>
          </article>
          <article className="product-detail-stat">
            <span>Unidade</span>
            <strong>{unit?.nome ?? `Unidade #${item.unidade_id}`}</strong>
            <small>{unit?.simbolo || 'Sem símbolo cadastrado'}</small>
          </article>
          <article className="product-detail-stat">
            <span>Situação</span>
            <strong>
              <span className={`product-detail-status ${item.ativo ? (stockIsLow ? 'is-warning' : 'is-active') : 'is-inactive'}`}>
                {!item.ativo ? 'Inativo' : stockIsLow ? 'Estoque baixo' : 'Ativo'}
              </span>
            </strong>
            <small>{item.ativo ? 'Cadastro ativo' : 'Cadastro inativo'}</small>
          </article>
        </div>

        {balanceError && (
          <div className="product-detail-message is-error" role="alert">
            <span>{balanceError}</span>
          </div>
        )}

        <section className="product-detail-card">
          <div className="product-detail-section-heading">
            <div>
              <span className="eyebrow">IDENTIFICAÇÃO</span>
              <h3>Dados do cadastro</h3>
            </div>
            {canWrite && (
              <button type="button" className="button-secondary product-detail-edit" onClick={() => onEdit(item)}>
                Editar produto
              </button>
            )}
          </div>
          <dl className="product-detail-description-grid">
            <div>
              <dt>Nome</dt>
              <dd>{item.nome || '—'}</dd>
            </div>
            <div>
              <dt>ID do produto</dt>
              <dd>#{item.id}</dd>
            </div>
            <div className="product-detail-description-full">
              <dt>Descrição</dt>
              <dd>{item.descricao || 'Nenhuma descrição cadastrada.'}</dd>
            </div>
          </dl>
        </section>

        <section className="product-detail-card">
          <div className="product-detail-section-heading">
            <div>
              <span className="eyebrow">PERSONALIZAÇÃO</span>
              <h3>Campos personalizados</h3>
              <p>Valores vinculados à categoria do produto.</p>
            </div>
            {customCategoryName && <span className="product-detail-category">{customCategoryName}</span>}
          </div>

          {customLoading ? (
            <div className="product-detail-state" role="status">Carregando dados personalizados…</div>
          ) : customError ? (
            <div className="product-detail-message is-error" role="alert">{customError}</div>
          ) : customValues.length === 0 ? (
            <div className="product-detail-state">
              {customCategoryId
                ? 'O produto possui uma categoria, mas ainda não há valores personalizados salvos.'
                : 'Este produto não possui valores personalizados cadastrados.'}
            </div>
          ) : (
            <div className="product-detail-custom-grid">
              {customValues.map((record) => {
                const field = fieldById.get(Number(record.campo_id))
                return (
                  <article className="product-detail-custom-value" key={record.id}>
                    <span>{field?.nome ?? `Campo #${record.campo_id}`}</span>
                    <strong>{formatCustomValue(record, optionById)}</strong>
                    {field && <small>{field.tipo_dado.replaceAll('_', ' ').toLocaleLowerCase('pt-BR')}</small>}
                  </article>
                )
              })}
            </div>
          )}
        </section>

        <section className="product-detail-card product-detail-history-card">
          <div className="product-detail-section-heading">
            <div>
              <span className="eyebrow">RASTREABILIDADE</span>
              <h3>Histórico de movimentações</h3>
              <p>Movimentações mais recentes primeiro. O saldo é calculado a partir desses registros.</p>
            </div>
            <span className="product-detail-history-count">{movements.length} registro(s)</span>
          </div>

          {historyLoading ? (
            <div className="product-detail-state" role="status">Carregando histórico…</div>
          ) : historyError && movements.length === 0 ? (
            <div className="product-detail-message is-error" role="alert">
              <span>{historyError}</span>
              <button type="button" className="text-button" onClick={retryHistory}>Tentar novamente</button>
            </div>
          ) : movements.length === 0 ? (
            <div className="product-detail-state">Ainda não existem movimentações para este produto.</div>
          ) : (
            <>
              {historyError && <div className="product-detail-message is-error" role="alert">{historyError}</div>}
              <div className="product-detail-history-scroll">
                <table className="product-detail-history-table">
                  <thead>
                    <tr>
                      <th>Data e hora</th>
                      <th>Tipo</th>
                      <th className="is-number">Quantidade</th>
                      <th>Motivo / observação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {movements.map((movement) => (
                      <tr key={movement.id}>
                        <td>{formatDateTime(movement.ocorrida_em)}</td>
                        <td>
                          <span className={`product-detail-movement-type ${movement.tipo?.includes('SAIDA') ? 'is-out' : 'is-in'}`}>
                            {MOVEMENT_LABELS[movement.tipo] ?? movement.tipo}
                          </span>
                        </td>
                        <td className="is-number">{formatQuantity(movement.quantidade)}</td>
                        <td>
                          <span className="product-detail-reason">{movement.motivo || 'Sem motivo informado'}</span>
                          {movement.observacao && <small className="product-detail-observation">{movement.observacao}</small>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {hasMoreMovements && (
                <div className="product-detail-history-footer">
                  <span>Exibindo as {movements.length} movimentações mais recentes carregadas.</span>
                  <button type="button" className="button-secondary" onClick={loadMoreMovements} disabled={historyLoadingMore}>
                    {historyLoadingMore ? 'Carregando…' : 'Carregar mais antigas'}
                  </button>
                </div>
              )}
            </>
          )}
        </section>

        <footer className="product-detail-footer">
          <span>Consulta somente leitura · O saldo não é alterado nesta tela.</span>
          <button type="button" className="button-primary" onClick={onClose}>Concluir consulta</button>
        </footer>
      </section>
    </div>
  )
}

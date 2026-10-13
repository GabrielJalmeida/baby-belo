
import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'

const PAGE_SIZE = 10

function formatQuantity(value) {
  const number = Number(value)

  if (!Number.isFinite(number)) {
    return '—'
  }

  return new Intl.NumberFormat('pt-BR', {
    maximumFractionDigits: 4,
  }).format(number)
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle
        cx="10.8"
        cy="10.8"
        r="6.8"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="m16 16 4.5 4.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  )
}

function ProductEmpty({ title, description, action }) {
  return (
    <div className="records-empty">
      <span className="records-empty-symbol" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path
            d="m5 11 11-6 11 6v12l-11 6-11-6V11Z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <path
            d="m5.5 11.5 10.5 6 10.5-6M16 18v10"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <strong>{title}</strong>
      <p>{description}</p>
      {action}
    </div>
  )
}

export default function ProductsPage({
  companyId,
  onLogout,
  onNavigateUnits,
}) {
  const [items, setItems] = useState([])
  const [units, setUnits] = useState([])
  const [balances, setBalances] = useState([])
  const [lowStockItems, setLowStockItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [formError, setFormError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [formMode, setFormMode] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const [draft, setDraft] = useState({
    nome: '',
    descricao: '',
    unidade_id: '',
    estoque_minimo: '0',
  })

  useEffect(() => {
    let cancelled = false

    async function loadProducts() {
      try {
        const [
          productList,
          unitList,
          balanceList,
          lowStockList,
        ] = await Promise.all([
          api.items(companyId),
          api.units(companyId),
          api.stockBalancesAll(companyId),
          api.lowStockAll(companyId),
        ])

        if (cancelled) {
          return
        }

        setItems(productList)
        setUnits(unitList)
        setBalances(balanceList)
        setLowStockItems(lowStockList)
        setLoadError('')
      } catch (error) {
        if (cancelled) {
          return
        }

        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }

        setLoadError(error.message)
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadProducts()

    return () => {
      cancelled = true
    }
  }, [companyId, onLogout, reloadKey])

  const unitById = useMemo(
    () => new Map(units.map((unit) => [Number(unit.id), unit])),
    [units],
  )

  const balanceByItemId = useMemo(
    () => new Map(
      balances.map((balance) => [Number(balance.item_id), balance]),
    ),
    [balances],
  )

  const lowStockIds = useMemo(
    () => new Set(lowStockItems.map((item) => Number(item.item_id))),
    [lowStockItems],
  )

  const filteredItems = useMemo(() => {
    const query = search.trim().toLocaleLowerCase('pt-BR')

    if (!query) {
      return items
    }

    return items.filter((item) => (
      item.nome.toLocaleLowerCase('pt-BR').includes(query)
      || (item.descricao ?? '').toLocaleLowerCase('pt-BR').includes(query)
      || String(item.id).includes(query)
    ))
  }, [items, search])

  const pageCount = Math.max(
    1,
    Math.ceil(filteredItems.length / PAGE_SIZE),
  )
  const currentPage = Math.min(page, pageCount - 1)

  const visibleItems = filteredItems.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  )

  function retryLoad() {
    setLoading(true)
    setLoadError('')
    setReloadKey((value) => value + 1)
  }

  function startCreate() {
    setEditingId(null)
    setDraft({
      nome: '',
      descricao: '',
      unidade_id: units[0] ? String(units[0].id) : '',
      estoque_minimo: '0',
    })
    setFormError('')
    setFeedback('')
    setFormMode('create')
  }

  function startEdit(item) {
    setEditingId(item.id)
    setDraft({
      nome: item.nome,
      descricao: item.descricao ?? '',
      unidade_id: String(item.unidade_id),
      estoque_minimo: String(item.estoque_minimo ?? '0'),
    })
    setFormError('')
    setFeedback('')
    setFormMode('edit')
  }

  function closeForm() {
    setFormMode(null)
    setEditingId(null)
    setFormError('')
  }

  function updateDraft(field, value) {
    setDraft((previous) => ({
      ...previous,
      [field]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setFeedback('')

    const name = draft.nome.trim()
    const unitId = Number(draft.unidade_id)
    const minimumText = draft.estoque_minimo.trim().replace(',', '.')
    const minimum = Number(minimumText)
    const selectedUnit = unitById.get(unitId)
    const existingItem = items.find((item) => item.id === editingId)

    const keepingExistingUnit = (
      existingItem
      && Number(existingItem.unidade_id) === unitId
    )

    if (!name) {
      setFormError('Informe o nome do produto.')
      return
    }

    if (!unitId || (!selectedUnit && !keepingExistingUnit)) {
      setFormError('Selecione uma unidade de medida disponível.')
      return
    }

    if (
      !minimumText
      || !Number.isFinite(minimum)
      || minimum < 0
    ) {
      setFormError('Informe um estoque mínimo válido e não negativo.')
      return
    }

    if (
      selectedUnit
      && !selectedUnit.permite_decimal
      && !Number.isInteger(minimum)
    ) {
      setFormError(
        'Esta unidade aceita somente quantidades inteiras. Ajuste o estoque mínimo.',
      )
      return
    }

    const payload = {
      nome: name,
      descricao: draft.descricao.trim() || null,
      estoque_minimo: minimumText,
    }

    if (!existingItem || Number(existingItem.unidade_id) !== unitId) {
      payload.unidade_id = unitId
    }

    setSaving(true)

    try {
      if (formMode === 'edit') {
        await api.updateItem(companyId, editingId, payload)
      } else {
        payload.unidade_id = unitId
        await api.createItem(companyId, payload)
      }

      setFormMode(null)
      setEditingId(null)
      setFeedback(
        formMode === 'edit'
          ? 'Produto atualizado com sucesso.'
          : 'Produto cadastrado com sucesso.',
      )
      setSearch('')
      setPage(0)
      setLoading(true)
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

  return (
    <section className="records-page">
      {feedback && (
        <div className="record-feedback success" role="status">
          <span aria-hidden="true">✓</span>
          {feedback}
          <button
            type="button"
            className="feedback-dismiss"
            onClick={() => setFeedback('')}
            aria-label="Dispensar mensagem"
          >
            ×
          </button>
        </div>
      )}

      {loadError && (
        <div className="record-feedback error" role="alert">
          <span>{loadError}</span>
          <button
            type="button"
            className="text-button"
            onClick={retryLoad}
          >
            Tentar novamente
          </button>
        </div>
      )}

      <div className="records-toolbar">
        <label className="records-search">
          <SearchIcon />
          <span className="sr-only">Buscar produto</span>
          <input
            type="search"
            value={search}
            placeholder="Buscar por nome, descrição ou ID..."
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(0)
            }}
          />

          {search && (
            <button
              type="button"
              className="search-clear"
              onClick={() => {
                setSearch('')
                setPage(0)
              }}
              aria-label="Limpar busca"
            >
              ×
            </button>
          )}
        </label>

        <div className="records-toolbar-actions">
          <span className="records-count">
            {filteredItems.length}{' '}
            {filteredItems.length === 1 ? 'produto' : 'produtos'}
          </span>
          <button
            type="button"
            className="button-primary records-primary-action"
            onClick={startCreate}
          >
            <span aria-hidden="true">+</span>
            Novo produto
          </button>
        </div>
      </div>

      {formMode && (
        <form className="record-editor" onSubmit={handleSubmit}>
          <div className="record-editor-heading">
            <div>
              <span className="eyebrow">
                {formMode === 'edit'
                  ? 'ATUALIZAÇÃO DE CADASTRO'
                  : 'NOVO CADASTRO'}
              </span>
              <h2>
                {formMode === 'edit'
                  ? 'Editar produto'
                  : 'Cadastrar produto'}
              </h2>
              <p>
                Preencha os dados do produto. O saldo é controlado pelas movimentações.
              </p>
            </div>

            <button
              type="button"
              className="editor-close"
              onClick={closeForm}
              disabled={saving}
            >
              Cancelar
            </button>
          </div>

          {formError && (
            <div className="record-feedback error" role="alert">
              {formError}
            </div>
          )}

          {units.length === 0 && formMode === 'create' && (
            <div className="record-feedback notice" role="status">
              Cadastre uma unidade de medida antes de criar um produto.
              <button
                type="button"
                className="text-button"
                onClick={onNavigateUnits}
              >
                Ir para unidades
              </button>
            </div>
          )}

          <div className="record-form-grid">
            <div className="form-field">
              <label htmlFor="product-name">Nome do produto *</label>
              <input
                id="product-name"
                value={draft.nome}
                onChange={(event) => updateDraft('nome', event.target.value)}
                maxLength={160}
                placeholder="Ex.: Café em grãos"
                required
                autoFocus
              />
            </div>

            <div className="form-field">
              <label htmlFor="product-unit">Unidade de medida *</label>
              <select
                id="product-unit"
                className="record-field-select"
                value={draft.unidade_id}
                onChange={(event) => updateDraft('unidade_id', event.target.value)}
                required
              >
                <option value="">Selecione uma unidade</option>
                {formMode === 'edit'
                  && draft.unidade_id
                  && !unitById.has(Number(draft.unidade_id)) && (
                    <option value={draft.unidade_id}>
                      Unidade atual (#{draft.unidade_id})
                    </option>
                )}
                {units.map((unit) => (
                  <option value={unit.id} key={unit.id}>
                    {unit.nome}{unit.simbolo ? ` (${unit.simbolo})` : ''}
                  </option>
                ))}
              </select>

              {unitById.get(Number(draft.unidade_id)) && (
                <small className="field-help">
                  {unitById.get(Number(draft.unidade_id)).permite_decimal
                    ? 'Esta unidade permite quantidades fracionárias.'
                    : 'Esta unidade aceita somente quantidades inteiras.'}
                </small>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="product-minimum">Estoque mínimo</label>
              <input
                id="product-minimum"
                type="number"
                min="0"
                step={
                  unitById.get(Number(draft.unidade_id))?.permite_decimal
                    ? '0.0001'
                    : '1'
                }
                value={draft.estoque_minimo}
                onChange={(event) => updateDraft(
                  'estoque_minimo',
                  event.target.value,
                )}
                required
              />
              <small className="field-help">
                Quantidade mínima usada para sinalizar a necessidade de atenção.
              </small>
            </div>

            <div className="form-field record-description-field">
              <label htmlFor="product-description">Descrição</label>
              <textarea
                id="product-description"
                value={draft.descricao}
                onChange={(event) => updateDraft(
                  'descricao',
                  event.target.value,
                )}
                maxLength={2000}
                rows={3}
                placeholder="Detalhes úteis para identificar o produto (opcional)"
              />
              <small className="field-help">
                {draft.descricao.length}/2000 caracteres
              </small>
            </div>
          </div>

          <div className="record-editor-footer">
            <button
              type="button"
              className="button-secondary"
              onClick={closeForm}
              disabled={saving}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="button-primary"
              disabled={saving || (units.length === 0 && formMode === 'create')}
            >
              {saving
                ? 'Salvando...'
                : formMode === 'edit'
                  ? 'Salvar alterações'
                  : 'Cadastrar produto'}
            </button>
          </div>
        </form>
      )}

      <div className="records-table-panel">
        <div className="records-table-heading">
          <div>
            <h2>Catálogo de produtos</h2>
            <p>Produtos ativos cadastrados na empresa selecionada.</p>
          </div>
          <span className="table-live-indicator">
            <i />
            Dados da API
          </span>
        </div>

        {loading ? (
          <div className="records-loading" aria-label="Carregando produtos">
            {Array.from({ length: 5 }, (_, index) => (
              <div className="records-loading-row" key={index}>
                <span />
                <span />
                <span />
              </div>
            ))}
          </div>
        ) : loadError ? (
          <ProductEmpty
            title="Não foi possível carregar os produtos"
            description="Verifique a conexão com o backend e tente novamente."
          />
        ) : filteredItems.length === 0 ? (
          search ? (
            <ProductEmpty
              title="Nenhum resultado encontrado"
              description="Tente outro nome, descrição ou identificador de produto."
              action={(
                <button
                  type="button"
                  className="button-secondary records-empty-action"
                  onClick={() => setSearch('')}
                >
                  Limpar busca
                </button>
              )}
            />
          ) : (
            <ProductEmpty
              title="Seu catálogo começa aqui"
              description="Cadastre o primeiro produto para começar a acompanhar seu estoque."
              action={(
                <button
                  type="button"
                  className="button-primary records-empty-action"
                  onClick={startCreate}
                >
                  Cadastrar primeiro produto
                </button>
              )}
            />
          )
        ) : (
          <>
            <div className="records-table-scroll">
              <table className="records-table">
                <thead>
                  <tr>
                    <th>Produto</th>
                    <th>Unidade</th>
                    <th className="records-number-column">Saldo atual</th>
                    <th className="records-number-column">Mínimo</th>
                    <th>Situação</th>
                    <th><span className="sr-only">Ações</span></th>
                  </tr>
                </thead>
                <tbody>
                  {visibleItems.map((item) => {
                    const unit = unitById.get(Number(item.unidade_id))
                    const balance = balanceByItemId.get(Number(item.id))
                    const isLow = lowStockIds.has(Number(item.id))

                    return (
                      <tr key={item.id}>
                        <td>
                          <div className="records-product">
                            <span className="records-product-symbol">
                              {(item.nome || 'P').trim().charAt(0).toUpperCase()}
                            </span>
                            <span>
                              <strong>{item.nome}</strong>
                              <small>
                                Item #{item.id}
                                {item.descricao ? ` · ${item.descricao}` : ''}
                              </small>
                            </span>
                          </div>
                        </td>

                        <td>
                          <span className="records-unit-name">
                            {unit?.nome ?? `Unidade #${item.unidade_id}`}
                          </span>
                          <small className="records-unit-symbol">
                            {unit?.simbolo || '—'}
                          </small>
                        </td>

                        <td className="records-number-column">
                          {balance
                            ? formatQuantity(balance.saldo_atual)
                            : '—'}
                        </td>

                        <td className="records-number-column">
                          {formatQuantity(item.estoque_minimo)}
                        </td>

                        <td>
                          <span
                            className={`status-chip ${
                              isLow ? 'status-warning' : 'status-neutral'
                            }`}
                          >
                            {isLow ? 'Estoque baixo' : 'Sem alerta'}
                          </span>
                        </td>

                        <td>
                          <button
                            type="button"
                            className="table-action"
                            onClick={() => startEdit(item)}
                            aria-label={`Editar ${item.nome}`}
                          >
                            Editar
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="records-pagination">
              <span>
                Exibindo {currentPage * PAGE_SIZE + 1}–
                {Math.min(
                  (currentPage + 1) * PAGE_SIZE,
                  filteredItems.length,
                )}{' '}
                de {filteredItems.length} produtos
              </span>

              <div className="pagination-controls">
                <button
                  type="button"
                  className="pagination-button"
                  onClick={() => setPage((value) => Math.max(0, value - 1))}
                  disabled={currentPage === 0}
                >
                  Anterior
                </button>
                <span>{currentPage + 1} / {pageCount}</span>
                <button
                  type="button"
                  className="pagination-button"
                  onClick={() => setPage(
                    (value) => Math.min(pageCount - 1, value + 1),
                  )}
                  disabled={currentPage >= pageCount - 1}
                >
                  Próxima
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      <p className="records-page-note">
        O cadastro do produto não altera o saldo. Entradas, saídas e ajustes
        serão realizados pela área de movimentações.
      </p>
    </section>
  )
}

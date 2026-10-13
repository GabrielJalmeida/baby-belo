
import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import ProductCustomFields from './ProductCustomFields.jsx'

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


function customRecordColumn(record) {
  const columns = [
    'valor_texto', 'valor_inteiro', 'valor_decimal',
    'valor_monetario', 'valor_booleano', 'valor_data', 'opcao_id',
  ]
  return columns.find((column) => record[column] !== null && record[column] !== undefined) ?? null
}

function customRecordDraftValue(record) {
  const column = customRecordColumn(record)
  if (!column) return ''
  return String(record[column])
}

function parseCustomFieldValue(field, rawValue) {
  const text = String(rawValue ?? '').trim()
  if (text === '') return null

  if (field.tipo_dado === 'TEXTO_CURTO' || field.tipo_dado === 'TEXTO_LONGO') {
    return { valor_texto: text }
  }
  if (field.tipo_dado === 'INTEIRO') {
    const value = Number(text)
    if (!Number.isSafeInteger(value)) throw new Error(`O campo "${field.nome}" precisa ser um número inteiro válido.`)
    return { valor_inteiro: value }
  }
  if (field.tipo_dado === 'DECIMAL' || field.tipo_dado === 'DINHEIRO') {
    const normalized = text.includes(',') ? text.replace(/\./g, '').replace(',', '.') : text
    const value = Number(normalized)
    if (!Number.isFinite(value)) throw new Error(`Informe um número válido no campo "${field.nome}".`)
    const fraction = normalized.split('.')[1] ?? ''
    const maxDecimals = field.tipo_dado === 'DINHEIRO' ? 2 : 4
    if (fraction.length > maxDecimals) {
      throw new Error(`O campo "${field.nome}" aceita no máximo ${maxDecimals} casas decimais.`)
    }
    return field.tipo_dado === 'DINHEIRO'
      ? { valor_monetario: value }
      : { valor_decimal: value }
  }
  if (field.tipo_dado === 'BOOLEANO') {
    if (text !== 'true' && text !== 'false') throw new Error(`Escolha Sim ou Não no campo "${field.nome}".`)
    return { valor_booleano: text === 'true' }
  }
  if (field.tipo_dado === 'DATA') {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) throw new Error(`Informe uma data válida no campo "${field.nome}".`)
    return { valor_data: text }
  }
  if (field.tipo_dado === 'LISTA') {
    const value = Number(text)
    if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`Selecione uma opção no campo "${field.nome}".`)
    return { opcao_id: value }
  }
  throw new Error(`O tipo do campo "${field.nome}" não é suportado pelo formulário.`)
}

function customRecordMatches(record, payload) {
  const column = Object.keys(payload)[0]
  if (customRecordColumn(record) !== column) return false
  const oldValue = record[column]
  const newValue = payload[column]
  if (typeof newValue === 'number') return Number(oldValue) === newValue
  return String(oldValue) === String(newValue)
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

  const [customCategories, setCustomCategories] = useState([])
  const [customCategoriesLoading, setCustomCategoriesLoading] = useState(false)
  const [customCategoriesError, setCustomCategoriesError] = useState('')
  const [customCategoriesReloadKey, setCustomCategoriesReloadKey] = useState(0)
  const [customCategoryId, setCustomCategoryId] = useState('')
  const [originalCustomCategoryId, setOriginalCustomCategoryId] = useState('')
  const [customFields, setCustomFields] = useState([])
  const [customOptions, setCustomOptions] = useState({})
  const [customDraft, setCustomDraft] = useState({})
  const [customRecords, setCustomRecords] = useState([])
  const [customLoading, setCustomLoading] = useState(false)
  const [customError, setCustomError] = useState('')
  const [customItemDataLoading, setCustomItemDataLoading] = useState(false)
  const [customFieldsReloadKey, setCustomFieldsReloadKey] = useState(0)


  useEffect(() => {
    if (!formMode) return undefined
    let cancelled = false

    api.customCategories(companyId)
      .then((result) => {
        if (!cancelled) {
          setCustomCategories(result)
          setCustomCategoriesError('')
        }
      })
      .catch((error) => {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setCustomCategoriesError(error.message)
      })
      .finally(() => {
        if (!cancelled) setCustomCategoriesLoading(false)
      })

    return () => { cancelled = true }
  }, [companyId, formMode, onLogout, customCategoriesReloadKey])

  useEffect(() => {
    if (!formMode || !customCategoryId) return undefined
    let cancelled = false

    async function loadFieldsAndOptions() {
      try {
        const nextFields = await api.customFields(companyId, Number(customCategoryId))
        const optionEntries = await Promise.all(
          nextFields
            .filter((field) => field.tipo_dado === 'LISTA')
            .map(async (field) => [String(field.id), await api.customOptions(companyId, field.id)]),
        )
        if (cancelled) return
        setCustomFields(nextFields)
        setCustomOptions(Object.fromEntries(optionEntries))
        setCustomError('')
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setCustomFields([])
        setCustomOptions({})
        setCustomError(error.message)
      } finally {
        if (!cancelled) setCustomLoading(false)
      }
    }

    void loadFieldsAndOptions()
    return () => { cancelled = true }
  }, [companyId, formMode, customCategoryId, customFieldsReloadKey, onLogout])


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


  async function loadItemCustomData(itemId) {
    setCustomItemDataLoading(true)
    setCustomError('')
    try {
      const associationPromise = api.itemCategory(companyId, itemId).catch((error) => {
        if (error instanceof ApiError && error.status === 404) return null
        throw error
      })
      const [association, records] = await Promise.all([
        associationPromise,
        api.itemCustomValues(companyId, itemId),
      ])
      const categoryId = association?.categoria_id ? String(association.categoria_id) : ''
      setCustomCategoryId(categoryId)
      setOriginalCustomCategoryId(categoryId)
      setCustomRecords(records)
      setCustomDraft(Object.fromEntries(records.map((record) => [String(record.campo_id), customRecordDraftValue(record)])))
      if (categoryId) setCustomLoading(true)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setCustomError(`Não foi possível carregar os valores personalizados deste produto: ${error.message}`)
    } finally {
      setCustomItemDataLoading(false)
    }
  }

  function handleCustomCategoryChange(categoryId) {
    if (customRecords.length > 0 || customItemDataLoading) return
    setCustomCategoryId(categoryId)
    setCustomDraft({})
    setCustomFields([])
    setCustomOptions({})
    setCustomError('')
    setCustomLoading(Boolean(categoryId))
  }

  function handleCustomValueChange(fieldId, value) {
    setCustomDraft((previous) => ({ ...previous, [fieldId]: value }))
  }

  function retryCustomCategories() {
    setCustomCategoriesError('')
    setCustomCategoriesLoading(true)
    setCustomCategoriesReloadKey((value) => value + 1)
  }

  function retryCustomFields() {
    setCustomError('')
    setCustomLoading(true)
    setCustomFieldsReloadKey((value) => value + 1)
  }


  function startCreate() {
    setEditingId(null)
    setDraft({
      nome: '',
      descricao: '',
      unidade_id: units[0] ? String(units[0].id) : '',
      estoque_minimo: '0',
    })
    setCustomCategoryId('')
    setOriginalCustomCategoryId('')
    setCustomFields([])
    setCustomOptions({})
    setCustomDraft({})
    setCustomRecords([])
    setCustomError('')
    setCustomLoading(false)
    setCustomItemDataLoading(false)
    setCustomCategoriesError('')
    setCustomCategoriesLoading(true)
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
    setCustomCategoryId('')
    setOriginalCustomCategoryId('')
    setCustomFields([])
    setCustomOptions({})
    setCustomDraft({})
    setCustomRecords([])
    setCustomError('')
    setCustomLoading(false)
    setCustomItemDataLoading(true)
    setCustomCategoriesError('')
    setCustomCategoriesLoading(true)
    setFormError('')
    setFeedback('')
    setFormMode('edit')
    void loadItemCustomData(item.id)
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
    const keepingExistingUnit = existingItem && Number(existingItem.unidade_id) === unitId

    if (!name) return setFormError('Informe o nome do produto.')
    if (!unitId || (!selectedUnit && !keepingExistingUnit)) return setFormError('Selecione uma unidade de medida disponível.')
    if (!minimumText || !Number.isFinite(minimum) || minimum < 0) return setFormError('Informe um estoque mínimo válido e não negativo.')
    if (selectedUnit && !selectedUnit.permite_decimal && !Number.isInteger(minimum)) {
      return setFormError('Esta unidade aceita somente quantidades inteiras. Ajuste o estoque mínimo.')
    }
    if (customItemDataLoading || customLoading) {
      return setFormError('Aguarde o carregamento dos campos personalizados antes de salvar.')
    }
    if (customError && (customCategoryId || formMode === 'edit')) {
      return setFormError('Resolva o erro ao carregar os dados personalizados antes de salvar.')
    }
    if (customCategoryId && customCategoriesError) {
      return setFormError('Não foi possível confirmar as categorias. Tente carregar as categorias novamente.')
    }

    const recordByField = new Map(customRecords.map((record) => [String(record.campo_id), record]))
    const parsedCustomValues = new Map()
    if (customCategoryId) {
      for (const field of customFields) {
        const raw = customDraft[String(field.id)] ?? ''
        const isBlank = String(raw).trim() === ''
        const record = recordByField.get(String(field.id))
        if (field.obrigatorio && isBlank) {
          return setFormError(`O campo personalizado "${field.nome}" é obrigatório.`)
        }
        if (isBlank && record) {
          return setFormError(`O campo "${field.nome}" já possui um valor salvo. A API atual não oferece exclusão de valores personalizados; mantenha o valor ou restaure-o antes de salvar.`)
        }
        if (!isBlank) {
          try {
            parsedCustomValues.set(String(field.id), parseCustomFieldValue(field, raw))
          } catch (error) {
            return setFormError(error.message)
          }
        }
      }
    }

    const payload = {
      nome: name,
      descricao: draft.descricao.trim() || null,
      estoque_minimo: minimumText,
    }
    if (!existingItem || Number(existingItem.unidade_id) !== unitId) payload.unidade_id = unitId

    const wasCreating = formMode === 'create'
    let baseSaved = false
    let savedItemId = editingId
    let completedRecords = [...customRecords]

    setSaving(true)
    try {
      if (wasCreating) {
        payload.unidade_id = unitId
        const createdItem = await api.createItem(companyId, payload)
        savedItemId = createdItem.id
        baseSaved = true
        // Persistir o ID no formulário evita duplicar o produto se uma chamada CUSTOM falhar.
        setEditingId(savedItemId)
        setFormMode('edit')
        setOriginalCustomCategoryId('')
        setCustomRecords([])
        completedRecords = []
      } else {
        await api.updateItem(companyId, editingId, payload)
        baseSaved = true
      }

      if (customCategoryId && String(customCategoryId) !== String(originalCustomCategoryId)) {
        await api.assignItemCategory(companyId, savedItemId, customCategoryId)
        setOriginalCustomCategoryId(String(customCategoryId))
      }

      if (customCategoryId) {
        for (const field of customFields) {
          const fieldId = String(field.id)
          const valuePayload = parsedCustomValues.get(fieldId)
          if (!valuePayload) continue

          const existingRecord = completedRecords.find((record) => String(record.campo_id) === fieldId)
          if (existingRecord && customRecordMatches(existingRecord, valuePayload)) continue

          let savedRecord
          if (existingRecord) {
            savedRecord = await api.updateItemCustomValue(companyId, existingRecord.id, valuePayload)
          } else {
            savedRecord = await api.createItemCustomValue(companyId, savedItemId, {
              campo_id: Number(field.id),
              ...valuePayload,
            })
          }
          completedRecords = existingRecord
            ? completedRecords.map((record) => record.id === savedRecord.id ? savedRecord : record)
            : [...completedRecords, savedRecord]
          setCustomRecords(completedRecords)
        }
      }

      setFormMode(null)
      setEditingId(null)
      setFeedback(wasCreating ? 'Produto cadastrado com sucesso.' : 'Produto atualizado com sucesso.')
      setSearch('')
      setPage(0)
      setLoading(true)
      setReloadKey((value) => value + 1)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setCustomRecords(completedRecords)
      setFormError(baseSaved
        ? `Os dados básicos do produto foram salvos, mas não foi possível concluir todos os campos personalizados. O produto ${savedItemId ? `#${savedItemId} ` : ''}já existe. Revise o erro e tente salvar novamente. ${error.message}`
        : error.message)
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


          <ProductCustomFields
            categories={customCategories}
            categoriesLoading={customCategoriesLoading}
            categoriesError={customCategoriesError}
            categoryId={customCategoryId}
            originalCategoryId={originalCustomCategoryId}
            categoryLocked={customRecords.length > 0}
            fields={customFields}
            options={customOptions}
            values={customDraft}
            loading={customLoading}
            error={customError}
            itemDataLoading={customItemDataLoading}
            onCategoryChange={handleCustomCategoryChange}
            onValueChange={handleCustomValueChange}
            onRetryCategories={retryCustomCategories}
            onRetryFields={retryCustomFields}
          />

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
              disabled={saving || customItemDataLoading || customLoading || (units.length === 0 && formMode === 'create')}
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

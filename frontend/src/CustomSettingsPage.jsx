import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'
import './CustomSettingsPage.css'

const FIELD_TYPES = [
  { value: 'TEXTO_CURTO', label: 'Texto curto' },
  { value: 'TEXTO_LONGO', label: 'Texto longo' },
  { value: 'INTEIRO', label: 'Número inteiro' },
  { value: 'DECIMAL', label: 'Número decimal' },
  { value: 'DINHEIRO', label: 'Dinheiro' },
  { value: 'BOOLEANO', label: 'Sim ou não' },
  { value: 'DATA', label: 'Data' },
  { value: 'LISTA', label: 'Lista de opções' },
]

function fieldTypeLabel(type) {
  return FIELD_TYPES.find((item) => item.value === type)?.label ?? type
}

function FieldSettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 16.5h7m-7 4h7m3-4h6m-6 4h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

function InlineEmpty({ title, description }) {
  return (
    <div className="custom-empty">
      <span className="custom-empty-icon" aria-hidden="true"><FieldSettingsIcon /></span>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
}

function formatDate(value) {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '—'
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' }).format(parsed)
}

function emptyFieldDraft() {
  return {
    nome: '',
    tipo_dado: 'TEXTO_CURTO',
    obrigatorio: false,
    ordem_exibicao: '0',
    configuracao: '{}',
  }
}

export default function CustomSettingsPage({ companyId, onLogout }) {
  const [categories, setCategories] = useState([])
  const [categoriesLoading, setCategoriesLoading] = useState(true)
  const [categoriesError, setCategoriesError] = useState('')
  const [categoriesReloadKey, setCategoriesReloadKey] = useState(0)
  const [selectedCategoryId, setSelectedCategoryId] = useState(null)
  const [categorySearch, setCategorySearch] = useState('')
  const [categoryFormMode, setCategoryFormMode] = useState(null)
  const [categoryDraft, setCategoryDraft] = useState({ nome: '', descricao: '' })
  const [categorySaving, setCategorySaving] = useState(false)
  const [categoryFormError, setCategoryFormError] = useState('')

  const [fields, setFields] = useState([])
  const [fieldsCategoryId, setFieldsCategoryId] = useState(null)
  const [fieldsLoading, setFieldsLoading] = useState(false)
  const [fieldsError, setFieldsError] = useState('')
  const [fieldsReloadKey, setFieldsReloadKey] = useState(0)
  const [fieldFormMode, setFieldFormMode] = useState(null)
  const [editingFieldId, setEditingFieldId] = useState(null)
  const [fieldDraft, setFieldDraft] = useState(emptyFieldDraft)
  const [fieldSaving, setFieldSaving] = useState(false)
  const [fieldFormError, setFieldFormError] = useState('')

  const [expandedFieldId, setExpandedFieldId] = useState(null)
  const [optionsByField, setOptionsByField] = useState({})
  const [optionsLoading, setOptionsLoading] = useState({})
  const [optionsErrors, setOptionsErrors] = useState({})
  const [optionDraft, setOptionDraft] = useState({ valor: '', ordem_exibicao: '0' })
  const [optionSaving, setOptionSaving] = useState(false)
  const [optionFormError, setOptionFormError] = useState('')
  const [editingOptionId, setEditingOptionId] = useState(null)
  const [feedback, setFeedback] = useState('')

  const selectedCategory = useMemo(
    () => categories.find((category) => Number(category.id) === Number(selectedCategoryId)) ?? null,
    [categories, selectedCategoryId],
  )

  const filteredCategories = useMemo(() => {
    const query = categorySearch.trim().toLocaleLowerCase('pt-BR')
    if (!query) return categories
    return categories.filter((category) => (
      category.nome.toLocaleLowerCase('pt-BR').includes(query)
      || String(category.id).includes(query)
      || (category.descricao ?? '').toLocaleLowerCase('pt-BR').includes(query)
    ))
  }, [categories, categorySearch])

  const visibleFields = fieldsCategoryId === selectedCategoryId ? fields : []
  const visibleFieldsLoading = fieldsLoading || (selectedCategoryId !== null && fieldsCategoryId !== selectedCategoryId)

  useEffect(() => {
    let cancelled = false

    async function loadCategories() {
      try {
        const result = await api.customCategories(companyId)
        if (cancelled) return
        const activeCategories = Array.isArray(result) ? result : []
        setCategories(activeCategories)
        setSelectedCategoryId((previous) => (
          activeCategories.some((item) => Number(item.id) === Number(previous))
            ? previous
            : activeCategories[0]?.id ?? null
        ))
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setCategoriesError(error.message)
      } finally {
        if (!cancelled) setCategoriesLoading(false)
      }
    }

    void loadCategories()
    return () => { cancelled = true }
  }, [companyId, categoriesReloadKey, onLogout])

  useEffect(() => {
    if (!selectedCategoryId) return undefined
    let cancelled = false

    async function loadFields() {
      try {
        const result = await api.customFields(companyId, selectedCategoryId)
        if (cancelled) return
        setFields(Array.isArray(result) ? result : [])
        setFieldsCategoryId(selectedCategoryId)
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setFieldsError(error.message)
        setFields([])
        setFieldsCategoryId(selectedCategoryId)
      } finally {
        if (!cancelled) setFieldsLoading(false)
      }
    }

    void loadFields()
    return () => { cancelled = true }
  }, [companyId, selectedCategoryId, fieldsReloadKey, onLogout])

  function reloadCategories() {
    setCategoriesLoading(true)
    setCategoriesError('')
    setCategoriesReloadKey((value) => value + 1)
  }

  function reloadFields() {
    setFieldsLoading(true)
    setFieldsError('')
    setFieldsReloadKey((value) => value + 1)
  }

  function startCreateCategory() {
    setCategoryDraft({ nome: '', descricao: '' })
    setCategoryFormError('')
    setCategoryFormMode('create')
  }

  function startEditCategory(category) {
    setCategoryDraft({ nome: category.nome, descricao: category.descricao ?? '' })
    setCategoryFormError('')
    setCategoryFormMode('edit')
  }

  async function saveCategory(event) {
    event.preventDefault()
    setCategoryFormError('')
    const nome = categoryDraft.nome.trim()
    if (!nome) {
      setCategoryFormError('Informe um nome para a categoria.')
      return
    }

    setCategorySaving(true)
    try {
      const payload = { nome, descricao: categoryDraft.descricao.trim() || null }
      const saved = categoryFormMode === 'edit'
        ? await api.updateCustomCategory(companyId, selectedCategoryId, payload)
        : await api.createCustomCategory(companyId, payload)

      setCategories((previous) => (
        categoryFormMode === 'edit'
          ? previous.map((item) => Number(item.id) === Number(saved.id) ? saved : item)
          : [...previous, saved].sort((a, b) => Number(a.id) - Number(b.id))
      ))
      setSelectedCategoryId(saved.id)
      setCategorySearch('')
      setCategoryFormMode(null)
      setFeedback(categoryFormMode === 'edit' ? 'Categoria atualizada.' : 'Categoria criada.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setCategoryFormError(error.message)
    } finally {
      setCategorySaving(false)
    }
  }

  async function deactivateCategory(category) {
    const confirmed = window.confirm(`Inativar a categoria “${category.nome}”? Ela deixará de aparecer como opção normal.`)
    if (!confirmed) return

    try {
      await api.updateCustomCategory(companyId, category.id, { ativo: false })
      const remainingCategories = categories.filter((item) => Number(item.id) !== Number(category.id))
      setCategories(remainingCategories)
      if (Number(selectedCategoryId) === Number(category.id)) {
        setSelectedCategoryId(remainingCategories[0]?.id ?? null)
      }
      setExpandedFieldId(null)
      setFieldsError('')
      setFeedback('Categoria inativada. O histórico existente foi preservado.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setCategoriesError(error.message)
    }
  }

  function startCreateField() {
    setEditingFieldId(null)
    setFieldDraft(emptyFieldDraft())
    setFieldFormError('')
    setFieldFormMode('create')
  }

  function startEditField(field) {
    setEditingFieldId(field.id)
    setFieldDraft({
      nome: field.nome,
      tipo_dado: field.tipo_dado,
      obrigatorio: Boolean(field.obrigatorio),
      ordem_exibicao: String(field.ordem_exibicao ?? 0),
      configuracao: JSON.stringify(field.configuracao ?? {}, null, 2),
    })
    setFieldFormError('')
    setFieldFormMode('edit')
  }

  function closeFieldForm() {
    setFieldFormMode(null)
    setEditingFieldId(null)
    setFieldFormError('')
  }

  async function saveField(event) {
    event.preventDefault()
    setFieldFormError('')
    const nome = fieldDraft.nome.trim()
    const ordem = Number(fieldDraft.ordem_exibicao)
    if (!nome) {
      setFieldFormError('Informe o nome do campo.')
      return
    }
    if (!Number.isInteger(ordem) || ordem < 0) {
      setFieldFormError('A ordem deve ser um número inteiro igual ou maior que zero.')
      return
    }

    let configuracao
    try {
      configuracao = JSON.parse(fieldDraft.configuracao || '{}')
    } catch {
      setFieldFormError('A configuração precisa ser um JSON válido.')
      return
    }
    if (!configuracao || typeof configuracao !== 'object' || Array.isArray(configuracao)) {
      setFieldFormError('A configuração precisa ser um objeto JSON, por exemplo: {}.')
      return
    }

    setFieldSaving(true)
    try {
      const payload = {
        nome,
        tipo_dado: fieldDraft.tipo_dado,
        obrigatorio: fieldDraft.obrigatorio,
        ordem_exibicao: ordem,
        configuracao,
      }
      const saved = fieldFormMode === 'edit'
        ? await api.updateCustomField(companyId, editingFieldId, payload)
        : await api.createCustomField(companyId, { ...payload, categoria_id: selectedCategoryId })

      setFields((previous) => (
        fieldFormMode === 'edit'
          ? previous.map((item) => Number(item.id) === Number(saved.id) ? saved : item)
          : [...previous, saved].sort((a, b) => Number(a.ordem_exibicao) - Number(b.ordem_exibicao) || Number(a.id) - Number(b.id))
      ))
      setFieldsCategoryId(selectedCategoryId)
      setFieldFormMode(null)
      setEditingFieldId(null)
      setFeedback(fieldFormMode === 'edit' ? 'Campo atualizado.' : 'Campo criado.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setFieldFormError(error.message)
    } finally {
      setFieldSaving(false)
    }
  }

  async function deactivateField(field) {
    const confirmed = window.confirm(`Inativar o campo “${field.nome}”? Os valores já registrados não serão apagados.`)
    if (!confirmed) return
    try {
      await api.updateCustomField(companyId, field.id, { ativo: false })
      setFields((previous) => previous.filter((item) => Number(item.id) !== Number(field.id)))
      setOptionsByField((previous) => {
        const next = { ...previous }
        delete next[field.id]
        return next
      })
      if (Number(expandedFieldId) === Number(field.id)) setExpandedFieldId(null)
      setFeedback('Campo inativado. Os valores históricos foram preservados.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setFieldsError(error.message)
    }
  }

  async function loadOptions(field) {
    if (Number(expandedFieldId) === Number(field.id)) {
      setExpandedFieldId(null)
      setOptionFormError('')
      setEditingOptionId(null)
      return
    }
    setExpandedFieldId(field.id)
    setOptionDraft({ valor: '', ordem_exibicao: '0' })
    setEditingOptionId(null)
    setOptionFormError('')
    setOptionsErrors((previous) => ({ ...previous, [field.id]: '' }))
    setOptionsLoading((previous) => ({ ...previous, [field.id]: true }))
    try {
      const result = await api.customOptions(companyId, field.id)
      setOptionsByField((previous) => ({ ...previous, [field.id]: Array.isArray(result) ? result : [] }))
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setOptionsErrors((previous) => ({ ...previous, [field.id]: error.message }))
    } finally {
      setOptionsLoading((previous) => ({ ...previous, [field.id]: false }))
    }
  }

  function startEditOption(option) {
    setEditingOptionId(option.id)
    setOptionDraft({ valor: option.valor, ordem_exibicao: String(option.ordem_exibicao ?? 0) })
    setOptionFormError('')
  }

  async function saveOption(event, field) {
    event.preventDefault()
    setOptionFormError('')
    const valor = optionDraft.valor.trim()
    const ordem = Number(optionDraft.ordem_exibicao)
    if (!valor) {
      setOptionFormError('Informe o texto da opção.')
      return
    }
    if (!Number.isInteger(ordem) || ordem < 0) {
      setOptionFormError('A ordem deve ser um número inteiro igual ou maior que zero.')
      return
    }

    setOptionSaving(true)
    try {
      const payload = { valor, ordem_exibicao: ordem }
      if (editingOptionId !== null) {
        const saved = await api.updateCustomOption(companyId, editingOptionId, payload)
        setOptionsByField((previous) => ({
          ...previous,
          [field.id]: (previous[field.id] ?? []).map((item) => Number(item.id) === Number(saved.id) ? saved : item),
        }))
      } else {
        const saved = await api.createCustomOption(companyId, { ...payload, campo_id: field.id })
        setOptionsByField((previous) => ({
          ...previous,
          [field.id]: [...(previous[field.id] ?? []), saved].sort((a, b) => Number(a.ordem_exibicao) - Number(b.ordem_exibicao) || Number(a.id) - Number(b.id)),
        }))
      }
      setOptionDraft({ valor: '', ordem_exibicao: '0' })
      setEditingOptionId(null)
      setOptionFormError('')
      setFeedback(editingOptionId !== null ? 'Opção atualizada.' : 'Opção adicionada.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setOptionFormError(error.message)
    } finally {
      setOptionSaving(false)
    }
  }

  async function deactivateOption(field, option) {
    const confirmed = window.confirm(`Inativar a opção “${option.valor}”?`)
    if (!confirmed) return
    try {
      await api.updateCustomOption(companyId, option.id, { ativo: false })
      setOptionsByField((previous) => ({
        ...previous,
        [field.id]: (previous[field.id] ?? []).filter((item) => Number(item.id) !== Number(option.id)),
      }))
      if (Number(editingOptionId) === Number(option.id)) setEditingOptionId(null)
      setFeedback('Opção inativada.')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setOptionsErrors((previous) => ({ ...previous, [field.id]: error.message }))
    }
  }

  return (
    <section className="custom-settings-page">
      {feedback && (
        <div className="custom-feedback custom-feedback-success" role="status">
          <span aria-hidden="true">✓</span><span>{feedback}</span>
          <button type="button" onClick={() => setFeedback('')} aria-label="Dispensar mensagem">×</button>
        </div>
      )}

      <div className="custom-intro">
        <div className="custom-intro-icon"><FieldSettingsIcon /></div>
        <div>
          <span className="custom-kicker">ESTRUTURA CONFIGURÁVEL</span>
          <h2>Adapte os cadastros ao seu negócio</h2>
          <p>Crie categorias e defina campos específicos sem alterar a estrutura fixa do estoque.</p>
        </div>
      </div>

      <div className="custom-settings-layout">
        <aside className="custom-category-panel">
          <div className="custom-panel-heading">
            <div><h3>Categorias</h3><p>{categories.length} ativas</p></div>
            <button type="button" className="custom-button-primary custom-button-compact" onClick={startCreateCategory}>+ Nova</button>
          </div>

          <label className="custom-search-label">
            <span className="custom-sr-only">Buscar categoria</span>
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" strokeWidth="1.7" /><path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
            <input value={categorySearch} onChange={(event) => setCategorySearch(event.target.value)} placeholder="Buscar categoria..." />
          </label>

          {categoryFormMode && (
            <form className="custom-inline-editor" onSubmit={saveCategory}>
              <h4>{categoryFormMode === 'edit' ? 'Editar categoria' : 'Nova categoria'}</h4>
              <label>Nome<input autoFocus maxLength={120} value={categoryDraft.nome} onChange={(event) => setCategoryDraft((previous) => ({ ...previous, nome: event.target.value }))} required /></label>
              <label>Descrição <span className="custom-optional">(opcional)</span><textarea rows={3} maxLength={2000} value={categoryDraft.descricao} onChange={(event) => setCategoryDraft((previous) => ({ ...previous, descricao: event.target.value }))} /></label>
              {categoryFormError && <p className="custom-inline-error" role="alert">{categoryFormError}</p>}
              <div className="custom-editor-actions"><button className="custom-button-secondary" type="button" onClick={() => setCategoryFormMode(null)} disabled={categorySaving}>Cancelar</button><button className="custom-button-primary" type="submit" disabled={categorySaving}>{categorySaving ? 'Salvando…' : 'Salvar'}</button></div>
            </form>
          )}

          {categoriesError && <div className="custom-inline-error" role="alert">{categoriesError}<button type="button" className="custom-link-button" onClick={reloadCategories}>Tentar novamente</button></div>}
          {categoriesLoading ? (
            <div className="custom-loading" aria-label="Carregando categorias"><span /><span /><span /></div>
          ) : filteredCategories.length === 0 ? (
            <InlineEmpty title={categories.length ? 'Nenhuma categoria encontrada' : 'Comece pelas categorias'} description={categories.length ? 'Tente outro termo de busca.' : 'Crie uma categoria para organizar os campos específicos dos produtos.'} />
          ) : (
            <div className="custom-category-list">
              {filteredCategories.map((category) => (
                <button key={category.id} type="button" className={`custom-category-item${Number(selectedCategoryId) === Number(category.id) ? ' is-selected' : ''}`} onClick={() => { setSelectedCategoryId(category.id); setFieldsError(''); setFieldFormMode(null); setExpandedFieldId(null); setOptionFormError('') }} aria-pressed={Number(selectedCategoryId) === Number(category.id)}>
                  <span className="custom-category-symbol">{category.nome.trim().charAt(0).toLocaleUpperCase('pt-BR')}</span>
                  <span className="custom-category-copy"><strong>{category.nome}</strong><small>{category.descricao || `Criada em ${formatDate(category.criado_em)}`}</small></span>
                  <span className="custom-category-chevron" aria-hidden="true">›</span>
                </button>
              ))}
            </div>
          )}
        </aside>

        <div className="custom-fields-panel">
          {!selectedCategory ? (
            <div className="custom-no-category">
              <InlineEmpty title="Selecione uma categoria" description="Escolha uma categoria à esquerda ou crie uma nova para configurar os campos." />
            </div>
          ) : (
            <>
              <div className="custom-selected-category">
                <div className="custom-selected-category-copy">
                  <span className="custom-kicker">CATEGORIA SELECIONADA</span>
                  <h3>{selectedCategory.nome}</h3>
                  <p>{selectedCategory.descricao || 'Sem descrição cadastrada.'}</p>
                </div>
                <div className="custom-category-actions">
                  <button type="button" className="custom-button-secondary" onClick={() => startEditCategory(selectedCategory)}>Editar categoria</button>
                  <button type="button" className="custom-button-quiet-danger" onClick={() => deactivateCategory(selectedCategory)}>Inativar</button>
                </div>
              </div>

              <div className="custom-field-section-heading">
                <div><h3>Campos personalizados</h3><p>Os campos aparecem no cadastro do produto associado a esta categoria.</p></div>
                <button type="button" className="custom-button-primary" onClick={startCreateField}>+ Novo campo</button>
              </div>

              {fieldFormMode && (
                <form className="custom-field-editor" onSubmit={saveField}>
                  <div className="custom-editor-title"><div><span className="custom-kicker">CONFIGURAÇÃO DO CAMPO</span><h4>{fieldFormMode === 'edit' ? 'Editar campo' : 'Adicionar campo'}</h4></div><button type="button" className="custom-icon-button" onClick={closeFieldForm} aria-label="Fechar formulário" disabled={fieldSaving}>×</button></div>
                  <div className="custom-form-grid">
                    <label className="custom-span-two">Nome do campo<input autoFocus maxLength={120} value={fieldDraft.nome} onChange={(event) => setFieldDraft((previous) => ({ ...previous, nome: event.target.value }))} placeholder="Ex.: Composição, tamanho, acabamento" required /></label>
                    <label>Tipo de dado<select value={fieldDraft.tipo_dado} onChange={(event) => setFieldDraft((previous) => ({ ...previous, tipo_dado: event.target.value }))}>{FIELD_TYPES.map((type) => <option value={type.value} key={type.value}>{type.label}</option>)}</select>{fieldFormMode === 'edit' && <small className="custom-help">Se já houver valores, o backend pode bloquear a troca de tipo.</small>}</label>
                    <label>Ordem de exibição<input type="number" min="0" step="1" value={fieldDraft.ordem_exibicao} onChange={(event) => setFieldDraft((previous) => ({ ...previous, ordem_exibicao: event.target.value }))} required /></label>
                    <label className="custom-checkbox-label"><input type="checkbox" checked={fieldDraft.obrigatorio} onChange={(event) => setFieldDraft((previous) => ({ ...previous, obrigatorio: event.target.checked }))} /><span><strong>Campo obrigatório</strong><small>O preenchimento será exigido na experiência de cadastro integrada.</small></span></label>
                    <label className="custom-span-two">Configuração (JSON)<textarea className="custom-json-input" spellCheck="false" rows={4} value={fieldDraft.configuracao} onChange={(event) => setFieldDraft((previous) => ({ ...previous, configuracao: event.target.value }))} /><small className="custom-help">Use um objeto JSON. Para começar sem restrições adicionais, mantenha <code>{'{}'}</code>.</small></label>
                  </div>
                  {fieldFormError && <p className="custom-inline-error" role="alert">{fieldFormError}</p>}
                  <div className="custom-editor-actions"><button className="custom-button-secondary" type="button" onClick={closeFieldForm} disabled={fieldSaving}>Cancelar</button><button className="custom-button-primary" type="submit" disabled={fieldSaving}>{fieldSaving ? 'Salvando…' : 'Salvar campo'}</button></div>
                </form>
              )}

              {fieldsError && <div className="custom-error-banner" role="alert"><span>{fieldsError}</span><button className="custom-button-secondary" type="button" onClick={reloadFields}>Tentar novamente</button></div>}
              {visibleFieldsLoading ? (
                <div className="custom-loading-card"><div /><div /><div /></div>
              ) : visibleFields.length === 0 ? (
                <InlineEmpty title="Esta categoria ainda não tem campos" description="Adicione campos para registrar características próprias deste tipo de produto." />
              ) : (
                <div className="custom-field-list">
                  {visibleFields.map((field) => (
                    <article className="custom-field-card" key={field.id}>
                      <div className="custom-field-card-main">
                        <span className="custom-field-order">{field.ordem_exibicao}</span>
                        <div className="custom-field-card-copy"><div className="custom-field-name-row"><h4>{field.nome}</h4>{field.obrigatorio && <span className="custom-required-badge">Obrigatório</span>}</div><p>{fieldTypeLabel(field.tipo_dado)} <span aria-hidden="true">·</span> ID {field.id}</p></div>
                        <div className="custom-field-actions"><button type="button" className="custom-button-text" onClick={() => startEditField(field)}>Editar</button>{field.tipo_dado === 'LISTA' && <button type="button" className="custom-button-text" onClick={() => void loadOptions(field)}>{Number(expandedFieldId) === Number(field.id) ? 'Fechar opções' : 'Gerenciar opções'}</button>}<button type="button" className="custom-button-text custom-text-danger" onClick={() => deactivateField(field)}>Inativar</button></div>
                      </div>

                      {field.tipo_dado === 'LISTA' && Number(expandedFieldId) === Number(field.id) && (
                        <div className="custom-options-panel">
                          <div className="custom-options-heading"><div><h5>Opções de “{field.nome}”</h5><p>As opções inativas deixam de aparecer nos novos cadastros.</p></div><span>{(optionsByField[field.id] ?? []).length} opções</span></div>
                          {optionsErrors[field.id] && <div className="custom-inline-error" role="alert">{optionsErrors[field.id]}<button type="button" className="custom-link-button" onClick={() => void loadOptions(field)}>Tentar novamente</button></div>}
                          {optionsLoading[field.id] ? <div className="custom-loading"><span /><span /></div> : (optionsByField[field.id] ?? []).length === 0 ? <p className="custom-option-empty">Nenhuma opção ativa. Adicione a primeira abaixo.</p> : (
                            <div className="custom-option-list">
                              {(optionsByField[field.id] ?? []).map((option) => (
                                <div className="custom-option-row" key={option.id}>
                                  {Number(editingOptionId) === Number(option.id) ? (
                                    <form className="custom-option-edit" onSubmit={(event) => saveOption(event, field)}>
                                      <label>Valor<input autoFocus maxLength={150} value={optionDraft.valor} onChange={(event) => setOptionDraft((previous) => ({ ...previous, valor: event.target.value }))} required /></label>
                                      <label>Ordem<input type="number" min="0" step="1" value={optionDraft.ordem_exibicao} onChange={(event) => setOptionDraft((previous) => ({ ...previous, ordem_exibicao: event.target.value }))} required /></label>
                                      <div className="custom-editor-actions"><button type="button" className="custom-button-secondary" onClick={() => { setEditingOptionId(null); setOptionFormError('') }} disabled={optionSaving}>Cancelar</button><button type="submit" className="custom-button-primary" disabled={optionSaving}>{optionSaving ? 'Salvando…' : 'Salvar'}</button></div>
                                      {optionFormError && <p className="custom-inline-error" role="alert">{optionFormError}</p>}
                                    </form>
                                  ) : (
                                    <><span className="custom-option-order">{option.ordem_exibicao}</span><strong>{option.valor}</strong><div className="custom-field-actions"><button type="button" className="custom-button-text" onClick={() => startEditOption(option)}>Editar</button><button type="button" className="custom-button-text custom-text-danger" onClick={() => deactivateOption(field, option)}>Inativar</button></div></>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          {!editingOptionId && (
                            <form className="custom-option-create" onSubmit={(event) => saveOption(event, field)}>
                              <label>Nova opção<input maxLength={150} value={optionDraft.valor} onChange={(event) => setOptionDraft((previous) => ({ ...previous, valor: event.target.value }))} placeholder="Ex.: Algodão" required /></label>
                              <label>Ordem<input type="number" min="0" step="1" value={optionDraft.ordem_exibicao} onChange={(event) => setOptionDraft((previous) => ({ ...previous, ordem_exibicao: event.target.value }))} required /></label>
                              <button type="submit" className="custom-button-primary" disabled={optionSaving}>{optionSaving ? 'Salvando…' : 'Adicionar opção'}</button>
                              {optionFormError && <p className="custom-inline-error" role="alert">{optionFormError}</p>}
                            </form>
                          )}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}

import { useState } from 'react'
import { ApiError, api } from './api.js'
import './QuickCreate.css'

// Cadastro rápido usado dentro do formulário de produto.
// Não usa <form> próprio (não é permitido aninhar formulários):
// os botões são type="button" e o Enter é tratado manualmente,
// para nunca enviar o formulário do produto por engano.

function useQuickCreate({ onLogout, onCreated, save, validate, emptyDraft }) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(emptyDraft)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function openPanel() {
    setDraft(emptyDraft)
    setError('')
    setOpen(true)
  }

  function closePanel() {
    if (saving) return
    setOpen(false)
    setError('')
  }

  async function submit() {
    if (saving) return
    const validationError = validate(draft)
    if (validationError) {
      setError(validationError)
      return
    }
    setSaving(true)
    setError('')
    try {
      const saved = await save(draft)
      setOpen(false)
      onCreated(saved)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setError(err.message || 'Não foi possível salvar. Tente novamente.')
    } finally {
      setSaving(false)
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && event.target.tagName !== 'TEXTAREA') {
      event.preventDefault()
      void submit()
    } else if (event.key === 'Escape') {
      event.preventDefault()
      closePanel()
    }
  }

  return { open, draft, setDraft, saving, error, openPanel, closePanel, submit, handleKeyDown }
}

export function QuickCreateUnit({ companyId, onLogout, onCreated, disabled = false }) {
  const quick = useQuickCreate({
    onLogout,
    onCreated,
    emptyDraft: { nome: '', simbolo: '', permite_decimal: true },
    validate: (draft) => (draft.nome.trim() ? '' : 'Informe o nome da unidade.'),
    save: (draft) => api.createUnit(companyId, {
      nome: draft.nome.trim(),
      simbolo: draft.simbolo.trim() || null,
      permite_decimal: draft.permite_decimal,
    }),
  })

  if (!quick.open) {
    return (
      <button
        type="button"
        className="text-button quick-create-toggle"
        onClick={quick.openPanel}
        disabled={disabled}
      >
        + Nova unidade
      </button>
    )
  }

  return (
    <div className="quick-create-panel" onKeyDown={quick.handleKeyDown}>
      <div className="quick-create-title">Nova unidade de medida</div>

      {quick.error && (
        <div className="record-feedback error quick-create-error" role="alert">{quick.error}</div>
      )}

      <div className="quick-create-grid">
        <div className="form-field">
          <label htmlFor="quick-unit-name">Nome *</label>
          <input
            id="quick-unit-name"
            value={quick.draft.nome}
            onChange={(event) => quick.setDraft((prev) => ({ ...prev, nome: event.target.value }))}
            maxLength={80}
            placeholder="Ex.: Metro"
            disabled={quick.saving}
            autoFocus
          />
        </div>
        <div className="form-field">
          <label htmlFor="quick-unit-symbol">Símbolo</label>
          <input
            id="quick-unit-symbol"
            value={quick.draft.simbolo}
            onChange={(event) => quick.setDraft((prev) => ({ ...prev, simbolo: event.target.value }))}
            maxLength={20}
            placeholder="Ex.: m"
            disabled={quick.saving}
          />
        </div>
      </div>

      <label className="quick-create-check">
        <input
          type="checkbox"
          checked={quick.draft.permite_decimal}
          onChange={(event) => quick.setDraft((prev) => ({ ...prev, permite_decimal: event.target.checked }))}
          disabled={quick.saving}
        />
        Permite quantidades fracionárias (ex.: 1,5)
      </label>

      <div className="quick-create-actions">
        <button type="button" className="button-secondary" onClick={quick.closePanel} disabled={quick.saving}>
          Cancelar
        </button>
        <button type="button" className="button-primary" onClick={() => void quick.submit()} disabled={quick.saving}>
          {quick.saving ? 'Salvando…' : 'Salvar unidade'}
        </button>
      </div>
      <small className="field-help">
        Para editar ou inativar unidades, use a tela Unidades de medida.
      </small>
    </div>
  )
}

export function QuickCreateCategory({ companyId, onLogout, onCreated, disabled = false }) {
  const quick = useQuickCreate({
    onLogout,
    onCreated,
    emptyDraft: { nome: '', descricao: '' },
    validate: (draft) => (draft.nome.trim() ? '' : 'Informe o nome da categoria.'),
    save: (draft) => api.createCustomCategory(companyId, {
      nome: draft.nome.trim(),
      descricao: draft.descricao.trim() || null,
    }),
  })

  if (!quick.open) {
    return (
      <button
        type="button"
        className="text-button quick-create-toggle"
        onClick={quick.openPanel}
        disabled={disabled}
      >
        + Nova categoria
      </button>
    )
  }

  return (
    <div className="quick-create-panel" onKeyDown={quick.handleKeyDown}>
      <div className="quick-create-title">Nova categoria</div>

      {quick.error && (
        <div className="record-feedback error quick-create-error" role="alert">{quick.error}</div>
      )}

      <div className="quick-create-grid">
        <div className="form-field">
          <label htmlFor="quick-category-name">Nome *</label>
          <input
            id="quick-category-name"
            value={quick.draft.nome}
            onChange={(event) => quick.setDraft((prev) => ({ ...prev, nome: event.target.value }))}
            maxLength={120}
            placeholder="Ex.: Tecidos"
            disabled={quick.saving}
            autoFocus
          />
        </div>
        <div className="form-field">
          <label htmlFor="quick-category-description">Descrição</label>
          <input
            id="quick-category-description"
            value={quick.draft.descricao}
            onChange={(event) => quick.setDraft((prev) => ({ ...prev, descricao: event.target.value }))}
            placeholder="Opcional"
            disabled={quick.saving}
          />
        </div>
      </div>

      <div className="quick-create-actions">
        <button type="button" className="button-secondary" onClick={quick.closePanel} disabled={quick.saving}>
          Cancelar
        </button>
        <button type="button" className="button-primary" onClick={() => void quick.submit()} disabled={quick.saving}>
          {quick.saving ? 'Salvando…' : 'Salvar categoria'}
        </button>
      </div>
      <small className="field-help">
        A categoria é criada sem campos. Para adicionar campos, editar ou inativar, use a tela Categorias e campos.
      </small>
    </div>
  )
}

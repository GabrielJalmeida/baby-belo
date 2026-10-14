
import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from './api.js'

const PAGE_SIZE = 10

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

export default function UnitsPage({ companyId, onLogout, canWrite = true }) {
  const [units, setUnits] = useState([])
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
  const [showInactive, setShowInactive] = useState(false)
  const [actionBusyId, setActionBusyId] = useState(null)
  const [actionError, setActionError] = useState('')

  const [draft, setDraft] = useState({
    nome: '',
    simbolo: '',
    permite_decimal: true,
  })

  useEffect(() => {
    let cancelled = false

    async function loadUnits() {
      try {
        const result = await api.units(companyId, showInactive)

        if (!cancelled) {
          setUnits(result)
          setLoadError('')
        }
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

    void loadUnits()

    return () => {
      cancelled = true
    }
  }, [companyId, onLogout, reloadKey, showInactive])

  const filteredUnits = useMemo(() => {
    const query = search.trim().toLocaleLowerCase('pt-BR')

    if (!query) {
      return units
    }

    return units.filter((unit) => (
      unit.nome.toLocaleLowerCase('pt-BR').includes(query)
      || (unit.simbolo ?? '').toLocaleLowerCase('pt-BR').includes(query)
      || String(unit.id).includes(query)
    ))
  }, [units, search])

  const pageCount = Math.max(
    1,
    Math.ceil(filteredUnits.length / PAGE_SIZE),
  )
  const currentPage = Math.min(page, pageCount - 1)

  const visibleUnits = filteredUnits.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  )

  async function toggleUnitActive(unit) {
    const nextActive = !unit.ativo
    const action = nextActive ? 'reativar' : 'inativar'
    if (!window.confirm(`Deseja ${action} a unidade "${unit.nome}"? Os cadastros históricos serão preservados.`)) return

    setActionError('')
    setActionBusyId(unit.id)
    try {
      await api.updateUnit(companyId, unit.id, { ativo: nextActive })
      setFeedback(`Unidade "${unit.nome}" ${nextActive ? 'reativada' : 'inativada'} com sucesso.`)
      setLoading(true)
      setReloadKey((value) => value + 1)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout('Sua sessão expirou. Entre novamente.')
        return
      }
      setActionError(error.message || 'Não foi possível alterar a situação da unidade.')
    } finally {
      setActionBusyId(null)
    }
  }

  function retryLoad() {
    setLoading(true)
    setLoadError('')
    setReloadKey((value) => value + 1)
  }

  function startCreate() {
    setEditingId(null)
    setDraft({
      nome: '',
      simbolo: '',
      permite_decimal: true,
    })
    setFormError('')
    setFeedback('')
    setFormMode('create')
  }

  function startEdit(unit) {
    setEditingId(unit.id)
    setDraft({
      nome: unit.nome,
      simbolo: unit.simbolo ?? '',
      permite_decimal: unit.permite_decimal,
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

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setFeedback('')

    const name = draft.nome.trim()

    if (!name) {
      setFormError('Informe o nome da unidade.')
      return
    }

    const payload = {
      nome: name,
      simbolo: draft.simbolo.trim() || null,
      permite_decimal: draft.permite_decimal,
    }

    setSaving(true)

    try {
      if (formMode === 'edit') {
        await api.updateUnit(companyId, editingId, payload)
      } else {
        await api.createUnit(companyId, payload)
      }

      setFormMode(null)
      setEditingId(null)
      setFeedback(
        formMode === 'edit'
          ? 'Unidade atualizada com sucesso.'
          : 'Unidade cadastrada com sucesso.',
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

      {actionError && (
        <div className="record-feedback error" role="alert">
          <span>{actionError}</span>
          <button type="button" className="feedback-dismiss" onClick={() => setActionError('')} aria-label="Dispensar mensagem">×</button>
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
          <span className="sr-only">Buscar unidade</span>
          <input
            type="search"
            value={search}
            placeholder="Buscar por nome, símbolo ou ID..."
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
            {filteredUnits.length}{' '}
            {filteredUnits.length === 1 ? 'unidade' : 'unidades'}
          </span>
          <label className="records-include-inactive">
            <input type="checkbox" checked={showInactive} onChange={(event) => { setPage(0); setLoading(true); setShowInactive(event.target.checked) }} />
            <span>Incluir inativas</span>
          </label>
          {canWrite && (
            <button
              type="button"
              className="button-primary records-primary-action"
              onClick={startCreate}
            >
              <span aria-hidden="true">+</span>
              Nova unidade
            </button>
          )}
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
                  ? 'Editar unidade'
                  : 'Cadastrar unidade'}
              </h2>
              <p>
                A unidade define como as quantidades dos produtos serão registradas.
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

          <div className="record-form-grid">
            <div className="form-field">
              <label htmlFor="unit-name">Nome da unidade *</label>
              <input
                id="unit-name"
                value={draft.nome}
                onChange={(event) => setDraft((previous) => ({
                  ...previous,
                  nome: event.target.value,
                }))}
                maxLength={80}
                placeholder="Ex.: Unidade, Quilograma, Litro"
                required
                autoFocus
              />
            </div>

            <div className="form-field">
              <label htmlFor="unit-symbol">Símbolo</label>
              <input
                id="unit-symbol"
                value={draft.simbolo}
                onChange={(event) => setDraft((previous) => ({
                  ...previous,
                  simbolo: event.target.value,
                }))}
                maxLength={20}
                placeholder="Ex.: un, kg, L"
              />
              <small className="field-help">
                Opcional. Use uma abreviação reconhecível.
              </small>
            </div>
          </div>

          <label className="precision-option">
            <input
              type="checkbox"
              checked={draft.permite_decimal}
              onChange={(event) => setDraft((previous) => ({
                ...previous,
                permite_decimal: event.target.checked,
              }))}
            />

            <span className="precision-check" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path
                  d="m4 10 4 4 8-8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>

            <span>
              <strong>Permitir quantidades fracionárias</strong>
              <small>
                Ative para aceitar valores como 1,5 kg ou 0,75 litro.
                Desative para unidades contadas em números inteiros.
              </small>
            </span>
          </label>

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
              disabled={saving}
            >
              {saving
                ? 'Salvando...'
                : formMode === 'edit'
                  ? 'Salvar alterações'
                  : 'Cadastrar unidade'}
            </button>
          </div>
        </form>
      )}

      <div className="records-table-panel">
        <div className="records-table-heading">
          <div>
            <h2>Unidades cadastradas</h2>
            <p>{showInactive ? 'Unidades ativas e inativas cadastradas nesta empresa.' : 'Unidades ativas disponíveis para os produtos desta empresa.'}</p>
          </div>
          <span className="table-live-indicator">
            <i />
            Dados da API
          </span>
        </div>

        {loading ? (
          <div className="records-loading" aria-label="Carregando unidades">
            {Array.from({ length: 4 }, (_, index) => (
              <div className="records-loading-row" key={index}>
                <span />
                <span />
                <span />
              </div>
            ))}
          </div>
        ) : loadError ? (
          <div className="records-empty">
            <strong>Não foi possível carregar as unidades</strong>
            <p>Verifique a conexão com o backend e tente novamente.</p>
          </div>
        ) : filteredUnits.length === 0 ? (
          search ? (
            <div className="records-empty">
              <strong>Nenhuma unidade encontrada</strong>
              <p>Tente outro nome, símbolo ou identificador.</p>
              <button
                type="button"
                className="button-secondary records-empty-action"
                onClick={() => setSearch('')}
              >
                Limpar busca
              </button>
            </div>
          ) : (
            <div className="records-empty">
              <span className="records-empty-symbol" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none">
                  <path
                    d="M4 9h24v14H4zM10 9v5m6-5v8m6-8v5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <strong>Cadastre as unidades da sua operação</strong>
              <p>
                Exemplos: unidade, caixa, quilograma ou litro.
                Produtos precisam de uma unidade de medida.
              </p>
                  {canWrite && (
                    <button
                      type="button"
                      className="button-primary records-empty-action"
                      onClick={startCreate}
                    >
                      Cadastrar primeira unidade
                    </button>
                  )}
            </div>
          )
        ) : (
          <>
            <div className="records-table-scroll">
              <table className="records-table units-table">
                <thead>
                  <tr>
                    <th>Unidade</th>
                    <th>Símbolo</th>
                    <th>Precisão</th>
                    <th>Disponibilidade</th>
                    <th><span className="sr-only">Ações</span></th>
                  </tr>
                </thead>
                <tbody>
                  {visibleUnits.map((unit) => (
                    <tr key={unit.id}>
                      <td>
                        <div className="records-product">
                          <span className="records-product-symbol unit-symbol-mark">
                            {(unit.nome || 'U').trim().charAt(0).toUpperCase()}
                          </span>
                          <span>
                            <strong>{unit.nome}</strong>
                            <small>Unidade #{unit.id}</small>
                          </span>
                        </div>
                      </td>

                      <td>{unit.simbolo || '—'}</td>

                      <td>
                        <span
                          className={`status-chip ${
                            unit.permite_decimal
                              ? 'status-neutral'
                              : 'status-integer'
                          }`}
                        >
                          {unit.permite_decimal
                            ? 'Aceita frações'
                            : 'Inteiros'}
                        </span>
                      </td>

                      <td>
                        <span className={`unit-availability${unit.ativo ? '' : ' is-inactive'}`}>
                          <i />
                          {unit.ativo ? 'Ativa' : 'Inativa'}
                        </span>
                      </td>

                      <td>
                        {canWrite && (
                          <button
                            type="button"
                            className="table-action"
                            onClick={() => startEdit(unit)}
                            aria-label={`Editar unidade ${unit.nome}`}
                          >
                            Editar
                          </button>
                        )}
                        {canWrite && (
                          <button
                            type="button"
                            className="table-action"
                            disabled={actionBusyId === unit.id}
                            onClick={() => void toggleUnitActive(unit)}
                            aria-label={`${unit.ativo ? 'Inativar' : 'Reativar'} unidade ${unit.nome}`}
                          >
                            {actionBusyId === unit.id ? 'Salvando…' : unit.ativo ? 'Inativar' : 'Reativar'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="records-pagination">
              <span>
                Exibindo {currentPage * PAGE_SIZE + 1}–
                {Math.min(
                  (currentPage + 1) * PAGE_SIZE,
                  filteredUnits.length,
                )}{' '}
                de {filteredUnits.length} unidades
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
        Alterações na precisão de uma unidade podem ser recusadas quando
        existirem saldos fracionários ou inventários abertos.
      </p>
    </section>
  )
}

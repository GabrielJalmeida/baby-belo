import { useCallback, useEffect, useState } from 'react'
import { ApiError, api, session } from './api.js'
import ProductsPage from './ProductsPage.jsx'
import UnitsPage from './UnitsPage.jsx'
import MovementsPage from './MovementsPage.jsx'
import InventoriesPage from './InventoriesPage.jsx'
import StockLowPage from './StockLowPage.jsx'
import CustomSettingsPage from './CustomSettingsPage.jsx'
import './App.css'

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 40 40" fill="none">
        <rect x="1" y="1" width="38" height="38" rx="13" fill="currentColor" fillOpacity=".08" />
        <path d="M11 14.5 20 9l9 5.5v11L20 31l-9-5.5v-11Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        <path d="m11.5 14.5 8.5 5 8.5-5M20 20v10" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        <path d="m24 11.5 5 3" stroke="#8C8AE8" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    </span>
  )
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h14m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function BuildingIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 21V5.5L12 2l8 3.5V21M2 21h20M8 8h1m6 0h1M8 12h1m6 0h1M10 21v-5h4v5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5M15 16l4-4-4-4m4 4H9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M20 7v5h-5M4 17v-5h5m10-2a7 7 0 0 0-12-3L4 12m16 0-3 5a7 7 0 0 1-12-1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function OverviewIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3.5" y="3.5" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  )
}

function ProductsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="m4.5 7.8 7.5 4.4 7.5-4.4M12 12.2V21" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}

function MovementIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M7 7h13m0 0-4-4m4 4-4 4M17 17H4m0 0 4-4m-4 4 4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function InventoryIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7.5 12 3l8 4.5v9L12 21l-8-4.5v-9Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M4.5 7.7 12 12l7.5-4.3M12 12v9" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="m9 15 2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function StockLowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 22 20H2L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M12 9v5m0 3h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function CustomSettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 16.5h7m-7 4h7m3-4h6m-6 4h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

function AuthLayout({ children }) {
  return (
    <main className="auth-layout">
      <section className="auth-showcase">
        <a className="brand-lockup" href="#inicio" aria-label="Estoque Flex">
          <BrandMark />
          <span>
            <strong>Estoque Flex</strong>
            <small>GESTÃO DE ESTOQUE</small>
          </span>
        </a>

        <div className="showcase-copy" id="inicio">
          <span className="eyebrow">CLAREZA PARA O DIA A DIA</span>
          <h1>Seu estoque,<br /><span>em equilíbrio.</span></h1>
          <p>Informação organizada para acompanhar seus produtos, entender seus saldos e manter a operação sob controle.</p>
        </div>

        <div className="showcase-art" aria-hidden="true">
          <div className="art-orbit art-orbit-one" />
          <div className="art-orbit art-orbit-two" />
          <div className="art-window">
            <div className="art-window-top">
              <div className="art-window-dots"><i /><i /><i /></div>
              <span>ESPAÇO DE TRABALHO</span>
            </div>
            <div className="art-window-content">
              <div className="art-mini-sidebar"><i /><i /><i /><i /></div>
              <div className="art-mini-main">
                <div className="art-line art-line-title" />
                <div className="art-mini-cards"><div><i /><b /></div><div><i /><b /></div><div><i /><b /></div></div>
                <div className="art-mini-table"><i /><i /><i /></div>
              </div>
            </div>
          </div>
          <div className="art-floating-chip"><span className="art-chip-dot" />Organização em cada detalhe</div>
        </div>
        <p className="showcase-footer">Simples de entender. Confiável para trabalhar.</p>
      </section>

      <section className="auth-content">
        <div className="auth-content-inner">{children}</div>
        <p className="auth-legal">Estoque Flex <span>·</span> Ambiente de gestão</p>
      </section>
    </main>
  )
}

function LoginScreen({ onLogin, busy, error, notice }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  function handleSubmit(event) {
    event.preventDefault()
    onLogin(email, password)
  }

  return (
    <AuthLayout>
      <div className="auth-heading">
        <span className="eyebrow">ACESSO À CONTA</span>
        <h2>Bom ter você por aqui.</h2>
        <p>Entre com o e-mail e a senha da sua conta.</p>
      </div>
      {notice && <div className="notice-message" role="status">{notice}</div>}
      {error && <div className="error-message" role="alert">{error}</div>}
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="login-email">E-mail</label>
          <input id="login-email" name="email" type="email" autoComplete="username" placeholder="voce@empresa.com.br" value={email} onChange={(event) => setEmail(event.target.value)} required maxLength={254} autoFocus />
        </div>
        <div className="form-field">
          <div className="field-label-row"><label htmlFor="login-password">Senha</label></div>
          <div className="password-field">
            <input id="login-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Digite sua senha" value={password} onChange={(event) => setPassword(event.target.value)} required />
            <button type="button" className="password-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}>{showPassword ? 'Ocultar' : 'Mostrar'}</button>
          </div>
        </div>
        <button className="button-primary login-submit" type="submit" disabled={busy}>
          <span>{busy ? 'Validando acesso...' : 'Entrar na conta'}</span>
          {!busy && <ArrowIcon />}
          {busy && <span className="button-spinner" aria-hidden="true" />}
        </button>
      </form>
      <div className="auth-divider"><span /><i>ACESSO SEGURO</i><span /></div>
      <p className="auth-footnote">O acesso utiliza as credenciais cadastradas no sistema.</p>
    </AuthLayout>
  )
}

function CompanyScreen({ user, companies, onSelect, onCreate, onLogout }) {
  const [showCreate, setShowCreate] = useState(companies.length === 0)
  const [companyName, setCompanyName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleCreate(event) {
    event.preventDefault()
    const name = companyName.trim()
    if (!name) {
      setError('Informe o nome da empresa.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const company = await onCreate(name)
      onSelect(company)
    } catch (createError) {
      setError(createError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout>
      <div className="account-strip">
        <span className="user-avatar">{getInitials(user.nome)}</span>
        <div className="account-details">
          <span>CONTA AUTENTICADA</span>
          <strong>{user.nome}</strong>
          <small>{user.email}</small>
        </div>
        <button type="button" className="text-button" onClick={onLogout}>Sair</button>
      </div>
      <div className="auth-heading company-heading">
        <span className="eyebrow">SEU ESPAÇO DE TRABALHO</span>
        <h2>{companies.length ? 'Qual empresa vamos acessar?' : 'Vamos começar?'}</h2>
        <p>Escolha o contexto da operação. Seus dados serão consultados de acordo com a empresa selecionada.</p>
      </div>
      {error && <div className="error-message" role="alert">{error}</div>}
      {companies.length > 0 && (
        <div className="company-list">
          {companies.map((company) => (
            <button className="company-choice" type="button" key={company.id} onClick={() => onSelect(company)}>
              <span className="company-icon"><BuildingIcon /></span>
              <span className="company-choice-copy"><strong>{company.nome}</strong><small>{company.ativo ? 'Empresa disponível' : 'Empresa inativa'}</small></span>
              <span className="company-arrow"><ArrowIcon /></span>
            </button>
          ))}
        </div>
      )}
      {showCreate ? (
        <form className="create-company-form" onSubmit={handleCreate}>
          <div className="form-field">
            <label htmlFor="company-name">Nome da empresa</label>
            <input id="company-name" name="companyName" value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="Ex.: Minha empresa" maxLength={160} required autoFocus />
          </div>
          <button className="button-primary" type="submit" disabled={busy}>
            <span>{busy ? 'Criando empresa...' : 'Criar empresa e continuar'}</span>
            {!busy && <ArrowIcon />}
            {busy && <span className="button-spinner" aria-hidden="true" />}
          </button>
          {companies.length > 0 && <button type="button" className="secondary-button" onClick={() => { setShowCreate(false); setError('') }} disabled={busy}>Voltar às empresas</button>}
        </form>
      ) : (
        <button type="button" className="create-company-link" onClick={() => { setShowCreate(true); setError('') }}><span aria-hidden="true">+</span>Adicionar outra empresa</button>
      )}
      <p className="company-footnote">O contexto da empresa será enviado nas consultas que exigem isolamento de dados.</p>
    </AuthLayout>
  )
}

function getInitials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'EF'
  return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

function formatQuantity(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 4 }).format(number)
}

function EmptyState({ title, description }) {
  return (
    <div className="empty-state">
      <span className="empty-state-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="m5 11 11-6 11 6v12l-11 6-11-6V11Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="m5.5 11.5 10.5 6 10.5-6M16 18v10" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
        </svg>
      </span>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
}

function Dashboard({ user, company, companies, onSelectCompany, onLogout }) {
  const [balances, setBalances] = useState([])
  const [lowStockItems, setLowStockItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [activeSection, setActiveSection] = useState('overview')

  const refresh = () => {
    setError('')
    setLoading(true)
    setRefreshing(true)
    setReloadKey((value) => value + 1)
  }

  const navigateToSection = (section) => {
    if (section === activeSection) return
    if (section === 'overview') {
      setError('')
      setLoading(true)
      setRefreshing(false)
    }
    setActiveSection(section)
  }

  useEffect(() => {
    if (activeSection !== 'overview') return undefined
    let cancelled = false

    async function loadStockData() {
      try {
        const [stockBalances, lowStock] = await Promise.all([
          api.stockBalances(company.id),
          api.lowStock(company.id),
        ])
        if (cancelled) return
        setBalances(Array.isArray(stockBalances) ? stockBalances : [])
        setLowStockItems(Array.isArray(lowStock) ? lowStock : [])
        setError('')
      } catch (loadError) {
        if (cancelled) return
        if (loadError instanceof ApiError && loadError.status === 401) {
          onLogout('Sua sessão expirou. Entre novamente.')
          return
        }
        setError(loadError.message)
      } finally {
        if (!cancelled) {
          setLoading(false)
          setRefreshing(false)
        }
      }
    }

    void loadStockData()
    return () => { cancelled = true }
  }, [company.id, reloadKey, onLogout, activeSection])

  const pageTitle = activeSection === 'overview'
    ? 'Visão geral'
    : activeSection === 'products'
      ? 'Produtos'
      : activeSection === 'units'
        ? 'Unidades de medida'
        : activeSection === 'movements'
          ? 'Movimentações'
          : activeSection === 'inventories'
            ? 'Inventários'
            : activeSection === 'custom'
              ? 'Configurações personalizadas'
              : 'Estoque baixo'

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <a className="sidebar-brand" href="#visao-geral">
          <BrandMark />
          <span><strong>Estoque Flex</strong><small>GESTÃO DE ESTOQUE</small></span>
        </a>

        <div className="sidebar-section-label">ESPAÇO DE TRABALHO</div>
        <nav className="sidebar-navigation" aria-label="Navegação principal">
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'overview' ? 'page' : undefined} onClick={() => navigateToSection('overview')}><OverviewIcon /><span>Visão geral</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'products' ? 'page' : undefined} onClick={() => navigateToSection('products')}><ProductsIcon /><span>Produtos</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'units' ? 'page' : undefined} onClick={() => navigateToSection('units')}><BuildingIcon /><span>Unidades de medida</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'movements' ? 'page' : undefined} onClick={() => navigateToSection('movements')}><MovementIcon /><span>Movimentações</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'inventories' ? 'page' : undefined} onClick={() => navigateToSection('inventories')}><InventoryIcon /><span>Inventários</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'stock-low' ? 'page' : undefined} onClick={() => navigateToSection('stock-low')}><StockLowIcon /><span>Estoque baixo</span></button>
          <button type="button" className="sidebar-nav-item" aria-current={activeSection === 'custom' ? 'page' : undefined} onClick={() => navigateToSection('custom')}><CustomSettingsIcon /><span>Configurações CUSTOM</span></button>
        </nav>

        <div className="sidebar-context">
          <span className="context-label">EMPRESA ATIVA</span>
          <span className="context-name">{company.nome}</span>
          <p>Os dados exibidos pertencem ao contexto selecionado.</p>
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-user">
            <span className="user-avatar">{getInitials(user.nome)}</span>
            <span className="sidebar-user-copy"><strong>{user.nome}</strong><small>{user.email}</small></span>
          </div>
          <button className="sidebar-logout" type="button" onClick={() => onLogout()}><LogoutIcon /><span>Sair da conta</span></button>
        </div>
      </aside>

      <main className="app-main" id="visao-geral">
        <header className="app-topbar">
          <div className="topbar-context"><span className="topbar-kicker">ESTOQUE FLEX</span><span className="topbar-separator">/</span><span>{pageTitle}</span></div>
          <div className="topbar-actions">
            <label className="company-select-wrap">
              <span className="sr-only">Empresa ativa</span>
              <BuildingIcon />
              <select value={company.id} onChange={(event) => onSelectCompany(Number(event.target.value))} aria-label="Selecionar empresa ativa">
                {companies.map((item) => <option value={item.id} key={item.id}>{item.nome}</option>)}
              </select>
            </label>
            <span className="topbar-avatar" title={user.nome}>{getInitials(user.nome)}</span>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <span className="eyebrow">
                {activeSection === 'overview'
                  ? 'RESUMO OPERACIONAL'
                  : activeSection === 'products'
                    ? 'CATÁLOGO DE PRODUTOS'
                    : activeSection === 'units'
                      ? 'CONFIGURAÇÃO DO ESTOQUE'
                      : activeSection === 'inventories'
                      ? 'CONTAGEM E CONCILIAÇÃO'
                      : activeSection === 'custom'
                        ? 'CATEGORIAS E CAMPOS CONFIGURÁVEIS'
                        : activeSection === 'stock-low'
                          ? 'ACOMPANHAMENTO DE REPOSIÇÃO'
                          : 'OPERAÇÕES DE ESTOQUE'}
              </span>
              <h1>{pageTitle}</h1>
              <p>
                {activeSection === 'overview' ? (
                  <>Acompanhe os saldos e identifique o que precisa de atenção em <strong>{company.nome}</strong>.</>
                ) : activeSection === 'products' ? (
                  'Consulte, cadastre e atualize os produtos da empresa selecionada.'
                ) : activeSection === 'units' ? (
                  'Configure as unidades e a precisão das quantidades usadas no estoque.'
                ) : activeSection === 'inventories' ? (
                  'Registre a contagem física e concilie diferenças sem editar saldos diretamente.'
                ) : activeSection === 'custom' ? (
                  'Defina categorias, campos personalizados e opções de listas para adaptar os cadastros.'
                ) : activeSection === 'stock-low' ? (
                  'Priorize itens abaixo do mínimo e acesse as movimentações para repor o estoque.'
                ) : (
                  'Registre entradas, saídas e ajustes e consulte o histórico por produto.'
                )}
              </p>
            </div>
            {activeSection === 'overview' && (
              <button className="button-secondary refresh-button" type="button" onClick={refresh} disabled={loading || refreshing}>
                <RefreshIcon /><span>{refreshing ? 'Atualizando...' : 'Atualizar dados'}</span>
              </button>
            )}
          </section>

          {activeSection === 'products' ? (
            <ProductsPage companyId={company.id} onLogout={onLogout} onNavigateUnits={() => navigateToSection('units')} />
          ) : activeSection === 'units' ? (
            <UnitsPage companyId={company.id} onLogout={onLogout} />
          ) : activeSection === 'movements' ? (
            <MovementsPage companyId={company.id} onLogout={onLogout} onNavigateProducts={() => navigateToSection('products')} />
          ) : activeSection === 'inventories' ? (
            <InventoriesPage companyId={company.id} onLogout={onLogout} />
          ) : activeSection === 'custom' ? (
            <CustomSettingsPage companyId={company.id} onLogout={onLogout} />
          ) : activeSection === 'stock-low' ? (
            <StockLowPage
              companyId={company.id}
              onLogout={onLogout}
              onNavigateProducts={() => navigateToSection('products')}
              onNavigateMovements={() => navigateToSection('movements')}
            />
          ) : (
            <>
              {error && (
                <div className="error-banner" role="alert">
                  <div><strong>Não foi possível carregar os dados.</strong><p>{error}</p></div>
                  <button type="button" className="text-button" onClick={refresh}>Tentar novamente</button>
                </div>
              )}

              <section className="dashboard-grid">
                <article className="data-panel stock-panel">
                  <div className="panel-heading">
                    <div className="panel-icon panel-icon-lavender"><BuildingIcon /></div>
                    <div><h2>Saldos do estoque</h2><p>Produtos e quantidades retornados pela API.</p></div>
                  </div>
                  {loading && !error ? (
                    <div className="loading-lines" aria-label="Carregando saldos">
                      {Array.from({ length: 5 }, (_, index) => <div className="loading-line" key={index}><span /><i /></div>)}
                    </div>
                  ) : !error && balances.length === 0 ? (
                    <EmptyState title="Nenhum saldo para exibir" description="Quando houver itens e movimentações de estoque, os saldos aparecerão aqui." />
                  ) : !error ? (
                    <div className="table-scroll">
                      <table className="stock-table">
                        <thead><tr><th>Produto</th><th>Saldo atual</th><th>Mínimo</th></tr></thead>
                        <tbody>
                          {balances.map((item) => (
                            <tr key={item.item_id}>
                              <td><div className="table-product"><span className="product-symbol">{(item.item_nome || 'P').trim().charAt(0).toUpperCase()}</span><span className="product-cell-copy"><strong>{item.item_nome}</strong><small>Item #{item.item_id}</small></span></div></td>
                              <td className="numeric-cell">{formatQuantity(item.saldo_atual)}<small className="unit-suffix">{item.unidade_simbolo || item.unidade_nome || ''}</small></td>
                              <td className="numeric-cell">{formatQuantity(item.estoque_minimo)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                  <div className="panel-footnote">Exibindo até 8 resultados desta consulta.</div>
                </article>

                <article className="data-panel alerts-panel">
                  <div className="panel-heading">
                    <div className="panel-icon panel-icon-amber">
                      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M12 3 22 20H2L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                        <path d="M12 9v5m0 3h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                      </svg>
                    </div>
                    <div><h2>Estoque baixo</h2><p>Itens sinalizados pela regra da API.</p></div>
                  </div>
                  {loading && !error ? (
                    <div className="loading-lines" aria-label="Carregando alertas">
                      {Array.from({ length: 4 }, (_, index) => <div className="loading-line" key={index}><span /><i /></div>)}
                    </div>
                  ) : !error && lowStockItems.length === 0 ? (
                    <EmptyState title="Nenhum alerta retornado" description="A consulta atual não retornou itens abaixo do mínimo." />
                  ) : !error ? (
                    <div className="low-stock-list">
                      {lowStockItems.map((item) => (
                        <div className="low-stock-row" key={item.item_id}>
                          <span className="low-stock-indicator" />
                          <div className="low-stock-copy"><strong>{item.item_nome}</strong><small>Mínimo: {formatQuantity(item.estoque_minimo)}</small></div>
                          <div className="low-stock-amount"><strong>{formatQuantity(item.saldo_atual)}</strong><small>{item.unidade_simbolo || item.unidade_nome || 'unid.'}</small></div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  <div className="panel-footnote">Exibindo até 8 resultados desta consulta.</div>
                </article>
              </section>

              <p className="dashboard-note">Os saldos são consultados no backend. Esta visão não calcula nem altera o estoque no navegador.</p>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

function BootScreen() {
  return (
    <main className="boot-screen">
      <BrandMark />
      <span className="boot-spinner" />
      <h1>Preparando seu espaço</h1>
      <p>Validando a sessão e consultando suas empresas.</p>
    </main>
  )
}

function OfflineScreen({ message, onRetry, onLogout }) {
  return (
    <main className="boot-screen offline-screen">
      <BrandMark />
      <h1>Não foi possível conectar</h1>
      <p>{message}</p>
      <button className="button-primary" type="button" onClick={onRetry}>Tentar novamente <ArrowIcon /></button>
      <button className="text-button" type="button" onClick={onLogout}>Voltar ao login</button>
    </main>
  )
}

function App() {
  const [screen, setScreen] = useState(() => session.getToken() ? 'boot' : 'login')
  const [retryCount, setRetryCount] = useState(0)
  const [user, setUser] = useState(null)
  const [companies, setCompanies] = useState([])
  const [activeCompany, setActiveCompany] = useState(null)
  const [loginError, setLoginError] = useState('')
  const [loginNotice, setLoginNotice] = useState('')
  const [loginBusy, setLoginBusy] = useState(false)
  const [bootError, setBootError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      if (!session.getToken()) return
      try {
        const [profile, availableCompanies] = await Promise.all([api.me(), api.companies()])
        if (cancelled) return
        setUser(profile)
        setCompanies(availableCompanies)
        const savedCompanyId = session.getCompanyId()
        const savedCompany = availableCompanies.find((company) => String(company.id) === savedCompanyId)
        if (savedCompany) {
          setActiveCompany(savedCompany)
          setScreen('app')
        } else {
          session.clearCompany()
          setActiveCompany(null)
          setScreen('companies')
        }
      } catch (error) {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          session.clear()
          setLoginNotice('Sua sessão expirou. Entre novamente.')
          setScreen('login')
        } else {
          setBootError(error.message)
          setScreen('offline')
        }
      }
    }

    void restoreSession()
    return () => { cancelled = true }
  }, [retryCount])

  const handleLogout = useCallback((notice = '') => {
    session.clear()
    setUser(null)
    setCompanies([])
    setActiveCompany(null)
    setLoginError('')
    setLoginNotice(notice)
    setBootError('')
    setScreen('login')
  }, [])

  async function handleLogin(email, password) {
    setLoginBusy(true)
    setLoginError('')
    setLoginNotice('')
    session.clear()
    try {
      const tokenResponse = await api.login(email, password)
      session.saveToken(tokenResponse.access_token)
      const [profile, availableCompanies] = await Promise.all([api.me(), api.companies()])
      setUser(profile)
      setCompanies(availableCompanies)
      setActiveCompany(null)
      session.clearCompany()
      setScreen('companies')
    } catch (error) {
      session.clear()
      setLoginError(error instanceof ApiError && error.status === 401
        ? 'E-mail ou senha não conferem.'
        : error.message)
    } finally {
      setLoginBusy(false)
    }
  }

  async function handleCreateCompany(name) {
    const company = await api.createCompany(name)
    setCompanies((previous) => [...previous, company])
    return company
  }

  function handleSelectCompany(company) {
    session.saveCompanyId(company.id)
    setActiveCompany(company)
    setScreen('app')
  }

  function handleChangeCompany(companyId) {
    const company = companies.find((item) => item.id === companyId)
    if (company) handleSelectCompany(company)
  }

  function handleRetry() {
    setBootError('')
    setScreen('boot')
    setRetryCount((value) => value + 1)
  }

  if (screen === 'boot') return <BootScreen />
  if (screen === 'offline') {
    return <OfflineScreen message={bootError} onRetry={handleRetry} onLogout={() => handleLogout()} />
  }
  if (screen === 'login') {
    return <LoginScreen onLogin={handleLogin} busy={loginBusy} error={loginError} notice={loginNotice} />
  }
  if (screen === 'companies' && user) {
    return <CompanyScreen user={user} companies={companies} onSelect={handleSelectCompany} onCreate={handleCreateCompany} onLogout={() => handleLogout()} />
  }
  if (screen === 'app' && user && activeCompany) {
    return (
      <Dashboard
        key={activeCompany.id}
        user={user}
        company={activeCompany}
        companies={companies}
        onSelectCompany={handleChangeCompany}
        onLogout={handleLogout}
      />
    )
  }
  return <BootScreen />
}

export default App

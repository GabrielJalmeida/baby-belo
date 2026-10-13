const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '')
  .trim()
  .replace(/\/+$/, '')

const TOKEN_KEY = 'estoque-flex.access-token'
const COMPANY_KEY = 'estoque-flex.active-company-id'

export class ApiError extends Error {
  constructor(message, status = 0, payload = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export const session = {
  getToken() {
    return sessionStorage.getItem(TOKEN_KEY)
  },
  saveToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token)
  },
  getCompanyId() {
    return sessionStorage.getItem(COMPANY_KEY)
  },
  saveCompanyId(companyId) {
    sessionStorage.setItem(COMPANY_KEY, String(companyId))
  },
  clearCompany() {
    sessionStorage.removeItem(COMPANY_KEY)
  },
  clear() {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(COMPANY_KEY)
  },
}

function errorMessage(status, payload) {
  if (status === 401) return 'Sua sessão expirou ou não é válida. Entre novamente.'
  if (status === 403) return 'Você não tem permissão para realizar esta operação.'
  if (status === 404) return 'O recurso solicitado não foi encontrado.'
  if (status === 409) {
    return typeof payload?.detail === 'string'
      ? payload.detail
      : 'A operação entrou em conflito com o estado atual do sistema.'
  }
  if (status === 422) {
    if (Array.isArray(payload?.detail)) {
      return payload.detail.map((item) => {
        const field = item.loc?.at(-1)
        return field ? `${field}: ${item.msg}` : item.msg
      }).join(' · ')
    }
    return typeof payload?.detail === 'string'
      ? payload.detail
      : 'Confira os dados enviados e tente novamente.'
  }
  if (status >= 500) return 'O servidor encontrou um problema. Tente novamente em instantes.'
  return typeof payload?.detail === 'string'
    ? payload.detail
    : 'Não foi possível concluir a operação.'
}

async function readResponse(response) {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return { detail: text }
  }
}

export async function request(path, options = {}) {
  const {
    method = 'GET', body, form, companyId, signal,
    headers: extraHeaders, auth = true,
  } = options

  const headers = new Headers(extraHeaders)
  headers.set('Accept', 'application/json')
  const token = session.getToken()

  if (auth && token) headers.set('Authorization', `Bearer ${token}`)
  if (companyId !== undefined && companyId !== null) {
    headers.set('X-Company-ID', String(companyId))
  }

  let requestBody
  if (form !== undefined) {
    headers.set('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8')
    requestBody = new URLSearchParams(form)
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method, headers, body: requestBody, signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Não foi possível conectar à API. Verifique se o backend está ativo.')
  }

  const payload = await readResponse(response)
  if (!response.ok) {
    throw new ApiError(errorMessage(response.status, payload), response.status, payload)
  }
  return payload
}

async function fetchAllPages(path, options = {}) {
  const limit = 100
  const results = []
  for (let offset = 0; ; offset += limit) {
    const separator = path.includes('?') ? '&' : '?'
    const page = await request(`${path}${separator}limit=${limit}&offset=${offset}`, options)
    if (!Array.isArray(page)) {
      throw new ApiError('A API retornou um formato inesperado para uma listagem.')
    }
    results.push(...page)
    if (page.length < limit) return results
  }
}

export const api = {
  login(email, password) {
    return request('/api/v1/auth/login', {
      method: 'POST',
      auth: false,
      form: { username: email.trim(), password },
    })
  },

  me() {
    return request('/api/v1/auth/me')
  },

  companies() {
    return fetchAllPages('/api/v1/empresas')
  },

  createCompany(nome) {
    return request('/api/v1/empresas', { method: 'POST', body: { nome } })
  },

  items(companyId) {
    return fetchAllPages('/api/v1/itens', { companyId })
  },

  createItem(companyId, payload) {
    return request('/api/v1/itens', { method: 'POST', companyId, body: payload })
  },

  updateItem(companyId, itemId, payload) {
    return request(`/api/v1/itens/${itemId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  units(companyId) {
    return fetchAllPages('/api/v1/unidades', { companyId })
  },

  createUnit(companyId, payload) {
    return request('/api/v1/unidades', { method: 'POST', companyId, body: payload })
  },

  updateUnit(companyId, unitId, payload) {
    return request(`/api/v1/unidades/${unitId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  createMovement(companyId, payload) {
    return request('/api/v1/movimentacoes', {
      method: 'POST', companyId, body: payload,
    })
  },

  itemMovements(companyId, itemId, limit = 50, offset = 0) {
    return request(
      `/api/v1/itens/${itemId}/movimentacoes?limit=${limit}&offset=${offset}`,
      { companyId },
    )
  },

  itemBalance(companyId, itemId) {
    return request(`/api/v1/itens/${itemId}/saldo`, { companyId })
  },

  inventories(companyId) {
    return fetchAllPages('/api/v1/inventarios', { companyId })
  },

  createInventory(companyId, payload) {
    return request('/api/v1/inventarios', {
      method: 'POST', companyId, body: payload,
    })
  },

  inventoryDetail(companyId, inventoryId) {
    return request(`/api/v1/inventarios/${inventoryId}`, { companyId })
  },

  recordInventoryCount(companyId, inventoryId, itemId, quantity) {
    return request(`/api/v1/inventarios/${inventoryId}/itens/${itemId}/contagem`, {
      method: 'PUT', companyId, body: { quantidade_contada: quantity },
    })
  },

  completeInventory(companyId, inventoryId) {
    return request(`/api/v1/inventarios/${inventoryId}/concluir`, {
      method: 'POST', companyId,
    })
  },

  cancelInventory(companyId, inventoryId) {
    return request(`/api/v1/inventarios/${inventoryId}/cancelar`, {
      method: 'POST', companyId,
    })
  },

  customCategories(companyId) {
    return fetchAllPages('/api/v1/custom/categorias', { companyId })
  },

  createCustomCategory(companyId, payload) {
    return request('/api/v1/custom/categorias', {
      method: 'POST', companyId, body: payload,
    })
  },

  updateCustomCategory(companyId, categoryId, payload) {
    return request(`/api/v1/custom/categorias/${categoryId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  customFields(companyId, categoryId) {
    return fetchAllPages(
      `/api/v1/custom/campos?categoria_id=${encodeURIComponent(categoryId)}`,
      { companyId },
    )
  },

  createCustomField(companyId, payload) {
    return request('/api/v1/custom/campos', {
      method: 'POST', companyId, body: payload,
    })
  },

  updateCustomField(companyId, fieldId, payload) {
    return request(`/api/v1/custom/campos/${fieldId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  customOptions(companyId, fieldId) {
    return fetchAllPages(`/api/v1/custom/campos/${fieldId}/opcoes`, { companyId })
  },

  createCustomOption(companyId, payload) {
    return request('/api/v1/custom/opcoes', {
      method: 'POST', companyId, body: payload,
    })
  },

  updateCustomOption(companyId, optionId, payload) {
    return request(`/api/v1/custom/opcoes/${optionId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  itemCategory(companyId, itemId) {
    return request(`/api/v1/custom/itens/${itemId}/categoria`, { companyId })
  },

  assignItemCategory(companyId, itemId, categoryId) {
    return request(`/api/v1/custom/itens/${itemId}/categoria`, {
      method: 'PUT', companyId, body: { categoria_id: Number(categoryId) },
    })
  },

  itemCustomValues(companyId, itemId) {
    return fetchAllPages(`/api/v1/custom/itens/${itemId}/valores`, { companyId })
  },

  createItemCustomValue(companyId, itemId, payload) {
    return request(`/api/v1/custom/itens/${itemId}/valores`, {
      method: 'POST', companyId, body: payload,
    })
  },

  updateItemCustomValue(companyId, valueId, payload) {
    return request(`/api/v1/custom/valores/${valueId}`, {
      method: 'PATCH', companyId, body: payload,
    })
  },

  stockBalances(companyId, signal) {
    return request('/api/v1/estoque/saldos?limit=8&offset=0', { companyId, signal })
  },

  lowStock(companyId, signal) {
    return request('/api/v1/estoque/baixo?limit=8&offset=0', { companyId, signal })
  },

  stockBalancesAll(companyId) {
    return fetchAllPages('/api/v1/estoque/saldos', { companyId })
  },

  lowStockAll(companyId) {
    return fetchAllPages('/api/v1/estoque/baixo', { companyId })
  },
}

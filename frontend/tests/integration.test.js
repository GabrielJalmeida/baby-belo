import test from 'node:test'
import assert from 'node:assert/strict'
import { api, session, ApiError } from '../src/api.js'
import { resolveAtelier } from '../src/atelier.js'
import { readPreferences, applyPreferences, normalizePreferences } from '../src/accessibility.js'

const values = new Map()
globalThis.sessionStorage = { getItem: key => values.get(key) ?? null, setItem: (key,value) => values.set(key,String(value)), removeItem: key => values.delete(key) }
globalThis.window = new EventTarget()

// These are HTTP-contract tests only. Live PostgreSQL tests run separately.
test('protected requests require login and session expiry clears access', async () => {
  session.clear()
  let calls = 0
  globalThis.fetch = async () => { calls++; return Response.json({ detail:'expired' }, { status:401 }) }
  await assert.rejects(api.items(42), error => error.status === 401)
  assert.equal(calls,0)
  session.saveToken('contract-test-token')
  session.saveCompanyId(42)
  let expired = 0
  window.addEventListener('baby-belo:session-expired', () => expired++, { once:true })
  await assert.rejects(api.items(42), error => error.status === 401)
  assert.equal(expired,1)
  assert.equal(session.getToken(),null)
  assert.equal(session.getCompanyId(),null)
})

test('login uses the existing form endpoint without an authorization header', async () => {
  globalThis.fetch = async (url,options) => {
    assert.equal(url,'/api/v1/auth/login')
    assert.equal(options.method,'POST')
    assert.equal(options.headers.has('Authorization'),false)
    assert.equal(options.body.get('username'),'pessoa@example.com')
    assert.equal(options.body.get('password'),'contract-test-value')
    return Response.json({ access_token:'contract-test-token' })
  }
  assert.equal((await api.login(' pessoa@example.com ','contract-test-value')).access_token,'contract-test-token')
  assert.throws(() => session.saveToken(undefined), ApiError)
})

test('every stock module sends authenticated requests in the resolved tenant context', async () => {
  session.saveToken('contract-test-token')
  const cases = [
    [() => api.createItem(42,{nome:'Item'}),'/api/v1/itens','POST'],
    [() => api.updateItem(42,9,{ativo:false}),'/api/v1/itens/9','PATCH'],
    [() => api.createUnit(42,{nome:'Unidade'}),'/api/v1/unidades','POST'],
    [() => api.updateUnit(42,9,{ativo:false}),'/api/v1/unidades/9','PATCH'],
    [() => api.createMovement(42,{item_id:9,tipo:'ENTRADA',quantidade:2}),'/api/v1/movimentacoes','POST'],
    [() => api.itemMovements(42,9,20,0),'/api/v1/itens/9/movimentacoes?limit=20&offset=0','GET'],
    [() => api.itemBalance(42,9),'/api/v1/itens/9/saldo','GET'],
    [() => api.createInventory(42,{}),'/api/v1/inventarios','POST'],
    [() => api.inventoryDetail(42,9),'/api/v1/inventarios/9','GET'],
    [() => api.recordInventoryCount(42,9,8,2),'/api/v1/inventarios/9/itens/8/contagem','PUT'],
    [() => api.completeInventory(42,9),'/api/v1/inventarios/9/concluir','POST'],
    [() => api.cancelInventory(42,9),'/api/v1/inventarios/9/cancelar','POST'],
    [() => api.createCustomCategory(42,{nome:'Categoria'}),'/api/v1/custom/categorias','POST'],
    [() => api.updateCustomCategory(42,9,{ativo:false}),'/api/v1/custom/categorias/9','PATCH'],
    [() => api.createCustomField(42,{}),'/api/v1/custom/campos','POST'],
    [() => api.updateCustomField(42,9,{}),'/api/v1/custom/campos/9','PATCH'],
    [() => api.createCustomOption(42,{}),'/api/v1/custom/opcoes','POST'],
    [() => api.updateCustomOption(42,9,{}),'/api/v1/custom/opcoes/9','PATCH'],
    [() => api.assignItemCategory(42,9,8),'/api/v1/custom/itens/9/categoria','PUT'],
    [() => api.createItemCustomValue(42,9,{}),'/api/v1/custom/itens/9/valores','POST'],
    [() => api.updateItemCustomValue(42,9,{}),'/api/v1/custom/valores/9','PATCH'],
    [() => api.companyMembership(42),'/api/v1/empresas/42/membership','GET'],
  ]
  for (const [action,path,method] of cases) {
    globalThis.fetch = async (url,options) => {
      assert.equal(url,path)
      assert.equal(options.method,method)
      assert.equal(options.headers.get('Authorization'),'Bearer contract-test-token')
      assert.equal(options.headers.get('X-Company-ID'),'42')
      return Response.json({})
    }
    await action()
  }
})

test('all pages are read for filters and totals', async () => {
  session.saveToken('contract-test-token')
  let count=0
  globalThis.fetch=async url=>{count++; return Response.json(url.includes('offset=0')?Array.from({length:100},(_,id)=>({id})):[{id:100}])}
  assert.equal((await api.items(42)).length,101)
  assert.equal(count,2)
})

test('network and invalid server responses produce safe errors',async()=>{
  globalThis.fetch=async()=>{throw new Error('transport details')}
  await assert.rejects(api.items(42),error=>!error.message.includes('transport details'))
  globalThis.fetch=async()=>new Response('<html>Internal details</html>',{status:500})
  await assert.rejects(api.items(42),error=>error.status===500&&!error.message.includes('Internal details'))
  globalThis.fetch=async()=>new Response('<html>wrong service</html>')
  await assert.rejects(api.items(42),ApiError)
})

test('atelier is derived from authorized companies, with no fixed id or first-company fallback',()=>{
  assert.equal(resolveAtelier([{id:300,nome:'Outra empresa',ativo:true},{id:812,nome:'Baby Belo Ateliê',ativo:true}]).id,812)
  assert.throws(()=>resolveAtelier([{id:1,nome:'Outra empresa',ativo:true}]))
  assert.throws(()=>resolveAtelier([{id:1,nome:'Baby Belo',ativo:false}]))
  assert.throws(()=>resolveAtelier([{id:1,nome:'Baby Belo',ativo:true},{id:2,nome:'Ateliê Baby Belo',ativo:true}]))
})

test('accessibility preferences validate, persist, recover from corrupt storage and apply globally',()=>{
  const selected={dark:true,fontSize:'larger',contrast:true,underline:true}
  const storage={getItem:()=>JSON.stringify(selected)}
  assert.deepEqual(readPreferences(storage),selected)
  assert.equal(readPreferences({getItem:()=>'{broken'}).fontSize,'normal')
  assert.equal(readPreferences({getItem:()=>{throw new Error('blocked')}}).dark,false)
  assert.equal(normalizePreferences({dark:'true',fontSize:'invalid'}).dark,false)
  const root={dataset:{}}
  applyPreferences(root,selected)
  assert.deepEqual(root.dataset,{theme:'dark',fontSize:'larger',contrast:'true',underline:'true'})
})

import fs from 'node:fs/promises'
import path from 'node:path'
import crypto from 'node:crypto'
import { fileURLToPath } from 'node:url'
import EmbeddedPostgres from '../.local/node_modules/embedded-postgres/dist/index.js'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const stateDir = path.join(root, '.local')
await fs.mkdir(stateDir, { recursive: true })
const configPath = path.join(stateDir, 'config.json')
let config
try { config = JSON.parse(await fs.readFile(configPath, 'utf8')) }
catch (error) {
  if (error.code !== 'ENOENT') throw error
  config = { port: 55432, user: 'baby_belo_local', password: crypto.randomBytes(32).toString('hex'), secret: crypto.randomBytes(48).toString('hex') }
  await fs.writeFile(configPath, JSON.stringify(config, null, 2), { mode: 0o600, flag: 'wx' })
}
const pg = new EmbeddedPostgres({
  databaseDir: path.join(stateDir, 'postgres'), user: config.user, password: config.password,
  port: config.port, authMethod: 'scram-sha-256', persistent: true, autoRehydrateSymlinks: true,
  postgresFlags: ['-h', '127.0.0.1'], initdbFlags: ['--encoding=UTF8'],
  onLog: () => {}, onError: () => {},
})
try { await fs.access(path.join(stateDir, 'postgres', 'PG_VERSION')) }
catch { await pg.initialise() }
await pg.start()
const files = (await fs.readFile(path.join(root, 'database', 'apply_all.sql'), 'utf8'))
  .split(/\r?\n/).map(line => line.match(/^\\ir\s+(.+)$/)?.[1]).filter(Boolean)
const admin = pg.getPgClient('postgres', '127.0.0.1')
await admin.connect()
for (const name of ['baby_belo_dev', 'baby_belo_test', 'baby_belo_auth_test']) {
  const exists = await admin.query('SELECT 1 FROM pg_database WHERE datname = $1', [name])
  if (exists.rowCount) continue // Never modify an existing database automatically.
  await pg.createDatabase(name)
  const client = pg.getPgClient(name, '127.0.0.1')
  await client.connect()
  try {
    await client.query('BEGIN')
    for (const file of files) await client.query(await fs.readFile(path.join(root, 'database', file), 'utf8'))
    await client.query('COMMIT')
    console.log(`Banco novo preparado: ${name}`)
  } catch (error) { await client.query('ROLLBACK'); throw error }
  finally { await client.end() }
}
await admin.end()
console.log(`PostgreSQL local em 127.0.0.1:${config.port}. Dados preservados em .local/postgres. Ctrl+C encerra o servidor.`)
// Keep this process alive; embedded-postgres stops its child safely on exit.
setInterval(() => {}, 60_000)

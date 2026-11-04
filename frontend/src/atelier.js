/** Resolve only an active Baby Belo company returned for the authenticated user. */
export function resolveAtelier(companies) {
  const matches = companies.filter(company => company.ativo && /\bbaby\s+belo\b/.test(
    company.nome.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' '),
  ))
  if (matches.length === 0) throw new Error('Seu acesso ainda não está vinculado ao Baby Belo Ateliê. Peça ao responsável para verificar seu cadastro.')
  if (matches.length > 1) throw new Error('Há mais de um cadastro Baby Belo vinculado à sua conta. Peça ao responsável para revisar os vínculos antes de continuar.')
  return matches[0]
}

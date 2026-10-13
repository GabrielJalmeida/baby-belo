import './ProductCustomFields.css'

function fieldInput(field, value, options, onChange, disabled) {
  const common = {
    id: `custom-field-${field.id}`,
    value: value ?? '',
    onChange: (event) => onChange(String(field.id), event.target.value),
    disabled,
    'aria-required': field.obrigatorio ? 'true' : 'false',
  }

  switch (field.tipo_dado) {
    case 'TEXTO_CURTO':
      return <input {...common} type="text" maxLength={255} placeholder="Preencha o valor" />
    case 'TEXTO_LONGO':
      return <textarea {...common} rows={3} maxLength={10000} placeholder="Preencha o valor" />
    case 'INTEIRO':
      return <input {...common} type="number" step="1" placeholder="0" />
    case 'DECIMAL':
      return <input {...common} type="text" inputMode="decimal" placeholder="Ex.: 1,5" />
    case 'DINHEIRO':
      return <input {...common} type="text" inputMode="decimal" placeholder="Ex.: 29,90" />
    case 'BOOLEANO':
      return (
        <select {...common} className="record-field-select">
          <option value="">Selecione uma opção</option>
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      )
    case 'DATA':
      return <input {...common} type="date" />
    case 'LISTA': {
      const fieldOptions = options[String(field.id)] ?? []
      const optionIsMissing = value !== '' && !fieldOptions.some((option) => String(option.id) === String(value))
      return (
        <select {...common} className="record-field-select">
          <option value="">Selecione uma opção</option>
          {optionIsMissing && <option value={value}>Opção atual (#{value}) indisponível</option>}
          {fieldOptions.map((option) => (
            <option value={String(option.id)} key={option.id}>{option.valor}</option>
          ))}
        </select>
      )
    }
    default:
      return <input {...common} type="text" disabled placeholder="Tipo de campo não suportado" />
  }
}

export default function ProductCustomFields({
  categories,
  categoriesLoading,
  categoriesError,
  categoryId,
  originalCategoryId,
  categoryLocked,
  fields,
  options,
  values,
  loading,
  error,
  itemDataLoading,
  onCategoryChange,
  onValueChange,
  onRetryCategories,
  onRetryFields,
}) {
  const currentCategoryMissing = categoryId
    && !categories.some((category) => String(category.id) === String(categoryId))

  return (
    <section className="product-custom-section" aria-labelledby="product-custom-title">
      <div className="product-custom-heading">
        <div>
          <span className="eyebrow">PERSONALIZAÇÃO</span>
          <h3 id="product-custom-title">Campos personalizados</h3>
          <p>Use uma categoria para definir características específicas deste produto.</p>
        </div>
        <span className="product-custom-count">{categoryId ? `${fields.length} ${fields.length === 1 ? 'campo' : 'campos'}` : 'Opcional'}</span>
      </div>

      {categoriesError && (
        <div className="record-feedback error" role="alert">
          <span>{categoriesError}</span>
          <button type="button" className="text-button" onClick={onRetryCategories}>Tentar novamente</button>
        </div>
      )}

      {error && !categoryId && (
        <div className="record-feedback error" role="alert">
          <span>{error} Feche e reabra a edição deste produto para tentar carregar os dados novamente.</span>
        </div>
      )}

      <div className="product-custom-category">
        <label htmlFor="product-custom-category">Categoria</label>
        <select
          id="product-custom-category"
          className="record-field-select"
          value={categoryId}
          onChange={(event) => onCategoryChange(event.target.value)}
          disabled={itemDataLoading || categoriesLoading || categoryLocked}
        >
          {!originalCategoryId && <option value="">Sem categoria personalizada</option>}
          {currentCategoryMissing && <option value={categoryId}>Categoria atual (#{categoryId})</option>}
          {categories.map((category) => (
            <option key={category.id} value={String(category.id)}>
              {category.nome}
            </option>
          ))}
        </select>
        <small className="field-help">
          {itemDataLoading
            ? 'Carregando categoria e valores atuais…'
            : categoryLocked
              ? 'A categoria fica bloqueada porque o produto já possui valores personalizados salvos. Isso evita deixar valores incompatíveis.'
              : originalCategoryId
                ? 'Este produto já possui uma categoria. A API não oferece a ação de remover totalmente a associação.'
                : 'A categoria é opcional. Cadastre categorias e campos em Configurações CUSTOM.'}
        </small>
      </div>

      {categoryId && (
        <div className="product-custom-fields-area">
          {loading ? (
            <div className="product-custom-state" role="status">Carregando campos e opções…</div>
          ) : error ? (
            <div className="record-feedback error" role="alert">
              <span>{error}</span>
              <button type="button" className="text-button" onClick={onRetryFields}>Tentar novamente</button>
            </div>
          ) : fields.length === 0 ? (
            <div className="product-custom-state">
              Esta categoria ainda não tem campos ativos. Você pode salvar o produto e configurar os campos depois.
            </div>
          ) : (
            <div className="record-form-grid product-custom-grid">
              {fields.map((field) => (
                <div className="form-field" key={field.id}>
                  <label htmlFor={`custom-field-${field.id}`}>
                    {field.nome}{field.obrigatorio ? ' *' : ''}
                  </label>
                  {fieldInput(field, values[String(field.id)], options, onValueChange, itemDataLoading)}
                  <small className="field-help">
                    {field.tipo_dado.replaceAll('_', ' ').toLocaleLowerCase('pt-BR')}
                    {field.obrigatorio ? ' · obrigatório' : ' · opcional'}
                  </small>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

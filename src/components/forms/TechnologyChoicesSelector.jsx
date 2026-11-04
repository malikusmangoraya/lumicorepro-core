import { useTranslation } from 'react-i18next';
import Select from './Select';

const SINGLE_FIELDS = [
  ['frontend_framework', 'frontend_frameworks', 'frontendFramework'],
  ['admin_platform', 'admin_platforms', 'adminPlatform'],
  ['frontend_host', 'hosting_providers', 'frontendHost', 'frontend_host'],
  ['backend_host', 'hosting_providers', 'backendHost', ['backend_host', 'backend_and_database_host']],
  ['database_host', 'hosting_providers', 'databaseHost', ['database_host', 'backend_and_database_host']],
  ['source_control_provider', 'source_control_providers', 'sourceControlProvider'],
  ['ci_provider', 'ci_providers', 'ciProvider'],
  ['authentication_profile', 'authentication_profiles', 'authenticationProfile'],
];

const LIST_FIELDS = [
  ['testing_tools', 'testing_tools', 'testingTools'],
  ['quality_tools', 'quality_tools', 'qualityTools'],
];

const CATALOG_ONLY_STATUS = 'catalog_only_not_generated';

function compatibilityStatus(framework, provider, catalog) {
  if (!framework || !provider) return null;
  const frameworkOption = catalog?.frontend_frameworks?.find(({ id }) => id === framework);
  const providerOption = catalog?.hosting_providers?.find(({ id }) => id === provider);
  if (!frameworkOption || !providerOption) return null;

  const relations = [
    ...(frameworkOption.compatibility || [])
      .filter((item) => item.group === 'hosting_providers' && item.id === provider)
      .map((item) => item.status),
    ...(providerOption.compatibility || [])
      .filter((item) => item.group === 'frontend_frameworks' && item.id === framework)
      .map((item) => item.status),
  ];
  if (relations.includes('incompatible')) return 'incompatible';
  if (relations.includes('compatible')) return 'compatible';
  return 'unknown';
}

export default function TechnologyChoicesSelector({
  catalog,
  selection,
  onChange,
  manual,
  loading = false,
  error = false,
  disabled = false,
}) {
  const { t } = useTranslation();
  const selectedFramework = selection.frontend_framework || '';
  const selectedFrontendHost = selection.frontend_host || '';
  const hostStatus = compatibilityStatus(selectedFramework, selectedFrontendHost, catalog);

  const providers = catalog?.hosting_providers || [];
  const providerOptions = {
    frontend_host: providers.filter(({ category }) => category === 'frontend_host'),
    backend_host: providers.filter(({ category }) =>
      ['backend_host', 'backend_and_database_host'].includes(category)
    ),
    database_host: providers.filter(({ category }) =>
      ['database_host', 'backend_and_database_host'].includes(category)
    ),
  };

  if (!manual) return null;

  const update = (field, value) => {
    const next = { ...selection };
    if (value) next[field] = value;
    else delete next[field];
    onChange(next);
  };

  const frontendHosts = providerOptions.frontend_host.filter((provider) =>
    compatibilityStatus(selectedFramework, provider.id, catalog) !== 'incompatible'
  );

  const multiSelectField = ([field, catalogKey, labelKey]) => (
    <fieldset
      key={field}
      disabled={disabled || loading || !catalog}
      className="space-y-2"
    >
      <legend className="mb-1.5 text-sm font-medium text-foreground">
        {t(`technologyChoices.${labelKey}`)}
      </legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {(catalog?.[catalogKey] || []).map((option) => (
          <label key={option.id} className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={(selection[field] || []).includes(option.id)}
              onChange={(event) => {
                const selected = new Set(selection[field] || []);
                if (event.target.checked) selected.add(option.id);
                else selected.delete(option.id);
                const ordered = (catalog?.[catalogKey] || [])
                  .filter(({ id }) => selected.has(id))
                  .map(({ id }) => id);
                update(field, ordered);
              }}
              disabled={disabled || loading || !catalog}
              className="mt-1 accent-primary"
            />
            <span>
              <span className="block">{option.label}</span>
              <span className="block text-xs text-muted-foreground">
                {t('technologyChoices.catalogOnly')}
              </span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );

  return (
    <section
      className="space-y-4 rounded-xl border border-border/70 bg-background/40 p-4"
      aria-labelledby="technology-choices-heading"
    >
      <div>
        <h3 id="technology-choices-heading" className="text-sm font-semibold text-foreground">
          {t('technologyChoices.title')}
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {t('technologyChoices.description')}
        </p>
      </div>

      {loading && (
        <p className="text-xs text-muted-foreground" role="status">
          {t('technologyChoices.loading')}
        </p>
      )}
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {t('technologyChoices.catalogLoadError')}
        </p>
      )}

      <fieldset disabled={disabled || loading || !catalog} className="grid gap-3 sm:grid-cols-2">
        <legend className="sr-only">{t('technologyChoices.title')}</legend>
        {SINGLE_FIELDS.map(([field, catalogKey, labelKey, category]) => {
          const allOptions = catalog?.[catalogKey] || [];
          const options = category
            ? allOptions.filter((option) =>
              Array.isArray(category)
                ? category.includes(option.category)
                : option.category === category
            )
            : allOptions;
          const filtered = field === 'frontend_host' ? frontendHosts : options;
          return (
            <Select
              key={field}
              label={t(`technologyChoices.${labelKey}`)}
              value={selection[field] || ''}
              onChange={(event) => update(field, event.target.value)}
              disabled={disabled || loading || !catalog}
            >
              <option value="">{t('technologyChoices.recommended')}</option>
              {filtered.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </Select>
          );
        })}
      </fieldset>

      {hostStatus === 'unknown' && (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-800 dark:text-amber-200" role="status">
          {t('technologyChoices.unverifiedCompatibility')}
        </p>
      )}

      {LIST_FIELDS.map(multiSelectField)}

      {['authentication_libraries', 'engineering_topics'].map((catalogKey) => (
        <details key={catalogKey} className="rounded-lg border border-border/60 p-3">
          <summary className="cursor-pointer text-sm font-medium">
            {t(`technologyChoices.${catalogKey}`)}
          </summary>
          <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            {(catalog?.[catalogKey] || []).map((option) => (
              <li key={option.id} className="flex flex-wrap items-center justify-between gap-2">
                <span>{option.label}</span>
                <span className="text-xs text-muted-foreground">
                  {t('technologyChoices.catalogOnly')}
                </span>
              </li>
            ))}
          </ul>
        </details>
      ))}

      <p className="text-xs text-muted-foreground">
        {t('technologyChoices.providerTerms')}
      </p>
    </section>
  );
}

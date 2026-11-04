import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Select from './Select';

const ADVANCED_FIELDS = [
  ['api_style', 'api_styles', 'apiStyle'],
  ['architecture', 'architectures', 'architecture'],
  ['authentication', 'authentication', 'authentication'],
  ['cache', 'cache_options', 'cache'],
  ['queue', 'queue_options', 'queue'],
  ['testing', 'testing_options', 'testing'],
  ['observability', 'observability_options', 'observability'],
  ['deployment', 'deployment_options', 'deployment'],
];

export default function BackendStackSelector({
  catalog,
  selection,
  onChange,
  loading = false,
  error = false,
  disabled = false,
}) {
  const { t } = useTranslation();
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const languages = Object.entries(catalog?.languages || {});
  const selectedLanguage = catalog?.languages?.[selection.language];
  const frameworks = selectedLanguage?.frameworks || [];
  const selectedFramework = frameworks.find(({ id }) => id === selection.framework);
  const compatibleDatabaseIds = selectedFramework?.databases || [];
  const supportsDatabase = (orm, databaseId) => {
    const database = catalog?.databases?.find(({ id }) => id === databaseId);
    return Boolean(database && catalog?.orm_database_types?.[orm]?.includes(database.type));
  };
  const databases = (catalog?.databases || []).filter(({ id, type }) =>
    compatibleDatabaseIds.includes(id) &&
    (!selection.orm || catalog?.orm_database_types?.[selection.orm]?.includes(type))
  );
  const compatibleOrms = (selectedFramework?.orms || []).filter(
    (orm) => !selection.database || supportsDatabase(orm, selection.database)
  );
  const manual = selection.mode === 'manual';

  const update = (field, value) => {
    const nextSelection = { ...selection, [field]: value || undefined };
    if (
      field === 'database' &&
      nextSelection.orm &&
      !supportsDatabase(nextSelection.orm, nextSelection.database)
    ) {
      nextSelection.orm = undefined;
    }
    if (
      field === 'orm' &&
      nextSelection.database &&
      !supportsDatabase(nextSelection.orm, nextSelection.database)
    ) {
      nextSelection.database = undefined;
    }
    onChange(nextSelection);
  };

  const changeMode = (mode) => {
    onChange(mode === 'auto' ? { mode } : { mode: 'manual' });
  };

  const changeLanguage = (language) => {
    onChange({ mode: 'manual', language });
  };

  const changeFramework = (framework) => {
    onChange({
      ...selection,
      framework,
      database: undefined,
      orm: undefined,
    });
  };

  const renderOptions = (items, placeholder) => (
    <>
      <option value="">{t(placeholder)}</option>
      {items.map((item) => (
        <option key={item.id} value={item.id}>
          {item.label}
        </option>
      ))}
    </>
  );

  return (
    <section className="space-y-3 rounded-xl border border-border/70 bg-background/40 p-4">
      <fieldset disabled={disabled}>
        <legend className="mb-2 text-sm font-semibold text-foreground">
          {t('backendStack.title')}
        </legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {[
            ['auto', t('backendStack.auto'), t('backendStack.autoDescription')],
            ['manual', t('backendStack.manual'), t('backendStack.manualDescription')],
          ].map(([mode, label, description]) => (
            <label
              key={mode}
              className="flex cursor-pointer items-start gap-2 rounded-lg border border-border p-3 has-[:checked]:border-primary has-[:checked]:bg-primary/5 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50"
            >
              <input
                type="radio"
                name="backend-stack-mode"
                value={mode}
                aria-label={label}
                checked={selection.mode === mode}
                onChange={() => changeMode(mode)}
                disabled={mode === 'manual' && (!catalog || loading)}
                className="mt-1 accent-primary"
              />
              <span>
                <span className="block text-sm font-medium">{label}</span>
                <span className="block text-xs text-muted-foreground">{description}</span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {loading && (
        <p className="text-xs text-muted-foreground" role="status">
          {t('backendStack.loading')}
        </p>
      )}
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {t('backendStack.catalogLoadError')}
        </p>
      )}

      {manual && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Select
            label={t('backendStack.language')}
            value={selection.language || ''}
            onChange={(event) => changeLanguage(event.target.value)}
            disabled={disabled || loading || !catalog}
          >
            {renderOptions(
              languages.map(([id, language]) => ({ id, label: language.label })),
              'backendStack.selectLanguage'
            )}
          </Select>
          <Select
            label={t('backendStack.framework')}
            value={selection.framework || ''}
            onChange={(event) => changeFramework(event.target.value)}
            disabled={disabled || loading || !selectedLanguage}
          >
            {renderOptions(frameworks, 'backendStack.selectFramework')}
          </Select>
          <Select
            label={t('backendStack.database')}
            value={selection.database || ''}
            onChange={(event) => update('database', event.target.value)}
            disabled={disabled || loading || !selectedFramework}
          >
            {renderOptions(databases, 'backendStack.selectDatabase')}
          </Select>
          {compatibleOrms.length > 0 && (
            <Select
              label={t('backendStack.orm')}
              value={selection.orm || ''}
              onChange={(event) => update('orm', event.target.value)}
              disabled={disabled || loading || !selectedFramework}
            >
              {renderOptions(
                compatibleOrms.map((id) => ({ id, label: id })),
                'backendStack.selectOption'
              )}
            </Select>
          )}

          {(selectedLanguage?.scaffold_supported === false ||
            selectedFramework?.scaffold_supported === false) && (
            <p className="text-xs text-muted-foreground sm:col-span-2">
              {t('backendStack.unsupportedScaffold')}
            </p>
          )}

          <div className="sm:col-span-2">
            <button
              type="button"
              className="text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
              aria-expanded={advancedOpen}
              aria-label={t('backendStack.advancedOptions')}
              onClick={() => setAdvancedOpen((open) => !open)}
              disabled={disabled || loading || !catalog}
            >
              {t('backendStack.advancedOptions')}
            </button>
          </div>

          {advancedOpen &&
            ADVANCED_FIELDS.map(([field, catalogKey, labelKey]) => (
              <Select
                key={field}
                label={t(`backendStack.${labelKey}`)}
                value={selection[field] || ''}
                onChange={(event) => update(field, event.target.value)}
                disabled={disabled || loading}
              >
                {renderOptions(catalog?.[catalogKey] || [], 'backendStack.selectOption')}
              </Select>
            ))}
        </div>
      )}
    </section>
  );
}

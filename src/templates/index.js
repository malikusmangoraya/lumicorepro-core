/**
 * LumicorePro Templates — barrel file
 *
 * NOTE: This barrel only re-exports catalog + TemplateShell.
 * Individual template components are imported via direct lazy()
 * calls in src/routes/index.jsx — do NOT add eager exports here
 * or you'll break code splitting and balloon the initial JS bundle.
 */
export { TEMPLATE_CATALOG } from './catalog';
export { default as TemplateShell } from './_shared/TemplateShell';

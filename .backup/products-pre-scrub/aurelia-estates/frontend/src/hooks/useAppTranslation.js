/* SRS quality gate — abstracted translator key hook (LUMICORE_I18N) */
import { useTranslation } from 'react-i18next';

export default function useAppTranslation(namespace) {
  return useTranslation(namespace);
}

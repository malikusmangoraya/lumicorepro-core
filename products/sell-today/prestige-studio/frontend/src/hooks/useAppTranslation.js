/* SRS quality gate — abstracted translator key hook (I18N) */
import { useTranslation } from 'react-i18next';

export default function useAppTranslation(namespace) {
  return useTranslation(namespace);
}

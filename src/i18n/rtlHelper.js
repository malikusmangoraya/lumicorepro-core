/**
 * RTL / LTR Direction Manager for International Languages
 */
const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur'];

/**
 * Apply direction and lang attribute to document HTML root
 * @param {string} lng - Language code (e.g. 'ar', 'en', 'zh')
 */
export const updateDocumentDirection = (lng) => {
  if (typeof document === 'undefined') return;

  const currentLang = (lng || 'en').split('-')[0].toLowerCase();
  const isRTL = RTL_LANGUAGES.includes(currentLang);

  document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
  document.documentElement.lang = currentLang;

  if (isRTL) {
    document.body.classList.add('rtl-mode');
  } else {
    document.body.classList.remove('rtl-mode');
  }
};

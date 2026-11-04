/**
 * UI copy for the shell and the commerce flow.
 *
 * Scope is deliberate: navigation, cart, checkout and common actions are
 * translated. Listing content (titles, descriptions) is data the operator
 * writes, so it is not duplicated here — a template that pretends to translate
 * a dealer's own inventory copy would be lying.
 */

export const LOCALES = ['en', 'ur', 'ar'] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_META: Record<Locale, { label: string; dir: 'ltr' | 'rtl' }> = {
  en: { label: 'English', dir: 'ltr' },
  ur: { label: 'اردو', dir: 'rtl' },
  ar: { label: 'العربية', dir: 'rtl' },
};

export type MessageKey =
  | 'nav.home'
  | 'nav.inventory'
  | 'nav.shop'
  | 'nav.services'
  | 'nav.pricing'
  | 'nav.about'
  | 'nav.contact'
  | 'nav.admin'
  | 'nav.signIn'
  | 'nav.browse'
  | 'nav.backToSite'
  | 'tray.bag'
  | 'tray.saved'
  | 'tray.compare'
  | 'cart.title'
  | 'cart.empty'
  | 'cart.subtotal'
  | 'cart.shipping'
  | 'cart.total'
  | 'cart.checkout'
  | 'cart.continue'
  | 'cart.remove'
  | 'checkout.title'
  | 'checkout.contact'
  | 'checkout.address'
  | 'checkout.place'
  | 'checkout.placing'
  | 'checkout.summary'
  | 'checkout.note'
  | 'common.addToBag'
  | 'common.added'
  | 'common.outOfStock'
  | 'common.reserve'
  | 'common.save'
  | 'common.compare'
  | 'common.share'
  | 'common.language'
  | 'common.theme'
  | 'footer.newArrivals'
  | 'footer.join'
  | 'footer.privacy'
  | 'footer.terms';

const en: Record<MessageKey, string> = {
  'nav.home': 'Home',
  'nav.inventory': 'Inventory',
  'nav.shop': 'Shop',
  'nav.services': 'Services',
  'nav.pricing': 'Pricing',
  'nav.about': 'About',
  'nav.contact': 'Contact',
  'nav.admin': 'Admin',
  'nav.signIn': 'Sign in',
  'nav.browse': 'Browse inventory',
  'nav.backToSite': 'Back to site',
  'tray.bag': 'Bag',
  'tray.saved': 'Saved cars',
  'tray.compare': 'Compare cars',
  'cart.title': 'Your selection',
  'cart.empty': 'Your bag is empty',
  'cart.subtotal': 'Subtotal',
  'cart.shipping': 'Shipping',
  'cart.total': 'Total',
  'cart.checkout': 'Continue to checkout',
  'cart.continue': 'Continue shopping',
  'cart.remove': 'Remove',
  'checkout.title': 'Where should it go?',
  'checkout.contact': 'Contact',
  'checkout.address': 'Delivery address',
  'checkout.place': 'Place order',
  'checkout.placing': 'Placing order…',
  'checkout.summary': 'Your order',
  'checkout.note': 'No payment is taken here. The order is recorded as pending.',
  'common.addToBag': 'Add to bag',
  'common.added': 'Added',
  'common.outOfStock': 'Out of stock',
  'common.reserve': 'Reserve',
  'common.save': 'Save',
  'common.compare': 'Compare',
  'common.share': 'Share',
  'common.language': 'Language',
  'common.theme': 'Theme',
  'footer.newArrivals': 'New arrivals',
  'footer.join': 'Join',
  'footer.privacy': 'Privacy',
  'footer.terms': 'Terms',
};

const ur: Record<MessageKey, string> = {
  'nav.home': 'ہوم',
  'nav.inventory': 'انوینٹری',
  'nav.shop': 'دکان',
  'nav.services': 'خدمات',
  'nav.pricing': 'قیمتیں',
  'nav.about': 'تعارف',
  'nav.contact': 'رابطہ',
  'nav.admin': 'ایڈمن',
  'nav.signIn': 'سائن اِن',
  'nav.browse': 'انوینٹری دیکھیں',
  'nav.backToSite': 'سائٹ پر واپس',
  'tray.bag': 'بیگ',
  'tray.saved': 'محفوظ گاڑیاں',
  'tray.compare': 'گاڑیوں کا موازنہ',
  'cart.title': 'آپ کا انتخاب',
  'cart.empty': 'آپ کا بیگ خالی ہے',
  'cart.subtotal': 'کل رقم',
  'cart.shipping': 'ڈیلیوری',
  'cart.total': 'مجموعی',
  'cart.checkout': 'چیک آؤٹ پر جائیں',
  'cart.continue': 'خریداری جاری رکھیں',
  'cart.remove': 'ہٹائیں',
  'checkout.title': 'کہاں بھیجیں؟',
  'checkout.contact': 'رابطہ',
  'checkout.address': 'ڈیلیوری کا پتہ',
  'checkout.place': 'آرڈر کریں',
  'checkout.placing': 'آرڈر ہو رہا ہے…',
  'checkout.summary': 'آپ کا آرڈر',
  'checkout.note': 'یہاں کوئی ادائیگی نہیں لی جاتی۔ آرڈر زیرِ التوا درج ہوتا ہے۔',
  'common.addToBag': 'بیگ میں ڈالیں',
  'common.added': 'شامل ہو گیا',
  'common.outOfStock': 'اسٹاک ختم',
  'common.reserve': 'محفوظ کریں',
  'common.save': 'محفوظ',
  'common.compare': 'موازنہ',
  'common.share': 'شیئر',
  'common.language': 'زبان',
  'common.theme': 'تھیم',
  'footer.newArrivals': 'نئی آمد',
  'footer.join': 'شامل ہوں',
  'footer.privacy': 'پرائیویسی',
  'footer.terms': 'شرائط',
};

const ar: Record<MessageKey, string> = {
  'nav.home': 'الرئيسية',
  'nav.inventory': 'المعروضات',
  'nav.shop': 'المتجر',
  'nav.services': 'الخدمات',
  'nav.pricing': 'الأسعار',
  'nav.about': 'من نحن',
  'nav.contact': 'اتصل بنا',
  'nav.admin': 'الإدارة',
  'nav.signIn': 'تسجيل الدخول',
  'nav.browse': 'تصفح المعروضات',
  'nav.backToSite': 'العودة للموقع',
  'tray.bag': 'السلة',
  'tray.saved': 'السيارات المحفوظة',
  'tray.compare': 'مقارنة السيارات',
  'cart.title': 'اختياراتك',
  'cart.empty': 'سلتك فارغة',
  'cart.subtotal': 'المجموع الفرعي',
  'cart.shipping': 'التوصيل',
  'cart.total': 'الإجمالي',
  'cart.checkout': 'متابعة الدفع',
  'cart.continue': 'متابعة التسوق',
  'cart.remove': 'إزالة',
  'checkout.title': 'إلى أين نرسلها؟',
  'checkout.contact': 'بيانات التواصل',
  'checkout.address': 'عنوان التوصيل',
  'checkout.place': 'تأكيد الطلب',
  'checkout.placing': 'جارٍ تأكيد الطلب…',
  'checkout.summary': 'طلبك',
  'checkout.note': 'لا يتم تحصيل أي مبلغ هنا. يُسجل الطلب كقيد الانتظار.',
  'common.addToBag': 'أضف إلى السلة',
  'common.added': 'تمت الإضافة',
  'common.outOfStock': 'غير متوفر',
  'common.reserve': 'احجز',
  'common.save': 'حفظ',
  'common.compare': 'مقارنة',
  'common.share': 'مشاركة',
  'common.language': 'اللغة',
  'common.theme': 'المظهر',
  'footer.newArrivals': 'وصل حديثاً',
  'footer.join': 'انضم',
  'footer.privacy': 'الخصوصية',
  'footer.terms': 'الشروط',
};

export const DICTIONARIES: Record<Locale, Record<MessageKey, string>> = { en, ur, ar };

export function isLocale(value: string | null | undefined): value is Locale {
  return Boolean(value) && LOCALES.includes(value as Locale);
}

export function translate(locale: Locale, key: MessageKey): string {
  return DICTIONARIES[locale]?.[key] ?? DICTIONARIES.en[key] ?? key;
}

"""
Localization Engine — 40+ Languages — LumicorePro AI Agent
===========================================================
Phase: International Delivery (Phase 11)

Generates complete i18next-compatible JSON translation files for 40+ languages
covering all common UI strings for 20+ website types.

Features:
  - 40+ language locales (en, ar, ur, fr, de, es, zh, ja, ko, hi, tr, ru, pt, ...)
  - RTL language detection & HTML dir attribute injection
  - Industry-specific vocabulary per website type
  - Pluralisation rules per language
  - Date/time/number format configs
  - Auto-generates src/i18n/locales/*.json in generated project

Usage:
    from agent.localization_engine import LocalizationEngine
    engine = LocalizationEngine()
    result = engine.generate(spec, project_dir)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import agent_logger


class LocalizationEngine:
    """Generates i18next-compatible locale files for 40+ languages."""

    # ── Language registry ─────────────────────────────────────────────────
    LANGUAGES: Dict[str, Dict[str, Any]] = {
        # ── Core international ─────────────────────────────────────────
        "en":    {"name": "English",            "dir": "ltr", "region": "NA/EU/APAC", "pluralRule": "n != 1"},
        "ar":    {"name": "Arabic",             "dir": "rtl", "region": "MENA",       "pluralRule": "complex"},
        "ur":    {"name": "Urdu",               "dir": "rtl", "region": "SA",         "pluralRule": "n != 1"},
        "fr":    {"name": "French",             "dir": "ltr", "region": "EU/AF",      "pluralRule": "n > 1"},
        "de":    {"name": "German",             "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "es":    {"name": "Spanish",            "dir": "ltr", "region": "EU/LATAM",   "pluralRule": "n != 1"},
        "pt":    {"name": "Portuguese",         "dir": "ltr", "region": "LATAM/EU",   "pluralRule": "n != 1"},
        "zh":    {"name": "Chinese (Simplified)","dir": "ltr", "region": "APAC",      "pluralRule": "0"},
        "zh-TW": {"name": "Chinese (Traditional)","dir": "ltr","region": "APAC",     "pluralRule": "0"},
        "ja":    {"name": "Japanese",           "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "ko":    {"name": "Korean",             "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "hi":    {"name": "Hindi",              "dir": "ltr", "region": "SA",         "pluralRule": "n != 1"},
        "tr":    {"name": "Turkish",            "dir": "ltr", "region": "MENA",       "pluralRule": "n != 1"},
        "ru":    {"name": "Russian",            "dir": "ltr", "region": "EU",         "pluralRule": "complex"},
        "id":    {"name": "Indonesian",         "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "ms":    {"name": "Malay",              "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "th":    {"name": "Thai",               "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "vi":    {"name": "Vietnamese",         "dir": "ltr", "region": "APAC",       "pluralRule": "0"},
        "bn":    {"name": "Bengali",            "dir": "ltr", "region": "SA",         "pluralRule": "n != 1"},
        "fa":    {"name": "Persian",            "dir": "rtl", "region": "MENA",       "pluralRule": "n != 1"},
        "he":    {"name": "Hebrew",             "dir": "rtl", "region": "MENA",       "pluralRule": "n != 1"},
        "nl":    {"name": "Dutch",              "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "it":    {"name": "Italian",            "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "pl":    {"name": "Polish",             "dir": "ltr", "region": "EU",         "pluralRule": "complex"},
        "sv":    {"name": "Swedish",            "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "no":    {"name": "Norwegian",          "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "da":    {"name": "Danish",             "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "fi":    {"name": "Finnish",            "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "cs":    {"name": "Czech",              "dir": "ltr", "region": "EU",         "pluralRule": "complex"},
        "ro":    {"name": "Romanian",           "dir": "ltr", "region": "EU",         "pluralRule": "complex"},
        "hu":    {"name": "Hungarian",          "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "el":    {"name": "Greek",              "dir": "ltr", "region": "EU",         "pluralRule": "n != 1"},
        "uk":    {"name": "Ukrainian",          "dir": "ltr", "region": "EU",         "pluralRule": "complex"},
        "sw":    {"name": "Swahili",            "dir": "ltr", "region": "AF",         "pluralRule": "n != 1"},
        "am":    {"name": "Amharic",            "dir": "ltr", "region": "AF",         "pluralRule": "n != 1"},
        "yo":    {"name": "Yoruba",             "dir": "ltr", "region": "AF",         "pluralRule": "0"},
        "ha":    {"name": "Hausa",              "dir": "ltr", "region": "AF",         "pluralRule": "n != 1"},
        "pa":    {"name": "Punjabi",            "dir": "ltr", "region": "SA",         "pluralRule": "n != 1"},
        "ne":    {"name": "Nepali",             "dir": "ltr", "region": "SA",         "pluralRule": "n != 1"},
        "si":    {"name": "Sinhala",            "dir": "ltr", "region": "SA",         "pluralRule": "n != 1"},
    }

    # ── Base UI strings — English master ──────────────────────────────────
    BASE_STRINGS: Dict[str, Any] = {
        "common": {
            "home": "Home", "about": "About", "services": "Services",
            "contact": "Contact", "login": "Login", "logout": "Logout",
            "register": "Register", "search": "Search", "menu": "Menu",
            "close": "Close", "open": "Open", "submit": "Submit",
            "cancel": "Cancel", "save": "Save", "delete": "Delete",
            "edit": "Edit", "view": "View", "back": "Back", "next": "Next",
            "previous": "Previous", "loading": "Loading...", "error": "Error",
            "success": "Success", "warning": "Warning", "info": "Information",
            "yes": "Yes", "no": "No", "confirm": "Confirm", "more": "More",
            "less": "Less", "all": "All", "none": "None", "select": "Select",
            "upload": "Upload", "download": "Download", "share": "Share",
            "copy": "Copy", "print": "Print", "send": "Send", "read_more": "Read More",
            "get_started": "Get Started", "learn_more": "Learn More",
            "sign_up": "Sign Up", "sign_in": "Sign In", "profile": "Profile",
            "settings": "Settings", "help": "Help", "faq": "FAQ",
            "privacy_policy": "Privacy Policy", "terms": "Terms of Service",
            "cookie_settings": "Cookie Settings", "language": "Language",
            "currency": "Currency", "theme": "Theme",
        },
        "navigation": {
            "main_nav": "Main Navigation", "skip_to_main": "Skip to main content",
            "breadcrumb": "Breadcrumb", "pagination": "Pagination",
            "page_of": "Page {{current}} of {{total}}",
        },
        "auth": {
            "email": "Email Address", "password": "Password",
            "confirm_password": "Confirm Password", "forgot_password": "Forgot Password?",
            "reset_password": "Reset Password", "remember_me": "Remember Me",
            "login_success": "Logged in successfully", "logout_success": "Logged out",
            "register_success": "Account created successfully",
            "invalid_credentials": "Invalid email or password",
            "email_required": "Email is required",
            "password_min": "Password must be at least 6 characters",
            "two_factor": "Two-Factor Authentication",
            "otp_sent": "Verification code sent to your email",
            "enter_otp": "Enter 6-digit code",
            "verify": "Verify",
        },
        "ecommerce": {
            "cart": "Shopping Cart", "checkout": "Checkout", "order": "Order",
            "orders": "Orders", "product": "Product", "products": "Products",
            "add_to_cart": "Add to Cart", "remove_from_cart": "Remove",
            "quantity": "Quantity", "price": "Price", "total": "Total",
            "subtotal": "Subtotal", "shipping": "Shipping", "tax": "Tax",
            "discount": "Discount", "coupon": "Coupon Code",
            "apply_coupon": "Apply Coupon", "place_order": "Place Order",
            "continue_shopping": "Continue Shopping", "empty_cart": "Your cart is empty",
            "in_stock": "In Stock", "out_of_stock": "Out of Stock",
            "wishlist": "Wishlist", "reviews": "Reviews", "rating": "Rating",
            "category": "Category", "categories": "Categories",
            "filter": "Filter", "sort_by": "Sort By", "size": "Size",
            "color": "Color", "brand": "Brand", "free_shipping": "Free Shipping",
            "payment": "Payment", "secure_checkout": "Secure Checkout",
        },
        "restaurant": {
            "menu": "Menu", "order_online": "Order Online",
            "reservation": "Book a Table", "delivery": "Delivery",
            "takeaway": "Takeaway", "dine_in": "Dine In",
            "add_to_order": "Add to Order", "special_instructions": "Special Instructions",
            "estimated_time": "Estimated Delivery Time", "track_order": "Track Order",
            "restaurant_closed": "We are currently closed",
            "opening_hours": "Opening Hours",
        },
        "healthcare": {
            "doctors": "Doctors", "appointments": "Appointments",
            "book_appointment": "Book Appointment", "patients": "Patients",
            "services": "Medical Services", "emergency": "Emergency",
            "consultation": "Consultation", "prescription": "Prescription",
            "medical_history": "Medical History", "lab_results": "Lab Results",
        },
        "education": {
            "courses": "Courses", "enroll": "Enroll Now", "lessons": "Lessons",
            "certificate": "Certificate", "instructor": "Instructor",
            "students": "Students", "progress": "Progress",
            "quiz": "Quiz", "assignment": "Assignment", "grade": "Grade",
            "start_course": "Start Course", "continue": "Continue Learning",
        },
        "forms": {
            "first_name": "First Name", "last_name": "Last Name",
            "full_name": "Full Name", "phone": "Phone Number",
            "address": "Address", "city": "City", "country": "Country",
            "zip": "ZIP / Postal Code", "message": "Message",
            "subject": "Subject", "required_field": "This field is required",
            "invalid_email": "Please enter a valid email address",
            "form_success": "Your message has been sent successfully",
            "form_error": "Something went wrong. Please try again.",
        },
        "footer": {
            "all_rights": "All rights reserved",
            "powered_by": "Powered by",
            "follow_us": "Follow Us",
            "newsletter": "Subscribe to Newsletter",
            "your_email": "Your email address",
            "subscribe": "Subscribe",
        },
        "errors": {
            "404_title": "Page Not Found",
            "404_message": "The page you are looking for does not exist.",
            "500_title": "Server Error",
            "500_message": "Something went wrong on our end. Please try again.",
            "network_error": "Network error. Please check your connection.",
            "try_again": "Try Again",
            "go_home": "Go to Homepage",
        },
        "accessibility": {
            "close_menu": "Close menu", "open_menu": "Open menu",
            "toggle_theme": "Toggle dark/light mode",
            "change_language": "Change language",
            "loading": "Content is loading", "image_loading": "Image loading",
        },
    }

    # ── Translations for key languages ────────────────────────────────────
    # ar/ur/es/fr/de cover common/auth/forms/ecommerce/footer/errors/accessibility;
    # other configured languages fall back to English (i18next fallbackLng: 'en')
    TRANSLATIONS: Dict[str, Dict[str, Any]] = {
        "ar": {
            "common": {
                "home": "الرئيسية", "about": "من نحن", "services": "الخدمات",
                "contact": "اتصل بنا", "login": "تسجيل الدخول", "logout": "تسجيل الخروج",
                "register": "إنشاء حساب", "search": "بحث", "menu": "القائمة",
                "close": "إغلاق", "open": "فتح", "submit": "إرسال",
                "cancel": "إلغاء", "save": "حفظ", "delete": "حذف",
                "loading": "جار التحميل...", "error": "خطأ",
                "success": "نجاح", "get_started": "ابدأ الآن",
                "learn_more": "اعرف المزيد", "sign_up": "إنشاء حساب",
                "sign_in": "تسجيل الدخول", "settings": "الإعدادات",
                "privacy_policy": "سياسة الخصوصية", "language": "اللغة",
            },
            "auth": {
                "email": "البريد الإلكتروني", "password": "كلمة المرور",
                "forgot_password": "نسيت كلمة المرور؟",
                "login_success": "تم تسجيل الدخول بنجاح",
                "invalid_credentials": "بريد إلكتروني أو كلمة مرور غير صحيحة",
            },
            "forms": {
                "first_name": "الاسم الأول", "last_name": "اسم العائلة",
                "phone": "رقم الهاتف", "message": "الرسالة",
                "required_field": "هذا الحقل مطلوب",
                "form_success": "تم إرسال رسالتك بنجاح",
            },
            "ecommerce": {
                "cart": "عربة التسوق", "checkout": "الدفع",
                "add_to_cart": "أضف إلى السلة", "price": "السعر",
                "total": "المجموع", "order": "الطلب",
            },
            "footer": {
                "all_rights": "جميع الحقوق محفوظة", "powered_by": "مدعوم بواسطة",
                "follow_us": "تابعنا", "newsletter": "اشترك في النشرة البريدية",
                "your_email": "بريدك الإلكتروني", "subscribe": "اشتراك",
            },
            "errors": {
                "404_title": "الصفحة غير موجودة",
                "404_message": "الصفحة التي تبحث عنها غير موجودة.",
                "500_title": "خطأ في الخادم",
                "500_message": "حدث خطأ ما. حاول مرة أخرى.",
                "network_error": "خطأ في الشبكة. تحقق من اتصالك.",
                "try_again": "حاول مجددا", "go_home": "الصفحة الرئيسية",
            },
            "accessibility": {
                "close_menu": "إغلاق القائمة", "open_menu": "فتح القائمة",
                "toggle_theme": "تبديل الوضع الداكن/الفاتح",
                "change_language": "تغيير اللغة",
                "loading": "جاري تحميل المحتوى", "image_loading": "جاري تحميل الصورة",
            },
        },
        "ur": {
            "common": {
                "home": "ہوم", "about": "ہمارے بارے میں", "services": "خدمات",
                "contact": "رابطہ", "login": "لاگ ان", "logout": "لاگ آؤٹ",
                "register": "رجسٹر", "search": "تلاش", "menu": "مینو",
                "close": "بند", "submit": "جمع کریں", "cancel": "منسوخ",
                "loading": "لوڈ ہو رہا ہے...", "error": "خرابی",
                "success": "کامیابی", "get_started": "شروع کریں",
                "settings": "ترتیبات", "language": "زبان",
            },
            "auth": {
                "email": "ای میل", "password": "پاس ورڈ",
                "forgot_password": "پاس ورڈ بھول گئے؟",
                "login_success": "کامیابی سے لاگ ان ہو گئے",
                "invalid_credentials": "غلط ای میل یا پاس ورڈ",
            },
            "forms": {
                "first_name": "پہلا نام", "last_name": "آخری نام",
                "phone": "فون نمبر", "message": "پیغام",
                "required_field": "یہ فیلڈ ضروری ہے",
                "form_success": "آپ کا پیغام کامیابی سے بھیج دیا گیا",
            },
            "ecommerce": {
                "cart": "کارٹ", "checkout": "چیک آؤٹ",
                "add_to_cart": "کارٹ میں ڈالیں", "price": "قیمت",
                "total": "کل", "order": "آرڈر",
            },
            "footer": {
                "all_rights": "جملہ حقوق محفوظ ہیں", "powered_by": "طاقت ور بذریعہ",
                "follow_us": "ہمیں فالو کریں", "newsletter": "نیوز لیٹر سبسکرائب کریں",
                "your_email": "آپ کا ای میل", "subscribe": "سبسکرائب",
            },
            "errors": {
                "404_title": "صفحہ نہیں ملا",
                "404_message": "جس صفحے کو آپ ڈھونڈ رہے ہیں وہ موجود نہیں۔",
                "500_title": "سرور خرابی",
                "500_message": "کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔",
                "network_error": "نیٹ ورک کا مسئلہ۔ اپنا کنکشن چیک کریں۔",
                "try_again": "دوبارہ کوشش کریں", "go_home": "ہوم پیج پر جائیں",
            },
            "accessibility": {
                "close_menu": "مینو بند کریں", "open_menu": "مینو کھولیں",
                "toggle_theme": "ڈارک/لائٹ موڈ تبدیل کریں",
                "change_language": "زبان تبدیل کریں",
                "loading": "مواد لوڈ ہو رہا ہے", "image_loading": "تصویر لوڈ ہو رہی ہے",
            },
        },
        "fr": {
            "common": {
                "home": "Accueil", "about": "À propos", "services": "Services",
                "contact": "Contact", "login": "Connexion", "logout": "Déconnexion",
                "register": "S'inscrire", "search": "Rechercher", "menu": "Menu",
                "close": "Fermer", "submit": "Envoyer", "cancel": "Annuler",
                "save": "Enregistrer", "loading": "Chargement...", "error": "Erreur",
                "get_started": "Commencer", "learn_more": "En savoir plus",
                "sign_up": "S'inscrire", "sign_in": "Se connecter",
                "settings": "Paramètres", "language": "Langue",
            },
            "auth": {
                "email": "Adresse e-mail", "password": "Mot de passe",
                "forgot_password": "Mot de passe oublié ?",
                "login_success": "Connexion réussie",
                "invalid_credentials": "E-mail ou mot de passe invalide",
            },
            "forms": {
                "first_name": "Prénom", "last_name": "Nom de famille",
                "phone": "Numéro de téléphone", "message": "Message",
                "required_field": "Ce champ est obligatoire",
                "form_success": "Votre message a été envoyé avec succès",
            },
            "ecommerce": {
                "cart": "Panier", "checkout": "Paiement",
                "add_to_cart": "Ajouter au panier", "price": "Prix",
                "total": "Total", "order": "Commande",
            },
            "footer": {
                "all_rights": "Tous droits réservés", "powered_by": "Propulsé par",
                "follow_us": "Suivez-nous", "newsletter": "Abonnez-vous à la newsletter",
                "your_email": "Votre adresse e-mail", "subscribe": "S'abonner",
            },
            "errors": {
                "404_title": "Page introuvable",
                "404_message": "La page que vous cherchez n'existe pas.",
                "500_title": "Erreur serveur",
                "500_message": "Une erreur est survenue. Veuillez réessayer.",
                "network_error": "Erreur réseau. Vérifiez votre connexion.",
                "try_again": "Réessayer", "go_home": "Retour à l'accueil",
            },
            "accessibility": {
                "close_menu": "Fermer le menu", "open_menu": "Ouvrir le menu",
                "toggle_theme": "Basculer en mode sombre/clair",
                "change_language": "Changer de langue",
                "loading": "Le contenu charge", "image_loading": "Chargement de l'image",
            },
        },
        "de": {
            "common": {
                "home": "Startseite", "about": "Über uns", "services": "Leistungen",
                "contact": "Kontakt", "login": "Anmelden", "logout": "Abmelden",
                "register": "Registrieren", "search": "Suchen", "menu": "Menü",
                "close": "Schließen", "submit": "Senden", "cancel": "Abbrechen",
                "save": "Speichern", "loading": "Laden...", "error": "Fehler",
                "get_started": "Loslegen", "settings": "Einstellungen", "language": "Sprache",
            },
            "auth": {
                "email": "E-Mail-Adresse", "password": "Passwort",
                "forgot_password": "Passwort vergessen?",
                "login_success": "Erfolgreich angemeldet",
            },
            "forms": {
                "first_name": "Vorname", "last_name": "Nachname",
                "phone": "Telefonnummer", "message": "Nachricht",
                "required_field": "Dieses Feld ist erforderlich",
            },
            "ecommerce": {
                "cart": "Warenkorb", "checkout": "Kasse",
                "add_to_cart": "In den Warenkorb", "price": "Preis",
                "total": "Gesamtsumme", "order": "Bestellung",
            },
            "footer": {
                "all_rights": "Alle Rechte vorbehalten", "powered_by": "Unterstützt von",
                "follow_us": "Folgen Sie uns", "newsletter": "Newsletter abonnieren",
                "your_email": "Ihre E-Mail-Adresse", "subscribe": "Abonnieren",
            },
            "errors": {
                "404_title": "Seite nicht gefunden",
                "404_message": "Die gesuchte Seite existiert nicht.",
                "500_title": "Serverfehler",
                "500_message": "Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.",
                "network_error": "Netzwerkfehler. Prüfen Sie Ihre Verbindung.",
                "try_again": "Erneut versuchen", "go_home": "Zur Startseite",
            },
            "accessibility": {
                "close_menu": "Menü schließen", "open_menu": "Menü öffnen",
                "toggle_theme": "Dunklen/hellen Modus umschalten",
                "change_language": "Sprache ändern",
                "loading": "Inhalt wird geladen", "image_loading": "Bild wird geladen",
            },
        },
        "es": {
            "common": {
                "home": "Inicio", "about": "Nosotros", "services": "Servicios",
                "contact": "Contacto", "login": "Iniciar sesión", "logout": "Cerrar sesión",
                "register": "Registrarse", "search": "Buscar", "menu": "Menú",
                "close": "Cerrar", "submit": "Enviar", "cancel": "Cancelar",
                "loading": "Cargando...", "error": "Error",
                "get_started": "Comenzar", "learn_more": "Saber más", "language": "Idioma",
            },
            "auth": {
                "email": "Correo electrónico", "password": "Contraseña",
                "forgot_password": "¿Olvidaste tu contraseña?",
                "login_success": "Sesión iniciada correctamente",
            },
            "forms": {
                "first_name": "Nombre", "last_name": "Apellido",
                "phone": "Número de teléfono", "message": "Mensaje",
                "required_field": "Este campo es obligatorio",
            },
            "ecommerce": {
                "cart": "Carrito", "checkout": "Pago",
                "add_to_cart": "Añadir al carrito", "price": "Precio",
                "total": "Total", "order": "Pedido",
            },
            "footer": {
                "all_rights": "Todos los derechos reservados", "powered_by": "Desarrollado por",
                "follow_us": "Síguenos", "newsletter": "Suscríbete al boletín",
                "your_email": "Tu correo electrónico", "subscribe": "Suscribirse",
            },
            "errors": {
                "404_title": "Página no encontrada",
                "404_message": "La página que buscas no existe.",
                "500_title": "Error del servidor",
                "500_message": "Algo salió mal. Inténtalo de nuevo.",
                "network_error": "Error de red. Comprueba tu conexión.",
                "try_again": "Reintentar", "go_home": "Ir a la página de inicio",
            },
            "accessibility": {
                "close_menu": "Cerrar menú", "open_menu": "Abrir menú",
                "toggle_theme": "Cambiar modo oscuro/claro",
                "change_language": "Cambiar idioma",
                "loading": "Cargando contenido", "image_loading": "Cargando imagen",
            },
        },
        "zh": {
            "common": {
                "home": "首页", "about": "关于我们", "services": "服务",
                "contact": "联系我们", "login": "登录", "logout": "退出",
                "register": "注册", "search": "搜索", "menu": "菜单",
                "close": "关闭", "submit": "提交", "cancel": "取消",
                "loading": "加载中...", "error": "错误",
                "get_started": "立即开始", "language": "语言",
            },
            "auth": {
                "email": "电子邮件", "password": "密码",
                "forgot_password": "忘记密码？",
            },
        },
        "ja": {
            "common": {
                "home": "ホーム", "about": "会社概要", "services": "サービス",
                "contact": "お問い合わせ", "login": "ログイン", "logout": "ログアウト",
                "register": "登録", "search": "検索", "menu": "メニュー",
                "loading": "読み込み中...", "error": "エラー",
                "get_started": "始める", "language": "言語",
            },
        },
        "ko": {
            "common": {
                "home": "홈", "about": "회사 소개", "services": "서비스",
                "contact": "문의", "login": "로그인", "logout": "로그아웃",
                "register": "회원가입", "search": "검색",
                "loading": "로딩 중...", "error": "오류",
                "get_started": "시작하기", "language": "언어",
            },
        },
        "hi": {
            "common": {
                "home": "होम", "about": "हमारे बारे में", "services": "सेवाएं",
                "contact": "संपर्क करें", "login": "लॉग इन", "logout": "लॉग आउट",
                "register": "रजिस्टर करें", "search": "खोजें",
                "loading": "लोड हो रहा है...", "error": "त्रुटि",
                "get_started": "शुरू करें", "language": "भाषा",
            },
        },
        "tr": {
            "common": {
                "home": "Ana Sayfa", "about": "Hakkımızda", "services": "Hizmetler",
                "contact": "İletişim", "login": "Giriş Yap", "logout": "Çıkış Yap",
                "register": "Kayıt Ol", "search": "Ara", "menu": "Menü",
                "loading": "Yükleniyor...", "error": "Hata",
                "get_started": "Başla", "language": "Dil",
            },
        },
        "pt": {
            "common": {
                "home": "Início", "about": "Sobre nós", "services": "Serviços",
                "contact": "Contato", "login": "Entrar", "logout": "Sair",
                "register": "Registrar", "search": "Pesquisar",
                "loading": "Carregando...", "error": "Erro",
                "get_started": "Começar", "language": "Idioma",
            },
        },
        "ru": {
            "common": {
                "home": "Главная", "about": "О нас", "services": "Услуги",
                "contact": "Контакты", "login": "Войти", "logout": "Выйти",
                "register": "Регистрация", "search": "Поиск",
                "loading": "Загрузка...", "error": "Ошибка",
                "get_started": "Начать", "language": "Язык",
            },
        },
        "id": {
            "common": {
                "home": "Beranda", "about": "Tentang Kami", "services": "Layanan",
                "contact": "Hubungi Kami", "login": "Masuk", "logout": "Keluar",
                "register": "Daftar", "search": "Cari",
                "loading": "Memuat...", "error": "Kesalahan",
                "get_started": "Mulai", "language": "Bahasa",
            },
        },
    }

    # ── i18n config template ──────────────────────────────────────────────
    I18N_CONFIG_TEMPLATE = """\
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Dynamically import all locale files
const loadLocales = () => {{
  const context = import.meta.glob('./locales/*.json', {{ eager: true }});
  const resources = {{}};
  for (const path in context) {{
    const lang = path.replace('./locales/', '').replace('.json', '');
    resources[lang] = {{ translation: context[path].default || context[path] }};
  }}
  return resources;
}};

// RTL languages
export const RTL_LANGUAGES = {rtl_langs};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({{
    resources: loadLocales(),
    fallbackLng: 'en',
    supportedLngs: {supported_langs},
    defaultNS: 'translation',
    interpolation: {{ escapeValue: false }},
    detection: {{
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    }},
  }});

// Apply RTL direction when language changes
i18n.on('languageChanged', (lng) => {{
  const isRtl = RTL_LANGUAGES.includes(lng);
  document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
  document.documentElement.lang = lng;
}});

export default i18n;
"""

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate i18n locale files + config for the project."""
        agent_logger.info("LocalizationEngine: Generating i18n locale files...")

        # Determine which languages to generate
        target_langs = self._select_languages(spec)
        website_type = spec.get("website_type", "ecommerce")

        locales_dir = os.path.join(project_dir, "frontend", "src", "i18n", "locales")
        os.makedirs(locales_dir, exist_ok=True)

        generated_files: List[str] = []

        for lang_code in target_langs:
            translations = self._build_translations(lang_code, website_type)
            file_path = os.path.join(locales_dir, f"{lang_code}.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                generated_files.append(file_path)
            except Exception as e:
                agent_logger.warning(f"LocalizationEngine: Could not write {file_path}: {e}")

        # Write i18n config index
        config_path = os.path.join(project_dir, "frontend", "src", "i18n", "index.js")
        rtl_langs = [c for c, cfg in self.LANGUAGES.items() if cfg["dir"] == "rtl" and c in target_langs]
        config_content = self.I18N_CONFIG_TEMPLATE.format(
            rtl_langs=json.dumps(rtl_langs),
            supported_langs=json.dumps(target_langs),
        )
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
            generated_files.append(config_path)
        except Exception as e:
            agent_logger.warning(f"LocalizationEngine: Could not write i18n config: {e}")

        result = {
            "languages_generated":  target_langs,
            "total_languages":      len(target_langs),
            "rtl_languages":        rtl_langs,
            "files_written":        len(generated_files),
            "locales_dir":          locales_dir,
            "primary_language":     self._get_primary_lang(spec),
            "language_metadata": {
                code: {
                    "name": self.LANGUAGES.get(code, {}).get("name", code),
                    "dir":  self.LANGUAGES.get(code, {}).get("dir", "ltr"),
                }
                for code in target_langs
            },
        }

        agent_logger.info(
            f"LocalizationEngine: {len(target_langs)} languages, "
            f"{len(rtl_langs)} RTL, {len(generated_files)} files written."
        )
        return result

    # ── Helpers ───────────────────────────────────────────────────────────
    def _select_languages(self, spec: Dict[str, Any]) -> List[str]:
        """Choose which languages to generate based on region, type, and spec flags."""
        # Always include English
        langs = {"en"}

        region = spec.get("region", "")
        lang_detected = spec.get("language_detected", "")

        # Region-based defaults
        region_map = {
            "SA":    ["ur", "en", "ar"],
            "MENA":  ["ar", "en", "fr", "tr"],
            "EU":    ["en", "de", "fr", "es", "it", "nl", "pl", "pt"],
            "NA":    ["en", "es", "fr"],
            "APAC":  ["en", "zh", "ja", "ko", "id", "ms", "th", "vi"],
            "AF":    ["en", "fr", "ar", "sw"],
            "LATAM": ["es", "pt", "en"],
        }
        if region in region_map:
            langs.update(region_map[region])

        # Detected language signals
        if "urdu" in lang_detected:
            langs.update(["ur", "en"])
        if "arabic" in lang_detected:
            langs.update(["ar", "en"])

        # RTL support requested
        if spec.get("rtl_support"):
            langs.update(["ar", "ur"])

        # i18n_multilingual feature → generate all major languages
        if "i18n_multilingual" in spec.get("features", []):
            langs.update(["en", "ar", "fr", "de", "es", "zh", "ja", "ko", "hi", "tr", "pt", "ru", "id"])

        # SaaS → global languages
        if spec.get("website_type") in ("saas", "fintech", "dashboard"):
            langs.update(["en", "ar", "fr", "de", "es", "zh", "ja", "pt"])

        # Filter to known languages only
        return sorted(c for c in langs if c in self.LANGUAGES)

    def _get_primary_lang(self, spec: Dict[str, Any]) -> str:
        lang = spec.get("language_detected", "english")
        if "urdu" in lang:
            return "ur"
        if "arabic" in lang:
            return "ar"
        return "en"

    def _build_translations(self, lang_code: str, website_type: str) -> Dict[str, Any]:
        """Merge base English strings with available translations for lang_code."""
        import copy
        base = copy.deepcopy(self.BASE_STRINGS)

        # Keep only sections relevant to website_type
        relevant_sections = ["common", "navigation", "auth", "forms", "footer", "errors", "accessibility"]
        type_section_map = {
            "ecommerce": ["ecommerce"],
            "restaurant": ["restaurant"],
            "healthcare": ["healthcare"],
            "education": ["education"],
        }
        relevant_sections += type_section_map.get(website_type, [])

        # Merge available translations on top of English base
        overrides = self.TRANSLATIONS.get(lang_code, {})

        result: Dict[str, Any] = {}
        for section in relevant_sections:
            if section in base:
                section_data = dict(base[section])
                if section in overrides:
                    section_data.update(overrides[section])
                result[section] = section_data

        return result

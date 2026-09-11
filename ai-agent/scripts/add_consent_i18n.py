"""Insert consent i18n block into all locale files (except en which is done)."""
import json
import io

BASE = r"C:\Users\AZAM COMPUTERS\OneDrive\Desktop\lumicorepro-core\src\i18n\locales"

CONSENT = {
    "ur": ("ہم آپ کی رازداری کی قدر کرتے ہیں", "ہم سائٹ کے کام کے لیے کوکیز استعمال کرتے ہیں اور جہاں آپ اتفاق کریں وہاں ٹریفک کا تجزیہ کریں۔ ضروری کوکیز ہمیشہ فعال رہتی ہیں۔", "رازداری کی پالیسی", "سب قبول کریں", "صرف ضروری"),
    "ar": ("نُقدّر خصوصيتك", "نستخدم ملفات تعريف الارتباط لتشغيل الموقع وعند موافقتك لتحليل الزيارات وتخصيص المحتوى. الكوكيز الأساسية نشطة دائماً.", "سياسة الخصوصية", "قبول الكل", "الأساسية فقط"),
    "de": ("Wir schätzen Ihre Privatsphäre", "Wir verwenden Cookies, damit unsere Website funktioniert und, wenn Sie zustimmen, um den Verkehr zu analysieren und Inhalte zu personalisieren. Essenzielle Cookies sind immer aktiv.", "Datenschutzrichtlinie", "Alle akzeptieren", "Nur erforderliche"),
    "es": ("Valoramos tu privacidad", "Usamos cookies para que el sitio funcione y, si aceptas, para analizar el tráfico y personalizar el contenido. Las cookies esenciales están siempre activas.", "Política de privacidad", "Aceptar todas", "Solo esenciales"),
    "fr": ("Nous respectons votre vie privée", "Nous utilisons des cookies pour faire fonctionner le site et, avec votre accord, pour analyser le trafic et personnaliser le contenu. Les cookies essentiels sont toujours actifs.", "Politique de confidentialité", "Tout accepter", "Essentiels uniquement"),
    "hi": ("हम आपकी गोपनीयता को महत्व देते हैं", "हम साइट चलाने के लिए कुकीज़ का उपयोग करते हैं और जहाँ आप सहमत हों वहाँ ट्रैफ़िक का विश्लेषण करके सामग्री निजीकृत करते हैं। आवश्यक कुकीज़ हमेशा सक्रिय रहती हैं।", "गोपनीयता नीति", "सभी स्वीकार करें", "केवल आवश्यक"),
    "it": ("Rispettiamo la tua privacy", "Usiamo cookie per far funzionare il sito e, se acconsenti, per analizzare il traffico e personalizzare i contenuti. I cookie essenziali sono sempre attivi.", "Informativa sulla privacy", "Accetta tutto", "Solo essenziali"),
    "ja": ("プライバシーを大切にします", "当サイトの動作のためCookieを使用し、同意をいただいた場合はトラフィック分析やコンテンツのパーソナライズにも使用します。必須Cookieは常に有効です。", "プライバシーポリシー", "すべて許可", "必須のみ"),
    "ko": ("귀하의 개인정보를 소중히 여깁니다", "사이트 운영을 위해 쿠키를 사용하며, 동의하시면 트래픽 분석 및 콘텐츠 개인화에도 사용합니다. 필수 쿠키는 항상 활성화됩니다.", "개인정보 처리방침", "모두 허용", "필수만"),
    "pt": ("Valorizamos sua privacidade", "Usamos cookies para o site funcionar e, com seu consentimento, para analisar o tráfego e personalizar conteúdo. Cookies essenciais estão sempre ativos.", "Política de Privacidade", "Aceitar todas", "Apenas essenciais"),
    "tr": ("Gizliliğinize değer veriyoruz", "Sitenin çalışması için çerezler kullanıyoruz ve onay verirseniz trafiği analiz edip içeriği kişiselleştirmek için de kullanıyoruz. Zorunlu çerezler her zaman aktiftir.", "Gizlilik Politikası", "Tümünü kabul et", "Yalnızca zorunlu"),
    "zh": ("我们重视您的隐私", "我们使用Cookie使网站运行，并在您同意的情况下分析流量和个性化内容。必要Cookie始终保持启用。", "隐私政策", "全部接受", "仅必要"),
}

for name, (title, desc, policy, accept, essential) in CONSENT.items():
    path = f"{BASE}\\{name}.json"
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["consent"] = {
        "title": title,
        "description": desc,
        "privacyPolicy": policy,
        "acceptAll": accept,
        "essentialOnly": essential,
    }
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Updated {name}.json")

print("Done")
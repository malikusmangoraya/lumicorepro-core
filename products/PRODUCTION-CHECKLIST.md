# PRODUCTION CHECKLIST
created: 2026-10-09
purpose: ek file jab bhi production publish karein, iski har cheez tick karein. be-empty rakhein.

## FINAL STATE
- [ ] `node products/_audit/verify-all.cjs` exit 0
- [ ] `npm run build` har 11 product mein exit 0
- [ ] `products/_audit/check-shells.mjs` exit 0

## 1. MISSING FILES
product mein jo file missing ho aur usse build ya feature tor pe break ho:
- [ ] har product ke `frontend/src/services/api.js` exist karta hai
- [ ] har product ke `frontend/src/services/apiConfig.js` exist karta hai
- [ ] har product ke `frontend/src/lib/paymentProvider.js` exist karta hai
- [ ] har product ke `frontend/src/components/checkout/CheckoutFlow.jsx` exist karta hai
- [ ] koi bhi relative / `@/` import unresolved nahi hai

## 2. DESIGN IDENTITY
- [ ] har product ka `src/index.css` exactly 1 `:root` block rakhta hai
- [ ] `--t-primary` aur `--t-canvas` har product mein alag hain (11/11 distinct)
- [ ] BRAND.js, design-tokens.json, index.css, tailwind.config.js ke primary colour same hain
- [ ] `src/components/brand/BRAND.js` mein har product ka apna name + palette hai
- [ ] `src/components/brand/BrandMark.jsx` har product ka alag vector logo hai
- [ ] `LandingLayout.jsx`, `AppLayout.jsx`, `Hero.jsx` har product ka alag design use kar rahe hain
- [ ] koi bhi file `PlatformPro` ya `ConsoleAdmin` nahi likh rahi
- [ ] koi bhi component class `index.css` mein undefined nahi hai

## 3. BUILD HEALTH
- [ ] `lucide-react` ke saare named imports exist karte hain (Spinner/Globe, Chrome/Globe, Github/Code2, Facebook/Users, Linkedin/Briefcase, Twitter/AtSign, etc.)
- [ ] koi duplicate declaration (jaise Register mein do Navbar/Footer) nahi hai
- [ ] koi unresolved route nahi hai
- [ ] `dist/index.html` har product ke `frontend/dist/` mein exist karta hai
- [ ] `vite.config.js` / `package.json` / dependencies sab product ke hisaab se thik hain

## 4. PAYMENT
- [ ] `paymentProvider.js` mock class nahi hai, real client hai
- [ ] `CheckoutFlow.jsx` koi bhi card number / expiry / CVC nahi collect kar raha
- [ ] payment endpoints ka integration koi card data frontend mein nahi collect kar raha
- [ ] `.env.example` mein saare payment keys ki entries documented hain

## 5. CACHE + COOKIES + PWA
- [ ] har product ka `public/sw.js` apne version ke saath exist karta hai
- [ ] `sw-cache-strategy.js` har product ke hisaab se thik hai
- [ ] `src/config/cookie-config.js` har product mein exist karta hai
- [ ] `src/components/common/CookieConsent.jsx` har product mein exist karta hai
- [ ] `App.jsx` mein `CookieConsent` mount kiya gaya hai
- [ ] `App.jsx` mein `path="*"` `NotFound` component ko route kar raha hai
- [ ] `src/pages/NotFound.jsx` har product mein exist karta hai

## 6. AUTH
- [ ] `Login.jsx`, `Register.jsx` har product mein exist karte hain
- [ ] social login / social share components exist karte hain agar use ho rahe hain
- [ ] auth context / session handling exist karta hai

## 7. LOCALES / i18n
- [ ] `src/i18n/locales/*.json` har product ke liye exist karte hain
- [ ] cookie banner copy har product mein localised hai (agar chahiye toh)
- [ ] koi hardcoded English string nahi hai jo i18n key se honi chahiye

## 8. STATIC ASSETS
- [ ] `public/favicon.svg` har product ka apna brand ka hisaab se hai
- [ ] hero / section images har product ka apna hain (agar req hai toh alag-alag)
- [ ] LazyImage / asset imports thik hain, broken imports nahi hain

## 9. BACKEND (agar publish karna hai toh)
- [ ] `backend/.env.example` pura hai
- [ ] payment, webhook, auth routes exist karte hain
- [ ] DB schema / migrations ready hain agar SQL/PG use karna hai
- [ ] CORS, rate limits, auth middleware configure hain

## 10. DOCUMENTATION + DELIVERY
- [ ] README.md har product mein exist karta hai aur isme Getting Started, env table, scripts, deploy hain
- [ ] LICENSE.md har product mein exist karta hai
- [ ] `.gitignore` sahi hai, `node_modules/`, `dist/`, `.env` excluded hain
- [ ] seller kit / Gumroad-ready files chahiye toh bane hain

## 11. DECISION NOTES
- [ ] kabhi-kabhi ek product mein koi file intentionally missing ho sakti hai (feature subset). usse yahan note karein: kis product mein, kis file ki, kyun, aur kya usse bypass karna safe hai.
- [ ] agar koi item tick nahi ho paaya, toh woh sirf tab production mein jayega agar uska cause fix kiya gaya ho.

## LAST VERIFIED
date: 2026-10-09
command: `node products/_audit/verify-all.cjs`
result: 7/7 check groups pass, exit 0
re-check: 2026-10-10, EXIT=0

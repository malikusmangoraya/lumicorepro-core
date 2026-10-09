const fs = require('fs');
const path = require('path');

const products = [
  'meridian-capital', 'nuage-events', 'prestige-studio',
  'resupro', 'saffron-voyage', 'studio-lumen'
];

const loginFormReplace = {
  oldImport: /import { Mail, Lock, Eye, ShieldCheck, ArrowRight } from 'lucide-react';/,
  newImport: "import { Mail, Lock, Eye, ShieldCheck, ArrowRight, Spinner } from 'lucide-react';",
  oldApi: null, // no api import yet
  newApi: "import api from '../services/api';\n",
  oldShow: "const [show, setShow] = useState(false);\r\n\r\n  return (",
  newShow: "const [show, setShow] = useState(false);\r\n  const [email, setEmail] = useState('');\r\n  const [password, setPassword] = useState('');\r\n  const [loading, setLoading] = useState(false);\r\n  const [error, setError] = useState('');\r\n  const [remember, setRemember] = useState(false);\r\n\r\n  return (",
  oldFormOpen: /<form onSubmit=\{\(e\) => e\.preventDefault\(\)\} className="mt-8 space-y-5">/,
  newFormOpen: `<form onSubmit={async (e) => {
              e.preventDefault();
              setError('');
              if (!email || !password) { setError(t('Login.email_and_password_required', 'Email and password are required.')); return; }
              setLoading(true);
              try {
                const res = await api.post('/auth/login', { email, password, remember });
                if (res.data?.success) {
                  localStorage.setItem('auth_token', res.data.data?.accessToken || '');
                  localStorage.setItem('refresh_token', res.data.data?.refreshToken || '');
                  window.location.href = '/account';
                } else {
                  setError(res.data?.message || t('Login.invalid_credentials', 'Invalid email or password.'));
                }
              } catch (err) {
                setError(err.response?.data?.message || t('Login.login_failed', 'Login failed. Please try again.'));
              } finally {
                setLoading(false);
              }
            }} className="mt-8 space-y-5">`,
  oldEmailInput: /<input\r?\n\s+id="email" name="email" type="email" required autoComplete="email"\r?\n\s+placeholder="([^"]+)"\r?\n\s+className="([^"]+)"\r?\n\s*\/>/,
  newEmailInput: (placeholder, cls) => `<input
                    id="email" name="email" type="email" required autoComplete="email"
                    placeholder="${placeholder}"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="${cls}"
                  />`,
  oldPasswordInput: /<input\r?\n\s+id="password" name="password" type=\{show \? 'text' : 'password'\} required autoComplete="current-password"\r?\n\s+placeholder="([^"]+)"\r?\n\s+className="([^"]+)"\r?\n\s*\/>/,
  newPasswordInput: (placeholder, cls) => `<input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="current-password"
                    placeholder="${placeholder}"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="${cls}"
                  />`,
  oldCheckbox: /<input type="checkbox" className="rounded border-\[var\(--t-border\)\]" \/> Keep me signed in/,
  newCheckbox: '<input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="rounded border-[var(--t-border)]" /> Keep me signed in',
  oldSubmitBtn: /<button type="submit" className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">\r?\n\s+Sign in <ArrowRight className="h-4 w-4" \/>\r?\n\s+<\/button>/,
  newSubmitBtn: `<button type="submit" disabled={loading} className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                {loading ? <><Spinner className="h-4 w-4 animate-spin" /> Signing in...</> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
              </button>`,
  oldLink: /New to [A-Za-z ]+\?{' '}\r?\n\s+<Link to="\/register" className="font-semibold text-primary">\{t\('Login\.create_an_account', t\('Login\.create_an_account', t\('Login\.create_an_account', 'Create an account'\)\)\)\}<\/Link>/,
  newLink: "New here?{' '}\r\n              <Link to=\"/register\" className=\"font-semibold text-primary\">{t('Login.create_an_account', t('Login.create_an_account', t('Login.create_an_account', 'Create an account')))}</Link>"
};

const registerFormReplace = {
  oldImport: /import { Mail, Lock, Eye, ShieldCheck, ArrowRight } from 'lucide-react';/,
  newImport: "import { Mail, Lock, Eye, ShieldCheck, ArrowRight, Spinner } from 'lucide-react';",
  oldApi: null,
  newApi: "import api from '../services/api';\n",
  oldShow: "const [show, setShow] = useState(false);\r\n\r\n  return (",
  newShow: "const [show, setShow] = useState(false);\r\n  const [name, setName] = useState('');\r\n  const [email, setEmail] = useState('');\r\n  const [password, setPassword] = useState('');\r\n  const [loading, setLoading] = useState(false);\r\n  const [error, setError] = useState('');\r\n\r\n  return (",
  oldFormOpen: /<form onSubmit=\{\(e\) => e\.preventDefault\(\)\} className="mt-8 space-y-5">/,
  newFormOpen: `<form onSubmit={async (e) => {
              e.preventDefault();
              setError('');
              if (!name || !email || !password) { setError(t('Register.all_fields_required', 'All fields are required.')); return; }
              if (password.length < 8) { setError(t('Register.password_min_8', 'Password must be at least 8 characters.')); return; }
              setLoading(true);
              try {
                const res = await api.post('/auth/register', { name, email, password });
                if (res.data?.success) {
                  localStorage.setItem('auth_token', res.data.data?.accessToken || '');
                  localStorage.setItem('refresh_token', res.data.data?.refreshToken || '');
                  window.location.href = '/account';
                } else {
                  setError(res.data?.message || t('Register.registration_failed', 'Registration failed. Please try again.'));
                }
              } catch (err) {
                setError(err.response?.data?.message || t('Register.registration_failed', 'Registration failed. Please try again.'));
              } finally {
                setLoading(false);
              }
            }} className="mt-8 space-y-5">`,
  oldNameInput: /<input\r?\n\s+id="name" name="name" type="text" required autoComplete="name"\r?\n\s+placeholder="Jane Doe"\r?\n\s+className="([^"]+)"\r?\n\s*\/>/,
  newNameInput: (cls) => `<input
                  id="name" name="name" type="text" required autoComplete="name" placeholder="Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="${cls}"
                />`,
  oldEmailInputReg: /<input\r?\n\s+id="email" name="email" type="email" required autoComplete="email"\r?\n\s+placeholder="([^"]+)"\r?\n\s+className="([^"]+)"\r?\n\s*\/>/,
  newEmailInputReg: (placeholder, cls) => `<input
                    id="email" name="email" type="email" required autoComplete="email" placeholder="${placeholder}"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="${cls}"
                  />`,
  oldPasswordInputReg: /<input\r?\n\s+id="password" name="password" type=\{show \? 'text' : 'password'\} required autoComplete="new-password"\r?\n\s+placeholder="([^"]+)"\r?\n\s+className="([^"]+)"\r?\n\s*\/>/,
  newPasswordInputReg: (placeholder, cls) => `<input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="new-password"
                    placeholder="${placeholder}"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="${cls}"
                  />`,
  oldSubmitBtnReg: /<button type="submit" className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">\r?\n\s+Create account <ArrowRight className="h-4 w-4" \/>\r?\n\s+<\/button>/,
  newSubmitBtnReg: `<button type="submit" disabled={loading} className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                {loading ? <><Spinner className="h-4 w-4 animate-spin" /> Creating account...</> : <>Create account <ArrowRight className="h-4 w-4" /></>}
              </button>`
};

for (const product of products) {
  const base = path.join('products', product, 'frontend', 'src', 'pages');
  
  // Fix Login.jsx
  fixFile(path.join(base, 'Login.jsx'), loginFormReplace, product, 'Login');
  
  // Fix Register.jsx
  fixFile(path.join(base, 'Register.jsx'), registerFormReplace, product, 'Register');
}

function fixFile(filePath, replacements, product, pageType) {
  if (!fs.existsSync(filePath)) {
    console.log(product + ': ' + pageType + '.jsx NOT FOUND');
    return;
  }
  
  let content = fs.readFileSync(filePath, 'utf8');
  let changed = false;
  
  // Import Spinner
  if (replacements.oldImport && replacements.newImport && content.match(replacements.oldImport)) {
    content = content.replace(replacements.oldImport, replacements.newImport);
    changed = true;
  }
  
  // Add api import (after lucide import)
  if (replacements.newApi && !content.includes(replacements.newApi.trim())) {
    content = content.replace(
      /import .*?from 'lucide-react';/,
      match => match + '\r\n' + replacements.newApi
    );
    changed = true;
  }
  
  // State vars
  if (replacements.oldShow && replacements.newShow && content.includes(replacements.oldShow)) {
    content = content.replace(replacements.oldShow, replacements.newShow);
    changed = true;
  }
  
  // Form open
  if (replacements.oldFormOpen && replacements.newFormOpen) {
    content = content.replace(replacements.oldFormOpen, replacements.newFormOpen);
    changed = true;
  }
  
  // Email input
  if (replacements.oldEmailInput && replacements.newEmailInput) {
    content = content.replace(replacements.oldEmailInput, (m, p1, p2) => replacements.newEmailInput(p1, p2));
    changed = true;
  }
  
  // Password input
  if (replacements.oldPasswordInput && replacements.newPasswordInput) {
    content = content.replace(replacements.oldPasswordInput, (m, p1, p2) => replacements.newPasswordInput(p1, p2));
    changed = true;
  }
  
  // Checkbox
  if (replacements.oldCheckbox && replacements.newCheckbox && content.includes(replacements.oldCheckbox)) {
    content = content.replace(replacements.oldCheckbox, replacements.newCheckbox);
    changed = true;
  }
  
  // Submit button
  if (replacements.oldSubmitBtn && replacements.newSubmitBtn) {
    content = content.replace(replacements.oldSubmitBtn, replacements.newSubmitBtn);
    changed = true;
  }
  
  // Link text
  if (replacements.oldLink && replacements.newLink) {
    content = content.replace(replacements.oldLink, replacements.newLink);
    changed = true;
  }
  
  // Register-specific
  if (replacements.oldNameInput && replacements.newNameInput && content.match(replacements.oldNameInput)) {
    content = content.replace(replacements.oldNameInput, (m, p1) => replacements.newNameInput(p1));
    changed = true;
  }
  if (replacements.oldEmailInputReg && replacements.newEmailInputReg) {
    content = content.replace(replacements.oldEmailInputReg, (m, p1, p2) => replacements.newEmailInputReg(p1, p2));
    changed = true;
  }
  if (replacements.oldPasswordInputReg && replacements.newPasswordInputReg) {
    content = content.replace(replacements.oldPasswordInputReg, (m, p1, p2) => replacements.newPasswordInputReg(p1, p2));
    changed = true;
  }
  if (replacements.oldSubmitBtnReg && replacements.newSubmitBtnReg) {
    content = content.replace(replacements.oldSubmitBtnReg, replacements.newSubmitBtnReg);
    changed = true;
  }
  
  if (changed) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(product + ': ' + pageType + ' wired');
  } else {
    console.log(product + ': ' + pageType + ' - no changes needed or pattern not matched');
  }
}

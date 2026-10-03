import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const names = fs.readdirSync(GP, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name).sort();

const grab = (src, re) => {
  const m = src.match(re);
  return m ? m[1].trim() : '';
};

const out = {};
for (const name of names) {
  const fe = path.join(GP, name, 'frontend');
  const htmlPath = path.join(fe, 'index.html');
  if (!fs.existsSync(htmlPath)) continue;
  const html = fs.readFileSync(htmlPath, 'utf8');

  const smPath = path.join(fe, 'public', 'sitemap.xml');
  let site = '';
  if (fs.existsSync(smPath)) {
    const sm = fs.readFileSync(smPath, 'utf8');
    site = grab(sm, /<loc>([^<]+)<\/loc>/);
  }
  const ogUrl = grab(html, /og:url"\s*content="([^"]*)"/);
  if (ogUrl) site = ogUrl;

  const title = grab(html, /<title[^>]*>([\s\S]*?)<\/title>/);
  const ogTitle = grab(html, /og:title"\s*content="([^"]*)"/);
  const desc = grab(html, /name="description"\s*content="([^"]*)"/);
  const ogDesc = grab(html, /og:description"\s*content="([^"]*)"/);
  const themeColor = grab(html, /name="theme-color"\s*content="([^"]*)"/);

  const cssPath = path.join(fe, 'src', 'index.css');
  let primary = '';
  let accent = '';
  if (fs.existsSync(cssPath)) {
    const css = fs.readFileSync(cssPath, 'utf8');
    primary = grab(css, /--t-primary:\s*(#[0-9a-fA-F]{3,8})/);
    accent = grab(css, /--t-accent:\s*(#[0-9a-fA-F]{3,8})/);
  }
  if (!primary) primary = grab(cssPath, /--t-primary:\s*(#[0-9a-fA-F]{3,8})/);

  const pub = path.join(fe, 'public');
  const pubFiles = fs.existsSync(pub) ? fs.readdirSync(pub) : [];

  out[name] = {
    title, ogTitle, desc, ogDesc, site, themeColor, primary, accent,
    hasOgImageFile: pubFiles.some((f) => /^og[-_.]?image\./i.test(f) || f === 'og.jpg'),
    ogFile: pubFiles.find((f) => /^og[-_.]?image\./i.test(f) || f === 'og.jpg') || '',
    hasFavicon: pubFiles.includes('favicon.svg') || /favicon\.svg/i.test(html),
    hasSitemap: fs.existsSync(smPath),
    hasRobots: fs.existsSync(path.join(pub, 'robots.txt')),
    routes: fs.existsSync(path.join(fe, 'src', 'pages'))
      ? fs.readdirSync(path.join(fe, 'src', 'pages')).filter((f) => f.endsWith('.jsx')).map((f) => path.basename(f, '.jsx'))
      : [],
  };
}

fs.writeFileSync('D:/lumicorepro-core/logs/rebuild/seo-inventory.json', JSON.stringify(out, null, 2));

const need = { desc: [], ogUrl: [], twitter: [], ogImageFile: [], jsonLd: 0, canonical: 0, noFavicon: [] };
for (const [n, v] of Object.entries(out)) {
  if (!v.desc) need.desc.push(n);
  if (!v.site) need.ogUrl.push(n);
  if (!/twitter:card/i.test(fs.readFileSync(path.join(GP, n, 'frontend', 'index.html'), 'utf8'))) need.twitter.push(n);
  if (!v.hasOgImageFile) need.ogImageFile.push(n);
  if (!v.hasFavicon) need.noFavicon.push(n);
}
console.log('projects:', Object.keys(out).length);
console.log('missing description      :', need.desc.length, need.desc.join(', '));
console.log('missing site/og:url      :', need.ogUrl.length, need.ogUrl.join(', '));
console.log('missing twitter:card     :', need.twitter.length);
console.log('missing og-image file    :', need.ogImageFile.length);
console.log('missing favicon          :', need.noFavicon.length, need.noFavicon.join(', '));
console.log('\nsample record (apex):', JSON.stringify(out.apex, null, 2).slice(0, 700));

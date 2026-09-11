import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// Alternative IDs for the 14 that failed
const RETRY = [
  ['1414235135510-cd386a95cef3',900,500,'restaurant/hero.jpg'],       // use dish4 as hero fallback
  ['1565299624946-b28f40a0ae38',600,400,'restaurant/dish4.jpg'],      // reuse dish2 id
  ['1605276374104-dee2a0ed3cd6',600,400,'realestate/prop5.jpg'],
  ['1570129477492-45c003dc5c19',1200,500,'realestate/hero.jpg'],      // try smaller
  ['1548690312-855d4bfaa66a',400,500,'fitness/trainer1.jpg'],
  ['1541534741688-7adf8a3f4a0a',400,500,'fitness/trainer2.jpg'],
  ['1552674605-db5fecabfe68',400,500,'fitness/trainer3.jpg'],
  ['1549476464-37392f717d84',400,500,'fitness/trainer4.jpg'],
  ['1523050854058-8df90110c9f1',1200,500,'education/hero.jpg'],
  ['1509062522246-3b57f9e6b4c4',600,380,'education/course3.jpg'],
  ['1434030216411-0b5e530e1b08',600,380,'education/course6.jpg'],
  ['1573843981267-be1480dca64b',600,400,'travel/dest5.jpg'],
  ['1500534314209-a157d0e14e17',600,400,'travel/dest6.jpg'],
  ['1529336953128-a85760f58ea1',700,500,'creative/project4.jpg'],
];

function download(url, dest) {
  return new Promise((resolve) => {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (fs.existsSync(dest) && fs.statSync(dest).size > 5000) { resolve(true); return; }
    const file = fs.createWriteStream(dest);
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 20000 }, (res) => {
      if ([301,302,303].includes(res.statusCode)) {
        file.close(); fs.unlink(dest, ()=>{});
        download(res.headers.location, dest).then(resolve); return;
      }
      if (res.statusCode !== 200) { file.close(); resolve(false); return; }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(fs.statSync(dest).size > 5000); });
    });
    req.on('error', () => { file.close(); resolve(false); });
    req.on('timeout', () => { req.destroy(); file.close(); resolve(false); });
  });
}

async function main() {
  let ok = 0;
  for (const [id,w,h,rel] of RETRY) {
    const url = `https://images.unsplash.com/photo-${id}?w=${w}&h=${h}&fit=crop&auto=format&q=80`;
    const dest = path.join(ROOT, 'src', 'assets', 'images', rel);
    const r = await download(url, dest);
    if (r) { ok++; console.log(`✓ ${rel}`); }
    else    { console.log(`✗ FAIL: ${rel}`); }
  }
  console.log(`\nRetry done: ${ok}/${RETRY.length}`);
}
main();

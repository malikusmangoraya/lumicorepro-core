/**
 * Retry failed image downloads using picsum.photos (reliable, no key needed)
 * and verified Unsplash IDs for product shots.
 * Run: node scripts/download-retry-picsum.mjs
 */
import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// Verified replacement targets: [category/relPath, width, height, seed|id, source]
const RETRIES = [
  // Business
  ['business/presentation.jpg', 900, 500, 'biz-presentation-01', 'picsum'],
  ['business/summit.jpg', 900, 500, 'biz-summit-02', 'picsum'],
  ['business/analytics-board.jpg', 900, 500, 'biz-analytics-03', 'picsum'],
  ['business/waterfall.jpg', 900, 500, 'nature-waterfall-04', 'picsum'],
  // AI
  ['ai/interconnect.jpg', 900, 500, 'tech-interconnect-05', 'picsum'],
  ['ai/data-flow.jpg', 900, 500, 'tech-dataflow-06', 'picsum'],
  ['ai/robot-arm.jpg', 900, 500, 'tech-robot-07', 'picsum'],
  ['ai/workspace-laptop.jpg', 900, 500, 'tech-workspace-08', 'picsum'],
  ['ai/brain-storm.jpg', 900, 500, 'tech-brainstorm-09', 'picsum'],
  // Creative
  ['creative/camera-work.jpg', 700, 500, 'creative-camera-10', 'picsum'],
  ['creative/painting.jpg', 700, 500, 'creative-paint-11', 'picsum'],
  ['creative/color-palette.jpg', 700, 500, 'creative-palette-12', 'picsum'],
  ['creative/brainstorm.jpg', 700, 500, 'creative-brain-13', 'picsum'],
  ['creative/swatches.jpg', 700, 500, 'creative-swatches-14', 'picsum'],
  ['creative/creative-mind.jpg', 700, 500, 'creative-mind-15', 'picsum'],
  ['creative/palette.jpg', 700, 500, 'creative-artpal-16', 'picsum'],
  ['creative/design-table.jpg', 700, 500, 'creative-table-17', 'picsum'],
  ['creative/workstation.jpg', 700, 500, 'creative-work-18', 'picsum'],
  // Dashboard
  ['dashboard/data-screen.jpg', 900, 500, 'dash-data-19', 'picsum'],
  ['dashboard/blueprint.jpg', 900, 500, 'dash-blueprint-20', 'picsum'],
  ['dashboard/circuit-dash.jpg', 900, 500, 'dash-circuit-21', 'picsum'],
  ['dashboard/planning.jpg', 900, 500, 'dash-plan-22', 'picsum'],
  // Education
  ['education/hero-grad.jpg', 1200, 500, 'edu-hero-23', 'picsum'],
  ['education/board-math.jpg', 600, 380, 'edu-math-24', 'picsum'],
  ['education/kid-study.jpg', 600, 380, 'edu-kid-25', 'picsum'],
  ['education/open-books.jpg', 600, 380, 'edu-books-26', 'picsum'],
  ['education/students.jpg', 900, 500, 'edu-students-27', 'picsum'],
  ['education/microscope.jpg', 600, 380, 'edu-micro-28', 'picsum'],
  ['education/online-class.jpg', 600, 380, 'edu-online-29', 'picsum'],
  ['education/teacher.jpg', 900, 500, 'edu-teacher-30', 'picsum'],
  // Ecommerce products (verified IDs)
  ['ecommerce/product-watch.jpg', 500, 500, '1523275335684-37898b6baf30', 'unsplash-verified'],
  ['ecommerce/product-headphones.jpg', 500, 500, '1583394838336-acd977736f90', 'unsplash-verified'],
  ['ecommerce/product-keyboard.jpg', 500, 500, '1587825140708-dfaf72ae4b04', 'unsplash-verified'],
  ['ecommerce/fashion-model.jpg', 900, 500, 'fashion-model-31', 'picsum'],
  ['ecommerce/fashion-look.jpg', 900, 500, 'fashion-look-32', 'picsum'],
  ['ecommerce/accessories.jpg', 900, 500, 'fashion-acc-33', 'picsum'],
  ['ecommerce/envelope.jpg', 900, 500, 'fashion-envelope-34', 'picsum'],
  ['ecommerce/watch-glass.jpg', 900, 500, 'fashion-glass-35', 'picsum'],
  ['ecommerce/product-bottle.jpg', 500, 500, 'product-bottle-36', 'picsum'],
  // Ecommerce electronics
  ['ecommerce/electronics/tv.jpg', 500, 500, 'elec-tv-37', 'picsum'],
  ['ecommerce/electronics/gadget.jpg', 500, 500, 'elec-gadget-38', 'picsum'],
  ['ecommerce/electronics/drone.jpg', 500, 500, 'elec-drone-39', 'picsum'],
  ['ecommerce/electronics/tablet.jpg', 500, 500, 'elec-tablet-40', 'picsum'],
  ['ecommerce/electronics/speaker.jpg', 500, 500, 'elec-speaker-41', 'picsum'],
  ['ecommerce/electronics/phone-dock.jpg', 500, 500, 'elec-dock-42', 'picsum'],
  ['ecommerce/electronics/server.jpg', 500, 500, 'elec-server-43', 'picsum'],
  // Fitness
  ['fitness/coach.jpg', 400, 500, 'fit-coach-44', 'picsum'],
  ['fitness/trainer.jpg', 400, 500, 'fit-trainer-45', 'picsum'],
  ['fitness/boxing.jpg', 400, 500, 'fit-box-46', 'picsum'],
  ['fitness/yoga-pose.jpg', 600, 400, 'fit-yoga-47', 'picsum'],
  ['fitness/healthy-diet.jpg', 600, 400, 'fit-diet-48', 'picsum'],
  ['fitness/bands.jpg', 600, 400, 'fit-bands-49', 'picsum'],
  ['fitness/strength.jpg', 600, 400, 'fit-strength-50', 'picsum'],
  ['fitness/woman-gym.jpg', 600, 400, 'fit-woman-51', 'picsum'],
  ['fitness/sprints.jpg', 600, 400, 'fit-sprint-52', 'picsum'],
  // Healthcare
  ['healthcare/shield-care.jpg', 800, 400, 'health-shield-53', 'picsum'],
  ['healthcare/video-consult.jpg', 800, 400, 'health-video-54', 'picsum'],
  ['healthcare/lab-test.jpg', 600, 400, 'health-lab-55', 'picsum'],
  ['healthcare/dental.jpg', 600, 400, 'health-dental-56', 'picsum'],
  ['healthcare/diagnostics.jpg', 600, 400, 'health-dia-57', 'picsum'],
  // Portfolio
  ['portfolio/editor.jpg', 700, 450, 'port-editor-58', 'picsum'],
  ['portfolio/team-collab.jpg', 700, 450, 'port-team-59', 'picsum'],
  ['portfolio/creative-coding.jpg', 700, 450, 'port-code-60', 'picsum'],
  ['portfolio/sketch.jpg', 700, 450, 'port-sketch-61', 'picsum'],
  // Real estate
  ['realestate/hero-house.jpg', 1200, 500, 're-hero-62', 'picsum'],
  ['realestate/bedroom.jpg', 600, 400, 're-bedroom-63', 'picsum'],
  // Restaurant
  ['restaurant/hero-cooking.jpg', 1200, 500, 'rest-hero-64', 'picsum'],
  ['restaurant/steak.jpg', 600, 400, 'rest-steak-65', 'picsum'],
  ['restaurant/flame-cook.jpg', 600, 400, 'rest-flame-66', 'picsum'],
  // SaaS
  ['saas/browser-app.jpg', 900, 500, 'saas-browser-67', 'picsum'],
  ['saas/startup-notes.jpg', 900, 500, 'saas-notes-68', 'picsum'],
  // Fintech
  ['fintech/crypto.jpg', 900, 500, 'fintech-crypto-69', 'picsum'],
  // Travel
  ['travel/bridge.jpg', 600, 400, 'travel-bridge-70', 'picsum'],
  ['travel/curves.jpg', 600, 400, 'travel-curves-71', 'picsum'],
];

function download(url, dest) {
  return new Promise((resolve) => {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (fs.existsSync(dest) && fs.statSync(dest).size > 20000) { resolve('skip'); return; }

    const file = fs.createWriteStream(dest);
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 25000 }, (res) => {
      if ([301, 302, 303].includes(res.statusCode)) {
        file.close(); fs.unlink(dest, () => {});
        download(res.headers.location, dest).then(resolve); return;
      }
      if (res.statusCode !== 200) { file.close(); fs.unlink(dest, () => {}); resolve(false); return; }
      res.pipe(file);
      file.on('finish', () => {
        let st = { size: 0 };
        try { st = fs.statSync(dest); } catch { st = { size: 0 }; }
        if (st.size < 20000) { file.close(); fs.unlink(dest, () => {}); resolve(false); return; }
        const buf = fs.readFileSync(dest).subarray(0, 3);
        const valid = (buf[0]===0xff&&buf[1]===0xd8) || (buf[0]===0x89&&buf[1]===0x50) || buf.toString('ascii',0,4)==='RIFF';
        if (!valid) { file.close(); fs.unlink(dest, () => {}); resolve(false); return; }
        file.close(); resolve(true);
      });
    });
    req.on('error', () => { file.close(); fs.unlink(dest, () => {}); resolve(false); });
    req.on('timeout', () => { req.destroy(); file.close(); fs.unlink(dest, () => {}); resolve(false); });
  });
}

function mkUrl(seed, w, h, source) {
  if (source === 'picsum') return `https://picsum.photos/seed/${encodeURIComponent(seed)}/${w}/${h}`;
  return `https://images.unsplash.com/photo-${seed}?w=${w}&h=${h}&fit=crop&fm=jpg&q=80`;
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function main() {
  let ok = 0, fail = 0;
  for (const [rel, w, h, seed, source] of RETRIES) {
    const dest = path.join(ROOT, 'src', 'assets', 'images', rel);
    const url = mkUrl(seed, w, h, source);
    const result = await download(url, dest);
    await sleep(120);
    if (result === true || result === 'skip') { ok++; process.stdout.write(`✓ ${rel}\n`); }
    else { fail++; process.stdout.write(`✗ ${rel}\n`); }
  }
  console.log(`\nDone: +${ok} files, ${fail} failed`);
}

main();
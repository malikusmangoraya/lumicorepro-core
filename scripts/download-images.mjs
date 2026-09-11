/**
 * LumicorePro — Image Downloader
 * Downloads 100 curated Unsplash images into src/assets/images/
 * Run: node scripts/download-images.mjs
 */
import https from 'https';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

const IMAGES = [
  // ── Restaurant ──────────────────────────────────────────────
  ['1414235135510-cd386a95cef3', 900, 500, 'restaurant/hero.jpg'],
  ['1546069901-ba9599a7e63c',   600, 400, 'restaurant/dish1.jpg'],
  ['1565299624946-b28f40a0ae38',600, 400, 'restaurant/dish2.jpg'],
  ['1567620905732-2d1ec7ab7445',600, 400, 'restaurant/dish3.jpg'],
  ['1555939594-58329b74c80a',   600, 400, 'restaurant/dish4.jpg'],
  ['1504674900247-0877df9cc836',600, 400, 'restaurant/dish5.jpg'],
  ['1512621776951-a57141f2eefd',600, 400, 'restaurant/dish6.jpg'],
  ['1559339352-11d035aa65de',   800, 400, 'restaurant/interior.jpg'],
  ['1577219491135-ce391730fb2c',400, 400, 'restaurant/chef.jpg'],
  // ── Real Estate ─────────────────────────────────────────────
  ['1570129477492-45c003dc5c19',1200,500, 'realestate/hero.jpg'],
  ['1512917774080-9991f1c4c750',600, 400, 'realestate/prop1.jpg'],
  ['1600585154340-be6161a56a0c',600, 400, 'realestate/prop2.jpg'],
  ['1558618666-fcd25c85cd64',   600, 400, 'realestate/prop3.jpg'],
  ['1564013799919-ab600027ffc6',600, 400, 'realestate/prop4.jpg'],
  ['1523217582562-09d05ba57b90',600, 400, 'realestate/prop5.jpg'],
  ['1586023492125-27b2c045efd7',800, 400, 'realestate/interior.jpg'],
  ['1560250097-0b93528c311a',   400, 400, 'realestate/agent.jpg'],
  // ── Healthcare ───────────────────────────────────────────────
  ['1576091160550-2173dba999ef',1200,500, 'healthcare/hero.jpg'],
  ['1612349317150-e413f6a5b16d',400, 400, 'healthcare/doctor1.jpg'],
  ['1559839734-2b71ea197ec2',   400, 400, 'healthcare/doctor2.jpg'],
  ['1582750433449-648ed127bb54',400, 400, 'healthcare/doctor3.jpg'],
  ['1594824476967-48c8b964273f',400, 400, 'healthcare/doctor4.jpg'],
  ['1527613426441-4da17471b66d',400, 400, 'healthcare/doctor5.jpg'],
  ['1519494026892-80bbd2d6fd0d',800, 400, 'healthcare/hospital.jpg'],
  // ── Fitness ──────────────────────────────────────────────────
  ['1534438327276-14e5300c3a48',1200,500, 'fitness/hero.jpg'],
  ['1571019613454-1cb2f99b2d8b',600, 400, 'fitness/gym1.jpg'],
  ['1517836357463-d25dfeac3438',600, 400, 'fitness/gym2.jpg'],
  ['1548690312-855d4bfaa66a',   400, 500, 'fitness/trainer1.jpg'],
  ['1549476464-37392f717d84',   400, 500, 'fitness/trainer2.jpg'],
  ['1541534741688-7adf8a3f4a0a',400, 500, 'fitness/trainer3.jpg'],
  ['1552674605-db5fecabfe68',   400, 500, 'fitness/trainer4.jpg'],
  ['1518611012118-696072aa579a',600, 400, 'fitness/class1.jpg'],
  ['1544367567-0f2fcb009e0b',   600, 400, 'fitness/class2.jpg'],
  // ── Education ────────────────────────────────────────────────
  ['1523050854058-8df90110c9f1',1200,500, 'education/hero.jpg'],
  ['1516321318423-f06f85e504b3',600, 380, 'education/course1.jpg'],
  ['1488190211105-8b0e65b80b4e',600, 380, 'education/course2.jpg'],
  ['1509062522246-3b57f9e6b4c4',600, 380, 'education/course3.jpg'],
  ['1558021212-51b6ecfa0db9',   600, 380, 'education/course4.jpg'],
  ['1456513080510-7bf3a84b82f8',600, 380, 'education/course5.jpg'],
  ['1434030216411-0b5e530e1b08',600, 380, 'education/course6.jpg'],
  ['1507003211169-0a1dd7228f2d',400, 300, 'education/student.jpg'],
  // ── Travel ───────────────────────────────────────────────────
  ['1506905925346-21bda4d32df4',1200,500, 'travel/hero.jpg'],
  ['1469854523086-cc02fe5d8800',600, 400, 'travel/dest1.jpg'],
  ['1537996194471-e657df975ab4',600, 400, 'travel/dest2.jpg'],
  ['1524231757912-21f4fe3a7200',600, 400, 'travel/dest3.jpg'],
  ['1512453979798-5ea266f8880c',600, 400, 'travel/dest4.jpg'],
  ['1573843981267-be1480dca64b',600, 400, 'travel/dest5.jpg'],
  ['1500534314209-a157d0e14e17',600, 400, 'travel/dest6.jpg'],
  ['1436491865332-7a61a109cc05',800, 400, 'travel/plane.jpg'],
  // ── Portfolio ────────────────────────────────────────────────
  ['1498050108023-c5249f4df085',1200,500, 'portfolio/hero.jpg'],
  ['1472099645785-5658abf4ff4e',400, 400, 'portfolio/avatar.jpg'],
  ['1467232004584-a241de8bcf5d',700, 450, 'portfolio/project1.jpg'],
  ['1460925895917-afdab827c52f',700, 450, 'portfolio/project2.jpg'],
  ['1504868584819-f8e8b4b6d7e3',700, 450, 'portfolio/project3.jpg'],
  ['1486312338219-ce68d2c6f44d',900, 500, 'portfolio/workspace.jpg'],
  ['1555066931-4365d14bab8c',   700, 400, 'portfolio/code.jpg'],
  // ── Creative ─────────────────────────────────────────────────
  ['1558655146-9f40138edfeb',   1200,500, 'creative/hero.jpg'],
  ['1561070791-2526d30994b5',   700, 500, 'creative/project1.jpg'],
  ['1573167243872-43c6433b9d40',700, 500, 'creative/project2.jpg'],
  ['1529336953128-a85760f58ea1',700, 500, 'creative/project3.jpg'],
  ['1541701494-16e8d485b12c',   700, 500, 'creative/project4.jpg'],
  ['1472099645785-5658abf4ff4e',400, 400, 'creative/team1.jpg'],
  ['1438761681033-6461ffad8d80',400, 400, 'creative/team2.jpg'],
  ['1500648767791-00dcc994a43e',400, 400, 'creative/team3.jpg'],
  ['1494790108377-be9c29b29330',400, 400, 'creative/team4.jpg'],
  // ── E-Commerce ───────────────────────────────────────────────
  ['1607082348824-0a96f2a4b9da',1200,500, 'ecommerce/hero.jpg'],
  ['1523275335684-37898b6baf30',500, 500, 'ecommerce/product1.jpg'],
  ['1585771724684-38269d6639fd',500, 500, 'ecommerce/product2.jpg'],
  ['1496181133206-80ce9b88a853',500, 500, 'ecommerce/product3.jpg'],
  ['1511707171634-5f897ff02aa9',500, 500, 'ecommerce/product4.jpg'],
  ['1491553895911-0055eca6402d',500, 500, 'ecommerce/product5.jpg'],
  ['1434056886845-dac89ffe9b56',500, 500, 'ecommerce/product6.jpg'],
  ['1560769629-975ec94e6a86',   500, 500, 'ecommerce/product7.jpg'],
  ['1542291026-7eec264c27ff',   500, 500, 'ecommerce/product8.jpg'],
  // ── Business ─────────────────────────────────────────────────
  ['1497366216548-37526070297c',1200,600, 'business/hero.jpg'],
  ['1522071820081-009f0129c71c',900, 500, 'business/team.jpg'],
  ['1497366811353-6870744d04b2',900, 500, 'business/office.jpg'],
  ['1600880292203-757bb62b4baf',900, 500, 'business/meeting.jpg'],
  ['1477959858617-67f85cf4f1df',1200,500, 'business/city.jpg'],
  ['1551288049-bebda4e38f71',   700, 400, 'business/growth.jpg'],
  // ── AI / Tech ────────────────────────────────────────────────
  ['1518770660439-4636190af475',1200,600, 'ai/hero.jpg'],
  ['1518770660439-4636190af475',600, 400, 'ai/chip.jpg'],
  ['1555066931-4365d14bab8c',   600, 400, 'ai/code.jpg'],
  ['1485827404703-89b55fcc595e',600, 400, 'ai/robot.jpg'],
  ['1551288049-bebda4e38f71',   600, 400, 'ai/data.jpg'],
  // ── Dashboard ────────────────────────────────────────────────
  ['1551288049-bebda4e38f71',   1200,600, 'dashboard/hero.jpg'],
  ['1460925895917-afdab827c52f',900, 500, 'dashboard/analytics.jpg'],
  ['1472099645785-5658abf4ff4e',200, 200, 'dashboard/user1.jpg'],
  ['1438761681033-6461ffad8d80',200, 200, 'dashboard/user2.jpg'],
  ['1500648767791-00dcc994a43e',200, 200, 'dashboard/user3.jpg'],
];

function download(url, dest) {
  return new Promise((resolve) => {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (fs.existsSync(dest) && fs.statSync(dest).size > 5000) { resolve(true); return; }

    const proto = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(dest);
    const req = proto.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 15000 }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        fs.unlink(dest, () => {});
        download(res.headers.location, dest).then(resolve);
        return;
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
  let ok = 0, fail = 0;
  for (const [id, w, h, rel] of IMAGES) {
    const url = `https://images.unsplash.com/photo-${id}?w=${w}&h=${h}&fit=crop&auto=format&q=80`;
    const dest = path.join(ROOT, 'src', 'assets', 'images', rel);
    const result = await download(url, dest);
    if (result) { ok++; process.stdout.write(`✓ [${ok}] ${rel}\n`); }
    else         { fail++; process.stdout.write(`✗ FAIL: ${rel}\n`); }
  }
  console.log(`\n✅ Done: ${ok} downloaded, ${fail} failed`);
}

main();

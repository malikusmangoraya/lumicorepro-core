// Phase 0 project scan — read-only. Writes .superpowers/phase0/projects-scan.json
import fs from 'node:fs';
import path from 'node:path';

const toPosix = (p) => p.split(path.sep).join('/');
const isDir = (p) => {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
};
const exists = (p) => fs.existsSync(p);

const parents = [
  ['delivery', 'delivery'],
  ['sell-today', 'products/sell-today'],
  ['generated', 'generated-projects'],
  ['backend-library', 'backend-library'],
  ['template-category', 'src/templates'],
];

const rows = [];
for (const [kind, parent] of parents) {
  if (!isDir(parent)) continue;
  for (const name of fs.readdirSync(parent).sort()) {
    const dir = path.join(parent, name);
    if (!isDir(dir)) continue;
    const sub = fs.readdirSync(dir);
    const subHas = (n) => sub.includes(n);
    const has = (rel) => exists(path.join(dir, rel));
    rows.push({
      kind,
      name,
      path: toPosix(dir),
      markers: {
        packageJson: subHas('package.json') || has('frontend/package.json') || has('backend/package.json'),
        frontend: subHas('frontend'),
        backend: subHas('backend'),
        readme: has('README.md') || has('readme.md'),
        license: has('LICENSE.md') || has('LICENSE'),
        envExample: has('.env.example') || has('frontend/.env.example') || has('backend/.env.example'),
        envFilePresent: has('.env') || has('frontend/.env') || has('backend/.env'),
        gitignore: has('.gitignore') || has('frontend/.gitignore') || has('backend/.gitignore'),
        tests: subHas('tests') || subHas('__tests__') || has('frontend/src/__tests__') || has('backend/__tests__'),
        i18n: has('frontend/src/i18n') || has('src/i18n'),
      },
    });
  }
}

const byKind = {};
for (const r of rows) {
  const k = (byKind[r.kind] ??= {
    count: 0,
    withPackageJson: 0,
    withReadme: 0,
    withLicense: 0,
    withEnvExample: 0,
    withEnvFile: 0,
    withGitignore: 0,
    withTests: 0,
    withI18n: 0,
    bothFrontendAndBackend: 0,
  });
  k.count++;
  if (r.markers.packageJson) k.withPackageJson++;
  if (r.markers.readme) k.withReadme++;
  if (r.markers.license) k.withLicense++;
  if (r.markers.envExample) k.withEnvExample++;
  if (r.markers.envFilePresent) k.withEnvFile++;
  if (r.markers.gitignore) k.withGitignore++;
  if (r.markers.tests) k.withTests++;
  if (r.markers.i18n) k.withI18n++;
  if (r.markers.frontend && r.markers.backend) k.bothFrontendAndBackend++;
}

const out = {
  generated_at: new Date().toISOString(),
  note: 'Read-only scan. Markers are filesystem presence checks, not quality or test results.',
  scanned_roots: parents.map((p) => p[1]),
  units_scanned: rows.length,
  by_kind: byKind,
  units_with_env_file: rows.filter((r) => r.markers.envFilePresent).map((r) => r.path),
  rows,
};
fs.mkdirSync('.superpowers/phase0', { recursive: true });
fs.writeFileSync('.superpowers/phase0/projects-scan.json', JSON.stringify(out, null, 2));
console.log('units scanned:', rows.length);
console.log(JSON.stringify(byKind, null, 2));
const withEnv = out.units_with_env_file;
console.log('units with an .env file present:', withEnv.length, withEnv.slice(0, 20).join(', '));

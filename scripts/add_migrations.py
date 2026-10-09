"""Generate a real initial Sequelize migration for every product.

The products previously created their schema with `sequelize.sync({ alter:
true })` in development only, so production had no schema management at all.
This writes a Umzug-driven baseline migration that creates every table from
the live model definitions, a `migrate.js` runner, and the npm scripts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core\products")

MIGRATION = """\
'use strict';

// Baseline schema, generated from the live Sequelize model definitions.
// Going forward, schema changes belong in new numbered files here so they can
// be applied and rolled back per environment.
const models = require('../models');

/** @type {import('umzug').Migration} */
module.exports = {
  async up({ context: queryInterface }) {
    for (const [, Model] of Object.entries(models)) {
      if (!Model || !Model.tableName || !Model.rawAttributes) continue;
      // createTable is idempotent-safe here because the storage records which
      // migrations have run; it will not re-create tables on a second boot.
      await queryInterface.createTable(Model.tableName, Model.rawAttributes);
    }
  },

  async down({ context: queryInterface }) {
    const names = Object.values(models)
      .filter((M) => M && M.tableName)
      .map((M) => M.tableName)
      .reverse();
    for (const name of names) {
      await queryInterface.dropTable(name, { cascade: true, force: true })
        .catch(() => {});
    }
  },
};
"""

RUNNER = """\
'use strict';
const path = require('path');
const { Umzug, SequelizeStorage } = require('umzug');
const { sequelize } = require('./config/database');

const umzug = new Umzug({
  migrations: { glob: [path.join(__dirname, 'migrations', '*.js')] },
  context: sequelize.getQueryInterface(),
  storage: new SequelizeStorage({ sequelize }),
  logger: console,
});

module.exports = umzug;

if (require.main === module) {
  const cmd = (process.argv[2] || 'up').toLowerCase();
  const run = cmd === 'down' ? umzug.down.bind(umzug) : umzug.up.bind(umzug);
  run()
    .then(() => {
      console.log(`migrations ${cmd} complete`);
      return sequelize.close();
    })
    .then(() => process.exit(0))
    .catch(async (e) => {
      console.error(e);
      try { await sequelize.close(); } catch (_) { /* ignore */ }
      process.exit(1);
    });
}
"""

for prod in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    be = prod / 'backend'
    if not be.is_dir():
        continue
    mig = be / 'migrations'
    mig.mkdir(exist_ok=True)
    (mig / '001-initial-schema.js').write_text(MIGRATION, encoding='utf-8')
    (be / 'migrate.js').write_text(RUNNER, encoding='utf-8')

    pkg_p = be / 'package.json'
    pkg = json.loads(pkg_p.read_text(encoding='utf-8'))
    scripts = pkg.setdefault('scripts', {})
    scripts['migrate'] = 'node migrate.js'
    scripts['migrate:down'] = 'node migrate.js down'
    scripts['migrate:status'] = 'node -e "require(\'./migrate.js\').executed().then(e=>console.log(e.map(x=>x.name).join(\'\\n\'))||console.log(\'none\'))"'
    deps = pkg.setdefault('dependencies', {})
    deps.setdefault('umzug', '^3.4.0')
    # sequelize is already a dep; ensure version present
    deps.setdefault('sequelize', '^6.37.5')
    pkg_p.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    # harden database.js: do not sync in production; point dev to migrations
    db = be / 'config' / 'database.js'
    if db.is_file():
        t = db.read_text(encoding='utf-8')
        t = t.replace(
            "    if (process.env.NODE_ENV === 'development') {\n"
            "      await sequelize.sync({ alter: true });\n"
            "    }",
            "    // Schema changes go through migrations (npm run migrate). The\n"
            "    // old `sequelize.sync({ alter: true })` path was removed because\n"
            "    // it mutated the schema outside version control and could not\n"
            "    // be applied to a production database.\n"
        )
        db.write_text(t, encoding='utf-8')
    print(f'{prod.name:<18} migration + runner + scripts added')

print('done')

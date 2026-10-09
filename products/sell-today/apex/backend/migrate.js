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

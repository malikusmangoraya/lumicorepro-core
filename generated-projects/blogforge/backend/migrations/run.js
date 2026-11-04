const { Umzug, SequelizeStorage } = require('umzug');
const { sequelize } = require('../models');

const umzug = new Umzug({
  migrations: { glob: 'migrations/00*.js' },
  context: sequelize.getQueryInterface(),
  storage: new SequelizeStorage({ sequelize }),
  logger: console,
});

module.exports = umzug;
if (require.main === module) {
  umzug.up().then(() => sequelize.close()).catch((error) => {
    console.error('Migration failed:', error.message);
    process.exitCode = 1;
  });
}

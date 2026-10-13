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
      // Models whose schema is owned by a later, versioned migration are
      // skipped here. Otherwise a fresh install would create the table from
      // rawAttributes first and the later migration would collide with it (or
      // silently lose the indexes and constraints it declares).
      if (Model.migrationManaged === true) continue;
      // createTable is idempotent-safe here because the storage records which
      // migrations have run; it will not re-create tables on a second boot.
      await queryInterface.createTable(Model.tableName, Model.rawAttributes);
    }
  },

  async down({ context: queryInterface }) {
    const names = Object.values(models)
      .filter((M) => M && M.tableName && M.migrationManaged !== true)
      .map((M) => M.tableName)
      .reverse();
    for (const name of names) {
      await queryInterface.dropTable(name, { cascade: true, force: true })
        .catch(() => {});
    }
  },
};

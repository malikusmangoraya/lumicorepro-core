const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('records', {
      id: { type: DataTypes.UUID, primaryKey: true },
      title: { type: DataTypes.STRING(160), allowNull: false },
      body: { type: DataTypes.TEXT },
      status: { type: DataTypes.ENUM('draft', 'published', 'archived'), defaultValue: 'draft' },
      userId: {
        type: DataTypes.UUID, allowNull: false,
        references: { model: 'users', key: 'id' }, onDelete: 'CASCADE',
      },
      createdAt: { type: DataTypes.DATE, allowNull: false },
      updatedAt: { type: DataTypes.DATE, allowNull: false },
    });
    await queryInterface.addIndex('records', ['userId']);
    await queryInterface.addIndex('records', ['status']);
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('records');
  },
};

const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('articles', {
      id: { type: DataTypes.UUID, primaryKey: true },
      title: { type: DataTypes.STRING(220), allowNull: false },
      slug: { type: DataTypes.STRING, allowNull: false },
      keyword: { type: DataTypes.STRING(160), allowNull: false },
      tone: { type: DataTypes.STRING(40), allowNull: false, defaultValue: 'professional' },
      length: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'medium' },
      audience: { type: DataTypes.STRING(160) },
      content: { type: DataTypes.TEXT, allowNull: false },
      content_html: { type: DataTypes.TEXT },
      meta_title: { type: DataTypes.STRING(70) },
      meta_description: { type: DataTypes.STRING(200) },
      keywords: { type: DataTypes.STRING(400) },
      word_count: { type: DataTypes.INTEGER, defaultValue: 0 },
      credits_used: { type: DataTypes.INTEGER, defaultValue: 1 },
      demo: { type: DataTypes.BOOLEAN, defaultValue: false },
      user_id: {
        type: DataTypes.UUID, allowNull: false,
        references: { model: 'users', key: 'id' }, onDelete: 'CASCADE',
      },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });
    await queryInterface.addIndex('articles', ['user_id']);
    await queryInterface.addIndex('articles', ['created_at']);
    await queryInterface.addIndex('articles', ['slug']);

    await queryInterface.createTable('credits', {
      id: { type: DataTypes.UUID, primaryKey: true },
      balance: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
      total_granted: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
      total_used: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
      user_id: {
        type: DataTypes.UUID, allowNull: false, unique: true,
        references: { model: 'users', key: 'id' }, onDelete: 'CASCADE',
      },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });
    await queryInterface.addIndex('credits', ['user_id']);
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('credits');
    await queryInterface.dropTable('articles');
  },
};

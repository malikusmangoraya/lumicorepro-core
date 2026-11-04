const { Sequelize, DataTypes } = require('sequelize');

const connectionUrl = process.env.DATABASE_URL;
const ssl = process.env.DB_SSL !== 'false' && Boolean(connectionUrl);

const sequelize = connectionUrl
  ? new Sequelize(connectionUrl, {
      dialect: 'postgres',
      logging: false,
      dialectOptions: ssl ? { ssl: { require: true, rejectUnauthorized: false } } : {},
    })
  : new Sequelize({
      dialect: 'postgres',
      host: process.env.DB_HOST || 'localhost',
      port: Number(process.env.DB_PORT || 5432),
      database: process.env.DB_NAME || 'lumicore_app',
      username: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || '',
      logging: false,
    });

const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
}, { tableName: 'users', underscored: true });

const Article = sequelize.define('Article', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  title: { type: DataTypes.STRING(220), allowNull: false },
  slug: { type: DataTypes.STRING, allowNull: false },
  keyword: { type: DataTypes.STRING(160), allowNull: false },
  tone: { type: DataTypes.STRING(40), allowNull: false, defaultValue: 'professional' },
  length: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'medium' },
  audience: { type: DataTypes.STRING(160) },
  content: { type: DataTypes.TEXT, allowNull: false },
  contentHtml: { type: DataTypes.TEXT },
  metaTitle: { type: DataTypes.STRING(70) },
  metaDescription: { type: DataTypes.STRING(200) },
  keywords: { type: DataTypes.STRING(400) },
  wordCount: { type: DataTypes.INTEGER, defaultValue: 0 },
  creditsUsed: { type: DataTypes.INTEGER, defaultValue: 1 },
  demo: { type: DataTypes.BOOLEAN, defaultValue: false },
}, { tableName: 'articles', underscored: true });

Article.belongsTo(User, { foreignKey: 'userId', as: 'author', onDelete: 'CASCADE' });
User.hasMany(Article, { foreignKey: 'userId', onDelete: 'CASCADE' });

const Credit = sequelize.define('Credit', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  balance: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
  totalGranted: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
  totalUsed: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
}, { tableName: 'credits', underscored: true });

Credit.belongsTo(User, { foreignKey: 'userId', onDelete: 'CASCADE' });
User.hasOne(Credit, { foreignKey: 'userId', onDelete: 'CASCADE' });

module.exports = { sequelize, User, Article, Credit };

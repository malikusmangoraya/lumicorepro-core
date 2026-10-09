"use strict";

const { Model, DataTypes } = require("sequelize");

class WebhookEvent extends Model {
  static init(sequelize) {
    return super.init(
      {
        id: {
          type: DataTypes.INTEGER,
          primaryKey: true,
          autoIncrement: true,
        },
        event_id: {
          type: DataTypes.STRING,
          allowNull: false,
          unique: true,
        },
        event_type: {
          type: DataTypes.STRING,
          allowNull: false,
        },
        gateway: {
          type: DataTypes.STRING,
          allowNull: false,
        },
        payload: {
          type: DataTypes.JSONB,
          allowNull: true,
        },
        status: {
          type: DataTypes.ENUM("pending", "processed", "failed"),
          defaultValue: "pending",
        },
        response_code: {
          type: DataTypes.INTEGER,
        },
        error_message: {
          type: DataTypes.TEXT,
        },
      },
      {
        sequelize,
        modelName: "WebhookEvent",
        tableName: "webhook_events",
        timestamps: true,
      }
    );
  }
}

module.exports = WebhookEvent;

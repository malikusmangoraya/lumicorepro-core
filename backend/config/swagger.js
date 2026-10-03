import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'LumiCorePro API',
      version: '1.0.0',
      description: 'Complete full-stack API for LumiCorePro platform with authentication, e-commerce, payments, analytics, and more',
      contact: {
        name: 'LumiCorePro Team',
        email: 'support@lumicorepro.com',
      },
    },
    servers: [
      {
        url: 'http://localhost:5000',
        description: 'Development server',
      },
      {
        url: process.env.PRODUCTION_URL || 'https://api.lumicorepro.com',
        description: 'Production server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
    security: [
      {
        bearerAuth: [],
      },
    ],
  },
  // Absolute glob: the old relative './routes/*.js' only resolved when the
  // process CWD happened to be backend/, so /api-docs was empty otherwise.
  apis: [path.join(__dirname, '..', 'routes', '*.js')],
};

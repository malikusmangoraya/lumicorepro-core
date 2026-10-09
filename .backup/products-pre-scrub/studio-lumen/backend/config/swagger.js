module.exports = {
  openapi: '3.0.0',
  info: {
    title: 'Enterprise REST API',
    version: '1.0.0',
    description: 'High-performance REST API backend for production services',
  },
  servers: [{ url: 'http://localhost:5000/api', description: 'Local Development Server' }],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      },
    },
  },
};

export const demoResults = {
  folderStructure: {
    title: 'Folder Structure Analysis',
    structure: [
      {
        path: 'src/',
        description: 'Main source code directory containing all application logic',
        children: [
          {
            path: 'controllers/',
            description: 'Handles incoming HTTP requests and orchestrates business logic',
          },
          {
            path: 'models/',
            description: 'Database schemas and data models using Mongoose/Sequelize',
          },
          {
            path: 'routes/',
            description: 'API endpoint definitions that map URLs to controller functions',
          },
          {
            path: 'middleware/',
            description: 'Request preprocessing (authentication, logging, validation)',
          },
          {
            path: 'services/',
            description: 'Business logic layer that controllers delegate to',
          },
          {
            path: 'utils/',
            description: 'Helper functions and utility modules used across the app',
          },
        ],
      },
      {
        path: 'config/',
        description: 'Configuration files for database, environment variables, and app settings',
      },
      {
        path: 'tests/',
        description: 'Unit and integration tests for the application',
      },
      {
        path: 'public/',
        description: 'Static assets like images, CSS, and client-side JavaScript',
      },
    ],
  },
  
  entryPoint: {
    title: 'Entry Point Detection',
    file: 'server.js',
    flow: [
      'server.js loads environment variables from .env file',
      'Establishes MongoDB connection via db.config.js',
      'Initializes Express middleware (CORS, body-parser, helmet)',
      'Registers authentication middleware for protected routes',
      'Mounts API routes from /routes/index.js',
      'Configures error handling middleware',
      'Starts HTTP server listening on PORT 3000',
    ],
    codeSnippet: `// server.js
const express = require('express');
const mongoose = require('mongoose');
const routes = require('./routes');

const app = express();

// Connect to database
mongoose.connect(process.env.DB_URI);

// Middleware
app.use(express.json());
app.use('/api', routes);

// Start server
app.listen(3000);`,
  },
  
  dependencyMapping: {
    title: 'Dependency Mapping',
    graph: [
      {
        file: 'routes/auth.routes.js',
        imports: ['controllers/auth.controller.js'],
        level: 1,
      },
      {
        file: 'controllers/auth.controller.js',
        imports: ['services/user.service.js', 'utils/jwt.util.js'],
        level: 2,
      },
      {
        file: 'services/user.service.js',
        imports: ['models/user.model.js', 'utils/bcrypt.util.js'],
        level: 3,
      },
      {
        file: 'models/user.model.js',
        imports: [],
        level: 4,
      },
    ],
    visualization: {
      nodes: [
        { id: 'auth.routes', label: 'auth.routes.js', type: 'route' },
        { id: 'auth.controller', label: 'auth.controller.js', type: 'controller' },
        { id: 'user.service', label: 'user.service.js', type: 'service' },
        { id: 'user.model', label: 'user.model.js', type: 'model' },
      ],
      edges: [
        { from: 'auth.routes', to: 'auth.controller' },
        { from: 'auth.controller', to: 'user.service' },
        { from: 'user.service', to: 'user.model' },
      ],
    },
  },
  
  criticalFiles: {
    title: 'Critical File Identification',
    files: [
      {
        name: 'server.js',
        role: 'Application Entry Point',
        importance: 'critical',
        description: 'Bootstraps the entire application, configures middleware, and starts the server',
        linesOfCode: 89,
      },
      {
        name: 'config/db.config.js',
        role: 'Database Configuration',
        importance: 'critical',
        description: 'Manages database connection pooling and configuration',
        linesOfCode: 45,
      },
      {
        name: 'middleware/auth.middleware.js',
        role: 'Authentication Gateway',
        importance: 'high',
        description: 'Validates JWT tokens and protects sensitive routes',
        linesOfCode: 67,
      },
      {
        name: 'controllers/auth.controller.js',
        role: 'Authentication Logic',
        importance: 'high',
        description: 'Handles user login, registration, and token generation',
        linesOfCode: 156,
      },
      {
        name: 'models/user.model.js',
        role: 'User Data Schema',
        importance: 'high',
        description: 'Defines user schema and database operations',
        linesOfCode: 78,
      },
    ],
  },
  
  executionFlow: {
    title: 'Execution Flow Explanation',
    scenarios: [
      {
        name: 'User Login Request',
        steps: [
          {
            step: 1,
            component: 'Client',
            action: 'POST /api/auth/login',
            description: 'User submits credentials',
          },
          {
            step: 2,
            component: 'routes/auth.routes.js',
            action: 'Route Matching',
            description: 'Maps request to auth controller',
          },
          {
            step: 3,
            component: 'controllers/auth.controller.js',
            action: 'Validate Input',
            description: 'Checks email and password format',
          },
          {
            step: 4,
            component: 'services/user.service.js',
            action: 'Query Database',
            description: 'Fetches user by email',
          },
          {
            step: 5,
            component: 'models/user.model.js',
            action: 'Execute Query',
            description: 'Runs MongoDB query',
          },
          {
            step: 6,
            component: 'utils/bcrypt.util.js',
            action: 'Compare Password',
            description: 'Verifies hashed password',
          },
          {
            step: 7,
            component: 'utils/jwt.util.js',
            action: 'Generate Token',
            description: 'Creates JWT with user payload',
          },
          {
            step: 8,
            component: 'Client',
            action: 'Receive Response',
            description: 'Gets token and user data',
          },
        ],
      },
    ],
  },
  
  repositorySummary: {
    title: 'Intelligent Repository Summary',
    overview: 'A modern Node.js REST API built with Express.js, following MVC architecture patterns with clear separation of concerns.',
    techStack: [
      { name: 'Node.js', version: '18.x', category: 'Runtime' },
      { name: 'Express.js', version: '4.18.2', category: 'Framework' },
      { name: 'MongoDB', version: '6.0', category: 'Database' },
      { name: 'Mongoose', version: '7.0.3', category: 'ODM' },
      { name: 'JWT', version: '9.0.0', category: 'Authentication' },
      { name: 'Bcrypt', version: '5.1.0', category: 'Security' },
    ],
    architecture: 'MVC (Model-View-Controller)',
    patterns: [
      'Repository Pattern for data access',
      'Service Layer for business logic',
      'Middleware Chain for request processing',
      'Dependency Injection in services',
    ],
    keyDecisions: [
      {
        decision: 'JWT-based Authentication',
        rationale: 'Stateless authentication enables horizontal scaling and microservices architecture',
      },
      {
        decision: 'MongoDB with Mongoose',
        rationale: 'Flexible schema design allows rapid iteration and handles complex nested data',
      },
      {
        decision: 'Layered Architecture',
        rationale: 'Clear separation between routes, controllers, services, and models improves maintainability',
      },
    ],
    metrics: {
      totalFiles: 47,
      linesOfCode: 3421,
      testCoverage: 78,
      dependencies: 23,
    },
  },
};

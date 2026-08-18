const fs = require('fs');
let code = fs.readFileSync('server.ts', 'utf8');

// Add imports
if (!code.includes("import helmet")) {
    code = code.replace(
        'import path from "path";',
        'import path from "path";\nimport helmet from "helmet";\nimport rateLimit from "express-rate-limit";\nimport cors from "cors";'
    );
}

// Add middleware
if (!code.includes("app.use(helmet")) {
    code = code.replace(
        'const app = express();',
        `const app = express();
  
  // Security middlewares
  app.use(helmet({
    contentSecurityPolicy: false, // Disabled for local development / Vite
  }));
  app.use(cors());
  
  // Rate limiting
  const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // Limit each IP to 1000 requests per windowMs
    standardHeaders: true,
    legacyHeaders: false,
  });
  app.use('/api/', apiLimiter);`
    );
}

fs.writeFileSync('server.ts', code);

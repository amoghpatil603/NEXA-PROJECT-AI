const fs = require('fs');
let code = fs.readFileSync('src/studio/StudioMain.tsx', 'utf8');

// replace everything between "import React" and "import { Dashboard }"
code = code.replace(
  /import \{\s*LayoutDashboard[\s\S]*?from 'lucide-react';/,
  "import { LayoutDashboard, Workflow, Bot, Blocks, Brain, Database, Box, Cloud, Activity, Mic } from 'lucide-react';"
);

fs.writeFileSync('src/studio/StudioMain.tsx', code);

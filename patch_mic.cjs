const fs = require('fs');
let code = fs.readFileSync('src/studio/StudioMain.tsx', 'utf8');

code = code.replace(
  /import \{[\s\S]*?\}   Mic\} from 'lucide-react';/,
  "import { LayoutDashboard, Workflow, Bot, Blocks, Brain, Database, Box, Cloud, Activity, Mic } from 'lucide-react';"
);

fs.writeFileSync('src/studio/StudioMain.tsx', code);

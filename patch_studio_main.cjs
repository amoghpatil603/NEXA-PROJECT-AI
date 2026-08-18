const fs = require('fs');
let code = fs.readFileSync('src/studio/StudioMain.tsx', 'utf8');

// 1. Add Mic to lucide-react imports
if (!code.includes('Mic,')) {
    code = code.replace(
        "import {\n  LayoutDashboard,",
        "import {\n  LayoutDashboard,\n  Mic,"
    );
}

// 2. Import VoiceManager
if (!code.includes('VoiceManager')) {
    code = code.replace(
        "import { MonitoringDashboard } from './pages/MonitoringDashboard';",
        "import { MonitoringDashboard } from './pages/MonitoringDashboard';\nimport { VoiceManager } from './pages/VoiceManager';"
    );
}

// 3. Add to StudioPage type
if (!code.includes("| 'voice'")) {
    code = code.replace(
        "| 'monitoring';",
        "| 'monitoring'\n  | 'voice';"
    );
}

// 4. Add to navItems
if (!code.includes("id: 'voice'")) {
    code = code.replace(
        "{ id: 'monitoring', label: 'Monitoring', icon: <Activity size={16} /> },",
        "{ id: 'monitoring', label: 'Monitoring', icon: <Activity size={16} /> },\n    { id: 'voice', label: 'Voice Manager', icon: <Mic size={16} /> },"
    );
}

// 5. Add to activePage rendering
if (!code.includes("<VoiceManager />")) {
    code = code.replace(
        "{activePage === 'monitoring' && <MonitoringDashboard />}",
        "{activePage === 'monitoring' && <MonitoringDashboard />}\n        {activePage === 'voice' && <VoiceManager />}"
    );
}

fs.writeFileSync('src/studio/StudioMain.tsx', code);

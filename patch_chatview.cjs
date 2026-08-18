const fs = require('fs');
let code = fs.readFileSync('src/components/ChatView.tsx', 'utf8');

// 1. Add import
if (!code.includes('VisionUploader')) {
    code = code.replace(
        "import { MarkdownMessage } from './MarkdownMessage';",
        "import { MarkdownMessage } from './MarkdownMessage';\nimport { VisionUploader } from './VisionUploader';"
    );
}

// 2. Add the VisionUploader to the input form bar
if (!code.includes('<VisionUploader')) {
    code = code.replace(
        '<div className="flex-1 bg-slate-900 border border-slate-700/80 focus-within:border-indigo-500 rounded-2xl p-2.5 shadow-inner transition-colors">',
        '<div className="flex-1 bg-slate-900 border border-slate-700/80 focus-within:border-indigo-500 rounded-2xl p-2.5 shadow-inner transition-colors">\n            <div className="flex items-center gap-2 mb-1">\n              <VisionUploader onExtracted={(text) => setInput((prev) => prev ? prev + "\\n\\n" + text : text)} />\n            </div>'
    );
}

fs.writeFileSync('src/components/ChatView.tsx', code);

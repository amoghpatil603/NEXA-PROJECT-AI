const fs = require('fs');
let code = fs.readFileSync('src/components/ChatView.tsx', 'utf8');

// 1. Add imports
if (!code.includes('VoiceRecorder')) {
    code = code.replace(
        "import { VisionUploader } from './VisionUploader';",
        "import { VisionUploader } from './VisionUploader';\nimport { VoiceRecorder } from './VoiceRecorder';\nimport { VoicePlayer } from './VoicePlayer';"
    );
}

// 2. Add VoiceRecorder to input bar
if (!code.includes('<VoiceRecorder')) {
    code = code.replace(
        '<VisionUploader onExtracted={(text) => setInput((prev) => prev ? prev + "\\n\\n" + text : text)} />',
        '<VisionUploader onExtracted={(text) => setInput((prev) => prev ? prev + "\\n\\n" + text : text)} />\n              <VoiceRecorder onTranscript={(text) => setInput((prev) => prev ? prev + " " + text : text)} />'
    );
}

// 3. Add VoicePlayer to Assistant message actions
if (!code.includes('<VoicePlayer')) {
    code = code.replace(
        '<button\n                            onClick={() => copyToClipboard(msg.text, msg.id)}\n                            className="p-1.5 hover:bg-slate-800 rounded-md text-slate-500 hover:text-slate-300 transition-colors"\n                            title="Copy"\n                          >\n                            {copiedMsgId === msg.id ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}\n                          </button>',
        '<button\n                            onClick={() => copyToClipboard(msg.text, msg.id)}\n                            className="p-1.5 hover:bg-slate-800 rounded-md text-slate-500 hover:text-slate-300 transition-colors"\n                            title="Copy"\n                          >\n                            {copiedMsgId === msg.id ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}\n                          </button>\n                          <VoicePlayer text={msg.text} />'
    );
}

fs.writeFileSync('src/components/ChatView.tsx', code);

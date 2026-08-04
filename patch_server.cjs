const fs = require('fs');
let code = fs.readFileSync('server.ts', 'utf8');

const target = `        // Try to parse the last JSON object in output
        const lines = output.trim().split("\\n");
        const lastLine = lines[lines.length - 1];
        const result = JSON.parse(lastLine);`;

const replacement = `        // Extract JSON between tags
        let result;
        const startTag = "---JSON_RESULT_START---";
        const endTag = "---JSON_RESULT_END---";
        if (output.includes(startTag) && output.includes(endTag)) {
            const jsonStr = output.split(startTag)[1].split(endTag)[0].trim();
            result = JSON.parse(jsonStr);
        } else {
            const lines = output.trim().split("\\n");
            result = JSON.parse(lines[lines.length - 1]);
        }`;

code = code.replace(target, replacement);
fs.writeFileSync('server.ts', code);

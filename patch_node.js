const fs = require('fs');
let content = fs.readFileSync('src/components/ModelPanel.tsx', 'utf8');

const target = `      const mData = await modelRes.json();
      const sData = await sysRes.json();

      setModelInfo(prev => ({ ...prev, ...mData }));
      setSysStatus(sData);`;

const replacement = `      if (modelRes.ok) {
        const text = await modelRes.text();
        if (text && text.trim().startsWith('{')) {
          try {
            const mData = JSON.parse(text);
            setModelInfo(prev => ({ ...prev, ...mData }));
          } catch(e) {}
        }
      }
      if (sysRes.ok) {
        const text = await sysRes.text();
        if (text && text.trim().startsWith('{')) {
          try {
            const sData = JSON.parse(text);
            setSysStatus(sData);
          } catch(e) {}
        }
      }`;

content = content.replace(target, replacement);
fs.writeFileSync('src/components/ModelPanel.tsx', content);

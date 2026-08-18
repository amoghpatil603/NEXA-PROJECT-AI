import re
with open("src/components/ModelPanel.tsx", "r") as f:
    content = f.read()

target = """      const mData = await modelRes.json();
      const sData = await sysRes.json();

      setModelInfo(prev => ({ ...prev, ...mData }));
      setSysStatus(sData);"""

replacement = """      if (modelRes.ok) {
        const text = await modelRes.text();
        if (text) {
          try {
            const mData = JSON.parse(text);
            setModelInfo(prev => ({ ...prev, ...mData }));
          } catch(e) {}
        }
      }
      if (sysRes.ok) {
        const text = await sysRes.text();
        if (text) {
          try {
            const sData = JSON.parse(text);
            setSysStatus(sData);
          } catch(e) {}
        }
      }"""

content = content.replace(target, replacement)

with open("src/components/ModelPanel.tsx", "w") as f:
    f.write(content)

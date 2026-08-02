import re
with open("src/components/ModelPanel.tsx", "r") as f:
    content = f.read()

target = """      const mData = await modelRes.json();
      const sData = await sysRes.json();

      setModelInfo(prev => ({ ...prev, ...mData }));
      setSysStatus(sData);"""

replacement = """      if (modelRes.ok && modelRes.headers.get('content-type')?.includes('application/json')) {
        const mData = await modelRes.json();
        setModelInfo(prev => ({ ...prev, ...mData }));
      }
      if (sysRes.ok && sysRes.headers.get('content-type')?.includes('application/json')) {
        const sData = await sysRes.json();
        setSysStatus(sData);
      }"""

# Since I messed up the sed, I'll just restore the original and replace it correctly.
content = content.replace("if (modelRes.ok && modelRes.headers.get('content-type')?.includes('application/json')) { const mData = await modelRes.json(); setModelInfo(prev => ({ ...prev, ...mData })); }", "const mData = await modelRes.json();")

content = content.replace(target, replacement)

with open("src/components/ModelPanel.tsx", "w") as f:
    f.write(content)

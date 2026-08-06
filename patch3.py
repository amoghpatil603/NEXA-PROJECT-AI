import re
with open("src/components/ModelPanel.tsx", "r") as f:
    content = f.read()

content = content.replace("try { const mData = JSON.parse(text);  }", "try { const mData = JSON.parse(text); setModelInfo(prev => ({ ...prev, ...mData })); }")
content = content.replace("try { const sData = JSON.parse(text);  }", "try { const sData = JSON.parse(text); setSysStatus(sData); }")

with open("src/components/ModelPanel.tsx", "w") as f:
    f.write(content)

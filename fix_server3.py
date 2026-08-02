import re

with open('server.ts', 'r') as f:
    content = f.read()

content = content.replace('import { spawn, ChildProcess } from "child_process";', 'import { spawn, spawnSync, ChildProcess } from "child_process";')
content = content.replace('const { spawnSync } = require("child_process");', '')

with open('server.ts', 'w') as f:
    f.write(content)


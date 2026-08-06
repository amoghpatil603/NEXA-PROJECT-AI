import os
import glob

def resolve_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    new_lines = []
    in_head = False
    in_main = False
    
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_head = True
            continue
        elif line.startswith('======='):
            in_head = False
            in_main = True
            continue
        elif line.startswith('>>>>>>> origin/main'):
            in_main = False
            continue
            
        if in_head:
            new_lines.append(line)
        elif in_main:
            pass # ignore main
        else:
            new_lines.append(line)
            
    with open(filepath, 'w') as f:
        f.writelines(new_lines)

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            resolve_file(os.path.join(root, file))

print("Resolved conflicts")

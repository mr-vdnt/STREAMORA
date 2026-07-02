import re

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\services\agent\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

endpoints = re.findall(r'@app\.(get|post|put|delete)\([\s\'\"]*\/([^\'\"]+)[\'\"]*\)', content)
for method, path in endpoints:
    print(f'{method.upper()} /{path}')

import re
import sys

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\style.css', 'r', encoding='utf-8') as f:
    content = f.read()

with open('scratch/css_analysis.txt', 'w', encoding='utf-8') as out:
    out.write("--- CSS SELECTORS WITH CARD/ROW ---\n")
    selectors = re.findall(r'([^}{]*?)\s*\{', content)
    for s in selectors:
        s = s.strip()
        if 'card' in s or 'row' in s:
            out.write(s + '\n')

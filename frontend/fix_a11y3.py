import os

landing_path = "src/pages/Landing.tsx"
with open(landing_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix heading order h4 -> h3
content = content.replace('<h4 ', '<h3 ')
content = content.replace('</h4>', '</h3>')

# Fix footer contrast
content = content.replace('text-slate-800', 'text-[#FAFAFA]')
content = content.replace('text-slate-400', 'text-slate-300')
content = content.replace('hover:text-slate-700', 'hover:text-slate-200')

with open(landing_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied final a11y fixes to Landing.tsx")

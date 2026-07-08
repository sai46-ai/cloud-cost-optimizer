import os
import re

base_dir = "src/pages"

# Fix Landing.tsx
landing_path = os.path.join(base_dir, "Landing.tsx")
with open(landing_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace root div with main
content = content.replace('<div className="relative min-h-screen overflow-x-hidden font-sans selection:bg-blue-300/40">', '<main className="relative min-h-screen overflow-x-hidden font-sans selection:bg-blue-300/40">')
# Revert inner main to div
content = content.replace('<main className="relative z-20 flex flex-col">', '<div className="relative z-20 flex flex-col">')
# Replace the first closing main with div
content = content.replace('</main>{/* end sections wrapper */}', '</div>{/* end sections wrapper */}')
# Replace the very last closing div with main
content = content.replace('    </div>\n  );\n}', '    </main>\n  );\n}')

with open(landing_path, "w", encoding="utf-8") as f:
    f.write(content)

# Fix Login.tsx
login_path = os.path.join(base_dir, "Login.tsx")
with open(login_path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('text-accent-primary', 'text-blue-400')
content = content.replace('hover:text-accent-primary-hover', 'hover:text-blue-300')
with open(login_path, "w", encoding="utf-8") as f:
    f.write(content)

# Fix Register.tsx
register_path = os.path.join(base_dir, "Register.tsx")
with open(register_path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('text-accent-primary', 'text-blue-400')
content = content.replace('hover:text-accent-primary-hover', 'hover:text-blue-300')
with open(register_path, "w", encoding="utf-8") as f:
    f.write(content)

print("A11y fixes applied.")

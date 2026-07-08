import os

landing_path = "src/pages/Landing.tsx"
with open(landing_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix footer contrast by removing the translucent glass background
content = content.replace('footer className="py-10 landing-section-glass"', 'footer className="py-10 border-t border-white/10"')

with open(landing_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied footer contrast fix to Landing.tsx")

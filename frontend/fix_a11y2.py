import os

landing_path = "src/pages/Landing.tsx"
with open(landing_path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to fix the FadeIn component closing tag.
# It currently has:
#       {children}
#     </main>
#   );
# }
# We need to change the FIRST </main>\n  );\n} back to </div>\n  );\n}

# Let's find the first occurrence
idx = content.find("    </main>\n  );\n}")
if idx != -1:
    content = content[:idx] + "    </div>\n  );\n}" + content[idx + len("    </main>\n  );\n}"):]

with open(landing_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Restored FadeIn closing tag.")

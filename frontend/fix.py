import re

file_path = "src/pages/Landing.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the duplicate block
# We will find the first occurrence of:
# </main>{/* end sections wrapper */}
# And the real end of file:
#       </div>{/* end scrollable content */}
#     </div>
#   );
# }

# Let's just find the first "        </main>{/* end sections wrapper */}"
# and drop everything after it, then append the proper closing tags.

main_end = "        </main>{/* end sections wrapper */}"
idx = content.find(main_end)

if idx != -1:
    content = content[:idx + len(main_end)]
    content += "\n\n      </div>{/* end scrollable content */}\n    </div>\n  );\n}\n"

# Fix the top part
# We need to ensure that the <main className="relative z-20 flex flex-col"> is there.
# Let's find: <main className="relative z-20 flex flex-col">
# It should be there.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed Landing.tsx")

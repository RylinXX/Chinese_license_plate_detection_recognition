import os

INDEX_PATH = r"C:\Users\RM\.gemini\antigravity\scratch\worksite_bookkeeping_app\templates\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Replace JS keys
content = content.replace("f.fleet_name", "f.company_name")
content = content.replace("f.paid_amount", "f.paid_cost")
content = content.replace("f.unpaid_amount", "f.unpaid_cost")

content = content.replace("s.dump_site", "s.site_name")
content = content.replace("s.paid_amount", "s.paid_cost")
content = content.replace("s.unpaid_amount", "s.unpaid_cost")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed variable names in index.html")

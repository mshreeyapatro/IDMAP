with open('docs/IDMAP_Complete_Knowledge_Transfer_Report.md', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Length of Knowledge Transfer Report:", len(text))
print("First 500 chars:")
print(text[:500])


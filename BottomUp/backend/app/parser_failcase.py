import json,os
try:
    with open(r"C:\Users\sushi\Downloads\fastapi_react_bottomup\backend\data\generated_project\_raw.json",'r') as f:
        parsed= json.load(f)
except Exception as e:
     parsed=None
     print(e)

outdir="./data/generated_project/"
if not parsed == None:
     for path, contents in (parsed.items() if isinstance(parsed, dict) else {'_raw': parsed} .items()):
        safe = os.path.join(outdir, path)
        folder = os.path.dirname(safe)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(safe, 'w', encoding='utf-8') as f:
            f.write(contents)
else:
    print("failes")


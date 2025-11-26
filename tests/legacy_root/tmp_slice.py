from pathlib import Path
lines = Path('frontend/src/components/dataImports/ControlModelConfigurator.tsx').read_text().splitlines()
for idx in range(200, 320):
    print(f"{idx+1}: {lines[idx]}")

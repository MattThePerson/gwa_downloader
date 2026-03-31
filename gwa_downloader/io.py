""" general io stuff """
from pathlib import Path
import json

def read_json(file: str|Path) -> dict:
    if not Path(file).exists():
        return {}
    with open(str(file), 'r') as f:
        return json.load(f)

def write_json(data: dict, file: str|Path):
    with open(str(file), 'w') as f:
        json.dump(data, f, indent=4)

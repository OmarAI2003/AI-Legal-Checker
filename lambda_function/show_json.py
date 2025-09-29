import json
import sys
import os

def pretty_print_json(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error reading JSON: {e}")

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'sample_event.json')
    pretty_print_json(path)

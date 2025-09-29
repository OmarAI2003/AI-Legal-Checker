import json
import os
import sys
from lambda_rag_processor import lambda_handler

def load_event(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json_output(data):
    output_file = 'lambda_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Output written to {output_file}")

def main():
    # accept optional filename argument
    event_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'sample_event.json')
    if not os.path.exists(event_path):
        print(f"Event file not found: {event_path}")
        return

    event = load_event(event_path)
    
    # Call the lambda handler
    response = lambda_handler(event, None)
    
    # Prepare output
    output = {"response": response}
    
    # If response body contains JSON, add parsed body to output
    body = response.get('body') if isinstance(response, dict) else None
    if body:
        try:
            parsed = json.loads(body)
            output["parsed_body"] = parsed
        except Exception:
            pass
    
    # Write to file
    write_json_output(output)

if __name__ == '__main__':
    main()


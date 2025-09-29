import json
import os
import sys
from lambda_rag_processor import lambda_handler

def load_event(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_input_files():
    input_dir = os.path.join(os.getcwd(), 'json_input_contracts')
    if not os.path.exists(input_dir):
        print(f"Input directory not found: {input_dir}")
        return []
    return [f for f in os.listdir(input_dir) if f.endswith('.json')]

def write_json_output(data, input_filename):
    output_dir = 'json_output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'output_{input_filename}')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Output written to {output_file}")

def main():
    input_files = get_input_files()
    if not input_files:
        print("No JSON files found in json_input_contracts directory")
        return

    for filename in input_files:
        print(f"Processing {filename}...")
        input_path = os.path.join(os.getcwd(), 'json_input_contracts', filename)
        event = load_event(input_path)
        
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
        write_json_output(output, filename)

if __name__ == '__main__':
    main()


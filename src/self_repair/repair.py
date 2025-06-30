import os
import json
import time
import argparse
from pathlib import Path
from generation import generation_in_parallel


base_prompt = '''You were asked to generate code according to the prompt to complete the task required in the instruction. However, the code you generated did not meet the constraints: {answer}.
## previous code
{prev_code}
Please regenerate a code to meet the constraints.
Only respond to the code, no more information. The following is the prompt:\n{prompt}'''


def self_repair(input_file, model_name, output_dir_path):
    print(f"=== Self-Repair Generation Started ===")
    print(f"Model: {model_name}")
    print(f"Input File: {input_file}")

    responses = []
    try:
        print("Loading input prompt file...")
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"Successfully loaded {len(data)} prompts.")
    except Exception as e:
        print(f"[ERROR] Failed to load input file: {e}")
        return

    for index, item in enumerate(data, start=1):
        if item['is_matched']:
            responses.append({"id": index, "response": [[item['prompt'], item['generated_code']]]})
            continue

        print(f"\n--- Processing prompt {index}/{len(data)} ---")

        prompt = base_prompt.format(
            answer=f"{item['constraint']}: {item['answer']}",
            prev_code=item['generated_code'],
            prompt=item['prompt']
        )

        try:
            print(f"Calling model '{model_name}' for prompt {index}...")
            result = generation_in_parallel(prompt, model_name)
            print(f"Model call completed for prompt {index}.")
            responses.append({"id": index, "response": result})
        except Exception as e:
            print(f"[ERROR] Model call failed for prompt {index}: {e}")
            responses.append({"id": index, "response": None, "error": str(e)})

    input_stem = Path(input_file).stem
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir_path) / model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_name = f"{input_stem}_{model_name}_{timestamp}.json"
    output_path = output_dir / output_file_name

    try:
        print("\nSaving responses to output file...")
        with open(output_path, 'w', encoding='utf-8') as out_file:
            json.dump(responses, out_file, ensure_ascii=False, indent=2)
        print(f"Responses successfully saved to: {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save output file: {e}")
    
    print("=== Self-Repair Generation Completed ===")


def repair_all_in_dir(file_dir, model_name, output_dir_path):
    files = os.listdir(file_dir)
    for file in files:
        input_path = os.path.join(file_dir, file)
        self_repair(input_path, model_name, output_dir_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Self-Repair Generation")
    parser.add_argument('--model', type=str, required=True, help='Model name (e.g., gpt-4o, claude-3-7-sonnet)')
    parser.add_argument('--input_dir', type=str, required=True, help='Input directory path')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory path')
    args = parser.parse_args()

    repair_all_in_dir(args.input_dir, args.model, args.output_dir)

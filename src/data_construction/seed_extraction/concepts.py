import random
import json
from pathlib import Path
from generation import generation_in_parallel
import os


def sample_jsonl_records(folder_path, sample_size=50, output_file="sampled_data.json"):
    all_samples = []

    # Traverse all .jsonl files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < sample_size:
                    print(f"Warning: There are only {len(lines)} records in file {filename}, which is less than {sample_size}. All will be used.")
                    sampled = [json.loads(line) for line in lines]
                else:
                    sampled_lines = random.sample(lines, sample_size)
                    sampled = [json.loads(line) for line in sampled_lines]
                all_samples.extend(sampled)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, ensure_ascii=False, indent=2)

    print(f"{len(all_samples)} records extracted from JSONL file in {folder_path} and written to {output_file}")


def sample_new_complex_jsonl_records(
    folder_path,
    existing_data_file,
    sample_size=50,
    min_code_length=200,
    output_file="new_sampled_data.json"
):
    # 读取已存在的数据，收集已有的code内容
    if os.path.exists(existing_data_file):
        with open(existing_data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_codes = set(item.get("code", "").strip() for item in existing_data)
    else:
        existing_codes = set()
        print(f"Warning: existing_data_file {existing_data_file} not found. Assuming no existing data.")

    new_samples = []

    # 遍历新的jsonl文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        code_content = record.get("code", "").strip()
                        # 过滤条件：
                        if (
                            code_content and
                            code_content not in existing_codes and
                            len(code_content) >= min_code_length
                        ):
                            new_samples.append(record)
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping invalid JSON line in file {filename}.")

    # 如果新采样的数据多于 sample_size，随机取样
    if len(new_samples) > sample_size:
        new_samples = random.sample(new_samples, sample_size)
    else:
        print(f"Warning: Only {len(new_samples)} valid new records found, less than requested {sample_size}.")

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_samples, f, ensure_ascii=False, indent=2)

    print(f"{len(new_samples)} new complex records written to {output_file}.")


prompt_template = """Extract key programming concepts from the provided code snippet. Programming concepts refer to the foundational principles and techniques used in programming , which are crucial for developers to master. You must list these concepts in a comma-separated format.
Code snippet:
{}"""


def process_and_save_code_snippets(output_file):
    # Load seed code snippets
    with open("test.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seed_code_list = [item["code"] for item in data]

    results = []
    
    for item in seed_code_list:
        # print(item)
        # Create the full prompt
        full_prompt = prompt_template.format(item)
        
        # Call the LLM (assuming Openai class has a generate method)
        try:
            responses = generation_in_parallel([full_prompt], 'gpt-4o')
            
            # Create the pair and add to results
            pair = {
                "code_snippet": item,
                "concepts": responses[0][1].strip()
            }
            results.append(pair)
        except Exception as e:
            print(f"Error processing code snippet: {e}")
            continue
    
    # Save results to a new file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully processed and saved {len(results)} pairs to {output_file}")


if __name__ == "__main__":
    process_and_save_code_snippets("test_out_task.json")

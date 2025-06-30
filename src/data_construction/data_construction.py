import re
import json
from generation import generation_in_parallel
from prompt_construction import generate_prompts_by_constraint
from multi_level_prompt_construction import data_structure_constraints_prompts

def extract_prompt_answer_pair(response):
    prompt_match = re.search(r'<prompt>(.*?)</prompt>', response, re.DOTALL)
    answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)

    prompt = ""
    answer = ""
    if prompt_match and answer_match:
        prompt = prompt_match.group(1).strip()
        answer = answer_match.group(1).strip()

    return prompt, answer


def run_explicit_generation(prompts_data):
    prompts = [item["prompt"] for item in prompts_data]
    responses = generation_in_parallel(prompts, "")

    new_data = []
    for index, item in enumerate(responses):
        prompt, answer = extract_prompt_answer_pair(item[1])
        new_entry = {
            "id": index + 1,
            "prompt": prompt,
            "answer": answer,
            "response": item
        }
        new_data.append(new_entry)
    return new_data


def run_implicit_generation(prompts_data):
    prompts = [item["prompt"] for item in prompts_data]
    responses = generation_in_parallel(prompts, "")

    new_data = []
    for index, item in enumerate(responses):
        prompt = item[1]
        new_entry = {
            "id": index + 1,
            "prompt": prompt,
            "answer": ""
        }
        new_data.append(new_entry)
    return new_data


def run_single_level_generation(constraint, count, output_file):
    explicit = not constraint in ['situation', 'code_contextual', 'example', 'non_functional_requirements']
    prompts_data = generate_prompts_by_constraint(constraint, count)

    if explicit:
        results = run_explicit_generation(prompts_data)
    else:
        results = run_implicit_generation(prompts_data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Success generate {len(results)} prompts with answers → {output_file}")


def extract_new_prompt_answer_pair(response):
    prompt_match = re.search(r'<new_prompt>(.*?)</new_prompt>', response, re.DOTALL)
    answer_match = re.search(r'<new_answer>(.*?)</new_answer>', response, re.DOTALL)

    prompt = ""
    answer = ""
    if prompt_match and answer_match:
        prompt = prompt_match.group(1).strip()
        answer = answer_match.group(1).strip()

    return prompt, answer


def generate_data_structure_level_constraints(input_file, output_file, level_num=3):
    responses = []
    index = 1

    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

        for item in data:
            responses.append({
                "id": index, 
                "category": "data_structure", 
                "level": 0, 
                "result": [],
                "prompt": item["prompt"],
                "answer": item["answer"]
            })
            index += 1

            prompt = data_structure_constraints_prompts(item["prompt"], item["answer"])
            for iteration in range(1, level_num + 1):
                result = generation_in_parallel(prompt, 'gpt-4-turbo-2024-04-09') # gpt-4-turbo-2024-04-09 llama3-70b-8192
                print(result)
                new_prompt, new_answer = extract_new_prompt_answer_pair(result[0][1])
                prompt = data_structure_constraints_prompts(new_prompt, new_answer)
                
                responses.append({
                    "id": index, 
                    "category": "data_structure",
                    "level": iteration,
                    "result": result,
                    "prompt": new_prompt,
                    "answer": new_answer
                })
                index += 1

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(responses, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run prompt generation experiments.")

    subparsers = parser.add_subparsers(dest="mode", required=True, help="Choose generation mode")

    # --- single-level subcommand ---
    single_parser = subparsers.add_parser("single-level", help="Run single-level prompt generation")
    single_parser.add_argument("--constraint", type=str, required=True, help="Constraint type")
    single_parser.add_argument("--count", type=int, default=50, help="Number of prompts to generate")
    single_parser.add_argument("--output", type=str, required=True, help="Path to save the output JSON")

    # --- multi-level subcommand ---
    multi_parser = subparsers.add_parser("multi-level", help="Run multi-level data structure constraint generation")
    multi_parser.add_argument("--input", type=str, required=True, help="Input JSON file from single-level output")
    multi_parser.add_argument("--output", type=str, required=True, help="Path to save the multi-level output JSON")
    multi_parser.add_argument("--levels", type=int, default=3, help="Number of levels to generate")

    args = parser.parse_args()

    if args.mode == "single-level":
        run_single_level_generation(args.constraint, args.count, args.output)

    elif args.mode == "multi-level":
        generate_data_structure_level_constraints(args.input, args.output, level_num=args.levels)
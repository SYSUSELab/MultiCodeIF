import os
import json
import argparse
from util import extract_code
from data_structure import check_data_structure_type, check_data_structure_operation, check_data_structure_size


def check_data_structure_constraint(code, answer):
    answer = answer.strip(';')
    if answer.count(';') > 1:
        if '[' in answer and ']' in answer:
            return int(check_data_structure_operation(code, answer))
        return int(check_data_structure_size(code, answer))
    return int(check_data_structure_type(code, answer))


def evaluate_prompt(generation_file, prompt_file):
    with open(generation_file, 'r', encoding='utf-8') as f:
        generations = json.load(f)

    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)

    results = {
        f'level{i}': {"total": 0, "matched": 0, "perfect_matches": 0}
        for i in range(6)
    }

    for index, generation in enumerate(generations):
        level = prompts[index]['level']
        if level > 5 or index < level:
            continue

        generated_code = extract_code(generation['response'][0][1])
        matches = [
            check_data_structure_constraint(generated_code, prompts[index - i]['answer'])
            for i in reversed(range(level + 1))
        ]
        results[f'level{level}']["total"] += 1
        results[f'level{level}']["matched"] += sum(matches)
        if all(m == 1 for m in matches):
            results[f'level{level}']["perfect_matches"] += 1

    return results


def print_results(results):
    print("Original metrics:")
    for level in range(6):
        level_key = f'level{level}'
        total = results[level_key]["total"]
        matched = results[level_key]["matched"]
        denom = total * (level + 1)
        acc = matched / denom if denom > 0 else 0
        print(f"{level_key}: {results[level_key]}. {matched} / {denom} = {acc:.3f}")

    print("\nPerfect match metrics (all checks must pass):")
    for level in range(6):
        level_key = f'level{level}'
        total = results[level_key]["total"]
        perfect = results[level_key]["perfect_matches"]
        perfect_acc = perfect / total if total > 0 else 0
        print(f"{level_key}: Perfect matches: {perfect} / {total} = {perfect_acc:.3f}")


def evaluate_multilevel_model(model, output_dir, prompt_dir):
    model_output_dir = os.path.join(output_dir, model)
    output_files = os.listdir(model_output_dir)
    print(f"[INFO] Evaluating {len(output_files)} files for model: {model}")

    model_results = {}

    for output_file in output_files:
        constraint = output_file.split(model)[0].strip('_')
        if not constraint.startswith("data_structure_multilevel"):
            continue

        output_path = os.path.join(model_output_dir, output_file)
        prompt_path = os.path.join(prompt_dir, f"{constraint}.json")

        if not os.path.exists(prompt_path):
            print(f"[WARN] Skipping (prompt not found): {prompt_path}")
            continue

        try:
            results = evaluate_prompt(output_path, prompt_path)
            model_results[constraint] = results
            print(f"[DONE] Evaluated: {constraint}")
        except Exception as e:
            print(f"[ERROR] Failed on {constraint}: {e}")
            continue

    return model_results


def aggregate_multilevel_results(model_results):
    aggregate = {
        f'level{i}': {"total": 0, "matched": 0, "perfect_matches": 0}
        for i in range(6)
    }

    for constraint_result in model_results.values():
        for level in range(6):
            level_key = f'level{level}'
            for metric in ["total", "matched", "perfect_matches"]:
                aggregate[level_key][metric] += constraint_result[level_key][metric]

    return aggregate


def calculate_multilevel_scores(output_dir, prompt_dir, save_path="multilevel_results.json"):
    models = os.listdir(output_dir)
    all_results = {}

    for model in models:
        print(f"\n=== Evaluating multi-level for model: {model} ===")
        model_results = evaluate_multilevel_model(model, output_dir, prompt_dir)
        aggregated = aggregate_multilevel_results(model_results)
        all_results[model] = {
            "per_constraint": model_results,
            "aggregate": aggregated,
        }

    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Multi-level results saved to {save_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save multi-level results: {e}")

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate multi-level data structure constraints across models.")
    parser.add_argument('--output_dir', type=str, required=True, help="Directory with model outputs")
    parser.add_argument('--prompt_dir', type=str, required=True, help="Directory with prompts")
    parser.add_argument('--save_path', type=str, default="multilevel_results.json", help="Path to save results")

    args = parser.parse_args()
    calculate_multilevel_scores(args.output_dir, args.prompt_dir, args.save_path)

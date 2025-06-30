import json
import os
import argparse
from rule_based_eval import rule_based_evaluation
from llm_based_eval import llm_based_evaluation

RULE_BASED_CATEGORIES = ['syntax', 'input_output', 'data_structure', 'code_convention']
LLM_BASED_CATEGORIES = ['situation', 'example', 'code_contextual', 'non_functional_requirements', 'algorithm']


def evaluate_model(model, output_dir, prompt_dir, detail_dir):
    scores = {
        "overall": {"total": 0, "matched": 0, "score": 0.0},
        "categories": {},
    }

    model_output_dir = os.path.join(output_dir, model)
    output_files = os.listdir(model_output_dir)
    print(f"[INFO] Evaluating {len(output_files)} files for model: {model}")

    for output_file in output_files:
        constraint = output_file.split(model)[0].strip('_')
        output_path = os.path.join(model_output_dir, output_file)
        prompt_path = os.path.join(prompt_dir, f"{constraint}.json")
        detail_path = os.path.join(detail_dir, model, f"{constraint}.json")

        if not os.path.exists(prompt_path):
            print(f"[WARN] Skipping (prompt not found): {prompt_path}")
            continue

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                generation = json.load(f)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load data for {output_file}: {e}")
            continue

        category = next((c for c in RULE_BASED_CATEGORIES if output_file.startswith(c)), None)
        if category:
            print(f"[RULE-BASED] {constraint}")
            total, matched = rule_based_evaluation(generation, prompt, detail_path)
        else:
            category = next((c for c in LLM_BASED_CATEGORIES if output_file.startswith(c)), None)
            if category:
                print(f"[LLM-BASED] {constraint}")
                total, matched = llm_based_evaluation(generation, prompt, detail_path)
            else:
                print(f"[SKIP] Unknown category: {constraint}")
                continue

        if total == 0:
            continue

        # Update overall
        scores["overall"]["total"] += total
        scores["overall"]["matched"] += matched

        # Update category
        if category not in scores["categories"]:
            scores["categories"][category] = {"total": 0, "matched": 0, "score": 0.0}
        scores["categories"][category]["total"] += total
        scores["categories"][category]["matched"] += matched

    if scores["overall"]["total"] > 0:
        scores["overall"]["score"] = scores["overall"]["matched"] / scores["overall"]["total"]
    for cat in scores["categories"]:
        cat_data = scores["categories"][cat]
        if cat_data["total"] > 0:
            cat_data["score"] = cat_data["matched"] / cat_data["total"]

    return scores


def calculate_scores(output_dir, prompt_dir, detail_dir, save_path="results.json"):
    print(f"[INFO] Starting evaluation")
    print(f"[DIR] Output: {output_dir}")
    print(f"[DIR] Prompts: {prompt_dir}")
    print(f"[DIR] Details: {detail_dir}")

    models = os.listdir(output_dir)
    result = {}

    for model in models:
        print(f"\n=== Evaluating model: {model} ===")
        result[model] = evaluate_model(model, output_dir, prompt_dir, detail_dir)

    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Results saved to {save_path}")
    except Exception as e:
        print(f"[ERROR] Saving results failed: {e}")
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model outputs.")
    parser.add_argument('--output_dir', type=str, required=True, help="Directory with model outputs")
    parser.add_argument('--prompt_dir', type=str, required=True, help="Directory with original prompts")
    parser.add_argument('--detail_dir', type=str, required=True, help="Directory with detailed results for evaluation")
    parser.add_argument('--save_path', type=str, default="results.json", help="Path to save final results")

    args = parser.parse_args()
    calculate_scores(args.output_dir, args.prompt_dir, args.detail_dir, args.save_path)

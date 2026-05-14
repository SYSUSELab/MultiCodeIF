import json
import os
import argparse
import sys
from ast_test import evaluate_ast


def run_ast_test_for_model(model_name, output_dir, prompt_dir, detail_dir):
    model_output_dir = os.path.join(output_dir, model_name)

    if not os.path.exists(model_output_dir):
        print(f"[ERROR] Model output directory does not exist: {model_output_dir}")
        return None

    output_files = os.listdir(model_output_dir)
    print(f"[INFO] Found {len(output_files)} files for model: {model_name}")

    results = {}
    total_all = 0
    matched_all = 0

    for output_file in output_files:
        filename_no_ext = output_file.replace(".json", "")
        model_pos = filename_no_ext.find(model_name)

        if model_pos == -1:
            print(f"[WARN] Unable to parse filename: {output_file}")
            continue

        constraint = filename_no_ext[:model_pos].rstrip("_")
        if not constraint:
            continue

        output_path = os.path.join(model_output_dir, output_file)
        prompt_path = os.path.join(prompt_dir, f"{constraint}.json")

        if not os.path.exists(prompt_path):
            print(f"[WARN] Prompt file does not exist: {prompt_path}")
            continue

        detail_path = os.path.join(
            detail_dir, model_name, f"{constraint}_ast.json"
        )

        try:
            with open(output_path, "r", encoding="utf-8") as f:
                generation = json.load(f)
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load file: {e}")
            continue

        print(f"[INFO] AST test: {constraint}")
        total, matched = evaluate_ast(generation, prompt, detail_path)

        if total > 0:
            score = matched / total
            results[constraint] = {
                "total": total,
                "matched": matched,
                "score": score
            }
            total_all += total
            matched_all += matched
            print(f"  [Result] {matched}/{total} Passed ({score:.2%})")

    if total_all > 0:
        results["overall"] = {
            "total": total_all,
            "matched": matched_all,
            "score": matched_all / total_all
        }
        print(
            f"\n[Overall] {matched_all}/{total_all} Passed "
            f"({matched_all / total_all:.2%})"
        )

    return results


def run_ast_test(output_dir, prompt_dir, detail_dir, save_path=None, model_name=None):
    print("[INFO] Starting AST verification tests")
    print(f"[DIR] Output directory: {output_dir}")
    print(f"[DIR] Prompt directory: {prompt_dir}")
    print(f"[DIR] Results directory: {detail_dir}")

    if model_name:
        models = [model_name]
    else:
        models = [
            d for d in os.listdir(output_dir)
            if os.path.isdir(os.path.join(output_dir, d))
        ]

    all_results = {}

    for model in models:
        print("\n" + "=" * 60)
        print(f"Testing model: {model}")
        print("=" * 60)
        result = run_ast_test_for_model(
            model, output_dir, prompt_dir, detail_dir
        )
        if result:
            all_results[model] = result

    if save_path:
        os.makedirs(
            os.path.dirname(save_path) if os.path.dirname(save_path) else ".",
            exist_ok=True
        )
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(f"\n[SUCCESS] AST results have been saved to: {save_path}")

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AST verification tests")

    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--prompt_dir", required=True)
    parser.add_argument("--detail_dir", required=True)
    parser.add_argument("--save_path", default=None)
    parser.add_argument("--model", default=None)

    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        print(f"[ERROR] Output directory does not exist: {args.output_dir}")
        sys.exit(1)

    if not os.path.exists(args.prompt_dir):
        print(f"[ERROR] Prompt directory does not exist: {args.prompt_dir}")
        sys.exit(1)

    run_ast_test(
        args.output_dir,
        args.prompt_dir,
        args.detail_dir,
        args.save_path,
        args.model
    )

'''
bash src/scripts/run_ast_test.sh \
  results/single_level \
  dataset/instructions/single_level \
  results/ast_details \
  results/ast_details/ast_results.json
'''

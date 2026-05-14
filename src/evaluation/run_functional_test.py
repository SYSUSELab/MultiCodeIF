import json
import os
import argparse
import sys
from func_test_llm import evaluate_functional


def run_functional_test_for_model(model_name, output_dir, prompt_dir, detail_dir, 
                                  testcase_dir=None, model_name_for_eval="deepseek-v3.2", 
                                  confidence_threshold=0.7):
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
        filename_no_ext = output_file.replace('.json', '')
        
        model_pos = filename_no_ext.find(model_name)
        if model_pos == -1:
            print(f"[WARN] Unable to extract constraint name from filename: {output_file}")
            continue
        
        constraint = filename_no_ext[:model_pos].rstrip('_')
        if not constraint:
            print(f"[WARN] Unable to extract constraint name from filename: {output_file}")
            continue
        
        output_path = os.path.join(model_output_dir, output_file)
        prompt_path = os.path.join(prompt_dir, f"{constraint}.json")
        
        if not os.path.exists(prompt_path):
            print(f"[WARN] Prompt file does not exist: {prompt_path}")
            continue
        
        testcase_data = None
        if testcase_dir:
            testcase_path = os.path.join(testcase_dir, f"{constraint}.json")
            if os.path.exists(testcase_path):
                try:
                    with open(testcase_path, 'r', encoding='utf-8') as f:
                        testcase_data = json.load(f)
                except Exception as e:
                    print(f"[WARN] Failed to load testcase file {testcase_path}: {e}")
                    testcase_data = None
            else:
                print(f"[INFO] Testcase file does not exist (will evaluate using prompt only): {testcase_path}")
        
        detail_path = os.path.join(detail_dir, model_name, f"{constraint}_functional.json")
        
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                generation = json.load(f)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load file {output_file}: {e}")
            continue
        
        if testcase_data is None:
            testcase_data = [{"id": i, "constraint": constraint} for i in range(len(prompt))]
        
        print(f"[INFO] Functional test: {constraint}")
        total, matched = evaluate_functional(
            generation, 
            prompt, 
            testcase_data, 
            detail_path,
            model_name=model_name_for_eval,
            confidence_threshold=confidence_threshold
        )
        
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
        overall_score = matched_all / total_all
        results["overall"] = {
            "total": total_all,
            "matched": matched_all,
            "score": overall_score
        }
        print(f"\n[Overall] {matched_all}/{total_all} Passed ({overall_score:.2%})")
    
    return results


def run_functional_test(output_dir, prompt_dir, detail_dir, testcase_dir=None, 
                       save_path=None, model_name=None, eval_model="deepseek-v3.2",
                       confidence_threshold=0.7):
    print(f"[INFO] Starting functional tests (LLM evaluation mode)")
    print(f"[INFO] Evaluation model: {eval_model}")
    print(f"[INFO] Confidence threshold: {confidence_threshold}")
    print(f"[DIR] Output directory: {output_dir}")
    print(f"[DIR] Prompt directory: {prompt_dir}")
    print(f"[DIR] Detail results directory: {detail_dir}")
    if testcase_dir:
        print(f"[DIR] Testcase directory: {testcase_dir} (will be used to enhance evaluation)")
    else:
        print(f"[INFO] No testcase directory provided, evaluation will be based on prompt only")
    
    if model_name:
        models = [model_name]
    else:
        models = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    
    print(f"[INFO] Will test {len(models)} models: {', '.join(models)}")
    
    all_results = {}
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")
        result = run_functional_test_for_model(
            model, output_dir, prompt_dir, detail_dir, testcase_dir,
            model_name_for_eval=eval_model,
            confidence_threshold=confidence_threshold
        )
        if result:
            all_results[model] = result
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        output_data = {
            "metadata": {
                "eval_model": eval_model,
                "confidence_threshold": confidence_threshold,
                "testcase_provided": testcase_dir is not None
            },
            "results": all_results
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Aggregated results have been saved to: {save_path}")
    
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run code functional tests (using LLM evaluation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

1. Basic usage (no testcases, prompt-based evaluation only):
  python run_functional_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --detail_dir results/functional_details \\
      --save_path results/functional_results.json

2. Enhance evaluation with testcases:
  python run_functional_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --testcase_dir dataset/instructions/testcase \\
      --detail_dir results/functional_details \\
      --save_path results/functional_results.json

3. Specify evaluation model and confidence threshold:
  python run_functional_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --detail_dir results/functional_details \\
      --eval_model gpt-4-turbo \\
      --confidence_threshold 0.8

4. Test a specific model only:
  python run_functional_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --detail_dir results/functional_details \\
      --model deepseek-r1 \\
      --save_path results/functional_deepseek-r1.json
        """
    )
    
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Model output directory (e.g., results/single_level)')
    parser.add_argument('--prompt_dir', type=str, required=True,
                       help='Prompt file directory (e.g., dataset/instructions/single_level)')
    parser.add_argument('--detail_dir', type=str, required=True,
                       help='Detail results output directory')
    
    parser.add_argument('--testcase_dir', type=str, default=None,
                       help='Testcase file directory (optional, enhances LLM evaluation if provided)')
    parser.add_argument('--save_path', type=str, default=None,
                       help='Path to save aggregated results (optional)')
    parser.add_argument('--model', type=str, default=None,
                       help='Model name to test (optional, if specified only this model is tested)')
    parser.add_argument('--eval_model', type=str, default='deepseek-v3.2',
                       help='LLM model used for evaluation (default: gpt-4)')
    parser.add_argument('--confidence_threshold', type=float, default=0.7,
                       help='Confidence threshold, 0.0–1.0 (default: 0.7)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(f"[ERROR] Output directory does not exist: {args.output_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.prompt_dir):
        print(f"[ERROR] Prompt directory does not exist: {args.prompt_dir}")
        sys.exit(1)
    
    if args.testcase_dir and not os.path.exists(args.testcase_dir):
        print(f"[WARN] Testcase directory does not exist: {args.testcase_dir}")
        print(f"[INFO] Will continue execution using prompt-based evaluation only")
        args.testcase_dir = None
    
    if not 0.0 <= args.confidence_threshold <= 1.0:
        print(f"[ERROR] Confidence threshold must be between 0.0 and 1.0, current value: {args.confidence_threshold}")
        sys.exit(1)
    
    run_functional_test(
        args.output_dir,
        args.prompt_dir,
        args.detail_dir,
        args.testcase_dir,
        args.save_path,
        args.model,
        args.eval_model,
        args.confidence_threshold
    )

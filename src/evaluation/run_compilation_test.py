import json
import os
import argparse
import sys
from compile_test import evaluate_compilation


def run_compilation_test_for_model(model_name, output_dir, prompt_dir, detail_dir):
    model_output_dir = os.path.join(output_dir, model_name)
    
    if not os.path.exists(model_output_dir):
        print(f"[ERROR] Model output directory does not exist: {model_output_dir}")
        return None
    
    output_files = os.listdir(model_output_dir)
    print(f"[INFO] Find {len(output_files)} files for the model: {model_name}")
    
    results = {}
    total_all = 0
    matched_all = 0
    
    for output_file in output_files:
        filename_no_ext = output_file.replace('.json', '')
        
        model_pos = filename_no_ext.find(model_name)
        if model_pos == -1:
            model_prefix = model_name.split('-')[0]
            model_pos = filename_no_ext.find(model_prefix + '-')
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
            possible_names = [
                f"{constraint}.json",
                f"{constraint.replace('_', '-')}.json",
            ]
            found = False
            for name in possible_names:
                test_path = os.path.join(prompt_dir, name)
                if os.path.exists(test_path):
                    prompt_path = test_path
                    found = True
                    break
            if not found:
                print(f"[WARN] The Prompt file does not exist.: {prompt_path}")
                continue
        
        detail_path = os.path.join(detail_dir, model_name, f"{constraint}_compilation.json")
        
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                generation = json.load(f)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = json.load(f)
        except Exception as e:
            print(f"[ERROR] File loading failed {output_file}: {e}")
            continue
        
        print(f"[INFO] Testing: {constraint}")
        total, matched = evaluate_compilation(generation, prompt, detail_path)
        
        if total > 0:
            score = matched / total
            results[constraint] = {
                "total": total,
                "matched": matched,
                "score": score
            }
            total_all += total
            matched_all += matched
            print(f"  [Results] {matched}/{total} Passed ({score:.2%})")
    
    if total_all > 0:
        overall_score = matched_all / total_all
        results["overall"] = {
            "total": total_all,
            "matched": matched_all,
            "score": overall_score
        }
        print(f"\n[Total] {matched_all}/{total_all} Passed ({overall_score:.2%})")
    
    return results


def run_compilation_test(output_dir, prompt_dir, detail_dir, save_path=None, model_name=None):
    print(f"[INFO] Starting compilation tests")
    print(f"[DIR] Output directory: {output_dir}")
    print(f"[DIR] Prompt directory: {prompt_dir}")
    print(f"[DIR] Detail results directory: {detail_dir}")
    
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
        result = run_compilation_test_for_model(model, output_dir, prompt_dir, detail_dir)
        if result:
            all_results[model] = result
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Aggregated results have been saved to: {save_path}")
    
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run code compilation tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Test all models
  python src/evaluation/run_compilation_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --detail_dir results/compilation_details \\
      --save_path results/compilation_results.json
  
  # Test a specific model only
  python src/evaluation/run_compilation_test.py \\
      --output_dir results/single_level \\
      --prompt_dir dataset/instructions/single_level \\
      --detail_dir results/compilation_details \\
      --model deepseek-r1 \\
      --save_path results/compilation_deepseek-r1.json
        """
    )
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Model output directory (e.g.: results/single_level)')
    parser.add_argument('--prompt_dir', type=str, required=True,
                       help='Prompt file directory (e.g.: dataset/instructions/single_level)')
    parser.add_argument('--detail_dir', type=str, required=True,
                       help='Detailed results output directory')
    parser.add_argument('--save_path', type=str, default=None,
                       help='Aggregated results save path (optional)')
    parser.add_argument('--model', type=str, default=None,
                       help='Specify the model name to test (optional, if specified only this model will be tested)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(f"[ERROR] Output directory does not exist: {args.output_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.prompt_dir):
        print(f"[ERROR] Prompt directory does not exist: {args.prompt_dir}")
        sys.exit(1)
    
    run_compilation_test(
        args.output_dir,
        args.prompt_dir,
        args.detail_dir,
        args.save_path,
        args.model
    )

'''
bash src/scripts/run_compilation_test.sh \
  results/single_level \
  dataset/instructions/single_level \
  results/compilation_details \
  results/compilation_details/compilation_results.json
'''

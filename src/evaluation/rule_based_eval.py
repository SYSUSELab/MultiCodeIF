import os
import json
from syntax import evaluate_syntax
from code_convention import evaluate_code_convention
from input_output import evaluate_input_output
from data_structure import evaluate_data_structure
from llm_based_eval import check_declaration_style_by_llm, check_framework_by_llm, check_input_range_by_llm, check_output_range_by_llm
from util import extract_code

constraint_category = ['syntax', 'input_output', 'data_structure', 'code_convention']

def rule_based_evaluation(generation, prompt, output_path="evaluation_results.json"):
    total = 0
    matched = 0
    results = []

    for index, response in enumerate(generation):
        if  prompt[index]['category'] in constraint_category:
            total += 1
            generated_code = extract_code(response['response'][0][1])

            if prompt[index]['constraint'] in ['declaration_style', 'framework', 'input_range', 'output_range']:
                is_matched = globals()[f"check_{prompt[index]['constraint']}_by_llm"](
                    generated_code,
                    prompt[index]['prompt'],
                    prompt[index]['answer']
                )
            else:
                is_matched = globals()[f"evaluate_{prompt[index]['category']}"](
                    generated_code,
                    prompt[index]['answer'],
                    prompt[index]['constraint']
                )
            
            if is_matched:
                matched += 1
            
            result_entry = {
                "id": index,
                "category": prompt[index]['category'],
                "constraint": prompt[index]['constraint'],
                "prompt": prompt[index]['prompt'],
                "answer": prompt[index]['answer'],
                "generated_code": generated_code,
                "is_matched": is_matched
            }
            results.append(result_entry)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return total, matched

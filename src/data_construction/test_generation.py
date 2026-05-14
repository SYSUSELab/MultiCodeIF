import json
from typing import List, Dict, Any

from generation import generation_in_parallel
import re

def clean_json_response(raw_text: str) -> str:
    text = raw_text.strip()
    
    pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.match(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return text

def build_test_generation_prompt(problem_prompt: str, answer: str, case_num: int = 10) -> str:
    """
    Build a prompt for generating functional test cases using an LLM.

    Conventions:
    - Input consists of a single programming problem's natural language description (`prompt`)
      and its expected function/interface specification (`answer`).
    - The `answer` field is recommended to be written in a form like:
      python;two_sum(nums: List[int], target: int) -> List[int]
    - Output must be in strict JSON format, containing only the `tests` field.
    """
    return f"""You are a senior software test engineer, highly experienced in designing high-quality,
executable functional test cases for programming problems.

Below is a programming problem and its expected function/interface specification:

<problem_prompt>
{problem_prompt}
</problem_prompt>

<answer_spec>
{answer}
</answer_spec>

Please design at least {case_num} test cases for this problem, covering:
- Basic normal cases
- Multiple edge cases
- Typical erroneous or extreme inputs (if allowed by the problem)

You must output **strict JSON only**, without any additional comments or natural language
explanations. The format must be exactly as follows:

{{
  "tests": [
    {{
      "name": "Short description of the test case (Chinese or English is acceptable)",
      "input": {{
        "args": [... list all positional arguments in call order ...],
        "kwargs": {{ "named_argument": value }}
      }},
      "expected_output": any value representable in JSON
    }}
  ]
}}

Requirements:
- If the function has multiple parameters, list all of them in `args` in the correct
  calling order. Use `kwargs` only when named arguments are truly necessary.
- `expected_output` must match the problem semantics and be consistent with the return
  value specification in `answer`.
- Do not generate any code. Only generate the JSON described above.
""".strip()


def generate_tests_for_dataset(
    data: List[Dict[str, Any]],
    case_num: int = 10,
    model_name: str = "",
) -> List[Dict[str, Any]]:
    prompts = [
        build_test_generation_prompt(item.get("prompt", ""), item.get("answer", ""), case_num)
        for item in data
    ]

    responses = generation_in_parallel(prompts, model_name)

    new_data: List[Dict[str, Any]] = []
    for item, resp in zip(data, responses):
        raw_text = resp[1]
        # print(raw_text)
        tests: List[Dict[str, Any]] = []
        try:
            cleaned_text = clean_json_response(raw_text)
            payload = json.loads(cleaned_text)
            if isinstance(payload, dict) and isinstance(payload.get("tests"), list):
                tests = payload["tests"]
        except Exception as e:
            print(f"Failed to parse response: {e}")
            tests = []

        new_item = dict(item)
        new_item["tests"] = tests
        new_data.append(new_item)

    return new_data


def run_generate_tests_for_file(
    input_file: str,
    output_file: str,
    case_num: int = 10,
    model_name: str = "",
) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = generate_tests_for_dataset(data, case_num=case_num, model_name=model_name)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

    print(f"[FUNC-TEST][DATA] Success generate tests for {len(new_data)} items → {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate functional test cases for existing prompt dataset.")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file (existing prompts with answers)")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file with tests field")
    parser.add_argument("--cases", type=int, default=10, help="Expected minimum test cases per problem")
    parser.add_argument("--model", type=str, default="", help="Model name for test generation")

    args = parser.parse_args()

    run_generate_tests_for_file(
        input_file=args.input,
        output_file=args.output,
        case_num=args.cases,
        model_name=args.model,
    )

'''
python test_generation.py \
  --input ../../dataset/instructions/single_level/algorithm_space_complexity.json \
  --output ../../dataset/instructions/testcase/algorithm_space_complexity.json \
  --cases 1 \
  --model claude-haiku-4-5-20251001
'''

'''
bash src/scripts/run_test_generation.sh \
    dataset/instructions/single_level \
    dataset/instructions/testcase \
    1 \
    claude-haiku-4-5-20251001
'''
import os
import json
from generation import generation_in_parallel
from util import extract_code


def create_evaluation_prompt(prompt_text, generated_code, language, function_name=None, testcase_data=None):
    """
    Create an evaluation prompt for LLM to judge if the generated code meets requirements
    
    :param prompt_text: str, original prompt/requirement
    :param generated_code: str, generated code to evaluate
    :param language: str, programming language
    :param function_name: str, function name (optional)
    :param testcase_data: dict, test case information (optional)
    :return: str, evaluation prompt in English
    """
    
    # Build test case information if available
    test_info = ""
    if testcase_data and 'tests' in testcase_data:
        tests = testcase_data['tests']
        if tests:
            test_info = "\n\n**Test Cases:**\n"
            for i, test in enumerate(tests[:5]):  # Limit to 5 examples
                test_input = test.get('input', {})
                expected_output = test.get('expected_output', 'N/A')
                test_name = test.get('name', f'Test {i+1}')
                
                args = test_input.get('args', [])
                kwargs = test_input.get('kwargs', {})
                
                test_info += f"- {test_name}:\n"
                test_info += f"  Input: args={args}, kwargs={kwargs}\n"
                test_info += f"  Expected Output: {expected_output}\n"
    
    function_info = f" The main function should be named `{function_name}`." if function_name else ""
    
    prompt = f"""You are a code evaluation expert. Your task is to determine whether the generated code meets the specified requirements.

**Programming Language:** {language}

**Requirements:**
{prompt_text}
{function_info}

**Generated Code:**
```{language}
{generated_code}
```
{test_info}

**Evaluation Instructions:**
1. Carefully read the requirements and understand what functionality is needed
2. Analyze the generated code to check if it implements the required functionality
3. Consider the following aspects:
   - Does the code address the main requirements?
   - Is the logic correct and complete?
   - Does the function signature match expectations (if specified)?
   - Would the code produce correct outputs for the given test cases (if provided)?
   - Are there any obvious bugs or logical errors?

4. Provide your evaluation in the following JSON format ONLY (no other text):

{{
  "meets_requirements": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your judgment",
  "issues": ["list", "of", "issues", "if", "any"]
}}

**Important:** 
- Respond ONLY with the JSON object, nothing else
- Set "meets_requirements" to true only if the code correctly implements the required functionality
- Set "confidence" between 0.0 and 1.0 based on how certain you are
- Be objective and thorough in your evaluation"""

    return prompt


def evaluate_with_llm(prompt_text, generated_code, language, function_name=None, 
                     testcase_data=None, model_name="deepseek-v3.2"):
    """
    Use LLM to evaluate if the generated code meets requirements
    
    :param prompt_text: str, original prompt/requirement
    :param generated_code: str, generated code to evaluate
    :param language: str, programming language
    :param function_name: str, function name (optional)
    :param testcase_data: dict, test case information (optional)
    :param model_name: str, LLM model name to use for evaluation
    :return: dict, evaluation result
    """
    
    # Create evaluation prompt
    eval_prompt = create_evaluation_prompt(
        prompt_text, generated_code, language, function_name, testcase_data
    )
    
    try:
        # Get LLM evaluation
        results = generation_in_parallel([eval_prompt], model_name)
        
        if not results or not results[0]:
            return {
                "meets_requirements": False,
                "confidence": 0.0,
                "reasoning": "Failed to get LLM evaluation response",
                "issues": ["No response from LLM"],
                "error": "Empty response"
            }
        
        _, llm_response = results[0]
        
        # Handle error responses
        if isinstance(llm_response, str) and "exception" in llm_response.lower():
            return {
                "meets_requirements": False,
                "confidence": 0.0,
                "reasoning": "LLM evaluation failed",
                "issues": ["LLM API error"],
                "error": llm_response
            }
        
        # Parse LLM response
        try:
            # Try to extract JSON from the response
            response_text = llm_response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            
            # Find JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                evaluation = json.loads(json_text)
                
                # Validate required fields
                if "meets_requirements" not in evaluation:
                    evaluation["meets_requirements"] = False
                if "confidence" not in evaluation:
                    evaluation["confidence"] = 0.5
                if "reasoning" not in evaluation:
                    evaluation["reasoning"] = "No reasoning provided"
                if "issues" not in evaluation:
                    evaluation["issues"] = []
                
                return evaluation
            else:
                # JSON not found, try to parse the whole response
                evaluation = json.loads(response_text)
                return evaluation
                
        except json.JSONDecodeError as e:
            return {
                "meets_requirements": False,
                "confidence": 0.0,
                "reasoning": f"Failed to parse LLM response as JSON: {str(e)}",
                "issues": ["Invalid JSON response"],
                "error": f"JSON parse error: {str(e)}",
                "raw_response": llm_response[:500]  # Include first 500 chars for debugging
            }
            
    except Exception as e:
        return {
            "meets_requirements": False,
            "confidence": 0.0,
            "reasoning": f"Evaluation error: {str(e)}",
            "issues": ["Exception during evaluation"],
            "error": str(e)
        }


def evaluate_functional(generation, prompt, testcase_data, output_path="functional_results.json", 
                       model_name="deepseek-v3.2", confidence_threshold=0.7):
    """
    Functional testing evaluation using LLM as judge
    
    :param generation: list, list of generated code responses
    :param prompt: list, list of prompts
    :param testcase_data: list, list of test case data
    :param output_path: str, output result save path
    :param model_name: str, LLM model name for evaluation
    :param confidence_threshold: float, minimum confidence threshold to consider as passed
    :return: tuple (int, int) - (total count, passed count)
    """
    total = 0
    matched = 0
    results = []
    
    print(f"[INFO] Starting LLM-based functional evaluation using model: {model_name}")
    print(f"[INFO] Confidence threshold: {confidence_threshold}")
    
    for index, response in enumerate(generation):
        if index >= len(prompt) or index >= len(testcase_data):
            continue
        
        total += 1
        
        # Extract generated code
        generated_code = extract_code(response['response'][0][1])
        
        # Get prompt text
        prompt_text = prompt[index].get('prompt', '')
        
        # Get language and function name from answer field (format: language;function_name;...)
        language = None
        function_name = None
        if 'answer' in prompt[index]:
            answer = prompt[index]['answer']
            parts = answer.split(';')
            if len(parts) >= 2:
                language = parts[0].strip()
                function_name = parts[1].strip()
            elif len(parts) == 1:
                language = parts[0].strip()
        
        # Default to Python if language not specified
        if not language:
            language = "Python"
        
        print(f"[INFO] Evaluating {index+1}/{len(generation)}: {testcase_data[index].get('constraint', 'Unknown')} ({language})")
        
        # Get test case data
        current_testcase = testcase_data[index] if index < len(testcase_data) else {}
        
        # Evaluate with LLM
        evaluation = evaluate_with_llm(
            prompt_text=prompt_text,
            generated_code=generated_code,
            language=language,
            function_name=function_name,
            testcase_data=current_testcase,
            model_name=model_name
        )
        
        # Determine if passed based on LLM evaluation and confidence threshold
        is_passed = (
            evaluation.get("meets_requirements", False) and 
            evaluation.get("confidence", 0.0) >= confidence_threshold
        )
        
        if is_passed:
            matched += 1
            print(f"  ✓ PASSED (confidence: {evaluation.get('confidence', 0.0):.2f})")
        else:
            print(f"  ✗ FAILED (confidence: {evaluation.get('confidence', 0.0):.2f})")
            if evaluation.get("reasoning"):
                print(f"    Reason: {evaluation['reasoning'][:100]}")
        
        # Build result entry
        result_entry = {
            "id": testcase_data[index].get('id', index),
            "category": testcase_data[index].get('category', ''),
            "constraint": testcase_data[index].get('constraint', ''),
            "prompt": prompt_text,
            "answer": testcase_data[index].get('answer', ''),
            "language": language,
            "function_name": function_name,
            "generated_code": generated_code,
            "is_matched": is_passed,
            "llm_evaluation": evaluation,
            "meets_requirements": evaluation.get("meets_requirements", False),
            "confidence": evaluation.get("confidence", 0.0),
            "reasoning": evaluation.get("reasoning", ""),
            "issues": evaluation.get("issues", [])
        }
        
        # Include error information if present
        if "error" in evaluation:
            result_entry["evaluation_error"] = evaluation["error"]
        if "raw_response" in evaluation:
            result_entry["raw_llm_response"] = evaluation["raw_response"]
        
        results.append(result_entry)
    
    # Save detailed results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create summary statistics
    summary = {
        "total": total,
        "matched": matched,
        "pass_rate": matched / total if total > 0 else 0.0,
        "model_name": model_name,
        "confidence_threshold": confidence_threshold,
        "average_confidence": sum(r.get("confidence", 0.0) for r in results) / len(results) if results else 0.0
    }
    
    output_data = {
        "summary": summary,
        "results": results
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Evaluation complete: {matched}/{total} passed ({matched/total*100:.1f}%)")
    print(f"[INFO] Detailed results saved to: {output_path}")
    
    return total, matched


def batch_evaluate_with_retry(prompts_list, model_name="deepseek-v3.2", max_retries=3):
    """
    Batch evaluate with retry mechanism for failed requests
    
    :param prompts_list: list, list of evaluation prompts
    :param model_name: str, LLM model name
    :param max_retries: int, maximum retry attempts
    :return: list, evaluation results
    """
    results = [None] * len(prompts_list)
    failed_indices = list(range(len(prompts_list)))
    
    for attempt in range(max_retries):
        if not failed_indices:
            break
            
        print(f"[INFO] Batch evaluation attempt {attempt + 1}/{max_retries}, {len(failed_indices)} items")
        
        # Prepare prompts for failed indices
        batch_prompts = [prompts_list[i] for i in failed_indices]
        
        # Get batch results
        batch_results = generation_in_parallel(batch_prompts, model_name)
        
        # Update results and track new failures
        new_failed_indices = []
        for i, (original_idx, (_, response)) in enumerate(zip(failed_indices, batch_results)):
            if response and not isinstance(response, str) or "exception" not in response.lower():
                results[original_idx] = response
            else:
                new_failed_indices.append(original_idx)
        
        failed_indices = new_failed_indices
    
    # Fill remaining failures with error messages
    for idx in failed_indices:
        results[idx] = "Failed after maximum retries"
    
    return results

import logging
import json
from datetime import datetime
from util import extract_code
from generation import generation_in_parallel


logging.basicConfig(
    filename=f'generation_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
BASE_MODEL = 'gpt-4o'
constraint_category = ['situation', 'example', 'code_contextual', 'non_functional_requirements', 'algorithm']


def log_generation_result(prompt, response, context=None):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'prompt': prompt,
        'response': response,
        'context': context
    }
    
    # Check for error response
    if isinstance(response, str) and response.startswith("Request generated an exception"):
        logger.error(str(log_entry))
    else:
        logger.info(str(log_entry))


def llm_based_evaluation(generation, prompt, output_path="evaluation_results.json"):
    total = 0
    matched = 0
    results = []

    for index, response in enumerate(generation):
        if prompt[index]['category'] in constraint_category:
            total += 1
            generated_code = extract_code(response['response'][0][1])
            if prompt[index]['category'] == 'algorithm':
                evaluation_prompt = generate_algorithm_evaluation_prompt(
                    prompt[index]['constraint'],
                    prompt[index]['prompt'],
                    generated_code,
                    prompt[index]['answer']
                )
            else:
                evaluation_prompt = genearte_evaluation_prompt(
                    prompt[index]['category'],
                    prompt[index]['prompt'],
                    prompt[index]['answer'],
                    generated_code
                )

            result = generation_in_parallel(evaluation_prompt, BASE_MODEL)
            log_generation_result(evaluation_prompt, result[0][1], {
                'category': prompt[index]['category'], 
                'constraint': prompt[index].get('constraint', prompt[index]['category']), 
                'index': index
            })

            if 'yes' in result[0][1].lower():
                matched += 1
            
            result_entry = {
                "id": index,
                "category": prompt[index]['category'],
                "constraint": prompt[index].get('constraint', prompt[index]['category']),
                "prompt": prompt[index]['prompt'],
                "answer": prompt[index]['answer'],
                "generated_code": generated_code,
                "is_matched": 'yes' in result[0][1].lower()
            }
            results.append(result_entry)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return total, matched


situation_prompt = '''Situation constraints refer to the restrictions imposed on the goals, methods, or results of tasks from real-world development or learning scenarios when constructing code generation tasks.
These scenarios can include: specific stages of software development, programming ability levels, usage purposes, application fields, or job roles, etc.'''

example_prompt = '''Example constraints refer to implicit or explicit constraints on the structure, style, calling method or implementation strategy of the generated code by providing one or more example code snippets in the code generation task.
The generated model should maintain consistency or make analogical extensions in terms of style, structure, interface, etc. based on these examples.'''

code_contextual_prompt = '''Code context constraints mean that in the code generation task, a piece of existing code (which may be partial code, framework, interface definition, etc.) is provided, and the generated code must be developed or modified based on this existing code.'''

non_functional_requirements_prompt = '''Non-functional requirement constraints refer to limitations or expectations placed on the generated code that ensure it aligns with specific non-functional attributes of software systems. These constraints do not dictate what the code must do, but rather how the resulting system should behave or operate in terms of quality and performance. In the context of code generation tasks, such constraints guide the model to produce code that upholds standards related to performance, usability, scalability, reliability, and other system qualities.'''

base_prompt = '''You are an expert code reviewer. Evaluate whether the following code satisfies the given constraint by comparing it with a reference implementation.

Code Generation Task:
{task}

Constraint:
{constraint}

Reference Implementation:
{reference}

Generated Implementation:
{generated}

Please answer with one of the following:
- YES: if the generated code satisfies the constraint and is functionally similar or equivalent to the reference implementation.
- NO: if the generated code clearly violates the constraint or behaves differently.

Output ONLY YES or NO, no additional information.'''


def genearte_evaluation_prompt(constraint, task, reference, generated):
    if constraint == 'situation':
        return base_prompt.format(task=task, constraint=situation_prompt, reference=reference, generated=generated)
    elif constraint == 'example':
        return base_prompt.format(task=task, constraint=example_prompt, reference=reference, generated=generated)
    elif constraint == 'code_contextual':
        return base_prompt.format(task=task, constraint=code_contextual_prompt, reference=reference, generated=generated)
    elif constraint == 'non_functional_requirements':
        return base_prompt.format(task=task, constraint=non_functional_requirements_prompt, reference=reference, generated=generated)


def generate_algorithm_evaluation_prompt(constraint, task, generated, answer):
    constraint_map = {
        "type": "The implementation must use the specified **algorithm type**, such as dynamic programming, greedy algorithm, divide and conquer, backtracking, or binary search. Any violation or use of a different algorithm paradigm is unacceptable.",
        "time_complexity": "The implementation must meet the required **time complexity**. Do not use approaches that exceed this complexity class. The Big O notation is used here to represent the complexity of the algorithm.",
        "space_complexity": "The implementation must meet the required **space complexity**. Avoid extra memory usage that violates the constraint. The Big O notation is used here to represent the complexity of the algorithm."
    }

    prompt = "You are an expert code reviewer. Please evaluate whether the following code strictly satisfies the given constraint.\nYou will be given a code generation task, a generated implementation, and a constraint description.\nYour job is to assess whether the generated implementation satisfies the constraint.\n\n"
    prompt += f"Constraint Type: {constraint}\n"
    prompt += f"Constraint Description:\n{constraint_map[constraint]}\n\n"
    prompt += f"Code Generation Task:\n{task}\n\n"
    prompt += f"Generated Implementation:\n{generated}\n\n"
    prompt += f"Expected Answer Based on Constraint: {answer}\n\n"
    prompt += '''Please answer with one of the following:
- YES: if the generated code satisfies the constraint answer given above.
- NO: if the generated code clearly violates the constraint.

Output ONLY YES or NO, no additional information.'''
    return prompt


def check_declaration_style_by_llm(generated, task, answer):
    lang, des = answer.split(';', maxsplit=1)
    prompt = f"You are a code style expert. Determine whether the following generated code follows the declaration style convention described below.\n\n"
    prompt += f"Code Generation Task: {task}\n\n"
    prompt += f"Declaration Style Constraint:\n- The generated code must use {lang} programming language.\n{des}\n\n"
    prompt += f"Generated Code:\n{generated}\n\n"
    prompt += '''Please answer with one of the following:
- YES — if the generated code follows the described declaration style convention.
- NO — if the generated code violates or ignores the convention.

Output ONLY YES or NO, no additional information.'''

    result = generation_in_parallel(prompt, BASE_MODEL)
    log_generation_result(prompt, result[0][1], {'function': 'check_declaration_style_by_llm', 'answer': answer})
    return 'yes' in result[0][1].lower()


def check_framework_by_llm(generated, task, answer):
    lang, framework, features = answer.split(';', maxsplit=2)
    prompt = f"You are a programming framework expert. Determine whether the following generated code uses the specified framework and aligns with its characteristics.\n\n"
    prompt += f"Code Generation Task: {task}\n\n"
    prompt += f"Framework Constraint:\n- The generated code must use the {framework} framework in the {lang} programming language.\n"
    prompt += f"- Framework Features: {features.strip()}\n\n"
    prompt += f"Generated Code:\n{generated}\n\n"
    prompt += '''Please answer with one of the following:
- YES — if the generated code uses the specified framework and reflects its core features or idioms.
- NO — if the generated code does not use the framework or ignores its relevant characteristics.

Output ONLY YES or NO, no additional information.'''

    result = generation_in_parallel(prompt, BASE_MODEL)
    log_generation_result(prompt, result[0][1], {'function': 'check_framework_by_llm', 'answer': answer})
    return 'yes' in result[0][1].lower()


def check_input_range_by_llm(generated, task, answer):
    lang, func_name, input_type, input_range = answer.split(';', maxsplit=3)

    prompt = f"You are a code correctness expert. Determine whether the following generated code satisfies the specified input value range constraints.\n\n"
    prompt += f"Code Generation Task: {task}\n\n"
    prompt += f"Input Range Constraint:\n"
    prompt += f"- Language: {lang}\n"
    prompt += f"- Function Name: {func_name}\n"
    prompt += f"- Input/Parameter Type: {input_type}\n"
    prompt += f"- Expected Input/Parameter Range: {input_range.strip()}\n\n"
    prompt += f"Generated Code:\n{generated}\n\n"
    prompt += '''Please answer with one of the following:
- YES — if the generated code handles the input values according to the expected input type and range.
- NO — if the generated code ignores, violates, or fails to fully enforce the input constraints.

Output ONLY YES or NO, no additional information.'''

    result = generation_in_parallel(prompt, BASE_MODEL)
    log_generation_result(prompt, result[0][1], {'function': 'check_input_range_by_llm', 'answer': answer})
    return 'yes' in result[0][1].lower()


def check_output_range_by_llm(generated, task, answer):
    lang, output_type, output_range = answer.split(';', maxsplit=2)

    prompt = f"You are a programming output validation expert. Determine whether the following generated code satisfies the output range and formatting constraints.\n\n"
    prompt += f"Code Generation Task: {task}\n\n"
    prompt += f"Output Range Constraint:\n"
    prompt += f"- Language: {lang}\n"
    prompt += f"- Output/Return Type: {output_type}\n"
    prompt += f"- Expected Output/Return Range or Format: {output_range.strip()}\n\n"
    prompt += f"Generated Code:\n{generated}\n\n"
    prompt += '''Please answer with one of the following:
- YES — if the generated code returns values that match the expected output format, structure, and range.
- NO — if the generated code violates or fails to enforce the output range or format constraints.

Output ONLY YES or NO, no additional information.'''

    result = generation_in_parallel(prompt, BASE_MODEL)
    log_generation_result(prompt, result[0][1], {'function': 'check_output_range_by_llm', 'answer': answer})
    return 'yes' in result[0][1].lower()

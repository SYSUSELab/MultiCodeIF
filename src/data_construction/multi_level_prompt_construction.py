import json

base_prompt_template = '''You are an expert in code task generation, capable of evolving existing tasks by incorporating additional constraints.
You will receive the following input content:

- **Natural language description of the code requirements with raw constraints** `<base_prompt>` .
- **Keywords to validate requirement fulfillment** `<base_answer>` .
- **Test script for validating code constraints** `<constraint_validation_script>` used to evaluate whether the generated code from large models satisfies the constraints in `<base_answer>`
- **Range of constraint type values** `<constraints_pool>` containing all optional constraint types


Your goal is to produce new code generation tasks by incorporating additional constraints among the optional constraints given to you. Key considerations:

1. Rewrite <base_prompt> into a new `<new_prompt>` that incorporates both the original and new constraints.
2. Generate a new `<new_answer>` that only includes your new constraints by reference to all <constraint_validation_script> given to you.
3. Generated new `<new_prompt>` tasks must be grounded in real development/production environments, ensuring diversity and avoiding duplication with existing examples. Tasks must not be overly simplistic.
4. Please add ONLY one appropriate constraint that is not reflected in <base_prompt> and exists in <constraints_pool>.

Output ONLY `<new_prompt>` and `<new_answer>`, no additional information.

<base_prompt>
{base_prompt}
</base_prompt>

<base_answer>
{base_answer}
</base_answer>

<constraint_validation_script>
{constraint_validation_script}
</constraint_validation_script>  

<constraints_pool>
{constraints_pool}
</constraints_pool>

<new_prompt></new_prompt>

<new_answer></new_answer>'''

data_structure_valid_script = '''def check_data_structure_type(generation, answer):
    """
    Determines whether the generated code uses the correct data structure type.

    Args:
        generation (str): The code generation to be evaluated.
        answer (str): A semicolon-separated string containing the target language and expected data structure type 
                      (e.g., "Python;list").

    Returns:
        bool: True if the code uses the expected data structure type, False otherwise.
    """
    language, typ = answer.split(';')
    return globals()[f"check_{language.lower()}_data_structure"](remove_comments(generation, language), typ)

def check_data_structure_size(generation, answer):
    """
    Determines whether the generated code uses a data structure of the correct type and size.

    Args:
        generation (str): The code generation to be evaluated.
        answer (str): A semicolon-separated string containing the target language, expected data structure type,
                      and the required size (e.g., "Python;list;3").

    Returns:
        bool: True if the data structure is of the correct type and size, False otherwise.
    """
    language, typ, size_str = answer.split(';')
    size = int(size_str)
    return globals()[f"check_{language.lower()}_data_structure_size"](remove_comments(generation, language), typ, size)

def check_data_structure_operation(generation, answer):
    """
    Determines whether the generated code performs specific operations on the correct type of data structure.

    Args:
        generation (str): The code generation to be evaluated.
        answer (str): A semicolon-separated string containing the target language, expected data structure type,
                      and a stringified list of operations to be validated 
                      (e.g., "Python;list;['append', 'pop']").

    Returns:
        bool: True if the code performs all specified operations on the correct data structure, False otherwise.
    """
    language, typ, op_list_str = answer.split(';')
    op_list = ast.literal_eval(op_list_str)
    return globals()[f"check_{language.lower()}_data_structure_operation"](remove_comments(generation, language), typ, op_list)
'''

data_structure_requirement = """1. Data Structure Type: Specifies or Adds the required data structure, such as a list, vector, stack.
2. Data Structure Operations: Restricts or Adds the operations that can be performed on a data structure, such as push() or pop() in stack.
3. Data Structure Size: Restricts the size, like maximum elements in an array."""


def data_structure_constraints_prompts(base_prompt, base_answer):
    prompt = base_prompt_template.format(
        base_prompt=base_prompt,
        base_answer=base_answer,
        constraint_validation_script=data_structure_valid_script,
        constraints_pool=data_structure_requirement
    )
    return prompt

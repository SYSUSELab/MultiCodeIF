import json
import random
from typing import List, Dict, Type


class UniformSelector:
    def __init__(self, items: List):
        self.items = items
        self.shuffled = []
        self.index = 0

    def select(self):
        if self.index >= len(self.shuffled):
            # Reshuffle and reset index
            self.shuffled = random.sample(self.items, len(self.items))
            self.index = 0
        selected = self.shuffled[self.index]
        self.index += 1
        return selected
    

class Constraint:
    def generate(self) -> str:
        raise NotImplementedError


constraint_reg: Dict[str, Type[Constraint]] = {}


def register_constraint(name):
    def decorator(cls: Type[Constraint]):
        constraint_reg[name] = cls
        return cls
    return decorator


def get_constraint(name) -> Constraint:
    if name not in constraint_reg:
        raise ValueError(f"Unknown constraint: {name}")
    return constraint_reg[name]()


algorithm_lists = []
with open("dataset/seeds/algorithm_type.json", 'r', encoding='utf-8') as f:
    algorithm_lists = json.load(f)
language_lists = ['cpp', 'rust', 'java', 'python']
framework_lists = []
with open("dataset/seeds/framework.json", "r", encoding="utf-8") as f:
    framework_lists = json.load(f)
function_lists = []
with open("dataset/seeds/function.json", 'r', encoding='utf-8') as f:
    function_lists = json.load(f)
library_lists = []
with open("dataset/seeds/library.json", 'r', encoding='utf-8') as f:
    library_lists = json.load(f)
advanced_syntax_lists = []
with open("dataset/seeds/advanced_syntax.json", 'r', encoding='utf-8') as f:
    advanced_syntax_lists = json.load(f)
brace_block_formatting_lists = []
with open("dataset/seeds/brace_block_formatting.json", 'r', encoding='utf-8') as f:
    advanced_syntax_lists = json.load(f)
data_structure_type_lists = []
with open("dataset/seeds/data_structure_type.json", 'r', encoding='utf-8') as f:
    data_structure_type_lists = json.load(f)
output_type_lists = []
with open("dataset/seeds/output_type.json", 'r', encoding='utf-8') as f:
    output_type_lists = json.load(f)
input_type_lists = []
with open("dataset/seeds/input_type.json", 'r', encoding='utf-8') as f:
    input_type_lists = json.load(f)
indentation_spacing_lists = []
with open("dataset/seeds/indentation_spacing.json", 'r', encoding='utf-8') as f:
    indentation_spacing_lists = json.load(f)
comment_formatting_lists = []
with open("dataset/seeds/comment_formatting.json", 'r', encoding='utf-8') as f:
    comment_formatting_lists = json.load(f)
data_structure_size_lists = []
with open("dataset/seeds/data_structure_size.json", 'r', encoding='utf-8') as f:
    data_structure_size_lists = json.load(f)
data_structure_operation_lists = []
with open("dataset/seeds/data_structure_operation.json", 'r', encoding='utf-8') as f:
    data_structure_operation_lists = json.load(f)
output_range_lists = []
with open("dataset/seeds/output_range.json", 'r', encoding='utf-8') as f:
    output_range_lists = json.load(f)
input_range_lists = []
with open("dodataset/seeds/input_range.json", 'r', encoding='utf-8') as f:
    input_range_lists = json.load(f)
input_order_lists = []
with open("dataset/seeds/input_order.json", 'r', encoding='utf-8') as f:
    input_order_lists = json.load(f)
output_order_lists = []
with open("dataset/seeds/output_order.json", 'r', encoding='utf-8') as f:
    output_order_lists = json.load(f)
declaration_style_lists = []
with open("dataset/seeds/declaration_style.json", 'r', encoding='utf-8') as f:
    declaration_style_lists = json.load(f)
situation_lists = []
with open("dataset/seeds/situation.json", 'r', encoding='utf-8') as f:
    situation_lists = json.load(f)
situation_selector = UniformSelector(situation_lists)
language_version_lists = []
with open("dataset/seeds/language_version.json", 'r', encoding='utf-8') as f:
    language_version_lists = json.load(f)
language_version_selector = UniformSelector(language_version_lists)
seed_concepts_lists = []
with open("dataset/seeds/code_snippet_concepts.json", 'r', encoding='utf-8') as f:
    seed_concepts_lists = json.load(f)
seed_concepts_selector = UniformSelector(seed_concepts_lists)


# Initialize the selector
language_selector = UniformSelector(language_lists)
algorithm_selector = UniformSelector(algorithm_lists)
framework_selector = UniformSelector(framework_lists)
function_selector = UniformSelector(function_lists)
library_selector = UniformSelector(library_lists)
advanced_syntax_selector = UniformSelector(advanced_syntax_lists)
brace_block_formatting_selector = UniformSelector(brace_block_formatting_lists)
data_structure_type_selector = UniformSelector(data_structure_type_lists)
output_type_selector = UniformSelector(output_type_lists)
input_type_selector = UniformSelector(input_type_lists)
indentation_spacing_selector = UniformSelector(indentation_spacing_lists)
comment_formatting_selector = UniformSelector(comment_formatting_lists)
data_structure_size_selector = UniformSelector(data_structure_size_lists)
data_structure_operation_selector = UniformSelector(data_structure_operation_lists)
output_range_selector = UniformSelector(output_range_lists)
input_range_selector = UniformSelector(input_range_lists)
input_order_selector = UniformSelector(input_order_lists)
output_order_selector = UniformSelector(output_order_lists)
declaration_style_selector = UniformSelector(declaration_style_lists)


@register_constraint("advanced_syntax")
class AdvancedSyntaxConstraint(Constraint):
    def generate(self):
        advanced_syntax = advanced_syntax_selector.select()
        return f"The generated tasks must use the {advanced_syntax['language']} high-level syntax {advanced_syntax['advanced_syntax']}\n" \
               f"- Feature: {advanced_syntax['features']}\n" \
               f"- Example:\n{advanced_syntax['example']}\n"

@register_constraint("algorithm_type")
class AlgorithmTypeConstraint(Constraint):
    def generate(self) -> str:
        lang = language_selector.select()
        algo = algorithm_selector.select()
        return f"- The programming language must belong to [{lang}]\n- The algorithm type must belong to [{algo}]"

@register_constraint("algorithm_space_complexity")
class AlgorithmSpaceeComplexityConstraint(Constraint):
    def generate(self) -> str:
        lang = language_selector.select()
        algo = algorithm_selector.select()
        return f"- The answer space complexity must use **Big O notation**, such as O(n), O(n^2)\n" \
               f"- The programming language must belong to [{lang}]\n- The algorithm type must belong to [{algo}]"

@register_constraint("algorithm_time_complexity")
class AlgorithmTimeComplexityConstraint(Constraint):
    def generate(self) -> str:
        lang = language_selector.select()
        algo = algorithm_selector.select()
        return f"- The answer time complexity must use **Big O notation**, such as O(log n), O(n^2)\n" \
               f"- The programming language must belong to [{lang}]\n- The algorithm type must belong to [{algo}]"

@register_constraint("brace_block_formatting")
class BraceBlockFormattingConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        brace_block_formatting = brace_block_formatting_selector.select()
        return f"The generated tasks must use proggramming language {lang} and follow the brace block formatting below:\n" \
               f"- **formatting name** : {brace_block_formatting['name']}\n" \
               f"- **feature** : {brace_block_formatting['description']}\n" \
               f"- **example** : \n{brace_block_formatting['example']}"

@register_constraint("comment_formatting")
class CommentFormattingConstraint(Constraint):
    def generate(self):
        lang_lists = ['C', 'C++', 'Python', 'Java', 'JavaScript', 'Rust', 'Go', 'Kotlin']
        lang_selector = UniformSelector(lang_lists)

        comment_formatting = comment_formatting_selector.select()
        comment_name = comment_formatting.get('name', '').lower()
        lang_mapping = {
            "python docstring": "Python",
            "javadoc": "Java",
            "rustdoc": "Rust",
            "godoc": "Go",
            "kotlindoc": "Kotlin"
        }
        lang = lang_mapping.get(comment_name, lang_selector.select())
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The generated tasks must only use comment formatting below:\n" \
               f"  - name: {comment_formatting['name']}\n" \
               f"  - feature: {comment_formatting['feature']}\n" \
               f"  - example:\n{comment_formatting['example']}"

@register_constraint("data_structure_operation")
class DataStructureOperationConstraint(Constraint):
    def generate(self):
        data_structure_operation = data_structure_operation_selector.select()
        return f"The generated tasks must use proggramming language **{data_structure_operation['language']}** and comply with data structure operation constraints:\n" \
               f"- **data structure** : {data_structure_operation['data_structure']}\n" \
               f"- **operation constraint** : The generated tasks must use specific operations on the data structure {data_structure_operation['operations']}"

@register_constraint("data_structure_size")
class DataStructureSize(Constraint):
    def generate(self):
        data_structure_size = data_structure_size_selector.select()
        return f"The generated tasks must use proggramming language **{data_structure_size['language']}** and comply with data structure size constraints:\n" \
               f"- **data structure** : {data_structure_size['data_structure']}\n" \
               f"- **size constraint** : The number of elements in the data structure, etc."

@register_constraint("data_structure_type")
class DataStructureType(Constraint):
    def generate(self):
        data_structure_type = data_structure_type_selector.select()
        return f"The generated tasks must use proggramming language **{data_structure_type['language']}** and use the data structure:\n" \
               f"- **data structure** : {data_structure_type['data_structure']}\n" \
               f"- **description** : {data_structure_type['description']}"

@register_constraint("declaration_style")
class DeclarationStyleConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        declaration_style = declaration_style_selector.select()
        return f"The generated tasks must use proggramming language {lang} and follow the declaration style below:\n" \
               f"- **declaration style** : {declaration_style['type']}\n" \
               f"- **feature** : {declaration_style['description']}\n" \
               f"- **example** : \n{declaration_style['example']}"

@register_constraint("framework")
class FrameworkConstraint(Constraint):
    def generate(self) -> str:
        framework = framework_selector.select()
        return f"The generated tasks must use the following framework:\n" \
               f"- **framework name** : {framework['framework']}\n" \
               f"- **framework programming language** : {framework['language']}\n" \
               f"- **framework features** : {framework['features']}"

@register_constraint("function")
class FunctionConstraint(Constraint):
    def generate(self) -> str:
        category = function_selector.select()
        func_selector = UniformSelector(category["functions"])
        func = func_selector.select()
        return f"The generated tasks must use the following function constraint:\n" \
               f"- **function name** : {func['name']}\n" \
               f"- **function programming language** : {func['language']}\n" \
               f"- **function category** : {category['category']}\n" \
               f"- **function features** : {func['description']}\n" \
               f"- **function usage example** : {func['example']}\n"

@register_constraint("indentation_spacing")
class IndentationSpacingConstraint(Constraint):
    def generate(self):
        lang_lists = ['C', 'C++', 'Python', 'Java', 'JavaScript', 'Rust', 'Go']
        lang_selector = UniformSelector(lang_lists)
        lang = lang_selector.select()
        indentation_spacing = indentation_spacing_selector.select()
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The generated tasks must follow indentation and spacing convention below:\n" \
               f"  - name: {indentation_spacing['name']}\n" \
               f"  - feature: {indentation_spacing['feature']}\n" \
               f"  - example:\n{indentation_spacing['example']}"

@register_constraint("input_order")
class InputOrderConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        input_order= input_order_selector.select()
        result = f"- The programming language must belong to [{lang}]\n" \
                 f"- The **input** or **passed parameter** of the generated code must follow the constraint below:\n" \
                 f"  - **{input_order['feature']}**\n" \
        
        parameter_list = input_order.get('parameter_list', [])
        if parameter_list:
            result += f"  - **Parameters details:**\n"
            for param in sorted(parameter_list, key=lambda x: x.get('position', 0)):
                position = param.get('position', 'unknown')
                data_structure = param.get('data_structure', 'unknown')
                description = param.get('description', '')
                result += f"    - Position {position}: `{data_structure}`"
                if description:
                    result += f", {description}"
                result += "\n"
        return result
               
@register_constraint("input_range")
class InputRangeConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        input_range = input_range_selector.select()
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The **input** or **passed parameter** of the generated code must be a **{input_range['data_structure']}** data structure type\n" \
               f"- The generated tasks must follow the input range constraints that the input values ​​satisfy a specific range.\n" \
               f"  - Specific ranges may include: {input_range['range']}\n" \
               f"  - Corresponding feature: {input_range['feature']}"

@register_constraint("input_type")
class InputTypeConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        input_type = input_type_selector.select()
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The **input** or **passed parameter** of the generated code must be a **{input_type['name']}** data structure type\n" \
               f"- The input data structure **{input_type['name']}** description: {input_type['description']}"

@register_constraint("library")
class LibraryConstraint(Constraint):
    def generate(self):
        library = library_selector.select()
        return f"The generated tasks must use the following framework:\n" \
               f"- **library name** : {library['name']}\n" \
               f"- **library programming language** : {library['language']}\n" \
               f"- **library category** : {library['category']}\n" \
               f"- **library features** : {library['description']}. {library['example']}\n"

@register_constraint("output_order")
class OutputOrderConstraint(Constraint):
    def generate(self):
        output_order = output_order_selector.select()
        result = f"- The programming language must belong to [{output_order['language_strategy']['language']}]\n" \
                 f"- The **output** or **return values** of the generated code must follow the constraint below:\n" \
                 f"  - **{output_order['feature']}**\n" \
        
        return_value_list = output_order.get('return_value_list', [])
        if return_value_list:
            result += f"  - **Return Value details:**\n"
            for param in sorted(return_value_list, key=lambda x: x.get('position', 0)):
                position = param.get('position', 'unknown')
                data_structure = param.get('data_structure', 'unknown')
                description = param.get('description', '')
                result += f"    - Position {position}: `{data_structure}`"
                if description:
                    result += f", {description}"
                result += "\n"
        return result

@register_constraint("output_range")
class OutputRangeConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        output_range = output_range_selector.select()
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The **output** of the generated code must be a **{output_range['data_structure']}** data structure type\n" \
               f"- The generated tasks must follow the output range constraints that the output values ​​satisfy a specific range.\n" \
               f"  - Specific ranges may include: {output_range['range']}\n" \
               f"  - Corresponding feature: {output_range['feature']}"

@register_constraint("output_type")
class OutputTypeConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        output_type = output_type_selector.select()
        return f"- The programming language must belong to [{lang}]\n" \
               f"- The **output** of the generated code must be a **{output_type['name']}** data structure type\n" \
               f"- The output data structure **{output_type['name']}** description: {output_type['description']}"


## situation
@register_constraint("situation")
class SituationConstraint(Constraint):
    def generate(self):
        situation = situation_selector.select()
        return f'''You are an expert in code task generation, specializing in creating code requirement tasks that align with real-world development scenarios.
You need to generate code generation tasks that meet the following constraints.
The tasks you generate need to be complex enough and realistic so that different large models can generate code with distinction.

<constraints pool>
Contextual constraints refer to the restrictions imposed on the goals, methods, or results of tasks from real-world development or learning scenarios when constructing code generation tasks.
These scenarios can include: specific stages of software development, programming ability levels, usage purposes, application fields, or job roles, etc.

Please follow the following scenario to generate tasks:
- Scenario: {situation['en']}

- Description: {situation['description_en']}

- Example: {situation['task_en']}
</constraints pool>

<prompt>
You are working on a microservice in an enterprise logistics platform. Your task is to implement a shipment tracking service using FastAPI. The service must expose a RESTful API endpoint POST /shipments that allows authenticated clients to create a new shipment tracking record. The service accepts a JSON payload with the following fields: order_id (string, required), carrier (string, required), tracking_number (string, required), estimated_delivery (ISO 8601 datetime string, optional) and stores the data in a PostgreSQL database. Ensure that the tracking_number is unique per carrier. Besides, use Pydantic for request validation and implement JWT-based authentication, reject unauthenticated requests with HTTP 401.
</prompt>
<prompt>
You are a beginner learning JavaScript and just starting to learn JavaScript. Now you need to write a JavaScript function that takes an array of strings and returns a new array containing only the strings that are palindromes (reads the same forwards and backwards). Then, sort this new array in alphabetical order and print each palindrome on a new line.
</prompt>
<prompt>
You are building a dashboard for a financial analytics platform using React and TypeScript. Create a reusable LineChart component that displays time-series data. The component should accept: an array of data points (date: string, value: number), a title (string), and optional props for customizing the chart's colors and dimensions. Implement responsive sizing, tooltips on hover showing exact values, and zoom/pan functionality for exploring data. Use D3.js for the chart rendering and ensure proper TypeScript typing throughout.
</prompt>
<prompt>
You are contributing to an open-source Markdown editor project. The issue tracker reports a bug where code blocks with triple backticks (```) are not properly preserved when converting Markdown to HTML. Fix the `markdownToHtml` function in `converter.js` to correctly handle code blocks, including maintaining syntax highlighting for specified languages and preserving whitespace. Ensure your solution follows the project's existing code style and passes all existing unit tests.
</prompt>

<prompt></prompt>

Output ONLY `<prompt>` , no additional information.'''

## example
@register_constraint("example")
class ExampleConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        return '''You are an expert in code task generation, specializing in creating code requirement tasks that align with real-world development scenarios.
You need to generate code generation tasks that meet the following constraints.
The tasks you generate need to be complex enough and realistic so that different large models can generate code with distinction.

<constraints pool>
Example constraints refer to implicit or explicit constraints on the structure, style, calling method or implementation strategy of the generated code by providing one or more example code snippets in the code generation task.
The generated model should maintain consistency or make analogical extensions in terms of style, structure, interface, etc. based on these examples.

Common forms include:

1. Example functions (such as sum_of_list(nums)) are used to agree on naming and parameter styles

2. Example style (such as always using list derivation in the function body) is used to limit the implementation style

3. Example calling method (such as api.post(url, data)) is used to limit interface calls

4. Example logical mode (such as using recursion instead of loops) is used to fix the algorithm implementation method
</constraints pool>

<prompt>Mimic the following `clean_text()` function’s structure, docstring style, and processing pattern to implement a new function `tokenize_text(text)`. The new function should split cleaned text into words by spaces and return the resulting list.\n\n**Example Code:**\n\n```python\ndef clean_text(text):\n    """\n    Cleans input text by removing HTML tags and extra spaces, and converting to lowercase.\n    \n    Args:\n        text (str): Raw input string\n\n    Returns:\n        str: Cleaned text\n    """\n    import re\n    text = re.sub(r"<[^>]*>", "", text)\n    text = re.sub(r"\\s+", " ", text)\n    return text.strip().lower()\n```</prompt>
<prompt>Replicate the function chaining and exception handling style from the `fetch_webpage()` function to implement a new function `download_json(url)` that downloads and parses JSON content from a URL, handling both network and JSON parsing errors.\n\n**Example Code:**\n\n```python\ndef fetch_webpage(url):\n    try:\n        import requests\n        response = requests.get(url, timeout=5)\n        response.raise_for_status()\n        return response.text\n    except requests.RequestException as e:\n        print(f"Network error: {e}")\n        return None\n```</prompt>
<prompt>Mimic the class-based organization, method structure, and backtracking control flow of the `SudokuSolver` class below to implement a `NQueensSolver` class that solves the N-Queens problem and returns one valid board configuration.\n\n**Example Code:**\n\n```python\nclass SudokuSolver:\n    def __init__(self, board):\n        self.board = board\n\n    def solve(self):\n        self._backtrack()\n\n    def _backtrack(self):\n        for i in range(9):\n            for j in range(9):\n                if self.board[i][j] == ".":\n                    for c in map(str, range(1, 10)):\n                        if self._is_valid(i, j, c):\n                            self.board[i][j] = c\n                            if self._backtrack():\n                                return True\n                            self.board[i][j] = "."\n                    return False\n        return True\n\n    def _is_valid(self, row, col, c):\n        for i in range(9):\n            if self.board[i][col] == c or self.board[row][i] == c:\n                return False\n        block_row, block_col = 3 * (row // 3), 3 * (col // 3)\n        for i in range(3):\n            for j in range(3):\n                if self.board[block_row + i][block_col + j] == c:\n                    return False\n        return True\n```</prompt>
<prompt>Implement a `PUT /user/:id` endpoint using the same structure and error handling conventions shown in the `POST /user` implementation below.\n\n**Example Code:**\n\n```javascript\n// Express.js API with Joi validation\nconst express = require('express');\nconst router = express.Router();\nconst Joi = require('joi');\nconst { User } = require('../models/user');\n\nconst userSchema = Joi.object({\n  username: Joi.string().alphanum().min(3).max(30).required(),\n  email: Joi.string().email().required()\n});\n\nrouter.post('/user', async (req, res) => {\n  const { error } = userSchema.validate(req.body);\n  if (error) return res.status(400).send({ message: error.details[0].message });\n\n  try {\n    const user = new User(req.body);\n    await user.save();\n    res.status(201).send({ user });\n  } catch (err) {\n    res.status(500).send({ message: 'Internal server error' });\n  }\n});\n\nmodule.exports = router;\n```\n</prompt>

<prompt></prompt>

Make sure you are using the programming language type''' \
        f''' {lang}. Output ONLY `<prompt>` , no additional information.'''

## Code Context Dependencies
@register_constraint("code_contextual")
class CodeContextualConstraint(Constraint):
    def generate(self):
        lang = language_selector.select()
        return '''You are an expert in code task generation, specializing in creating code requirement tasks that align with real-world development scenarios.
You need to generate code generation tasks that meet the following constraints.
The tasks you generate need to be complex enough and realistic so that different large models can generate code with distinction.

<constraints pool>
Code context constraints mean that in the code generation task, a piece of existing code (which may be partial code, framework, interface definition, etc.) is provided, and the generated code must be developed or modified based on this existing code.
This includes:

1. Use existing code: The generated code needs to call or extend the provided code.

2. Refactor existing code: Optimize, reorganize or repair the provided code.

3. Follow the existing style: The generated code needs to be consistent with the provided code in style, naming, and structure.

4. Satisfy interfaces or abstractions: The provided code may be an interface or an abstract class, and the generated code needs to implement or inherit them.
</constraints pool>

<prompt>Complete the function `load_and_clean(path)` so that it returns the fully cleaned text. It should call `read_file`, `clean_text`, and `remove_special_characters` in sequence. Ensure that the final text is ready for tokenization in the subsequent `analyze_text` function.\n```python\n# File I/O Module: file_io.py\n\ndef read_file(path):\n    with open(path, \'r\', encoding=\'utf-8\') as f:\n        return f.read()\n\ndef write_file(path, content):\n    with open(path, \'w\', encoding=\'utf-8\') as f:\n        f.write(content)\n\n\n# Data cleaning module: text_cleaner.py\n\ndef clean_text(text):\n    # Remove leading/trailing whitespace and reduce multiple spaces.\n    return \' \'.join(text.strip().split())\n\ndef remove_special_characters(text):\n    # Remove non-alphanumeric characters, except spaces.\n    import re\n    return re.sub(r\'[^A-Za-z0-9 ]+\', \'\', text)\n\ndef tokenize(text):\n    return text.lower().split()\n\n# Processing pipeline in a main module: text_pipeline.py\n\nfrom file_io import read_file, write_file\nfrom text_cleaner import clean_text, remove_special_characters, tokenize\n\ndef load_and_clean(path):\n    raw = read_file(path)\n    cleaned = clean_text(raw)\n    cleaned = remove_special_characters(cleaned)\n    # <generate-here>\n    \ndef analyze_text(text):\n    tokens = tokenize(text)\n    frequency = {}\n    for token in tokens:\n        frequency[token] = frequency.get(token, 0) + 1\n    return frequency\n\ndef run_pipeline(input_path, output_path):\n    cleaned_text = load_and_clean(input_path)\n    analysis = analyze_text(cleaned_text)\n    report = "\n".join(f"{word}: {count}" for word, count in analysis.items())\n    write_file(output_path, report)\n    return analysis\n```</prompt>
<prompt>```python
class Graph:
    def __init__(self):
        self.edges = {}  # Adjacency list representation

    def add_edge(self, src, dst):
        if src not in self.edges:
            self.edges[src] = []
        self.edges[src].append(dst)

    def get_neighbors(self, node):
        return self.edges.get(node, [])

    def has_path_recursive(self, src, dst, visited=None):
        if visited is None:
            visited = set()
        if src == dst:
            return True
        visited.add(src)
        for neighbor in self.get_neighbors(src):
            if neighbor not in visited and self.has_path_recursive(neighbor, dst, visited):
                return True
        return False

    def display(self):
        for node, neighbors in self.edges.items():
            print(f"{node}: {neighbors}")

# Breadth-First Search (BFS) utility.
def breadth_first_search(graph, start):
    visited = []
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node not in visited:
            visited.append(node)
            queue.extend([n for n in graph.get_neighbors(node) if n not in visited])
    return visited

# Depth-First Search (DFS) utility.
def depth_first_search(graph, start):
    visited = []
    stack = [start]
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.append(node)
            stack.extend([n for n in graph.get_neighbors(node) if n not in visited])
    return visited

# Advanced: We now want to implement an algorithm that finds
# all paths between a start node and a destination node.

def find_all_paths(graph, start, end, path=None):
    if path is None:
        path = []
    path = path + [start]
    if start == end:
        return [path]
    if start not in graph.edges:
        return []
    paths = []
    for node in graph.get_neighbors(start):
        if node not in path:
            new_paths = find_all_paths(graph, node, end, path)
            for new_path in new_paths:
                paths.append(new_path)
    return paths

# We intend to add another algorithm that, given a start node,
# performs a combined DFS that records the order of visit,
# and also computes some basic statistics about the traversal.
# <generate-here>
```

At the designated generation point, implement a function `complex_dfs_analysis(graph, start)` that:
1. Performs a depth-first search (you can use or modify the existing `depth_first_search` function) to obtain the list of visited nodes.
2. Computes and returns a dictionary with:
   - `"visited_nodes"`: the list of nodes in the order they were visited.
   - `"total_nodes"`: the total number of nodes visited.
   - `"unique_nodes"`: the count of unique nodes visited.</prompt>

<prompt></prompt>

Make sure you are using the programming language type''' \
        f''' {lang}. Output ONLY one `<prompt>` , no additional information.'''

@register_constraint("language_version")
## language version
class LanguageVersionConstraint(Constraint):
    def generate(self):
        lang_version = language_version_selector.select()
        return '''You are an expert in code task generation, specializing in creating code requirement tasks that align with real-world development scenarios.
You will receive the following input content:

- **Natural language description of the code requirement** `<prompt>` (example, for reference only)
- **Keywords to validate requirement fulfillment** `<answer>` (example, for reference only)
- **Test script for validating code constraints** `<constraint validation script>` used to evaluate whether the generated code from large models satisfies the constraints in `<answer>`
- **Range list of constraint type values** `<constraints pool>` containing all optional constraint types

Your task is to generate new `<prompt>` and `<answer>` based on the references. Key considerations:

1. Generate new `<prompt>` tasks grounded in real development/production environments, ensuring diversity and avoiding duplication with existing examples. Tasks must not be overly simplistic.
2. Generated `<prompt>` must comply with constraint types evaluated by the `<constraint validation script>`, strictly selecting constraint ranges from `<constraints pool>`.
3. Ensure generated `<answer>` can be validated by the `<constraint validation script>`.
4. Note: Provided `<prompt>` and `<answer>` are only examples; actual generated tasks/answers must address new requirements. 

Output ONLY `<prompt>` and `<answer>`, no additional information.
<prompt>
Implement a Rust utility that reads a list of filenames from standard input and concurrently compresses each file using GZIP. The tool should handle large numbers of files efficiently, using a bounded number of threads. Compressed files must be saved with a `.gz` extension in the same directory. Ensure that your implementation uses `std::io::pipe` and `std::thread` for concurrent I/O operations and demonstrates compatibility with Rust 1.87.0 features.
</prompt>

<answer>  
rust;1.87.0
</answer>

<prompt>
Develop a Python 3.13 script that scans a local directory tree for user password files and replaces any password hashes created using the deprecated `crypt` module with secure `hashlib.pbkdf2_hmac` hashes. The script must identify legacy `crypt` hashes based on format, re-hash them using a new salt, and update the files accordingly. Include a secure migration flow and log the number of upgraded hashes.
</prompt>

<answer>  
python;3.13
</answer>  

<prompt>
Implement a document preview service in Java that reads and summarizes text content from uploaded files (PDF, DOCX, and TXT). The application should expose a RESTful API using Java 11's HTTP Client and avoid using any JavaFX-based UI components. Instead, provide JSON-formatted summaries with metadata like word count, file type, and detected language (basic detection using charset or file heuristics). 
</prompt>

<answer>  
java;jdk11
</answer>

<constraint validation script>  
```python
def check_language_version(generation, answer):
    """
    Check if the generated code is of the specified language version

    :param generation: generated code
    :param answer: language type and version separated by semicolons, such as `rust;1.86.0`
    :return: True for yes, False for no
    """
    language_type, version = answer.split(';')
    return globals()[f"check_{language_type.lower()}_version"](generation, version)
```
</constraint validation script>  
''' + f'''
The generated tasks must use the programming language **{lang_version["language"]}** and must be a specific version of that language **{lang_version["version"]}**.
Here are some specific features of {lang_version["language"]} under {lang_version["version"]}. You can refer to these features to ensure that the tasks are more closely related to the version {lang_version["version"]}.
</constraints pool>

<prompt></prompt>

<answer></answer>
'''

base_prompt = '''You are an expert in code task generation, specializing in creating code requirement tasks that align with real-world development scenarios.
You will receive the following input content:

- **A seed code snippet that completes a specified task** `<seed code snippet>` (optional)
- **Fundamental principles and techniques that extracted from <seed code snippet> the task is designed to incorporate, which developers must understand to effectively solve the task** `<concepts>` (optional)
- **Natural language description of the code requirement** `<prompt>` (example, for reference only)
- **Keywords to validate requirement fulfillment** `<answer>` (example, for reference only)
- **Test script for validating code constraints** `<constraint validation script>` used to evaluate whether the generated code from large models satisfies the constraints in `<answer>`
- **Range list of constraint type values** `<constraints pool>` containing all optional constraint types

Your task is to generate new `<prompt>` and `<answer>` based on the references. Key considerations:

1. Generate new `<prompt>` tasks grounded in real development/production environments, ensuring diversity and avoiding duplication with existing examples. Tasks must not be overly simplistic.
2. Generated `<prompt>` must comply with constraint types evaluated by the `<constraint validation script>`, strictly selecting constraint ranges from `<constraints pool>`.
3. Ensure generated `<answer>` can be validated by the `<constraint validation script>`.
4. Note: Provided `<prompt>` and `<answer>` are only examples; actual generated tasks/answers must address new requirements. 

Output ONLY `<prompt>` and `<answer>`, no additional information.

<seed code snippet>
{seed}
</seed code snippet>

<concepts>
{concepts}
</concepts>

<prompt>
{prompt1}
</prompt>

<answer>  
{answer1}
</answer>

<prompt>
{prompt2}
</prompt>

<answer>  
{answer2}
</answer>  

<prompt>
{prompt3}
</prompt>

<answer>  
{answer3}
</answer>  

<constraint validation script>  
{verification}
</constraint validation script>  

<constraints pool>  
{constraints}
</constraints pool>

<prompt></prompt>

<answer></answer>'''

code = ''''''

concepts = ''''''

instruction1 = "Create a Rust function named `process_users` that takes a vector of tuples (consisting of a string for user ID and an integer status) as input. The function should iterate through the vector, add the user ID to a new vector if the status is exactly 1, and return two values: 1. A list of processed user IDs if the status is 1 (`Vec<String>`), 2. A boolean flag that is `true` if all users in the input had a status of 1, otherwise `false` (`bool`). Ensure the values are returned in this specific order without changing the order."

answer1 = "Rust;process_users;[Vec,bool]"

instruction2 = "Create a Python function named `process_files` that takes a list of file paths (strings) and processes each file to perform a certain operation (e.g., reading file contents). The function should return **exactly three values** in this specific order: 1. A list of processed filenames (`list[str]`), 2. The total number of files processed (`int`), 3. The total time taken to process all files in seconds, rounded to two decimal places (`float`). Ensure that the function handles various exceptions such as file not found or access denied gracefully and logs these errors."

answer2 = "python;process_files;[list,int,float]"

instruction3 = "Create a Python function named `calculate_velocity_statistics` that receives a list of float values representing speeds in kilometers per hour. The function should return exactly three values in this order: 1. The average speed as a float, rounded to two decimal places (`float`), 2. The maximum speed from the list as a float (`float`), 3. The minimum speed from the list as a float (`float`). The data must be returned in this precise order."

answer3 = "python;calculate_velocity_statistics;[float,float,float]"

verification = '''language, func_name, outputs = answer.split(';')
    output_list = outputs.strip('[]').split(',')
    
    return globals()[f"check_{language.lower()}_output_order"](
        remove_comments(generation, language),
        func_name,
        output_list
    )'''


def generate_prompt_json(constraint_type, output_path, count=50):
    constraint_obj = get_constraint(constraint_type)
    data = []
    
    # seed code concepts

    # seed_concepts = seed_concepts_selector.select()

    for i in range(1, count + 1):
        prompt_text = base_prompt.format(
            seed="",
            concepts="",
            prompt1=instruction1,
            answer1=answer1,
            prompt2=instruction2,
            answer2=answer2,
            prompt3=instruction3,
            answer3=answer3,
            verification=verification,
            constraints=constraint_obj.generate()
        )
        print(prompt_text)
        data.append({"id": i, "prompt": prompt_text, "answer": ""})

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Success generate {count} prompts for '{constraint_type}' → {output_path}")


def generate_language_version_prompt_json(output_path, count=50):
    constraint_obj = get_constraint("language_version")
    data = []

    for i in range(1, count + 1):
        print(constraint_obj.generate())
        data.append({"id": i, "prompt": constraint_obj.generate(), "answer": ""})
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Success generate {count} prompts for language version → {output_path}")


def generate_situation_prompt_json(output_path, count=50):
    constraint_obj = get_constraint("situation")
    data = []

    for i in range(1, count + 1):
        print(constraint_obj.generate())
        data.append({"id": i, "prompt": constraint_obj.generate(), "answer": ""})

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Success generate {count} prompts for situation → {output_path}")


def generate_example_prompt_json(output_path, count=50):
    constraint_obj = get_constraint("example")
    data = []

    for i in range(1, count + 1):
        print(constraint_obj.generate())
        data.append({"id": i, "prompt": constraint_obj.generate(), "answer": ""})

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Success generate {count} prompts for situation → {output_path}")


def generate_code_contextual_prompt_json(output_path, count=50):
    constraint_obj = get_constraint("code_contextual")
    data = []

    for i in range(1, count + 1):
        print(constraint_obj.generate())
        data.append({"id": i, "prompt": constraint_obj.generate(), "answer": ""})

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Success generate {count} prompts for situation → {output_path}")


def generate_prompts_by_constraint(constraint_type, count=50):
    constraint_obj = get_constraint(constraint_type)
    data = []

    if constraint_type == "language_version":
        for i in range(1, count + 1):
            prompt_text = constraint_obj.generate()
            data.append({"id": i, "prompt": prompt_text, "answer": ""})

    elif constraint_type == "situation":
        for i in range(1, count + 1):
            prompt_text = constraint_obj.generate()
            data.append({"id": i, "prompt": prompt_text, "answer": ""})

    elif constraint_type == "example":
        for i in range(1, count + 1):
            prompt_text = constraint_obj.generate()
            data.append({"id": i, "prompt": prompt_text, "answer": ""})

    elif constraint_type == "code_contextual":
        for i in range(1, count + 1):
            prompt_text = constraint_obj.generate()
            data.append({"id": i, "prompt": prompt_text, "answer": ""})

    else:
        for i in range(1, count + 1):
            prompt_text = base_prompt.format(
                seed="",
                concepts="",
                prompt1=instruction1,
                answer1=answer1,
                prompt2=instruction2,
                answer2=answer2,
                prompt3=instruction3,
                answer3=answer3,
                verification=verification,
                constraints=constraint_obj.generate()
            )
            data.append({"id": i, "prompt": prompt_text, "answer": ""})

    return data

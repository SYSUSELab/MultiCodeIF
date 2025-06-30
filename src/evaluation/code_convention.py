import re
import ast
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Name, Token
import tree_sitter_cpp as tscpp
import tree_sitter_c_sharp as tscsharp
import tree_sitter_go as tsgo
import tree_sitter_haskell as tshaskell
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_kotlin as tskotlin
import tree_sitter_python as tspython
import tree_sitter_rust as tsrust
import tree_sitter_zig as tszig
from tree_sitter import Language, Parser
from util import remove_comments, remove_strings


CPP_LANGUAGE = Language(tscpp.language())
CSHARP_LANGUAGE = Language(tscsharp.language())
GO_LANGUAGE = Language(tsgo.language())
HASKELL_LANGUAGE = Language(tshaskell.language())
JAVA_LANGUAGE = Language(tsjava.language())
JAVASCRIPT_LANGUAGE = Language(tsjavascript.language())
KOTLIN_LANGUAGE = Language(tskotlin.language())
PYTHON_LANGUAGE = Language(tspython.language())
RUST_LANGUAGE = Language(tsrust.language())
ZIG_LANGUAGE = Language(tszig.language())


def evaluate_code_convention(generation, answer, constraint):
    if constraint == 'naming_convention':
        return check_naming_convention(generation, answer)
    elif constraint == 'indentation_spacing':
        return check_indentation_spacing(generation, answer)
    elif constraint == 'brace_block_formatting':
        return check_brace_block_formatting(generation, answer)
    elif constraint == 'comment_formatting':
        return check_comment_formatting(generation, answer)
    # elif constraint == 'declaration_style':
    #     return check_declaration_style(generation, answer)
    else:
        return False


def check_brace_block_formatting(generation, answer):
    language_type, standard = answer.split(';')
    if standard not in ['K&R', 'Allman', '1TBS']:
        return False

    clean_code = remove_comments(generation, language_type.lower())
    code_lines = [line.rstrip() for line in clean_code.splitlines() if line.strip()]

    if standard == 'K&R':
        for line in code_lines:
            stripped = line.strip()
            if stripped == "{":
                return False
            if "{" in stripped:
                before_brace = stripped.split("{", 1)[0].strip()
                if not re.search(r'(\)|\w)\s*$', before_brace):
                    return False
        return True

    elif standard == 'Allman':
        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if stripped == "{":
                if i == 0 or not re.search(r'(\)|\w)\s*$', code_lines[i-1].strip()):
                    return False
            elif "{" in stripped:
                return False
        return True

    elif standard == '1TBS':
        for line in code_lines:
            stripped = line.strip()
            if stripped == "{":
                return False
            if "{" in stripped:
                before_brace = stripped.split("{", 1)[0].strip()
                if not re.search(r'(\)|\w)\s*$', before_brace):
                    return False

        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if "}" in stripped:
                after_brace = stripped.split("}", 1)[1].strip()
                if not after_brace.startswith(('else', 'catch', 'finally')):
                    if i < len(code_lines) - 1:
                        next_line = code_lines[i + 1].strip()
                        if next_line.startswith(('else', 'catch', 'finally')):
                            return False
        return True

    else:
        return False


def check_indentation_spacing(generation, answer):
    language_type, standard, spacing = answer.split(';')
    has_spacing = True if spacing == 'spacing' else False
    indent_type, _, indent_size = standard.partition(':')
    if indent_type == "spaces":
        indent_size = int(indent_size)
    elif indent_type == "tabs":
        indent_size = None
    else:
        return False

    generation = remove_comments(generation, language_type)
    generation = remove_strings(generation, language_type)

    lines = generation.replace("\r\n", "\n").split("\n")
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            continue

        leading_whitespace = line[:len(line) - len(stripped)]

        if indent_type == 'spaces':
            if "\t" in leading_whitespace:
                return False
            if len(leading_whitespace) % indent_size != 0:
                return False
        elif indent_type == 'tabs':
            if " " in leading_whitespace:
                return False

    def check_spacing_style_consistency(code, require_spaces):
        operators = [
            '=', r'\+', '-', r'\*', '/', '%',
            '==', '!=', '<', '>', '<=', '>=',
            r'\&\&', r'\|\|'
        ]

        for op in operators:
            spaced_pattern = re.compile(rf'\b\w+\s+{op}\s+\w+\b')
            unspaced_pattern = re.compile(rf'\b\w+{op}\w+\b')

            has_spaced = bool(spaced_pattern.search(code))
            has_unspaced = bool(unspaced_pattern.search(code))

            if require_spaces:
                if has_unspaced:
                    return False
            else:
                if has_spaced:
                    return False

        spaced_comma_pattern = re.compile(r',\s+\S')
        unspaced_comma_pattern = re.compile(r',\S')

        has_spaced_comma = bool(spaced_comma_pattern.search(code))
        has_unspaced_comma = bool(unspaced_comma_pattern.search(code))

        if require_spaces:
            if has_unspaced_comma:
                return False
        else:
            if has_spaced_comma:
                return False
        return True

    return check_spacing_style_consistency(generation, has_spacing)


def check_comment_formatting(generation, answer):
    SUPPORTED_COMMENT = ['single-line comment', 'multi-line comment', 'inline comment', 'block comment', 'python docstring', 'javadoc', 'rustdoc', 'godoc', 'kotlindoc']
    language_type, standard = answer.split(';')
    standard = standard.lower()
    if standard not in SUPPORTED_COMMENT:
        return False
    
    lexer = get_lexer_by_name(language_type.lower())
    tokens = list(lex(generation, lexer))
    
    if standard in ['single-line comment', 'multi-line comment']:
        has_single_line = False
        has_multi_line = False
        for token_type, _ in tokens:
            if token_type == Token.Comment.Single:
                has_single_line = True
            elif token_type == Token.Comment.Multiline:
                has_multi_line = True

        if standard == 'single-line comment':
            return has_single_line and not has_multi_line
        elif standard == 'multi-line comment':
            return has_multi_line and not has_single_line
    elif standard == 'inline comment':
        line_map = {}
        current_line = 1
        for token_type, token_value in tokens:
            line_count = token_value.count('\n')
            if token_type not in Token.Text:
                for i in range(line_count + 1):
                    line_map.setdefault(current_line + i, []).append(token_type)
            current_line += line_count

        for line_num, types in line_map.items():
            if any(t in [Token.Comment.Single, Token.Comment.Multiline] for t in types):
                if any(not t in [Token.Comment.Single, Token.Comment.Multiline] for t in types):
                    continue
                else:
                    return False
        return True
    elif standard == 'block comment':
        lines = generation.splitlines()
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            if line.startswith("/*"):
                while i < len(lines):
                    if "*/" in lines[i]:
                        break
                    i += 1

                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith(("//", "#", "/*")):
                        return True
                i += 1
                continue

            if line.startswith(("//", "#")):
                while i + 1 < len(lines) and lines[i + 1].strip().startswith(("//", "#")):
                    i += 1

                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith(("//", "#", "/*")):
                        return True
            i += 1
        return False
    elif standard == 'python docstring':
        return contain_python_docstring(generation)
    elif standard == 'javadoc':
        return contain_javadoc(generation)
    elif standard == 'godoc':
        return contain_godoc(generation)
    elif standard == 'kotlindoc':
        return contain_kotlindoc(generation)
    elif standard == 'rustdoc':
        return contain_rustdoc(generation)
    else:
        return False


def contain_python_docstring(code):
    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    return False
        return True

    except SyntaxError:
        return False
    

def contain_javadoc(code):
    lexer = get_lexer_by_name('java')
    tokens = list(lex(code, lexer))
    
    has_javadoc = False
    for token_type, token_value in tokens:
        if token_type == Token.Comment.Multiline and token_value.strip().startswith("/**") and token_value.strip().endswith("*/"):
            has_javadoc = True
            if not "@param" in token_value and "@return" in token_value:
                return False
    return has_javadoc


def contain_kotlindoc(code):
    lexer = get_lexer_by_name('kotlin')
    tokens = list(lex(code, lexer))

    has_kotlindoc = False
    for token_type, token_value in tokens:
        if token_type == Token.Comment.Multiline and token_value.strip().startswith("/**") and token_value.strip().endswith("*/"):
            has_kotlindoc = True
            if not "@param" in token_value and "@return" in token_value:
                return False
    return has_kotlindoc


def contain_godoc(code):
    def is_godoc_style_comment(comment: str, identifier: str) -> bool:
        comment = comment.strip().lstrip("//").strip()
        return comment.startswith(identifier)
    
    lines = code.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()

        match = re.match(r'^(func|type|var|const)\s+(\w+)', line)
        if match:
            kind, identifier = match.groups()
            if i == 0:
                return False
            prev_line = lines[i - 1].strip()
            if prev_line.startswith('//'):
                if not is_godoc_style_comment(prev_line, identifier):
                    return False
            else:
                return False
    return True


def contain_rustdoc(code):
    lexer = get_lexer_by_name('rust')
    tokens = list(lex(code, lexer))

    has_rustdoc = False

    for token_type, token_value in tokens:
        if token_type == Token.Literal.String.Doc and token_value.strip().startswith("///"):
            has_rustdoc = True
        elif token_type in [Token.Comment.Multiline, Token.Comment.Single]:
            return False
    return has_rustdoc


def check_naming_convention(generation, answer):
    def check_identifiers(identifiers, category):
        standard = standard_dict.get(category)
        if not standard:
            return True
        return all(match_naming_convention(name, standard) for name in identifiers)
    
    language_type, standard = answer.split(';')
    standard_dict = dict(item.split(':') for item in standard.split(','))

    classes, functions = globals()[f"extract_{language_type.lower()}_class_function"](generation)
    variables = set()

    try:
        lexer = get_lexer_by_name(language_type)
    except Exception:
        raise ValueError(f"Unsupported language type: {language_type}")
    tokens = lex(generation, lexer)

    for token_type, token_value in tokens:
        if token_type == Name:
            if token_value not in classes and token_value not in functions:
                if not token_value.startswith("_") and not bool(re.fullmatch(r'[A-Z0-9_]+', token_value)) and len(token_value) >= 5:
                    variables.add(token_value)
    
    all_pass = all([
        check_identifiers(classes, "class"),
        check_identifiers(functions, "function"),
        check_identifiers(variables, "variable")
    ])
    
    return all_pass
    

def match_naming_convention(name, convention):
    if convention == 'snake_case':
        return re.match(r'^[a-z]+[a-z0-9_]*$', name) is not None
    elif convention == 'PascalCase':
        return re.match(r'^[A-Z][A-Za-z0-9]*$', name) is not None
    elif convention == 'camelCase':
        return re.match(r'^[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)*$', name) is not None
    elif convention == 'kebab-case':
        return re.match(r'^[a-z]+(-[a-z]+)*$', name) is not None
    # elif convention == 'UPPER_SNAKE_CASE':
    #     return re.match(r'^[A-Z]+(_[A-Z0-9]+)*$', name) is not None
    # elif convention == '_camelCase':
    #     return re.match(r'^_[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)*$', name) is not None
    return False


def extract_class_function(code, language, class_query_str, function_query_str):
    parser = Parser(language)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    class_query = language.query(class_query_str)
    captures = class_query.captures(root_node).get("class.name")
    class_names = {capture.text.decode() for capture in captures} if captures else set()

    function_query = language.query(function_query_str)
    captures = function_query.captures(root_node).get("function.name")
    function_names = {capture.text.decode() for capture in captures} if captures else set()
    return class_names, function_names


def extract_python_class_function(code):
    classes, functions = extract_class_function(
        code,
        PYTHON_LANGUAGE,
        "(class_definition name: (identifier) @class.name)",
        "(function_definition name: (identifier) @function.name)"
    )
    functions = {name for name in functions if not re.match(r'^__.*__$', name)}
    return classes, functions


def extract_java_class_function(code):
    return extract_class_function(
        code,
        JAVA_LANGUAGE,
        "(class_declaration name: (identifier) @class.name)",
        "(method_declaration name: (identifier) @function.name)"
    )
    

def extract_javascript_class_function(code):
    classes, functions = extract_class_function(
        code,
        JAVASCRIPT_LANGUAGE,
        """(class_declaration name: (identifier) @class.name)
(variable_declarator
    name: (identifier) @class.name
    value: (new_expression
        constructor: (identifier) @class.name
        arguments: (arguments (string (string_fragment) @class.name))
    )
)""",   
        """(function_declaration name: (identifier) @function.name)
(method_definition name: (property_identifier) @function.name)
(variable_declarator name: (identifier) @function.name value: (arrow_function))"""
    )
    ignored_functions = {
    "constructor", "componentDidMount", "componentWillUnmount",
    "render", "getDerivedStateFromProps", "shouldComponentUpdate",
}
    functions = {name for name in functions if name not in ignored_functions and not name.startswith('__')}
    return classes, functions


def extract_cpp_class_function(code):
    return extract_class_function(
        code,
        CPP_LANGUAGE,
        """(class_specifier name: (type_identifier) @class.name)
(struct_specifier name: (type_identifier) @class.name)""",
        """(function_definition
    declarator: (function_declarator
        declarator: [
            (identifier) @function.name
            (field_identifier) @function.name
            (qualified_identifier
                name: (identifier) @function.name
            )
        ]
    )
)"""
    )
    

def extract_go_class_function(code):
    return extract_class_function(
        code,
        GO_LANGUAGE,
        "(type_declaration (type_spec name: (type_identifier) @class.name type: (struct_type)))",
        """(function_declaration name: (identifier) @function.name)
(method_declaration
      receiver: (parameter_list
        (parameter_declaration
          type: [
            (pointer_type (type_identifier) @function.name)
            (type_identifier) @function.name
          ]
        )
      )
      name: (field_identifier) @function.name
    )"""
    )
    

def extract_kotlin_class_function(code):
    return extract_class_function(
        code,
        KOTLIN_LANGUAGE,
        """(class_declaration name: (identifier) @class.name)
(object_declaration name: (identifier) @class.name) """,
        """(function_declaration name: (identifier) @function.name)
(class_body
    (function_declaration
        name: (identifier) @function.name
    )
)
(callable_reference
    (user_type
        (identifier) @function.name
    )
    (identifier) @function.name
)"""
    )
    
    
def extract_rust_class_function(code):
    return extract_class_function(
        code,
        RUST_LANGUAGE,
        """(struct_item name: (type_identifier) @class.name)
(enum_item name: (type_identifier) @class.name)
(trait_item name: (type_identifier) @class.name)""",
        """(function_item name: (identifier) @function.name)
(impl_item body: (declaration_list
    (function_item name: (identifier) @function.name)
))"""
    )


def extract_csharp_class_function(code):
    return extract_class_function(
        code,
        CSHARP_LANGUAGE,
        """(class_declaration name: (identifier) @class.name)
(struct_declaration name: (identifier) @class.name)
(interface_declaration name: (identifier) @class.name)""",
        """(method_declaration name: (identifier) @function.name)
(constructor_declaration name: (identifier) @function.name)"""
    )


def extract_haskell_class_function(code):
    return extract_class_function(
        code,
        HASKELL_LANGUAGE,
        "(class name: (name) @class.name)",
        "(function name: (variable) @function.name)"
    )


def extract_zig_class_function(code):
    return extract_class_function(
        code,
        ZIG_LANGUAGE,
        """(variable_declaration
    (identifier) @class.name
    (struct_declaration) 
)""",
        "(function_declaration name: (identifier) @function.name)"
    )

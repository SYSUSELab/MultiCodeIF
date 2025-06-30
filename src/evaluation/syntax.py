import ast
import os
import tempfile
import subprocess
from guesslang import Guess
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from util import remove_comments
import tree_sitter_kotlin as tskotlin
import tree_sitter_rust as tsrust
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_c_sharp as tscsharp
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser


KOTLIN_LANGUAGE = Language(tskotlin.language())
RUST_LANGUAGE = Language(tsrust.language())
JAVA_LANGUAGE = Language(tsjava.language())
JAVASCRIPT_LANGUAGE = Language(tsjs.language())
CPP_LANGUAGE = Language(tscpp.language())
GO_LANGUAGE = Language(tsgo.language())
C_SHARP_LANGUAGE = Language(tscsharp.language())
TYPESCRIPT_LANGUAGE = Language(tsts.language_typescript())


def evaluate_syntax(generation, answer, constraint):
    if constraint == 'language_type':
        return check_language_type(generation, answer)
    elif constraint == 'language_version':
        return check_language_version(generation, answer)
    elif constraint == 'advanced_syntax':
        return check_advanced_syntax(generation, answer)
    elif constraint == 'function':
        return check_contain_function(generation, answer)
    elif constraint == 'library':
        return check_contain_library(generation, answer)
    # elif constraint == 'framework':
    #     return check_contain_framework(generation, answer)
    else:
        return False


def check_language_type(generation, answer):
    """
    Check if the generated code is of the specified language type

    :param generation: generated code
    :param answer: language type
    :return: True for yes, False for no
    """
    answer = answer.lower()

    guess = Guess()
    lang = guess.language_name(generation)
    return lang.lower() == answer


def check_advanced_syntax(generation, answer):
    """
    Check if the generated code contains advanced syntax

    :param generation: generated code
    :param answer: standard answer: language type; advanced syntax, such as `python;list expression`
    :return: True means yes, False means no
    """
    language_type, advanced_syntax = answer.split(';')
    generation = remove_comments(generation, language_type)

    return globals()[f"check_{language_type.lower()}_advanced_syntax"](
        generation,
        advanced_syntax
    )


def check_javascript_advanced_syntax(code, advanced_syntax):
    SUPPORTED_SYNTAX = ['async/await', 'arrow functions', 'spread operator']
    if advanced_syntax.lower() not in SUPPORTED_SYNTAX:
        return False
    
    lexer = get_lexer_by_name('javascript')
    tokens = list(lex(code, lexer))
    if advanced_syntax.lower() == 'async/await':
        has_async = any(toktype == Token.Keyword and tokval == 'async' for toktype, tokval in tokens)
        has_await = any(toktype == Token.Keyword and tokval == 'await' for toktype, tokval in tokens)
        return has_async and has_await
    elif advanced_syntax.lower() == 'arrow functions':
        return any(toktype == Token.Punctuation and tokval == '=>' for toktype, tokval in tokens)
    elif advanced_syntax.lower() == 'spread operator':
        return any(toktype == Token.Punctuation and tokval == '...' for toktype, tokval in tokens)
    else:
        return False
    

def check_python_advanced_syntax(code, advanced_syntax):
    SUPPORTED_SYNTAX = ['generator and yield', 'list comprehension', 'dictionary comprehension', 'set comprehension']
    if advanced_syntax.lower() not in SUPPORTED_SYNTAX:
        return False
    
    try:
        tree = ast.parse(code)
        if advanced_syntax.lower() == 'generator and yield':
            for node in ast.walk(tree):
                if isinstance(node, (ast.Yield, ast.YieldFrom)):
                    return True
            return False
        elif advanced_syntax.lower() == 'list comprehension':
            for node in ast.walk(tree):
                if isinstance(node, ast.ListComp):
                    return True
            return False
        elif advanced_syntax.lower() == 'dictionary comprehension':
            for node in ast.walk(tree):
                if isinstance(node, ast.DictComp):
                    return True
            return False
        elif advanced_syntax.lower() == 'set comprehension':
            for node in ast.walk(tree):
                if isinstance(node, ast.SetComp):
                    return True
            return False
        else:
            return False
    except SyntaxError:
        return False 
    

def check_go_advanced_syntax(code, advanced_syntax):
    SUPPORTED_SYNTAX = ['goroutine and channel', 'defer statement']
    if advanced_syntax.lower() not in SUPPORTED_SYNTAX:
        return False
    
    lexer = get_lexer_by_name('go')
    tokens = list(lex(code, lexer))
    if advanced_syntax.lower() == 'goroutine and channel':
        has_goroutine = any(toktype == Token.Keyword and tok == 'go' for toktype, tok in tokens)
        has_channel = any(toktype == Token.Keyword.Declaration and tok == 'chan' for toktype, tok in tokens)
        has_channel_op = any(toktype == Token.Operator and tok == '<-' for toktype, tok in tokens)
        return has_goroutine and has_channel and has_channel_op
    elif advanced_syntax.lower() == 'defer statement':
        return any(toktype == Token.Keyword and tok == 'defer' for toktype, tok in tokens)
    else:
        return False


def check_kotlin_advanced_syntax(code, advanced_syntax):
    SUPPORTED_SYNTAX = ['lambda expression', 'when expression']
    if advanced_syntax.lower() not in SUPPORTED_SYNTAX:
        return False

    def find_lambda_expression(node):
        if node.type == "lambda_literal":
            return True
        for child in node.children:
            if find_lambda_expression(child):
                return True
        return False

    def find_when_expression(node):
        if node.type == "when_expression":
            return True
        return any(find_when_expression(child) for child in node.children)

    parser = Parser(KOTLIN_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node
    if advanced_syntax.lower() == 'lambda expression':
        return find_lambda_expression(root)
    elif advanced_syntax.lower() == 'when expression':
        return find_when_expression(root)
    else:
        return False


def check_rust_advanced_syntax(code, advanced_syntax):
    SUPPORTED_SYNTAX = ['match expression', 'if let syntax sugar', 'closures']
    if advanced_syntax.lower() not in SUPPORTED_SYNTAX:
        return False

    def find_match_expression(node):
        if node.type == 'match_expression':
            return True
        return any(find_match_expression(child) for child in node.children)
    
    def find_if_let_syntax_suger(node):
        if node.type == 'if_expression':
            for child in node.children:
                if child.type == 'let_condition':
                    return True
        return any(find_if_let_syntax_suger(child) for child in node.children)

    def find_closure(node):
        if node.type == 'closure_expression':
            return True
        return any(find_closure(child) for child in node.children)
    
    parser = Parser(RUST_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node
    if advanced_syntax.lower() == 'if let syntax sugar':
        return find_if_let_syntax_suger(root)
    elif advanced_syntax.lower() == 'match expression':
        return find_match_expression(root)
    elif advanced_syntax.lower() == 'closures':
        return find_closure(root)
    else:
        return False
    

def check_contain_function(generation, answer):
    """
    Check if the generated code contains the specified function

    :param generation: generated code
    :param answer: standard answer: language type; function name
    :return: True means yes, False means no
    """
    language_type, function_name = answer.split(';')
    if language_type.lower() == 'c#':
        language_type = 'csharp'
    
    generation = remove_comments(generation, language_type)
    
    return globals()[f"contain_{language_type.lower()}_function"](
        generation,
        function_name
    )


def contain_python_function(code, function_name):
    if '.' in function_name:
        function_name = function_name.split('.')[-1]
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    class FunctionCallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.found = False

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                self.found = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                self.found = True
            self.generic_visit(node)

    visitor = FunctionCallVisitor()
    visitor.visit(tree)
    return visitor.found


def contain_java_function(code, function_name):  
    if '.' in function_name:
        function_name = function_name.split('.')[-1]

    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    def find_method_invocation(node):
        if node.type == "method_invocation":
            for child in node.children:
                if child.type == "identifier" and code[child.start_byte:child.end_byte] == function_name:
                    return True
        for child in node.children:
            if find_method_invocation(child):
                return True
        return False
    
    return find_method_invocation(root_node)


def contain_javascript_function(code, function_name):  
    if '.' in function_name:
        function_name = function_name.split('.')[-1]

    parser = Parser(JAVASCRIPT_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    def find_function_call(node):
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee is not None:
                if callee.type == "identifier":
                    name = code[callee.start_byte:callee.end_byte]
                    if name == function_name:
                        return True
                elif callee.type == "member_expression":
                    member = callee.child_by_field_name("property")
                    if member is not None and code[member.start_byte:member.end_byte] == function_name:
                        return True

        for child in node.children:
            if find_function_call(child):
                return True
        return False

    return find_function_call(root_node)


def contain_rust_function(code, function_name):  
    if ':' in function_name:
        function_name = function_name.split(':')[-1]

    parser = Parser(RUST_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    def find_function_call(node):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                if func_node.type == "identifier":
                    name = code[func_node.start_byte:func_node.end_byte]
                    if name == function_name:
                        return True
                elif func_node.type == "field_expression":
                    field = func_node.child_by_field_name("field")
                    if field and code[field.start_byte:field.end_byte] == function_name:
                        return True
                elif func_node.type == "scoped_identifier":
                    name = func_node.child_by_field_name("name")
                    if name and code[name.start_byte:name.end_byte] == function_name:
                        return True

        for child in node.children:
            if find_function_call(child):
                return True
        return False

    return find_function_call(root_node)


def contain_go_function(code, function_name):  
    if '.' in function_name:
        function_name = function_name.split('.')[-1]

    parser = Parser(GO_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    def find_function_call(node):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                if func_node.type == "identifier":
                    name = code[func_node.start_byte:func_node.end_byte]
                    if name == function_name:
                        return True
                elif func_node.type == "selector_expression":
                    sel = func_node.child_by_field_name("field")
                    if sel and code[sel.start_byte:sel.end_byte] == function_name:
                        return True

        for child in node.children:
            if find_function_call(child):
                return True
        return False

    return find_function_call(root_node)


def contain_cpp_function(code, function_name):  
    if ':' in function_name:
        function_name = function_name.split(':')[-1]

    parser = Parser(CPP_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    def find_function_call(node) -> bool:
        # Look only at call_expressions
        if node.type == "call_expression":
            fn = node.child_by_field_name("function")
            if fn:
                text = code[fn.start_byte:fn.end_byte]
                # direct call: foo()
                if fn.type == "identifier" and text == function_name:
                    return True
                # namespace or class-qualified: ns::foo(), MyClass::bar()
                if fn.type in ("scoped_identifier", "qualified_identifier"):
                    # split on C++ scope operator and compare last segment
                    if text.split("::")[-1] == function_name:
                        return True
                # member call: obj.foo() or ptr->foo()
                if fn.type == "field_expression":
                    member = fn.child_by_field_name("field")
                    if member and code[member.start_byte:member.end_byte] == function_name:
                        return True

        # Recurse into children
        for child in node.children:
            if find_function_call(child):
                return True
        return False

    return find_function_call(root_node)


def contain_csharp_function(code, function_name):  
    if '.' in function_name:
        function_name = function_name.split('.')[-1]

    parser = Parser(C_SHARP_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root_node = tree.root_node

    query_str = """
    (invocation_expression
      function: [
        (member_access_expression
          name: (identifier) @func)
        (identifier) @func
      ])
    """
    query = parser.language.query(query_str)
    query_func = query.captures(root_node).get('func')
    if not query_func:
        return False
    
    for node in query_func:
        if node.text.decode('utf-8') == function_name:
            return True
    return False


def check_contain_library(generation, answer):
    """
    Check if the generated code contains the specified library

    :param generation: generated code
    :param answer: standard answer: language type; library name
    :return: True means yes, False means no
    """
    language_type, library = answer.split(';')
    
    return globals()[f"contain_{language_type.lower()}_library"](
        generation,
        library
    )


def contain_python_library(code, library_name):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == library_name:
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] == library_name:
                return True
    return False


def contain_javascript_library(code, lib_name):
    parser = Parser(JAVASCRIPT_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    def check_node(node):
        if node.type == 'import_statement':
            for child in node.children:
                if child.type == 'string':
                    if lib_name in child.text.decode('utf-8').strip('"\''):
                        return True
        if node.type == 'call_expression':
            func = node.child_by_field_name('function')
            if func and func.text.decode() == 'require':
                args = node.child_by_field_name('arguments')
                if args:
                    for child in args.children:
                        if child.type == 'string':
                            if lib_name in child.text.decode('utf-8').strip('"\''):
                                return True
        for child in node.children:
            if check_node(child):
                return True
        return False

    return check_node(root)


def contain_typescript_library(code, lib_name):
    parser = Parser(TYPESCRIPT_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    def check_node(node):
        if node.type == 'import_statement':
            for child in node.children:
                if child.type == 'string':
                    import_path = child.text.decode('utf-8').strip('"\'')
                    if lib_name in import_path:
                        return True
        elif node.type == 'call_expression':
            function = node.child_by_field_name('function')
            if function and function.text.decode('utf-8') == 'require':
                args = node.child_by_field_name('arguments')
                if args:
                    for child in args.children:
                        if child.type == 'string':
                            require_path = child.text.decode('utf-8').strip('"\'')
                            if lib_name in require_path:
                                return True
        for child in node.children:
            if check_node(child):
                return True
        return False

    return check_node(root)


def contain_go_library(code, lib_name):
    parser = Parser(GO_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    def extract_import_path(import_spec_node):
        for child in import_spec_node.children:
            if child.type == 'interpreted_string_literal':
                for grandchild in child.children:
                    if grandchild.type == 'interpreted_string_literal_content':
                        path = grandchild.text.decode('utf-8')
                        if lib_name in path:
                            return True
        return False

    def check_node(node):
        if node.type == 'import_declaration':
            for child in node.children:
                if child.type == 'import_spec':
                    if extract_import_path(child):
                        return True
                elif child.type == 'import_spec_list':
                    for import_spec in child.children:
                        if import_spec.type == 'import_spec' and extract_import_path(import_spec):
                            return True
        for child in node.children:
            if check_node(child):
                return True
        return False

    return check_node(root)


def contain_rust_library(code, lib_name):
    parser = Parser(RUST_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def check_node(node):
        if node.type in ['extern_crate_declaration', 'use_declaration']:
            text = node.text.decode('utf-8')
            if lib_name in text:
                return True
        for child in node.children:
            if check_node(child):
                return True
        return False

    return check_node(root)


def check_language_version(generation, answer):
    """
    Check if the generated code is of the specified language version

    :param generation: generated code
    :param answer: language type and version separated by semicolons, such as `rust;1.86.0`
    :return: True for yes, False for no
    """
    language_type, version = answer.split(';')
    return globals()[f"check_{language_type.lower()}_version"](generation, version)


def check_rust_version(code, version):
    SUPPORTED_VERSION = ['1.87.0', '1.86.0', '1.85.0', '1.78.0', '1.74.0', '1.70.0', '1.60.0']
    if version not in SUPPORTED_VERSION:
        return False
    return check_rust_compilation(code, version)


def check_python_version(code, version):
    SUPPORTED_VERSION = ['3.13', '3.10', '3.8']
    if not any(version.startswith(v) for v in SUPPORTED_VERSION):
        return False
    
    compile_version = {
        '3.13': '3.13.3',
        '3.10': '3.10.17',
        '3.8': '3.8.20'
    }
    pyenv_root = os.environ.get("PYENV_ROOT", os.path.expanduser("~/.pyenv"))
    python_path = os.path.join(pyenv_root, "versions", compile_version[version], "bin", "python")

    if not os.path.exists(python_path):
        return False
    
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            [python_path, "-m", "py_compile", temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        return success
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        return False
    finally:
        os.remove(temp_path)


def check_java_version(code, version):
    SUPPORTED_VERSION = ['jdk11', 'jdk17', 'jdk21']
    if not version in SUPPORTED_VERSION:
        return False
    
    java_versions = {
        "jdk11": "/usr/lib/jvm/java-11-openjdk-amd64",
        "jdk17": "/usr/lib/jvm/java-17-openjdk-amd64",
        "jdk21": "/usr/lib/jvm/java-21-openjdk-amd64"
    }
    java_home = java_versions[version]

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "Test.java")
        with open(file_path, "w") as f:
            f.write(code)

        env = os.environ.copy()
        env["JAVA_HOME"] = java_home
        env["PATH"] = os.path.join(java_home, "bin") + os.pathsep + env["PATH"]

        try:
            result = subprocess.run(
                ["javac", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                env=env,
                text=True
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False


def check_rust_compilation(code, rust_version):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "temp_check.rs")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            result = subprocess.run(
                [
                    "rustup", "run", rust_version, "rustc",
                    "--crate-type=lib", "--emit=metadata", file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            return success
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            return False

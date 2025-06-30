import ast
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser
from util import remove_comments
from syntax import check_contain_function


CPP_LANGUAGE = Language(tscpp.language())
GO_LANGUAGE =Language(tsgo.language())
JAVA_LANGUAGE = Language(tsjava.language())
RUST_LANGUAGE = Language(tsrust.language())
BUILTIN_STRUCTURES = {"list", "dict", "set", "tuple", "heapq"}
STDLIB_STRUCTURES = {"collections.deque", "collections.defaultdict", "collections.OrderedDict", "collections.Counter", "queue.Queue"}


def evaluate_data_structure(generation, answer, constraint):
    if constraint == 'type':
        return check_data_structure_type(generation, answer)
    elif constraint == 'size':
        return check_data_structure_size(generation, answer)
    elif constraint == 'operation':
        return check_data_structure_operation(generation, answer)
    else:
        return False


def check_data_structure_type(generation, answer):
    language, typ = answer.split(';')
    return globals()[f"check_{language.lower()}_data_structure"](remove_comments(generation, language), typ)
    

def check_python_data_structure(code, name):
    found_types = extract_python_data_structures(code)
    return name.lower() in {t.lower() for t in found_types}
    

def check_java_data_structure(code, data_structure):
    found_types = extract_java_data_structure(code)
    return data_structure.lower() in found_types


def check_cpp_data_structure(code, data_structure):
    found_types = extract_cpp_data_structure(code)
    return data_structure.lower() in found_types


def check_rust_data_structure(code, data_structure):
    found_types = extract_rust_data_structure(code)
    return data_structure.lower() in found_types


def check_go_data_structure(code, data_structure):
    found_types = extract_go_data_structure(code)
    return data_structure.lower() in found_types


def check_data_structure_size(generation, answer):
    language, typ, size_str = answer.split(';')
    size = int(size_str.strip())
    return globals()[f"check_{language.lower()}_data_structure_size"](remove_comments(generation, language), typ, size)


def check_python_data_structure_size(code, name, size):
    found_types = extract_python_data_structures(code)
    return name.lower() in {t.lower() for t in found_types} and str(size) in code


def check_java_data_structure_size(code, name, size):
    found_types = extract_java_data_structure(code)
    return name.lower() in found_types and str(size) in code


def check_cpp_data_structure_size(code, name, size):
    found_types = extract_cpp_data_structure(code)
    return name.lower() in found_types and str(size) in code


def check_rust_data_structure_size(code, name, size):
    found_types = extract_rust_data_structure(code)
    return name in found_types and str(size) in code


def check_go_data_structure_size(code, name, size):
    found_types = extract_go_data_structure(code)
    return name in found_types and str(size) in code


def check_data_structure_operation(generation, answer):
    language, typ, op_list_str = answer.split(';')
    op_list = ast.literal_eval(op_list_str.strip())
    return globals()[f"check_{language.lower()}_data_structure_operation"](remove_comments(generation, language), typ, op_list)


def check_python_data_structure_operation(code, name, op_list):
    found_types = extract_python_data_structures(code)
    op_matched = all(check_contain_function(code, f"python;{func_name}") for func_name in op_list)
    return name.lower() in {t.lower() for t in found_types} and op_matched


def check_java_data_structure_operation(code, name, op_list):
    found_types = extract_java_data_structure(code)
    op_matched = all(check_contain_function(code, f"java;{func_name}") for func_name in op_list)
    return name.lower() in found_types and op_matched


def check_cpp_data_structure_operation(code, name, op_list):
    found_types = extract_cpp_data_structure(code)
    op_matched = all(check_contain_function(code, f"cpp;{func_name}") for func_name in op_list)
    return name.lower() in found_types and op_matched


def check_rust_data_structure_operation(code, name, op_list):
    found_types = extract_rust_data_structure(code)
    op_matched = all(check_contain_function(code, f"rust;{func_name}") for func_name in op_list)
    return name.lower() in found_types and op_matched


def check_go_data_structure_operation(code, name, op_list):
    found_types = extract_go_data_structure(code)
    op_matched = all(check_contain_function(code, f"go;{func_name}") for func_name in op_list)
    return name.lower() in found_types and op_matched


class DataStructureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.structures = set()
        self.import_aliases = {}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "collections":
                self.import_aliases[alias.asname or "collections"] = "collections"
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == "collections":
            for alias in node.names:
                full_name = f"collections.{alias.name}"
                self.structures.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BUILTIN_STRUCTURES:
                self.structures.add(node.func.id)

        elif isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name):
                full_name = f"{self.import_aliases.get(value.id, value.id)}.{node.func.attr}"
                if full_name in STDLIB_STRUCTURES:
                    self.structures.add(full_name)

        self.generic_visit(node)

def extract_python_data_structures(code):
    try:
        tree = ast.parse(code)
        visitor = DataStructureVisitor()
        visitor.visit(tree)
        return visitor.structures
    except SyntaxError:
        return set()


def extract_java_data_structure(code):
    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(code.encode('utf8'))
    root_node = tree.root_node

    query = JAVA_LANGUAGE.query("""(type_identifier) @type""")
    captures = query.captures(root_node)
    found_types = set()
    for capture_name, nodes in captures.items():
        if capture_name == 'type':
            for node in nodes:
                type_name = node.text.decode()
                found_types.add(type_name.lower())
    
    return found_types


def extract_cpp_data_structure(code):
    parser = Parser(CPP_LANGUAGE)
    tree = parser.parse(code.encode('utf8'))
    root_node = tree.root_node
    
    query = CPP_LANGUAGE.query("""(type_identifier) @type""")
    captures = query.captures(root_node)
    found_types = set()

    for capture_name, nodes in captures.items():
        if capture_name == "type":
            for node in nodes:
                tname = node.text.decode()
                found_types.add(tname.lower())
    
    return found_types


def extract_rust_data_structure(code):
    parser = Parser(RUST_LANGUAGE)
    tree = parser.parse(code.encode('utf8'))
    root_node = tree.root_node

    query = RUST_LANGUAGE.query(f"""(type_identifier) @type""")

    captures = query.captures(root_node)
    found_types = set()

    for capture_name, nodes in captures.items():
        if capture_name == "type":
            for node in nodes:
                tname = node.text.decode()
                found_types.add(tname.lower())
    
    return found_types


def extract_go_data_structure(code):
    parser = Parser(GO_LANGUAGE)
    tree = parser.parse(code.encode("utf8"))
    root_node = tree.root_node

    query = GO_LANGUAGE.query("""(type_identifier) @type""")
    
    captures = query.captures(root_node)
    found_types = set()

    for capture_name, nodes in captures.items():
        if capture_name == "type":
            for node in nodes:
                tname = node.text.decode()
                found_types.add(tname.lower())
    
    return found_types

import ast
import re
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser
from util import remove_comments


JAVA = Language(tsjava.language())
CPP = Language(tscpp.language())
RUST = Language(tsrust.language())
GO = Language(tsgo.language())


def evaluate_input_output(generation, answer, constraint):
    if constraint == 'input_type':
        return check_input_type(generation, answer)
    # elif constraint == 'input_range':
    #     return check_input_range(generation, answer)
    elif constraint == 'input_order':
        return check_input_order(generation, answer)
    elif constraint == 'output_type':
        return check_output_type(generation, answer)
    # elif constraint == 'output_range':
    #     return check_output_range(generation, answer)
    elif constraint == 'output_order':
        return check_output_order(generation, answer)
    else:
        return False


def check_input_type(generation, answer):
    SUPPORTED_TYPE = ['List', 'Set', 'Map', 'Tuple', 'Matrix', 'Tree', 'Graph', 'Struct', 'String', 'JSONObject', 'Boolean', 'Integer', 'Float']
    language, func_name, input_type = answer.split(';')
    if input_type not in SUPPORTED_TYPE:
        if 'Struct:' not in input_type:
            return False
    
    return globals()[f"check_{language.lower()}_input_type"](
        remove_comments(generation, language),
        func_name,
        input_type
    )


def check_python_input_type(code, func_name, input_type):
    TYPE_MAPPING = {
        'List': {'List', 'list'},
        'Set': {'Set', 'set'},
        'Map': {'Dict', 'dict', 'Map'},
        'Tuple': {'Tuple', 'tuple'},
        'String': {'str', 'String'},
        'JSONObject': {'dict', 'Dict'},
        'Boolean': {'bool'},
        'Integer': {'int'},
        'Float': {'float'},
    }
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Code parse error: {e}")
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for arg in node.args.args:
                if arg.annotation:
                    annotation = ast.unparse(arg.annotation)

                    if input_type == 'Matrix':
                        if 'list' in annotation.lower():
                            if annotation.count('[') >= 2:
                                return True
                    
                    elif input_type == 'Tree':
                        if 'tree' in annotation.lower():
                            return True
                    
                    elif input_type == 'Graph':
                        if 'graph' in annotation.lower() or 'adj' in annotation.lower():
                            return True
                    
                    elif input_type.startswith('Struct:'):
                        struct_name = input_type.split(':', 1)[1]
                        if struct_name in annotation:
                            return True

                    else:
                        for mapped_type in TYPE_MAPPING.get(input_type, set()):
                            if annotation.startswith(mapped_type):
                                return True
    return False


def check_java_input_type(code, func_name, input_type):
    TYPE_MAPPING = {
        'List': {'List', 'ArrayList', 'LinkedList'},
        'Set': {'Set', 'HashSet', 'TreeSet', 'LinkedHashSet'},
        'Map': {'Map', 'HashMap', 'TreeMap', 'LinkedHashMap'},
        'Tuple': {'Pair', 'Triple', 'AbstractMap.SimpleEntry'},
        'String': {'String'},
        'JSONObject': {
            'JSONObject',
            'org.json.JSONObject',
            'com.google.gson.JsonObject',
            'com.fasterxml.jackson.databind.node.ObjectNode'
        },
        'Boolean': {'boolean', 'Boolean'},
        'Integer': {'int', 'Integer', 'long', 'Long', 'short', 'Short'},
        'Float': {'float', 'Float', 'double', 'Double'},
    }

    parser = Parser(JAVA)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)

    def find_method_parameters():
        result = []
        for node in walk(root):
            if node.type == 'method_declaration':
                method_name_node = node.child_by_field_name('name')
                if method_name_node and get_node_text(method_name_node) == func_name:
                    param_node = node.child_by_field_name('parameters')
                    if param_node:
                        for child in param_node.children:
                            if child.type == 'formal_parameter':
                                type_node = child.child_by_field_name('type')
                                if type_node:
                                    result.append(get_node_text(type_node))
        return result

    param_types = find_method_parameters()
    for param_type in param_types:
        if input_type == 'Matrix':
            if (('List' in param_type or 'ArrayList' in param_type or 'LinkedList' in param_type or 'Array' in param_type) 
                and param_type.count('<') >= 2) or '[][]' in param_type:
                return True
            
        elif input_type == 'Tree':
            if 'tree' in param_type.lower():
                return True
            
        elif input_type == 'Graph':
            if 'graph' in param_type.lower() or 'adj' in param_type.lower():
                return True
            
        elif input_type.startswith('Struct:'):
            struct_name = input_type.split(':', 1)[1]
            if struct_name in param_type:
                return True
            
        else:
            for match_type in TYPE_MAPPING.get(input_type, set()):
                if match_type in param_type:
                    return True
    return False


def check_cpp_input_type(code, func_name, input_type):
    TYPE_MAPPING = {
        'Set': {'std::set', 'std::unordered_set', 'set', 'unordered_set'},
        'Map': {'std::map', 'std::unordered_map', 'map', 'unordered_map'},
        'Tuple': {'std::pair', 'std::tuple', 'pair', 'tuple'},
        'String': {'std::string', 'string'},
        'JSONObject': {'nlohmann::json', 'Json::Value', 'json'},
        'Boolean': {'bool'},
        'Integer': {'int', 'long', 'short', 'size_t', 'uint32_t', 'int64_t', 'int32_t'},
        'Float': {'float', 'double'},
    }
    parser = Parser(CPP)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)
    
    def find_function_parameters():
        result = []
        for node in walk(root):
            if node.type == 'function_definition':
                decl = node.child_by_field_name('declarator')
                if decl:
                    # declarator -> function_declarator -> identifier
                    identifier_node = None
                    if decl.type == 'function_declarator':
                        identifier_node = decl.child_by_field_name('declarator')
                    elif decl.type == 'identifier':
                        identifier_node = decl

                    if identifier_node and get_node_text(identifier_node) == func_name:
                        params = decl.child_by_field_name('parameters')
                        if params:
                            for param in params.children:
                                if param.type == 'parameter_declaration':
                                    type_node = param.child_by_field_name('type')
                                    decl_node = param.child_by_field_name('declarator')
                                    if type_node:
                                        base_type = get_node_text(type_node)
                                        is_array = False
                                        
                                        # detect array usage in declarator, like num[]
                                        if decl_node:
                                            for child in walk(decl_node):
                                                if child.type == 'array_declarator':
                                                    is_array = True
                                                    break

                                        result.append((base_type, is_array))
        return result

    param_types = find_function_parameters()
    for param_type, is_arr in param_types:
        if input_type == 'Matrix':
            if ('vector' in param_type and param_type.count('<') >= 2) or is_arr:
                return True

        elif input_type == 'List':
            if 'vector' in param_type or 'list' in param_type or is_arr:
                return True
        
        elif input_type == 'Tree':
            if 'tree' in param_type.lower():
                return True

        elif input_type == 'Graph':
            if 'graph' in param_type.lower() or 'adj' in param_type.lower():
                return True

        elif input_type.startswith('Struct:'):
            struct_name = input_type.split(':', 1)[1]
            if struct_name in param_type:
                return True

        else:
            for match_type in TYPE_MAPPING.get(input_type, set()):
                if match_type in param_type:
                    return True
    return False


def check_rust_input_type(code, func_name, input_type):
    TYPE_MAPPING = {
        'List': {'Vec', 'vec', 'LinkedList'},
        'Set': {'HashSet', 'BTreeSet'},
        'Map': {'HashMap', 'BTreeMap'},
        'Tuple': {'(', 'tuple'},
        'String': {'String', '&str', 'str'},
        'JSONObject': {'serde_json::Value', 'serde_json::Map'},
        'Boolean': {'bool'},
        'Integer': {'i32', 'i64', 'u32', 'u64', 'usize', 'isize', 'i16', 'u16', 'i8', 'u8'},
        'Float': {'f32', 'f64'},
    }
    parser = Parser(RUST)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node
    
    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)
    
    def find_function_params():
        result = []
        for node in walk(root):
            if node.type == 'function_item':
                ident = node.child_by_field_name('name')
                if ident and get_node_text(ident) == func_name:
                    param_list = node.child_by_field_name('parameters')
                    if param_list:
                        for param in param_list.children:
                            if param.type == 'parameter':
                                type_node = param.child_by_field_name('type')
                                if type_node:
                                    result.append(get_node_text(type_node).strip())
        return result

    param_types = find_function_params()
    for param_type in param_types:
        if input_type == 'Matrix':
            if 'Vec' in param_type and param_type.count('<') >= 2:
                return True

        elif input_type == 'Tree':
            if 'tree' in param_type.lower():
                return True

        elif input_type == 'Graph':
            if 'graph' in param_type.lower() or 'adj' in param_type.lower():
                return True

        elif input_type.startswith('Struct:'):
            struct_name = input_type.split(':', 1)[1]
            if struct_name in param_type:
                return True

        else:
            for match_type in TYPE_MAPPING.get(input_type, set()):
                if match_type in param_type:
                    return True

    return False


def check_output_type(generation, answer):
    SUPPORTED_TYPE = ['List', 'Set', 'Map', 'Tuple', 'Matrix', 'Tree', 'Graph', 'Struct', 'String', 'JSONObject', 'Boolean', 'Integer', 'Float']
    language, func_name, output_type = answer.split(';')
    if output_type not in SUPPORTED_TYPE:
        if 'Struct:' not in output_type:
            return False
    
    return globals()[f"check_{language.lower()}_output_type"](
        remove_comments(generation, language),
        func_name,
        output_type
    )


def check_python_output_type(code, func_name, output_type):
    TYPE_MAPPING = {
        'List': {'List', 'list'},
        'Set': {'Set', 'set'},
        'Map': {'Dict', 'dict', 'Map'},
        'Tuple': {'Tuple', 'tuple'},
        'String': {'str', 'String'},
        'JSONObject': {'dict', 'Dict'},
        'Boolean': {'bool'},
        'Integer': {'int'},
        'Float': {'float'},
    }
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Code parse error: {e}")
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if node.returns:
                annotation = ast.unparse(node.returns)

                if output_type == 'Matrix':
                    if 'list' in annotation.lower() and annotation.count('[') >= 2:
                        return True

                elif output_type == 'Tree':
                    if 'tree' in annotation.lower():
                        return True

                elif output_type == 'Graph':
                    if 'graph' in annotation.lower() or 'adj' in annotation.lower():
                        return True

                elif output_type.startswith('Struct:'):
                    struct_name = output_type.split(':', 1)[1]
                    if struct_name in annotation:
                        return True

                else:
                    for mapped_type in TYPE_MAPPING.get(output_type, set()):
                        if annotation.startswith(mapped_type):
                            return True
    return False


def check_java_output_type(code, func_name, output_type):
    TYPE_MAPPING = {
        'List': {'List', 'ArrayList', 'LinkedList'},
        'Set': {'Set', 'HashSet', 'TreeSet', 'LinkedHashSet'},
        'Map': {'Map', 'HashMap', 'TreeMap', 'LinkedHashMap'},
        'Tuple': {'Pair', 'Triple', 'AbstractMap.SimpleEntry'},
        'String': {'String'},
        'JSONObject': {
            'JSONObject',
            'org.json.JSONObject',
            'com.google.gson.JsonObject',
            'com.fasterxml.jackson.databind.node.ObjectNode'
        },
        'Boolean': {'boolean', 'Boolean'},
        'Integer': {'int', 'Integer', 'long', 'Long', 'short', 'Short'},
        'Float': {'float', 'Float', 'double', 'Double'},
    }
    parser = Parser(JAVA)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    for node in walk(root):
        if node.type == 'method_declaration':
            method_name_node = node.child_by_field_name('name')
            if method_name_node and get_node_text(method_name_node) == func_name:
                type_node = node.child_by_field_name('type')
                if type_node:
                    return_type = get_node_text(type_node)

                    if output_type == 'Matrix':
                        if (('List' in return_type or 'ArrayList' in return_type or 'LinkedList' in return_type or 'Array' in return_type) 
                            and return_type.count('<') >= 2) or '[][]' in return_type:
                            return True
                    
                    elif output_type == 'Tree':
                        if 'tree' in return_type.lower():
                            return True
                    
                    elif output_type == 'Graph':
                        if 'graph' in return_type.lower() or 'adj' in return_type.lower():
                            return True
                    
                    elif output_type.startswith('Struct:'):
                        struct_name = output_type.split(':', 1)[1]
                        if struct_name in return_type:
                            return True
                    
                    else:
                        for mapped_type in TYPE_MAPPING.get(output_type, set()):
                            if mapped_type in return_type:
                                return True
    return False


def check_cpp_output_type(code, func_name, output_type):
    TYPE_MAPPING = {
        'Set': {'std::set', 'std::unordered_set', 'set', 'unordered_set'},
        'Map': {'std::map', 'std::unordered_map', 'map', 'unordered_map'},
        'Tuple': {'std::pair', 'std::tuple', 'pair', 'tuple'},
        'String': {'std::string', 'string'},
        'JSONObject': {'nlohmann::json', 'Json::Value', 'json'},
        'Boolean': {'bool'},
        'Integer': {'int', 'long', 'short', 'size_t', 'uint32_t', 'int64_t', 'int32_t'},
        'Float': {'float', 'double'},
    }
    parser = Parser(CPP)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    for node in walk(root):
        if node.type == 'function_definition':
            decl = node.child_by_field_name('declarator')
            type_node = node.child_by_field_name('type')
            if decl and type_node:
                func_name_node = None
                if decl.type == 'function_declarator':
                    func_name_node = decl.child_by_field_name('declarator')
                elif decl.type == 'identifier':
                    func_name_node = decl

                if func_name_node and get_node_text(func_name_node) == func_name:
                    return_type = get_node_text(type_node)

                    if output_type == 'Matrix':
                        if ('vector' in return_type and return_type.count('<') >= 2) or '[][]' in return_type:
                            return True

                    elif output_type == 'List':
                        if 'vector' in return_type or 'list' in return_type:
                            return True

                    elif output_type == 'Tree':
                        if 'tree' in return_type.lower():
                            return True

                    elif output_type == 'Graph':
                        if 'graph' in return_type.lower() or 'adj' in return_type.lower():
                            return True

                    elif output_type.startswith('Struct:'):
                        struct_name = output_type.split(':', 1)[1]
                        if struct_name in return_type:
                            return True

                    else:
                        for mapped_type in TYPE_MAPPING.get(output_type, set()):
                            if mapped_type in return_type:
                                return True
    return False


def check_rust_output_type(code, func_name, output_type):
    TYPE_MAPPING = {
        'List': {'Vec', 'vec', 'LinkedList'},
        'Set': {'HashSet', 'BTreeSet'},
        'Map': {'HashMap', 'BTreeMap'},
        'Tuple': {'(', 'tuple'},
        'String': {'String', '&str', 'str'},
        'JSONObject': {'serde_json::Value', 'serde_json::Map'},
        'Boolean': {'bool'},
        'Integer': {'i32', 'i64', 'u32', 'u64', 'usize', 'isize', 'i16', 'u16', 'i8', 'u8'},
        'Float': {'f32', 'f64'},
    }

    parser = Parser(RUST)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node

    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    def find_return_type():
        for node in walk(root):
            if node.type == 'function_item':
                ident = node.child_by_field_name('name')
                if ident and get_node_text(ident) == func_name:
                    ret_node = node.child_by_field_name('return_type')
                    if ret_node:
                        return get_node_text(ret_node).strip()
        return None

    ret_type = find_return_type()
    if not ret_type:
        return False

    if output_type == 'Matrix':
        if 'Vec' in ret_type and ret_type.count('<') >= 2:
            return True

    elif output_type == 'Tree':
        if 'tree' in ret_type.lower():
            return True

    elif output_type == 'Graph':
        if 'graph' in ret_type.lower() or 'adj' in ret_type.lower():
            return True

    elif output_type.startswith('Struct:'):
        struct_name = output_type.split(':', 1)[1]
        if struct_name in ret_type:
            return True

    else:
        for match_type in TYPE_MAPPING.get(output_type, set()):
            if match_type in ret_type:
                return True

    return False


def check_input_order(generation, answer):
    language, func_name, inputs = answer.split(';')
    input_list = inputs.strip('[]').split(',')
    
    return globals()[f"check_{language.lower()}_input_order"](
        remove_comments(generation, language),
        func_name,
        input_list
    )


def check_python_input_order(code, func_name, input_list):
    def get_function_param_annotations(code, func_name):
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    annotations = []
                    for arg in node.args.args:
                        if arg.annotation:
                            annotations.append(ast.unparse(arg.annotation))
                        else:
                            annotations.append('None')
                    return annotations
        except SyntaxError:
            return []
    
    param_list = get_function_param_annotations(code, func_name)
    if len(param_list) != len(input_list):
        return False
    
    for index, param in enumerate(param_list):
        if 'map' in input_list[index].lower():
            map_keywords = ['dict', 'map']
            if any(param.lower().startswith(k) for k in map_keywords):
                continue
            return False
        
        elif 'matrix' in input_list[index].lower():
            if param.lower().startswith('list') and param.count('[') >= 2:
                continue
            return False
        
        elif 'graph' in input_list[index].lower():
            graph_keywords = ['graph', 'adj']
            if any(k in param.lower() for k in graph_keywords):
                continue
            return False
        
        else:
            if not param.lower().startswith(input_list[index].lower()):
                return False
    return True


def check_java_input_order(code, func_name, input_list):
    STRUCT_MAP = {
        'list': {'List', 'ArrayList', 'LinkedList'},
        'set': {'Set', 'HashSet', 'TreeSet', 'LinkedHashSet'},
        'map': {'Map', 'HashMap', 'TreeMap', 'LinkedHashMap'},
        'tuple': {'Pair', 'Triple', 'AbstractMap.SimpleEntry'},
        'string': {'String'},
        'jsonobject': {'JSONObject', 'org.json.JSONObject', 'com.google.gson.JsonObject', 'com.fasterxml.jackson.databind.node.ObjectNode'},
        'boolean': {'boolean', 'Boolean'},
        'integer': {'int', 'Integer', 'long', 'Long', 'short', 'Short'},
        'float': {'float', 'Float', 'double', 'Double'},
        'tree': {'Tree', 'BinaryTree', 'Node', 'node'},
    }
    parser = Parser(JAVA)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)

    def find_method_parameters():
        result = []
        for node in walk(root):
            if node.type == 'method_declaration':
                method_name_node = node.child_by_field_name('name')
                if method_name_node and get_node_text(method_name_node) == func_name:
                    param_node = node.child_by_field_name('parameters')
                    if param_node:
                        for child in param_node.children:
                            if child.type == 'formal_parameter':
                                type_node = child.child_by_field_name('type')
                                if type_node:
                                    result.append(get_node_text(type_node))
        return result

    param_types = find_method_parameters()
    if len(param_types) != len(input_list):
        return False
    
    for index, param in enumerate(param_types):
        if 'matrix' in input_list[index].lower():
            if not (('List' in param or 'ArrayList' in param or 'LinkedList' in param or 'Array' in param) and param.count('<') >= 2) or '[][]' in param:
                return False
            
        elif 'graph' in input_list[index].lower():
            if not 'graph' in param.lower() or 'adj' in param.lower():
                return False
            
        else:
            if not any(k.lower() in param.lower() for k in STRUCT_MAP[input_list[index].lower()]):
                return False
    return True


def check_cpp_input_order(code, func_name, input_list):
    TYPE_MAPPING = {
        'list': {'std::vector', 'vector', 'std::list', 'list'},
        'set': {'std::set', 'std::unordered_set', 'set', 'unordered_set'},
        'map': {'std::map', 'std::unordered_map', 'map', 'unordered_map'},
        'tuple': {'std::pair', 'std::tuple', 'pair', 'tuple'},
        'string': {'std::string', 'string'},
        'jsonobject': {'nlohmann::json', 'Json::Value', 'json'},
        'boolean': {'bool'},
        'integer': {'int', 'long', 'short', 'size_t', 'uint32_t', 'int64_t', 'int32_t'},
        'float': {'float', 'double'},
        'graph': {'graph', 'adj', 'node'}
    }
    parser = Parser(CPP)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)
    
    def find_function_parameters():
        result = []
        for node in walk(root):
            if node.type == 'function_definition':
                decl = node.child_by_field_name('declarator')
                if decl:
                    # declarator -> function_declarator -> identifier
                    identifier_node = None
                    if decl.type == 'function_declarator':
                        identifier_node = decl.child_by_field_name('declarator')
                    elif decl.type == 'identifier':
                        identifier_node = decl

                    if identifier_node and get_node_text(identifier_node) == func_name:
                        params = decl.child_by_field_name('parameters')
                        if params:
                            for param in params.children:
                                if param.type == 'parameter_declaration':
                                    type_node = param.child_by_field_name('type')
                                    decl_node = param.child_by_field_name('declarator')
                                    if type_node:
                                        base_type = get_node_text(type_node)
                                        is_array = False
                                        
                                        # detect array usage in declarator, like num[]
                                        if decl_node:
                                            for child in walk(decl_node):
                                                if child.type == 'array_declarator':
                                                    is_array = True
                                                    break

                                        result.append((base_type, is_array))
        return result

    param_types = find_function_parameters()
    if len(input_list) != len(param_types):
        return False
    
    for index, (param, is_arr) in enumerate(param_types):
        if 'linkedlist' in input_list[index].lower():
            linkedlist_keywords = ['node', 'linkedlist', 'list']
            if any(param.lower().startswith(k) for k in linkedlist_keywords):
                continue
            return False
        
        elif 'matrix' in input_list[index].lower():
            if ('vector' in param and param.count('<') >= 2) or is_arr:
                continue
            return False
        
        else:
            if not any(k.lower() in param.lower() for k in TYPE_MAPPING[input_list[index].lower()]):
                return False
    return True


def check_rust_input_order(code, func_name, input_list):
    TYPE_MAPPING = {
        'list': {'Vec', 'vec', 'LinkedList'},
        'set': {'HashSet', 'BTreeSet'},
        'map': {'HashMap', 'BTreeMap'},
        'tuple': {'(', 'tuple'},
        'string': {'String', '&str', 'str'},
        'jsonobject': {'serde_json::Value', 'serde_json::Map'},
        'boolean': {'bool'},
        'integer': {'i32', 'i64', 'u32', 'u64', 'usize', 'isize', 'i16', 'u16', 'i8', 'u8'},
        'float': {'f32', 'f64'},
        'graph': {'graph', 'adj'}
    }
    parser = Parser(RUST)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node
    
    def get_node_text(node):
            return code[node.start_byte:node.end_byte]

    def walk(node):
            yield node
            for child in node.children:
                yield from walk(child)
    
    def find_function_params():
        result = []
        for node in walk(root):
            if node.type == 'function_item':
                ident = node.child_by_field_name('name')
                if ident and get_node_text(ident) == func_name:
                    param_list = node.child_by_field_name('parameters')
                    if param_list:
                        for param in param_list.children:
                            if param.type == 'parameter':
                                type_node = param.child_by_field_name('type')
                                if type_node:
                                    result.append(get_node_text(type_node).strip())
        return result

    param_types = find_function_params()
    if len(param_types) != len(input_list):
        return False
    
    for index, param in enumerate(param_types):
        if not any(k.lower() in param.lower() for k in TYPE_MAPPING[input_list[index].lower()]):
            return False
    return True


def check_output_order(generation, answer):
    language, func_name, outputs = answer.split(';')
    output_list = outputs.strip('[]').split(',')
    
    return globals()[f"check_{language.lower()}_output_order"](
        remove_comments(generation, language),
        func_name,
        output_list
    )


def check_python_output_order(code, func_name, output_list):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Code parse error: {e}")
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if node.returns:
                annotation = ast.unparse(node.returns)
                matched = re.search(r'\[(.*?)\]', annotation)
                if matched:
                    return_list = [item.strip() for item in matched.group(1).split(',')]

                    if len(return_list) != len(output_list):
                        return False
                    
                    for index, ret in enumerate(return_list):
                        if not (ret in output_list[index] or output_list[index] in ret):
                            return False
                    return True
    return False


def check_rust_output_order(code, func_name, output_list):
    parser = Parser(RUST)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node

    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    def find_return_type():
        for node in walk(root):
            if node.type == 'function_item':
                ident = node.child_by_field_name('name')
                if ident and get_node_text(ident) == func_name:
                    ret_node = node.child_by_field_name('return_type')
                    if ret_node:
                        return get_node_text(ret_node).strip()
        return None

    ret_type = find_return_type()
    if not ret_type:
        ret_list = []
    else:
        ret_list = [item.strip() for item in ret_type.strip('()').split(',')]

    if len(ret_list) != len(output_list):
        return False
    
    for index, ret in enumerate(ret_list):
        if not (ret in output_list[index] or output_list[index] in ret):
            return False
    return True


def check_go_output_order(code, func_name, output_list):
    parser = Parser(GO)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node

    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    def find_return_types():
        for node in walk(root):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node and get_node_text(name_node) == func_name:
                    result_node = node.child_by_field_name('result')
                    if not result_node:
                        return []
                    
                    if result_node.type == 'type_identifier':
                        return [get_node_text(result_node)]
                    elif result_node.type == 'parameter_list':
                        return [
                            get_node_text(child.child_by_field_name('type'))
                            for child in result_node.children
                            if child.type == 'parameter_declaration'
                        ]
        return None

    actual_outputs = find_return_types()

    if not actual_outputs or len(actual_outputs) != len(output_list):
        return False
    
    for index, ret in enumerate(actual_outputs):
        if not (ret in output_list[index] or output_list[index] in ret):
            return False
    return True
    
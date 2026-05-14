import os
from tree_sitter import Parser, Language

from tree_sitter_python import language as python_language
from tree_sitter_java import language as java_language
from tree_sitter_javascript import language as js_language
from tree_sitter_cpp import language as cpp_language
from tree_sitter_go import language as go_language
from tree_sitter_rust import language as rust_language
from tree_sitter_typescript import language_typescript as ts_language
from tree_sitter_kotlin import language as kt_language
from tree_sitter_c_sharp import language as csharp_language
from tree_sitter_haskell import language as hk_language
from tree_sitter_zig import language as zig_language


LANGUAGE_MAP = {
    "python": Language(python_language()),
    "java": Language(java_language()),
    "javascript": Language(js_language()),
    "typescript": Language(ts_language()),
    "cpp": Language(cpp_language()),
    "c++": Language(cpp_language()),
    "go": Language(go_language()),
    "rust": Language(rust_language()),
    "kotlin": Language(kt_language()),
    "csharp": Language(csharp_language()),
    "c#": Language(csharp_language()),
    "haskell": Language(hk_language()),
    "zig": Language(zig_language())
}


def ast_has_error(node):
    if node.type == "ERROR" or node.is_missing:
        return True

    for child in node.children:
        if ast_has_error(child):
            return True

    return False


def check_ast(code: str, language: str):
    if not language:
        return False, "Language not specified"

    language = language.lower()

    if language not in LANGUAGE_MAP:
        return False, f"Unsupported language type: {language}"

    try:
        parser = Parser(LANGUAGE_MAP[language])
        # parser.set_language(LANGUAGE_MAP[language])
        tree = parser.parse(bytes(code, "utf8"))
    except Exception as e:
        return False, f"AST parsing exception: {e}"

    root = tree.root_node

    if root.has_error:
        return False, "AST contains syntax errors"

    if ast_has_error(root):
        return False, "AST contains ERROR or MISSING nodes"

    return True, ""


def evaluate_ast(generation, prompt, output_path="ast_results.json"):
    import json
    from util import extract_code

    total = 0
    matched = 0
    results = []

    for index, response in enumerate(generation):
        if index >= len(prompt):
            continue

        total += 1
        generated_code = extract_code(response["response"][0][1])

        language = None
        if "answer" in prompt[index]:
            answer = prompt[index]["answer"]
            if ";" in answer:
                language = answer.split(";")[0].strip()
            elif answer:
                language = answer.strip()

        success, error_msg = check_ast(generated_code, language)

        if success:
            matched += 1

        results.append({
            "id": index,
            "category": prompt[index].get("category", ""),
            "constraint": prompt[index].get("constraint", ""),
            "prompt": prompt[index].get("prompt", ""),
            "answer": prompt[index].get("answer", ""),
            "generated_code": generated_code,
            "is_matched": success,
            "error_message": error_msg if not success else ""
        })

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return total, matched

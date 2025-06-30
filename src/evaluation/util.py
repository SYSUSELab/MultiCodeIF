import re
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token


def remove_strings(code, language_type):
    """
    Remove string constants from code

    :param code: str, code
    :param language_type: str, language type
    :return: str, code after removing string constants
    """
    lexer = get_lexer_by_name(language_type.lower())
    filtered_code = []
    for token_type, token_value in lex(code, lexer):
        if token_type in Token.String:
            continue

        filtered_code.append(token_value)
    return "".join(filtered_code)


def remove_comments(code, language_type):
    """
    Remove comments from code

    :param code: str, code
    :param language_type: str, language type
    :return: str, code after removing comments
    """
    filtered_code = []
    lexer = get_lexer_by_name(language_type.lower())
    for token_type, token_value in lex(code, lexer):
        if token_type in Token.Comment:
            continue

        filtered_code.append(token_value)
    return "".join(filtered_code)


def extract_code(code):
    """
    Remove markdown from code Edit

    :param code: str, code 
    :return: str, code after removing markdown tags
    """
    code = code.strip()
    match = re.search(r"```(?:\w+)?([\s\S]*?)```", code)
    return match.group(1).strip() if match else code

import os
import tempfile
import subprocess
from guesslang import Guess
from util import extract_code


def check_compilation(code, language=None):
    if not language:
        guess = Guess()
        try:
            language = guess.language_name(code).lower()
        except Exception:
            return False, "Unable to detect language type"
    
    language = language.lower()
    
    language_handlers = {
        'python': check_python_compilation,
        'java': check_java_compilation,
        'javascript': check_javascript_compilation,
        'rust': check_rust_compilation,
        'go': check_go_compilation,
        'cpp': check_cpp_compilation,
        'c++': check_cpp_compilation,
        'c': check_c_compilation,
        'csharp': check_csharp_compilation,
        'c#': check_csharp_compilation,
        'typescript': check_typescript_compilation,
        'kotlin': check_kotlin_compilation,
        'haskell': check_haskell_compilation,
        'prolog': check_prolog_compilation,
        'lua': check_lua_compilation,
        'julia': check_julia_compilation,
        'coffeescript': check_coffeescript_compilation,
    }
    
    handler = language_handlers.get(language)
    if handler:
        return handler(code)
    else:
        return False, f"Unsupported language type: {language}"


def check_python_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['python3', '-m', 'py_compile', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
    except Exception as e:
        return False, f"Compilation error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def check_java_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "Test.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['javac', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_javascript_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['node', '--check', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except subprocess.TimeoutExpired:
        return False, "Syntax check timed out"
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ['nodejs', '--check', temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except:
            return False, "node or nodejs command not found"
    except Exception as e:
        return False, f"Syntax check error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def check_rust_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "temp_check.rs")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['rustc', '--crate-type=lib', '--emit=metadata', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_go_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "main.go")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['go', 'build', '-o', os.path.join(temp_dir, 'test_bin'), file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_cpp_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['g++', '-std=c++17', '-c', file_path, '-o', os.path.join(temp_dir, 'test.o')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_c_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.c")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['gcc', '-c', file_path, '-o', os.path.join(temp_dir, 'test.o')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_csharp_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "Test.cs")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['mcs', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ['dotnet', 'new', 'console', '--force', '--output', temp_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    text=True
                )
                program_path = os.path.join(temp_dir, 'Program.cs')
                with open(program_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                result = subprocess.run(
                    ['dotnet', 'build', temp_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    text=True
                )
                success = result.returncode == 0
                error_msg = result.stderr if not success else ""
                return success, error_msg
            except:
                return False, "C# compiler not found (mcs/csc/dotnet)"
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_typescript_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['tsc', '--noEmit', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except FileNotFoundError:
            return False, "TypeScript compiler (tsc) not found"
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_kotlin_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "Test.kt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['kotlinc', file_path, '-d', temp_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except FileNotFoundError:
            return False, "Kotlin compiler (kotlinc) not found"
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_haskell_compilation(code):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "Test.hs")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ['ghc', '-fno-code', '-fwrite-interface', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
                cwd=temp_dir
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except FileNotFoundError:
            return False, "Haskell compiler (ghc) not found"
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"


def check_prolog_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['swipl', '-g', 'halt', '-t', 'halt(1)', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except FileNotFoundError:
        return False, "Prolog interpreter (swipl) not found"
    except subprocess.TimeoutExpired:
        return False, "Syntax check timed out"
    except Exception as e:
        return False, f"Syntax check error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def check_lua_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['luac', '-p', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ['lua', '-e', f'dofile("{temp_path}")'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            success = result.returncode == 0
            error_msg = result.stderr if not success else ""
            return success, error_msg
        except:
            return False, "Lua compiler (luac) or interpreter (lua) not found"
    except subprocess.TimeoutExpired:
        return False, "Syntax check timed out"
    except Exception as e:
        return False, f"Syntax check error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def check_julia_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jl', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['julia', '--check-bounds=yes', '--compile=min', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except FileNotFoundError:
        return False, "Julia interpreter (julia) not found"
    except subprocess.TimeoutExpired:
        return False, "Syntax check timed out"
    except Exception as e:
        return False, f"Syntax check error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def check_coffeescript_compilation(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.coffee', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['coffee', '--compile', '--print', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
        return success, error_msg
    except FileNotFoundError:
        return False, "CoffeeScript compiler (coffee) not found"
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
    except Exception as e:
        return False, f"Compilation error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass


def evaluate_compilation(generation, prompt, output_path="compilation_results.json"):
    import json
    
    total = 0
    matched = 0
    results = []
    
    for index, response in enumerate(generation):
        if index >= len(prompt):
            continue
            
        total += 1
        generated_code = extract_code(response['response'][0][1])
        
        language = None
        if 'answer' in prompt[index]:
            answer = prompt[index]['answer']
            if ';' in answer:
                language = answer.split(';')[0].strip()
            elif answer:
                language = answer.strip()
        
        success, error_msg = check_compilation(generated_code, language)
        
        if success:
            matched += 1
        
        result_entry = {
            "id": index,
            "category": prompt[index].get('category', ''),
            "constraint": prompt[index].get('constraint', ''),
            "prompt": prompt[index].get('prompt', ''),
            "answer": prompt[index].get('answer', ''),
            "generated_code": generated_code,
            "is_matched": success,
            "error_message": error_msg if not success else ""
        }
        results.append(result_entry)
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return total, matched

import os
import json
import tempfile
import subprocess
import resource
import signal
import atexit
import shutil
import stat
from util import extract_code

_temp_files_to_cleanup = []
_temp_dirs_to_cleanup = []
_cleanup_in_progress = False

def _cleanup_temp_resources():
    global _cleanup_in_progress
    if _cleanup_in_progress:
        return
    _cleanup_in_progress = True
    
    try:
        for temp_file in _temp_files_to_cleanup[:]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        _temp_files_to_cleanup.clear()
        
        for temp_dir in _temp_dirs_to_cleanup[:]:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
        _temp_dirs_to_cleanup.clear()
    finally:
        _cleanup_in_progress = False

def _signal_handler(signum, frame):
    _cleanup_temp_resources()
    os._exit(1)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
if hasattr(signal, 'SIGHUP'):
    signal.signal(signal.SIGHUP, _signal_handler)

atexit.register(_cleanup_temp_resources)

def _check_disk_space(path, min_free_mb=100):
    try:
        statvfs = os.statvfs(path)
        free_bytes = statvfs.f_bavail * statvfs.f_frsize
        free_mb = free_bytes / (1024 * 1024)
        if free_mb < min_free_mb:
            raise RuntimeError(f"Insufficient disk space: Only {free_mb:.1f} MB remaining, at least {min_free_mb} MB required.")
        return True
    except AttributeError:
        return True
    except Exception as e:
        print(f"[WARN] Unable to check disk space: {e}")
        return True

def _set_resource_limits():
    try:
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
        resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except:
        pass

def _kill_process_group(pid):
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        import time
        time.sleep(0.5)
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except:
            pass
    except:
        pass


def run_functional_test(code, tests, language, function_name, timeout=5):
    if not language:
        return False, 0, len(tests), [{"error": "Language type not specified"}]
    
    language = language.lower()
    
    language_handlers = {
        'python': run_python_functional_test,
        'rust': run_rust_functional_test,
        'java': run_java_functional_test,
        'javascript': run_javascript_functional_test,
        'typescript': run_typescript_functional_test,
        'cpp': run_cpp_functional_test,
        'c++': run_cpp_functional_test,
        'go': run_go_functional_test,
        'kotlin': run_kotlin_functional_test,
        'csharp': run_csharp_functional_test,
        'c#': run_csharp_functional_test,
    }
    
    handler = language_handlers.get(language)
    if handler:
        return handler(code, tests, function_name, timeout)
    else:
        return False, 0, len(tests), [{"error": f"Unsupported Language: {language}"}]


def run_python_functional_test(code, tests, function_name, timeout):
    test_wrapper = f"""
import json
import sys

{code}

def run_tests():
    results = []
    tests = {json.dumps(tests)}
    
    for test in tests:
        test_name = test.get('name', 'Unnamed test')
        test_input = test.get('input', {{}})
        args = test_input.get('args', [])
        kwargs = test_input.get('kwargs', {{}})
        expected = test.get('expected_output')
        
        try:
            result = {function_name}(*args, **kwargs)
            passed = result == expected
            results.append({{
                'name': test_name,
                'passed': passed,
                'expected': expected,
                'actual': result,
                'error': None
            }})
        except Exception as e:
            results.append({{
                'name': test_name,
                'passed': False,
                'expected': expected,
                'actual': None,
                'error': str(e)
            }})
    
    print(json.dumps(results))

if __name__ == '__main__':
    run_tests()
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_wrapper)
        temp_path = f.name
        _temp_files_to_cleanup.append(temp_path)
    
    try:
        result = subprocess.run(
            ['python3', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout * len(tests),
            text=True,
            preexec_fn=_set_resource_limits,
            start_new_session=True
        )
        
        if result.returncode != 0:
            return False, 0, len(tests), [{"error": f"Execution Error: {result.stderr}"}]
        
        try:
            test_results = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return False, 0, len(tests), [{"error": f"Output Parser Failure: {result.stdout}"}]
        
        passed = sum(1 for r in test_results if r.get('passed', False))
        failures = [r for r in test_results if not r.get('passed', False)]
        
        return passed == len(tests), passed, len(tests), failures
        
    except subprocess.TimeoutExpired as e:
        if hasattr(e, 'process') and e.process:
            _kill_process_group(e.process.pid)
        return False, 0, len(tests), [{"error": "Test Timeout"}]
    except Exception as e:
        return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_path in _temp_files_to_cleanup:
                _temp_files_to_cleanup.remove(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass


def run_rust_functional_test(code, tests, function_name, timeout):
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        if len(args) == 1 and isinstance(args[0], bool):
            test_cases.append(f"""
    let result{i} = {function_name}({str(args[0]).lower()});
    let expected{i} = {str(expected).lower()};
    println!("{{{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": {{}}, \\\"expected\\\": {{}}, \\\"actual\\\": {{}}}}}}", 
             result{i} == expected{i}, expected{i}, result{i});
""")
    
    test_wrapper = f"""
{code}

fn main() {{
{chr(10).join(test_cases)}
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "main.rs")
        binary_path = os.path.join(temp_dir, "main")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            compile_result = subprocess.run(
                ['rustc', source_path, '-o', binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Compilation Error: {compile_result.stderr}"}]
            
            run_result = subprocess.run(
                [binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution Error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test Timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def run_javascript_functional_test(code, tests, function_name, timeout):
    test_wrapper = f"""
{code}

const tests = {json.dumps(tests)};
const results = [];

for (const test of tests) {{
    const testName = test.name || 'Unnamed test';
    const testInput = test.input || {{}};
    const args = testInput.args || [];
    const kwargs = testInput.kwargs || {{}};
    const expected = test.expected_output;
    
    try {{
        const result = {function_name}(...args);
        const passed = JSON.stringify(result) === JSON.stringify(expected);
        results.push({{
            name: testName,
            passed: passed,
            expected: expected,
            actual: result,
            error: null
        }});
    }} catch (e) {{
        results.push({{
            name: testName,
            passed: false,
            expected: expected,
            actual: null,
            error: e.message
        }});
    }}
}}

console.log(JSON.stringify(results));
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(test_wrapper)
        temp_path = f.name
        _temp_files_to_cleanup.append(temp_path)
    
    try:
        result = subprocess.run(
            ['node', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout * len(tests),
            text=True,
            preexec_fn=_set_resource_limits,
            start_new_session=True
        )
        
        if result.returncode != 0:
            return False, 0, len(tests), [{"error": f"Execution Error: {result.stderr}"}]
        
        try:
            test_results = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return False, 0, len(tests), [{"error": f"Output Parser Failure: {result.stdout}"}]
        
        passed = sum(1 for r in test_results if r.get('passed', False))
        failures = [r for r in test_results if not r.get('passed', False)]
        
        return passed == len(tests), passed, len(tests), failures
        
    except subprocess.TimeoutExpired as e:
        if hasattr(e, 'process') and e.process:
            _kill_process_group(e.process.pid)
        return False, 0, len(tests), [{"error": "Test Timeout"}]
    except Exception as e:
        return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_path in _temp_files_to_cleanup:
                _temp_files_to_cleanup.remove(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass


def run_java_functional_test(code, tests, function_name, timeout):
    import re
    class_match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'Solution'
    
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        java_args = ', '.join([json.dumps(arg) if isinstance(arg, str) else str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args])
        java_expected = json.dumps(expected) if isinstance(expected, str) else str(expected).lower() if isinstance(expected, bool) else str(expected)
        
        test_cases.append(f"""
        try {{
            var result{i} = solution.{function_name}({java_args});
            var expected{i} = {java_expected};
            boolean passed{i} = result{i}.equals(expected{i});
            System.out.println("{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": " + passed{i} + ", \\\"expected\\\": \\\"" + expected{i} + "\\\", \\\"actual\\\": \\\"" + result{i} + "\\\"}}");
        }} catch (Exception e) {{
            System.out.println("{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": false, \\\"error\\\": \\\"" + e.getMessage() + "\\\"}}");
        }}
""")
    
    test_wrapper = f"""
{code}

public class TestRunner {{
    public static void main(String[] args) {{
        {class_name} solution = new {class_name}();
        {chr(10).join(test_cases)}
    }}
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "TestRunner.java")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            compile_result = subprocess.run(
                ['javac', source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                cwd=temp_dir,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Compilation Error: {compile_result.stderr}"}]
            
            run_result = subprocess.run(
                ['java', 'TestRunner'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                cwd=temp_dir,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution Error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test Timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def run_typescript_functional_test(code, tests, function_name, timeout):
    test_wrapper = f"""
{code}

const tests = {json.dumps(tests)};
const results: any[] = [];

for (const test of tests) {{
    const testName = test.name || 'Unnamed test';
    const testInput = test.input || {{}};
    const args = testInput.args || [];
    const expected = test.expected_output;
    
    try {{
        const result = {function_name}(...args);
        const passed = JSON.stringify(result) === JSON.stringify(expected);
        results.push({{
            name: testName,
            passed: passed,
            expected: expected,
            actual: result,
            error: null
        }});
    }} catch (e: any) {{
        results.push({{
            name: testName,
            passed: false,
            expected: expected,
            actual: null,
            error: e.message
        }});
    }}
}}

console.log(JSON.stringify(results));
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False, encoding='utf-8') as f:
        f.write(test_wrapper)
        temp_path = f.name
        _temp_files_to_cleanup.append(temp_path)
    
    js_path = None
    try:
        result = subprocess.run(
            ['ts-node', temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout * len(tests),
            text=True,
            preexec_fn=_set_resource_limits,
            start_new_session=True
        )
        
        if result.returncode != 0:
            js_path = temp_path.replace('.ts', '.js')
            _temp_files_to_cleanup.append(js_path)
            compile_result = subprocess.run(
                ['tsc', temp_path, '--outFile', js_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Compilation Error: {compile_result.stderr}"}]
            
            result = subprocess.run(
                ['node', js_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
        
        if result.returncode != 0:
            return False, 0, len(tests), [{"error": f"Execution Error: {result.stderr}"}]
        
        try:
            test_results = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return False, 0, len(tests), [{"error": f"Output Parser Failure: {result.stdout}"}]
        
        passed = sum(1 for r in test_results if r.get('passed', False))
        failures = [r for r in test_results if not r.get('passed', False)]
        
        return passed == len(tests), passed, len(tests), failures
        
    except subprocess.TimeoutExpired as e:
        if hasattr(e, 'process') and e.process:
            _kill_process_group(e.process.pid)
        return False, 0, len(tests), [{"error": "Test Timeout"}]
    except Exception as e:
        return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_path in _temp_files_to_cleanup:
                _temp_files_to_cleanup.remove(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if js_path and js_path in _temp_files_to_cleanup:
                _temp_files_to_cleanup.remove(js_path)
            if js_path and os.path.exists(js_path):
                os.remove(js_path)
        except:
            pass


def run_cpp_functional_test(code, tests, function_name, timeout):
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        cpp_args = ', '.join([f'"{arg}"' if isinstance(arg, str) else str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args])
        cpp_expected = f'"{expected}"' if isinstance(expected, str) else str(expected).lower() if isinstance(expected, bool) else str(expected)
        
        test_cases.append(f"""
    {{
        auto result{i} = {function_name}({cpp_args});
        auto expected{i} = {cpp_expected};
        bool passed{i} = (result{i} == expected{i});
        std::cout << "{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", "
                  << "\\\"passed\\\": " << (passed{i} ? "true" : "false") << ", "
                  << "\\\"expected\\\": " << expected{i} << ", "
                  << "\\\"actual\\\": " << result{i} << "}}" << std::endl;
    }}
""")
    
    test_wrapper = f"""
#include <iostream>
#include <string>
#include <vector>

{code}

int main() {{
{chr(10).join(test_cases)}
    return 0;
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "main.cpp")
        binary_path = os.path.join(temp_dir, "main")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            compile_result = subprocess.run(
                ['g++', '-std=c++17', source_path, '-o', binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Compilation Error: {compile_result.stderr}"}]
            
            run_result = subprocess.run(
                [binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution Error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test Timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def run_go_functional_test(code, tests, function_name, timeout):
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        go_args = ', '.join([f'"{arg}"' if isinstance(arg, str) else str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args])
        go_expected = f'"{expected}"' if isinstance(expected, str) else str(expected).lower() if isinstance(expected, bool) else str(expected)
        
        test_cases.append(f"""
    result{i} := {function_name}({go_args})
    expected{i} := {go_expected}
    passed{i} := result{i} == expected{i}
    fmt.Printf("{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": %v, \\\"expected\\\": %v, \\\"actual\\\": %v}}\\n", 
               passed{i}, expected{i}, result{i})
""")
    
    test_wrapper = f"""
package main

import "fmt"

{code}

func main() {{
{chr(10).join(test_cases)}
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "main.go")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            run_result = subprocess.run(
                ['go', 'run', source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution Error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test Timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def run_kotlin_functional_test(code, tests, function_name, timeout):
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        kotlin_args = ', '.join([f'"{arg}"' if isinstance(arg, str) else str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args])
        kotlin_expected = f'"{expected}"' if isinstance(expected, str) else str(expected).lower() if isinstance(expected, bool) else str(expected)
        
        test_cases.append(f"""
    val result{i} = {function_name}({kotlin_args})
    val expected{i} = {kotlin_expected}
    val passed{i} = result{i} == expected{i}
    println("{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": $passed{i}, \\\"expected\\\": $expected{i}, \\\"actual\\\": $result{i}}}")
""")
    
    test_wrapper = f"""
{code}

fun main() {{
{chr(10).join(test_cases)}
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "main.kt")
        jar_path = os.path.join(temp_dir, "main.jar")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            compile_result = subprocess.run(
                ['kotlinc', source_path, '-include-runtime', '-d', jar_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Compilation Error: {compile_result.stderr}"}]
            
            run_result = subprocess.run(
                ['java', '-jar', jar_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution Error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test Timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution Error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def run_csharp_functional_test(code, tests, function_name, timeout):
    import re
    class_match = re.search(r'class\s+(\w+)', code)
    class_name = class_match.group(1) if class_match else 'Solution'
    
    test_cases = []
    for i, test in enumerate(tests):
        args = test.get('input', {}).get('args', [])
        expected = test.get('expected_output')
        
        csharp_args = ', '.join([f'"{arg}"' if isinstance(arg, str) else str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args])
        csharp_expected = f'"{expected}"' if isinstance(expected, str) else str(expected).lower() if isinstance(expected, bool) else str(expected)
        
        test_cases.append(f"""
        var result{i} = solution.{function_name}({csharp_args});
        var expected{i} = {csharp_expected};
        var passed{i} = result{i}.Equals(expected{i});
        Console.WriteLine($"{{\\\"name\\\": \\\"{test.get('name', f'Test {i+1}')}\\\", \\\"passed\\\": {{passed{i}.ToString().ToLower()}}, \\\"expected\\\": {{expected{i}}}, \\\"actual\\\": {{result{i}}}}}");
""")
    
    test_wrapper = f"""
using System;

{code}

class Program
{{
    static void Main()
    {{
        var solution = new {class_name}();
{chr(10).join(test_cases)}
    }}
}}
"""
    
    _check_disk_space(tempfile.gettempdir())
    
    temp_dir = tempfile.mkdtemp()
    _temp_dirs_to_cleanup.append(temp_dir)
    try:
        source_path = os.path.join(temp_dir, "Program.cs")
        exe_path = os.path.join(temp_dir, "Program.exe")
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            compile_result = subprocess.run(
                ['csc', f'/out:{exe_path}', source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if compile_result.returncode != 0:
                compile_result = subprocess.run(
                    ['mcs', source_path, f'-out:{exe_path}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    text=True,
                    preexec_fn=_set_resource_limits,
                    start_new_session=True
                )
                
                if compile_result.returncode != 0:
                    return False, 0, len(tests), [{"error": f"Compilation failed: {compile_result.stderr}"}]
            
            run_result = subprocess.run(
                [exe_path] if os.name == 'nt' else ['mono', exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout * len(tests),
                text=True,
                preexec_fn=_set_resource_limits,
                start_new_session=True
            )
            
            if run_result.returncode != 0:
                return False, 0, len(tests), [{"error": f"Execution error: {run_result.stderr}"}]
            
            passed = 0
            failures = []
            for line in run_result.stdout.strip().split('\n'):
                try:
                    result = json.loads(line)
                    if result.get('passed', False):
                        passed += 1
                    else:
                        failures.append(result)
                except:
                    pass
            
            return passed == len(tests), passed, len(tests), failures
            
        except subprocess.TimeoutExpired as e:
            if hasattr(e, 'process') and e.process:
                _kill_process_group(e.process.pid)
            return False, 0, len(tests), [{"error": "Test timeout"}]
        except Exception as e:
            return False, 0, len(tests), [{"error": f"Execution error: {str(e)}"}]
    finally:
        try:
            if temp_dir in _temp_dirs_to_cleanup:
                _temp_dirs_to_cleanup.remove(temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def evaluate_functional(generation, prompt, testcase_data, output_path="functional_results.json"):
    total = 0
    matched = 0
    results = []
    
    for index, response in enumerate(generation):
        if index >= len(prompt) or index >= len(testcase_data):
            continue
        
        total += 1
        generated_code = extract_code(response['response'][0][1])
        
        language = None
        function_name = None
        if 'answer' in prompt[index]:
            answer = prompt[index]['answer']
            parts = answer.split(';')
            if len(parts) >= 2:
                language = parts[0].strip()
                function_name = parts[1].strip()
            elif len(parts) == 1:
                language = parts[0].strip()
        
        tests = testcase_data[index].get('tests', [])
        
        if not tests:
            results.append({
                "id": testcase_data[index].get('id', index),
                "category": testcase_data[index].get('category', ''),
                "constraint": testcase_data[index].get('constraint', ''),
                "prompt": testcase_data[index].get('prompt', ''),
                "answer": testcase_data[index].get('answer', ''),
                "generated_code": generated_code,
                "is_matched": False,
                "passed": 0,
                "total_tests": 0,
                "failures": [{"error": "No test cases"}]
            })
            continue
        
        if not function_name:
            results.append({
                "id": testcase_data[index].get('id', index),
                "category": testcase_data[index].get('category', ''),
                "constraint": testcase_data[index].get('constraint', ''),
                "prompt": testcase_data[index].get('prompt', ''),
                "answer": testcase_data[index].get('answer', ''),
                "generated_code": generated_code,
                "is_matched": False,
                "passed": 0,
                "total_tests": len(tests),
                "failures": [{"error": "No function name specified"}]
            })
            continue
        
        success, passed, total_tests, failures = run_functional_test(
            generated_code, tests, language, function_name, 5
        )
        
        if success:
            matched += 1
        
        results.append({
            "id": testcase_data[index].get('id', index),
            "category": testcase_data[index].get('category', ''),
            "constraint": testcase_data[index].get('constraint', ''),
            "prompt": testcase_data[index].get('prompt', ''),
            "answer": testcase_data[index].get('answer', ''),
            "generated_code": generated_code,
            "is_matched": success,
            "passed": passed,
            "total_tests": total_tests,
            "failures": failures if failures else []
        })
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return total, matched
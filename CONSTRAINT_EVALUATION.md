# MultiCodeIF Constraint Evaluation Methodology

This document details the evaluation criteria, methods, and examples for all 27 constraint types in the MultiCodeIF benchmark.

---

## 📜 Overview

Our evaluation covers 9 categories of constraints (27 specific types) with distinct verification approaches:
- **Rule-based checks**: Static analysis via AST parsing/regex (63% of constraints)
- **LLM-based verification**: Semantic validation via prompt engineering (37%)
- **Hybrid methods**: Combined static+neural approaches for complex cases

---

## 🧮 Table of contents

1. [Interface Specification](#1-interface-specification)
2. [Environment](#2-environment)
3. [Data Structure](#3-data-structure)
4. [Algorithm](#4-algorithm)
5. [Coding Style](#5-coding-style)
6. [Code Quality](#6-code-quality)
7. [Scenario](#7-scenario)
8. [Code Context](#8-code-context)
9. [Exemplar](#9-exemplar)

---

## 🔍 Constraint-Specific Evaluation

### 1. Interface Specification

**Evaluation Methods**
- **Parameter/Return Types**: Tree-Sitter + AST parsing & type checking
- **Ranges/Cardinality**: LLM verification via prompts comparing with human-reference implements

**Examples**

```python
# Example Rule Check (Return Type)
def validate_return_type(code, expected_type):
tree = ast.parse(code)
for node in ast.walk(tree):
if isinstance(node, ast.Return):
return compare_types(node.value, expected_type)

# Example LLM Check (LLM Prompt)
"""
You are an expert code reviewer. Evaluate whether the following code satisfies the given constraint by comparing it with a reference implementation.

Code Generation Task:
{task}

Constraint:
{constraint}

Reference Implementation:
{reference}

Generated Implementation:
{generated}

Please answer with one of the following:
- YES: if the generated code satisfies the constraint and is functionally similar or equivalent to the reference implementation.
- NO: if the generated code clearly violates the constraint or behaves differently.

Output ONLY YES or NO, no additional information.
"""
```

### 2. Environment

**Evaluation Methods**
- **Language Type**: Use the [Guesslang](https://github.com/yoeo/guesslang) tool
- **Language Version**: Compile tests with different versions of the language
- **Advanced Syntax/Function, Method Invocation/API, Library Usage**: Tree-Sitter + AST parsing & Regular matching
- **Framework**: LLM verification via prompts comparing with human-reference implements

**Examples**

```python
# API Usage Validation
def validate_library_usage(code, library):
imports = set()
tree = ast.parse(code)
for node in ast.walk(tree):
if isinstance(node, ast.Import):
imports.update(alias.name for alias in node.names)
elif isinstance(node, ast.ImportFrom):
imports.add(node.module)
return library in imports
```

### 3. Data Structure

**Evaluation Methods**
- **Data Structure Type**: Tree-Sitter + AST parsing & type checking
- **Data Structure Scale**: Tree-Sitter + AST parsing & Regular matching
- **Data Structure Operation**: Tree-Sitter + AST parsing + `Function, Method Invocation` used in `Environment` constraint

**Examples**

```python
# Stack Operation Validation
def validate_stack_operations(code):
required_methods = {'push', 'pop', 'peek'}
called_methods = set()
tree = ast.parse(code)
for node in ast.walk(tree):
if isinstance(node, ast.Call) and hasattr(node.func, 'attr'):
called_methods.add(node.func.attr)
return required_methods.issubset(called_methods)
```

### 4. Algorithm

**Evaluation Methods**
- **Algorithm Type/Time & Space Complexity**: LLM verification via prompts comparing with human-reference implements


### 5. Coding Style

**Evaluation Methods**
- **Naming Convention**: Regular matching
- **Indentation Style**: Regular matching + String matching
- **Brace Style**: Regular matching + Strings match by line
- **Comment Style**: Regular matching
- **Declaration Style**: LLM verification via prompts comparing with human-reference implements

**Examples**

```python
# Python Docstring Check
def has_docstring(code):
tree = ast.parse(code)
for node in ast.walk(tree):
if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
if not ast.get_docstring(node):
return False
return True

# Brace Style Validation
def validate_brace_style(code, style='K&R'):
pattern = r'\s*{\s*$' if style == 'Allman' else r'\)\s*{'
return bool(re.search(pattern, code))
```

### 6. Code Quality

**Evaluation Methods**: LLM verification via prompts comparing with human-reference implements

### 7. Scenario

**Evaluation Methods**: LLM verification via prompts comparing with human-reference implements

### 8. Code Context

**Evaluation Methods**: LLM verification via prompts comparing with human-reference implements

### 9. Exemplar

**Evaluation Methods**: LLM verification via prompts comparing with human-reference implements

---

## ⚖️ Scoring Metrics

| Metric | Definition | Use Case |
|--------|------------|----------|
| **SSR** (Soft Satisfaction Rate) | Percentage of individually satisfied constraints: `SSR = 𝟙[sat(c₁)] + 𝟙[sat(c₂)] + ... / n` | Granular per-constraint analysis |
| **HSR** (Hard Satisfaction Rate) | Binary all-or-nothing score: `HSR = 1` if all constraints satisfied | Strict compliance checking |


---

## 🛠️ Source Code Support

- **Rule-based Evaluation**: All evaluation codes are visible in file [rule_based_eval.py](src\evaluation\rule_based_eval.py)
- **LLM-based Evaluation**: All evaluation codes are visible in file [llm_based_eval.py](src\evaluation\llm_based_eval.py)

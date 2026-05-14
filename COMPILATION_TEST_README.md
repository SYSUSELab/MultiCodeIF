# Compilation Test Usage Guide

This document explains how to run the code compilation test feature, which is used to verify whether the generated code can successfully compile.

## 📋 Environment Requirements

The compilation test feature requires the corresponding compiler for each programming language. Depending on the language you want to test, you need to install the required tools. Please refer to the `setup.txt` file for details.

## 📦 Python Dependencies

Install all dependencies:

```bash
pip install -r requirements.txt
```

Ensure the required Python package is installed:

```bash
pip install guesslang
```

## 🚀 Usage

### Basic Usage

```bash
cd /workspace
python src/evaluation/run_compilation_test.py \
    --output_dir results/single_level \
    --prompt_dir dataset/instructions/single_level \
    --detail_dir results/compilation_details \
    --save_path results/compilation_results.json
```

### Parameter Description

* `--output_dir`: Directory of model output files (e.g., `results/single_level`)

  * This directory should contain subdirectories named after each model
* `--prompt_dir`: Directory of prompt files (e.g., `dataset/instructions/single_level`)

  * Contains JSON files with the original prompts
* `--detail_dir`: Directory for saving detailed results

  * Detailed compilation test results are stored here
  * Directory structure: `detail_dir/model_name/constraint_name_compilation.json`
* `--save_path`: Path to save the aggregated results (optional)

  * If specified, statistics for all models will be saved into a single JSON file
* `--model`: Name of the model to test (optional)

  * If specified, only this model will be tested, e.g., `--model deepseek-r1`

### Test All Models

```bash
python src/evaluation/run_compilation_test.py \
    --output_dir results/single_level \
    --prompt_dir dataset/instructions/single_level \
    --detail_dir results/compilation_details \
    --save_path results/compilation_results.json
```

### Test a Single Model

```bash
python src/evaluation/run_compilation_test.py \
    --output_dir results/single_level \
    --prompt_dir dataset/instructions/single_level \
    --detail_dir results/compilation_details \
    --model deepseek-r1 \
    --save_path results/compilation_deepseek-r1.json
```

### Test Other Directories

If you want to test the `results/multi_level` or `results/self_repair` directories:

```bash
# Test multi_level
python src/evaluation/run_compilation_test.py \
    --output_dir results/multi_level \
    --prompt_dir dataset/instructions/multi_level \
    --detail_dir results/compilation_details/multi_level \
    --save_path results/compilation_multi_level.json

# Test self_repair
python src/evaluation/run_compilation_test.py \
    --output_dir results/self_repair \
    --prompt_dir dataset/instructions/single_level \
    --detail_dir results/compilation_details/self_repair \
    --save_path results/compilation_self_repair.json
```

## 📊 Output Format

### Detailed Result Files

Detailed results for each constraint are saved in
`detail_dir/model_name/constraint_name_compilation.json` with the following format:

```json
[
  {
    "id": 0,
    "category": "syntax",
    "constraint": "language_type",
    "prompt": "...",
    "answer": "python",
    "generated_code": "def hello():\n    print('Hello')\n",
    "is_matched": true,
    "error_message": ""
  },
  {
    "id": 1,
    "category": "syntax",
    "constraint": "language_type",
    "prompt": "...",
    "answer": "python",
    "generated_code": "def hello(\n    print('Hello')\n",
    "is_matched": false,
    "error_message": "SyntaxError: invalid syntax"
  }
]
```

### Aggregated Result File

If `--save_path` is specified, an aggregated statistics file will be generated with the following format:

```json
{
  "model_name": {
    "constraint_name": {
      "total": 100,
      "matched": 85,
      "score": 0.85
    },
    "overall": {
      "total": 500,
      "matched": 425,
      "score": 0.85
    }
  }
}
```

## ⚠️ Notes

1. **Compiler Installation**: Make sure the appropriate compiler is installed for the language being tested
2. **File Paths**: Ensure that `output_dir` and `prompt_dir` paths are correct
3. **Permissions**: Make sure you have write permissions for `detail_dir` and `save_path`
4. **Time Limit**: Each compilation test has a timeout limit of 10 seconds
5. **Temporary Files**: Compilation tests create temporary files, which are automatically cleaned up after testing

## 🔍 Troubleshooting

### Issue: "Compiler not found"

**Solution**:

* Ensure the required compiler is installed
* Ensure the compiler is available in the system PATH
* Use `which compiler_name` to check the compiler location

### Issue: "Unable to detect language type"

**Solution**:

* Ensure the `guesslang` package is installed: `pip install guesslang`
* Or ensure the `answer` field in the prompt files contains language type information

### Issue: "Compilation timeout"

**Solution**:

* The code may be too complex
* Check the `error_message` field in the detailed result files
* The default timeout is 10 seconds and can be adjusted in the code

### Issue: "Prompt file not found"

**Solution**:

* Check whether the `prompt_dir` path is correct
* Check whether the file name format matches
* File names should match the constraint name (e.g., `syntax_language_type.json`)

## 📝 Example

Complete usage example:

```bash
# 1. Ensure the environment is properly configured
python3 --version  # Python
javac -version     # Java (if testing Java code)
node --version     # JavaScript (if testing JS code)

# 2. Install Python dependencies
pip install guesslang

# 3. Run the compilation test
python src/evaluation/run_compilation_test.py \
    --output_dir results/single_level \
    --prompt_dir dataset/instructions/single_level \
    --detail_dir results/compilation_details \
    --save_path results/compilation_results.json

# 4. View the results
cat results/compilation_results.json
```

## 🔗 Related Files

* **Compilation Test Module**: `src/evaluation/compile_test.py`
* **Execution Script**: `src/evaluation/run_compilation_test.py`

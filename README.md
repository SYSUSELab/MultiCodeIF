# MultiCodeIF: An Automatically Constructed Benchmark for Multi-Type, Multi-Level, and Multi-Turn Code Instruction Following

This is the official repository for the paper: **MultiCodeIF: An Automatically Constructed Benchmark for Multi-Type, Multi-Level, and Multi-Turn Code Instruction Following**

---

## 🧠 Overview

Large language models (LLMs) have made significant strides in code generation, but existing benchmarks often focus only on **functional correctness** and overlook models’ ability to follow **fine-grained, multi-constraint instructions**, especially in **multi-turn scenarios**.

**MultiCodeIF** fills this gap by introducing a large-scale, automatically constructed benchmark for evaluating **instruction-following ability** in code generation. It features:

- A **hierarchical constraint taxonomy**: 9 categories × 27 types of constraints, covering both functional and non-functional aspects.
- **2,021 tasks** across **14 programming languages**, automatically constructed and evolved using our `ConstraGen` pipeline.
- Support for **multi-type**, **multi-level**, and **multi-turn** evaluation settings.

---

## 🔍 Benchmark Dataset

The [`dataset/`](dataset/) directory contains the automatically constructed benchmark instructions and associated metadata for evaluation.

```
dataset/
└── instructions/
├── single_level/
└── multi_level/
```

- [`single_level/`](https://chatgpt.com/c/dataset/instructions/single_level/): Instruction sets automatically constructed to contain **only a single level of constraints**. These are atomic tasks with one layer of requirement, suitable for testing models’ ability to follow simple, flat instructions.
- [`multi_level/`](https://chatgpt.com/c/dataset/instructions/multi_level/): Instruction sets built through an **evolvable automatic construction pipeline**, containing **multi-level constraints** that require reasoning over **interrelated and hierarchically dependent** conditions.

---

## 📑 Key Features

* **Multi-Type Tasks**: Covers diverse instruction types including algorithm implementation, data structure operations, and edge-case handling.
* **Multi-Level Reasoning**: Assesses models' ability to follow composite, hierarchical instructions with interdependent subtasks.
* **Multi-Turn Interaction**: Evaluates how well models self-repair or update their code when given iterative feedback.

---

## 🔗 Constraint Evaluation Details

Briefly, we use tailored strategies per constraint type: rule-based checks (e.g., regex, Tree-sitter) for explicit constraints like naming or return types, and GPT-4-Turbo with structured prompts for subjective ones like algorithm choice or clarity, comparing outputs to human references.

For detailed evaluation methods for each type of constraint, see: [Constraint-specific Evaluation Methodology](CONSTRAINT_EVALUATION.md)

---

## 🛠️ Source Code

The [`src/`](src/) directory contains all scripts for dataset generation, evaluation, and self-repair.

```
src/
├── data_construction/    # Scripts and tools for automatically generating benchmark instructions
├── evaluation/           # Evaluation logic for checking constraint and functional correctness
├── scripts/              # Helper scripts for batch processing, running models, etc.
└── self_repair/          # Evaluation pipeline and tools for self-repair / multi-turn instruction following
```

---


### ⚙️ Environment Setup

To set up the environment for dataset generation, evaluation, and self-repair, follow the steps below:

---

#### 1. Create and Activate Python Environment

We recommend using **Python 3.9+** and [Conda Environment](https://anaconda.org/anaconda/conda).

```bash
conda create --name MultiCodeIF python=3.9
conda activate MultiCodeIF
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

#### 2. Set Up Compiler Versions

Some components (e.g., evaluation involving compilation) rely on specific versions of Python, Rust, and Java. Use the provided setup scripts to install consistent toolchain versions:


```bash
bash src/scripts/setup_python.sh
bash src/scripts/setup_rust.sh
bash src/scripts/setup_java.sh
```

#### 3. Configure Model API Key

If you plan to run self-repair or generation using models, complete code in [generation.py](src/data_construction/generation.py)

---

---


## 📈 Results and Usage

Experimental results are stored in the top-level [`results/`](results/) directory:

* [`results/single_level/`](results/single_level/): Model outputs and evaluations on single-level tasks
* [`results/multi_level/`](results/multi_level/): Model outputs and evaluations on multi-level tasks
* [`results/self_repair/`](results/self_repair/): Outputs and evaluations on multi-turn feedback tasks

You can reproduce or extend the evaluation using the provided scripts in [`src/`](src/).

---

### 🏗️ Constructing Single-level Constraint Instructions

To construct a set of single-level instruction samples with constraint-specific generation and Rouge-L filtering, use [`run_single_level_construct.sh`](src/scripts/run_single_level_construct.sh). Use it as:

```bash
bash src/scripts/run_single_level_construct.sh <constraint> <count> <raw_output_file> <filtered_output_file> <rouge_threshold>
# Example
bash src/scripts/run_single_level_construct.sh \
data_structure \
50 \
outputs/raw.json \
outputs/filtered.json \
0.7
```

---

### 🧱 Constructing Multi-level Constraint Instructions

To build multi-level instruction chains (where each level incrementally adds a new constraint), use [`run_multi_level_construct.sh`](src/scripts/run_multi_level_construct.sh). Use it as:

```bash
bash src/scripts/run_multi_level_construct.sh <input_file> <raw_output_file> <filtered_output_file> <level_num> <rouge_threshold>
# Example:
bash src/scripts/run_multi_level_construct.sh \
outputs/filtered_single.json \
outputs/raw_multi.json \
outputs/filtered_multi.json \
3 \
0.7
```

---

### 🔧 Running Single-level Constraint Evaluation

To evaluate model outputs against single-level constraints, use the main evaluation script [`run_evaluation.sh`](src/scripts/run_evaluation.sh). Use it as:

```bash
bash src/scripts/run_evaluation.sh --output_dir <output_dir> --prompt_dir <prompt_dir> --detail_dir <detail_dir> --save_path <save_path>
# Example
bash src/scripts/run_evaluation.sh \
--output_dir results/single_level \
--prompt_dir dataset/instructions/single_level \
--detail_dir results/evaluation_details \
--save_path results/evaluation_result.json
```

---

### 📚 Running Multi-level Constraint Evaluation

To evaluate multi-level constraint satisfaction (where each level builds upon prior constraints), use [`run_multi_level_eval.sh`](src/scripts/run_multi_level_eval.sh):

```bash
bash src/scripts/run_multi_level_eval.sh --output_dir <generation_dir> --prompt_dir <prompt_dir> --save_path <save_path>
# Example
bash src/scripts/run_multi_level_eval.sh \
--output_dir results/multi_level \
--prompt_dir dataset/instructions/multi_level \
--save_path results/multi_level_evaluation_result.json
```

---

### 🔁 Running Self-Repair Evaluation

To regenerate outputs for failed cases using multi-turn feedback, use the script [`run_self_repair.sh`](src/scripts/run_self_repair.sh). Use it as:

```bash
bash src/scripts/run_self_repair.sh --model <model_name> --input_dir <input_dir> --output_dir <output_dir>
# Example
bash src/scripts/run_self_repair.sh \
--model gpt-4o \
--input_dir results/evaluation_details/gpt-4o \
--output_dir results/self_repair/regenerated
```
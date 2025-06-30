#!/bin/bash

# Usage:
#   bash run_self_repair.sh <model_name> <input_dir> <output_dir>
#   Example:
#   bash run_self_repair.sh gpt-4o ./failed_cases ./self_repair_outputs

MODEL_NAME=$1
INPUT_DIR=$2
OUTPUT_DIR=$3

if [ -z "$MODEL_NAME" ] || [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
  echo "[ERROR] Usage: bash run_self_repair.sh <model_name> <input_dir> <output_dir>"
  exit 1
fi

python src/self_repair/repair.py \
  --model "$MODEL_NAME" \
  --input_dir "$INPUT_DIR" \
  --output_dir "$OUTPUT_DIR"

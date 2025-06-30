#!/bin/bash

# Usage:
#   bash run_evaluation.sh <output_dir> <prompt_dir> <detail_dir> <save_path>
#   Example:
#   bash run_evaluation.sh ./outputs ./prompts ./details ./results.json

OUTPUT_DIR=$1
PROMPT_DIR=$2
DETAIL_DIR=$3
SAVE_PATH=$4

# Fallback to default if save path not provided
if [ -z "$SAVE_PATH" ]; then
  SAVE_PATH="results.json"
fi

python src/evaluation/eval.py \
  --output_dir "$OUTPUT_DIR" \
  --prompt_dir "$PROMPT_DIR" \
  --detail_dir "$DETAIL_DIR" \
  --save_path "$SAVE_PATH"

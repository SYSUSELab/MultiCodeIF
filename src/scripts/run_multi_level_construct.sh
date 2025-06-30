#!/bin/bash

# Usage:
#   bash run_multi_level_construct.sh <input_file> <raw_output_file> <filtered_output_file> <level_num> <rouge_threshold>
#   Example:
#   bash run_multi_level_construct.sh ./outputs/filtered_single.json ./outputs/raw_multi.json ./outputs/filtered_multi.json 3 0.7

INPUT_FILE=$1
RAW_OUTPUT=$2
FILTERED_OUTPUT=$3
LEVEL_NUM=$4
ROUGE_THRESHOLD=$5

if [ -z "$INPUT_FILE" ] || [ -z "$RAW_OUTPUT" ] || [ -z "$FILTERED_OUTPUT" ] || [ -z "$LEVEL_NUM" ] || [ -z "$ROUGE_THRESHOLD" ]; then
  echo "[ERROR] Usage: bash run_multi_level_construct.sh <input_file> <raw_output_file> <filtered_output_file> <level_num> <rouge_threshold>"
  exit 1
fi

# Step 1: Run multi-level generation and save raw results
python src/data_construction/data_construction.py multi-level \
  --input "$INPUT_FILE" \
  --output "$RAW_OUTPUT" \
  --levels "$LEVEL_NUM"

# Step 2: Filter the multi-level output
python src/data_construction/filter.py \
  --input "$RAW_OUTPUT" \
  --output "$FILTERED_OUTPUT" \
  --limit "$ROUGE_THRESHOLD"

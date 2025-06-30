#!/bin/bash

# Usage:
#   bash run_single_level_construct.sh <constraint> <count> <raw_output_file> <filtered_output_file> <rouge_threshold>
#   Example:
#   bash run_single_level_construct.sh data_structure 50 ./outputs/raw.json ./outputs/filtered.json 0.7

CONSTRAINT=$1
COUNT=$2
RAW_OUTPUT=$3
FILTERED_OUTPUT=$4
ROUGE_THRESHOLD=$5

if [ -z "$CONSTRAINT" ] || [ -z "$COUNT" ] || [ -z "$RAW_OUTPUT" ] || [ -z "$FILTERED_OUTPUT" ] || [ -z "$ROUGE_THRESHOLD" ]; then
  echo "[ERROR] Usage: bash run_single_level_construct.sh <constraint> <count> <raw_output_file> <filtered_output_file> <rouge_threshold>"
  exit 1
fi

# Step 1: Run single-level generation
python src/data_construction/data_construction.py single-level \
  --constraint "$CONSTRAINT" \
  --count "$COUNT" \
  --output "$RAW_OUTPUT"

# Step 2: Filter with Rouge-L
python src/data_construction/filter.py \
  --input "$RAW_OUTPUT" \
  --output "$FILTERED_OUTPUT" \
  --limit "$ROUGE_THRESHOLD"

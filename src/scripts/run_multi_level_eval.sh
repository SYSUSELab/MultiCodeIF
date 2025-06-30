#!/bin/bash

# Usage:
#   bash run_multilevel_eval.sh <output_dir> <prompt_dir> [save_path]
#
# Example:
#   bash run_multilevel_eval.sh \
#       outputs \
#       prompts \
#       results/multilevel_results.json

OUTPUT_DIR=$1
PROMPT_DIR=$2
SAVE_PATH=$3

if [ -z "$OUTPUT_DIR" ] || [ -z "$PROMPT_DIR" ]; then
  echo "[ERROR] Usage: bash run_multilevel_eval.sh <output_dir> <prompt_dir> [save_path]"
  exit 1
fi

CMD="python your_script_name.py --output_dir \"$OUTPUT_DIR\" --prompt_dir \"$PROMPT_DIR\""

if [ -n "$SAVE_PATH" ]; then
  CMD+=" --save_path \"$SAVE_PATH\""
fi

echo "[INFO] Running multi-level evaluation with command:"
echo "$CMD"

eval $CMD

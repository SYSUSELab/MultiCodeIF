#!/bin/bash

OUTPUT_DIR=$1
PROMPT_DIR=$2
DETAIL_DIR=$3
SAVE_PATH=$4
MODEL_NAME=$5

if [ -z "$OUTPUT_DIR" ] || [ -z "$PROMPT_DIR" ] || [ -z "$DETAIL_DIR" ]; then
  echo "[ERROR] Usage: bash run_ast_test.sh <output_dir> <prompt_dir> <detail_dir> [save_path] [model_name]"
  echo ""
  echo "Example:"
  echo "  bash src/scripts/run_ast_test.sh \\"
  echo "      results/single_level \\"
  echo "      dataset/instructions/single_level \\"
  echo "      results/ast_details \\"
  echo "      results/ast_details/ast_results.json"
  exit 1
fi

CMD="python src/evaluation/run_ast_test.py --output_dir \"$OUTPUT_DIR\" --prompt_dir \"$PROMPT_DIR\" --detail_dir \"$DETAIL_DIR\""

if [ -n "$SAVE_PATH" ]; then
  CMD="$CMD --save_path \"$SAVE_PATH\""
fi

if [ -n "$MODEL_NAME" ]; then
  CMD="$CMD --model \"$MODEL_NAME\""
fi

echo "[INFO] Running AST certification test..."
echo "[INFO] Command: $CMD"
echo ""

eval $CMD

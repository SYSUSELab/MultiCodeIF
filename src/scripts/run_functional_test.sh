#!/bin/bash

OUTPUT_DIR=$1
PROMPT_DIR=$2
TESTCASE_DIR=$3
DETAIL_DIR=$4
SAVE_PATH=$5
MODEL_NAME=$6

if [ -z "$OUTPUT_DIR" ] || [ -z "$PROMPT_DIR" ] || [ -z "$DETAIL_DIR" ] || [ -z "$SAVE_PATH" ]; then
  echo "[ERROR] Usage: bash run_functional_test.sh <output_dir> <prompt_dir> [testcase_dir] <detail_dir> <save_path> [model_name]"
  echo ""
  echo "Example:"
  echo "  bash src/scripts/run_functional_test.sh \\"
  echo "      results/single_level \\"
  echo "      dataset/instructions/single_level \\"
  echo "      dataset/instructions/testcase \\"
  echo "      results/functional_details \\"
  echo "      results/functional_details/functional_results.json"
  echo ""
  echo "  # Without testcase_dir"
  echo "  bash src/scripts/run_functional_test.sh \\"
  echo "      results/single_level \\"
  echo "      dataset/instructions/single_level \\"
  echo "      \"\" \\"
  echo "      results/functional_details \\"
  echo "      results/functional_results.json"
  exit 1
fi

CMD="python src/evaluation/run_functional_test.py \
  --output_dir \"$OUTPUT_DIR\" \
  --prompt_dir \"$PROMPT_DIR\" \
  --detail_dir \"$DETAIL_DIR\" \
  --save_path \"$SAVE_PATH\""

if [ -n "$TESTCASE_DIR" ]; then
  CMD="$CMD --testcase_dir \"$TESTCASE_DIR\""
fi

if [ -n "$MODEL_NAME" ]; then
  CMD="$CMD --model \"$MODEL_NAME\""
fi

echo "[INFO] Running functional tests..."
echo "[INFO] Command: $CMD"
echo ""

eval $CMD

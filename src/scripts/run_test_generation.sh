#!/bin/bash

# Test case generation script
# Usage:
#   bash src/scripts/run_test_generation.sh <input_dir> <output_dir> [case_num] [model_name]
#   Example:
#   bash src/scripts/run_test_generation.sh \
#       dataset/instructions/single_level \
#       dataset/instructions/testcase \
#       10 \
#       claude-haiku-4-5-20251001

INPUT_DIR=$1
OUTPUT_DIR=$2
CASE_NUM=${3:-1}  # Default: 1 test case
MODEL_NAME=${4:-"claude-haiku-4-5-20251001"}  # Default: claude-haiku-4-5-20251001

# Check required parameters
if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
  echo "[ERROR] Usage: bash run_test_generation.sh <input_dir> <output_dir> [case_num] [model_name]"
  echo ""
  echo "Parameter description:"
  echo "  input_dir   - Directory containing input JSON files"
  echo "  output_dir  - Directory to save output JSON files"
  echo "  case_num    - Number of test cases generated per problem (default: 10)"
  echo "  model_name  - Model name to use (default: empty)"
  echo ""
  echo "Example:"
  echo "  bash src/scripts/run_test_generation.sh \\"
  echo "      dataset/instructions/single_level \\"
  echo "      dataset/instructions/testcase \\"
  echo "      10 \\"
  echo "      claude-haiku-4-5-20251001"
  exit 1
fi

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
  echo "[ERROR] Input directory does not exist: $INPUT_DIR"
  exit 1
fi

# Create output directory (if it does not exist)
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Test Case Generation Script"
echo "=========================================="
echo "[INFO] Input directory: $INPUT_DIR"
echo "[INFO] Output directory: $OUTPUT_DIR"
echo "[INFO] Number of test cases: $CASE_NUM"
echo "[INFO] Model name: ${MODEL_NAME:-Not specified}"
echo "=========================================="
echo ""

# Statistics variables
total_files=0
success_files=0
failed_files=0

# Iterate over all JSON files in the input directory
for input_file in "$INPUT_DIR"/*.json; do
  # Check if file exists (to avoid no-match situations)
  if [ ! -f "$input_file" ]; then
    echo "[WARN] No JSON files found: $INPUT_DIR/*.json"
    break
  fi
  
  # Get filename (without path)
  filename=$(basename "$input_file")
  
  # Construct output file path
  output_file="$OUTPUT_DIR/$filename"
  
  total_files=$((total_files + 1))
  
  echo "[INFO] [$total_files] Processing file: $filename"
  
  # Construct Python command
  CMD="python src/data_construction/test_generation.py --input \"$input_file\" --output \"$output_file\" --cases $CASE_NUM"
  
  if [ -n "$MODEL_NAME" ]; then
    CMD="$CMD --model \"$MODEL_NAME\""
  fi
  
  # Execute command
  if eval $CMD; then
    success_files=$((success_files + 1))
    echo "[SUCCESS] Generation completed: $output_file"
  else
    failed_files=$((failed_files + 1))
    echo "[FAILED] Generation failed: $filename"
  fi
  
  echo ""
done

# Output statistics
echo "=========================================="
echo "Generation Completed"
echo "=========================================="
echo "[STATS] Total files: $total_files"
echo "[STATS] Success: $success_files"
echo "[STATS] Failed: $failed_files"
echo "=========================================="

# Return appropriate exit code based on results
if [ $failed_files -gt 0 ]; then
  exit 1
else
  exit 0
fi
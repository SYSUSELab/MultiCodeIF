import json
from rouge_score import rouge_scorer
# import textdistance


def init_index_of_json(infile, outfile):
        with open(infile, 'r', encoding='utf-8') as f:
            data = json.load(f)
            index = 1
            for item in data:
                item["id"] = index
                index += 1
        
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


def filter_by_rouge_l(input_path, output_path, limit=0.7):
    """
    Filter JSON data based on Rouge-L score
    
    :param input_path: Input JSON file path
    :param output_path: Output JSON file path
    :param limit: Similarity threshold (0.0-1.0)
    """
    # Read input data
    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    output_data = []
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
    
    for item in input_data:
        candidate_prompt = item['prompt']
        add_candidate = True
        
        # Check all existing prompts
        for existing_item in output_data:
            existing_prompt = existing_item['prompt']
            # Calculate Rouge-L scores in both directions
            score1 = scorer.score(existing_prompt, candidate_prompt)['rougeL'].fmeasure
            score2 = scorer.score(candidate_prompt, existing_prompt)['rougeL'].fmeasure
            max_score = max(score1, score2)
            
            if max_score >= limit:
                add_candidate = False
                break  # Found similar item, skip subsequent comparisons
        
        if add_candidate:
            output_data.append(item)
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
# def filter_by_cos_similarity(input_path, output_path, limit=0.9):
#     """
#     Filter JSON data based on cosine similarity
    
#     :param input_path: Input JSON file path
#     :param output_path: Output JSON file path
#     :param limit: Similarity threshold (0.0-1.0)
#     """
#     # Read input data
#     with open(input_path, 'r', encoding='utf-8') as f:
#         input_data = json.load(f)
    
#     output_data = []
    
#     for item in input_data:
#         candidate_prompt = item['prompt']
#         add_candidate = True
        
#         # Check all existing prompts
#         for existing_item in output_data:
#             existing_prompt = existing_item['prompt']
#             # Calculate cosine similarity
#             similarity = textdistance.cosine.similarity(existing_prompt, candidate_prompt)
            
#             if similarity >= limit:
#                 add_candidate = False
#                 break  # Found similar item, skip subsequent comparisons
        
#         if add_candidate:
#             output_data.append(item)
    
#     # Write to output file
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(output_data, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filter JSON data using Rouge-L similarity.")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument("--output", type=str, required=True, help="Filtered output JSON file")
    parser.add_argument("--limit", type=float, default=0.7, help="Rouge-L similarity threshold")
    args = parser.parse_args()

    filter_by_rouge_l(args.input, args.output, args.limit)
    init_index_of_json(args.output, args.output)

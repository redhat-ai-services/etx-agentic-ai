judge_model_id = "llama32"
JUDGE_PROMPT = """
You are an expert in evaluating structured text formats for GitHub issues.
Your task is to determine if the GENERATED RESPONSE follows the required format based on the original INPUT QUERY.

The required format for the GitHub issue is as follows:
- Must contain a heading: '### Cluster/namespace location'
- Must contain a heading: '### Summary of the problem'
- Must contain a heading: '### Detailed error/code'
- Must contain a heading: '### Possible solutions'

Analyze the GENERATED RESPONSE and check if it includes all four of the required headings.
- If all four headings are present, the format is correct.
- If one or more headings are missing, the format is incorrect.

Provide your answer as a numerical score followed by a brief explanation.
Format: "Score: [score], Explanation: [your reasoning]"
- Use a score of 1 for a correct format.
- Use a score of 0 for an incorrect format.

Your actual task:

INPUT QUERY: {input_query}
GENERATED RESPONSE: {generated_answer}
"""
from typing import List, Dict, Any

def get_google_display_prompts_messages(url_context_sum: str, additional_context_sum: str) -> List[List[Dict[str, str]]]:
    """
    Generates prompt messages for Google Display ads.
    This returns a list containing ONE 'messages' list for a single API call.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter specializing in Google Display ads. Generate ad components in JSON format. Ensure the JSON is valid and contains all requested fields as specified."

    # This is a placeholder user prompt. User will edit.
    user_prompt_content = f"""
    Task: Generate Google Display ad components.

    Company Context:
    - URL Summary: {url_context_sum if url_context_sum else "Not provided."}
    - Additional Info Summary: {additional_context_sum if additional_context_sum else "Not provided."}

    Requirements:
    - Generate 5 ad variations.
    - For each variation, provide one Headline (MUST be approximately 30 characters or less) and one Description (MUST be approximately 90 characters or less).

    Output Format:
    Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
    The "ads" list must contain exactly 5 items.
    {{
      "ads": [
        {{ "Headline": "Headline 1 (<=30 chars)", "Description": "Description 1 (<=90 chars)" }},
        {{ "Headline": "Headline 2 (<=30 chars)", "Description": "Description 2 (<=90 chars)" }},
        {{ "Headline": "Headline 3 (<=30 chars)", "Description": "Description 3 (<=90 chars)" }},
        {{ "Headline": "Headline 4 (<=30 chars)", "Description": "Description 4 (<=90 chars)" }},
        {{ "Headline": "Headline 5 (<=30 chars)", "Description": "Description 5 (<=90 chars)" }}
      ]
    }}
    """
    messages = [
        {"role": "system", "content": base_system_prompt},
        {"role": "user", "content": user_prompt_content}
    ]
    return [messages] # Return a list containing this single 'messages' list
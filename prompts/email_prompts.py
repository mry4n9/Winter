from typing import List, Dict, Any

def get_email_prompts_messages(url_context_sum: str, additional_context_sum: str,
                               lead_objective: str, book_link: str, content_count: int) -> List[List[Dict[str, str]]]:
    """
    Generates a list containing ONE prompt messages list for email ad copy.
    This single prompt will ask the AI to generate 'content_count' variations.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
   
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter. Generate ad copy in JSON format. Ensure the JSON is valid and contains all requested fields."

    user_prompt_content = f"""
    Task: Generate {content_count} unique email ad variations.

    Company Context:
    - URL Summary: {url_context_sum if url_context_sum else "Not provided."}
    - Additional Info Summary: {additional_context_sum if additional_context_sum else "Not provided."}

    Campaign Details for all variations:
    - Funnel Stage: Demand Capture (This is fixed for emails as per spec)
    - Lead Objective: {lead_objective}
    - Booking Link (for CTA): {book_link}

    Output Format:
    Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
    The root key MUST be "email_ads" and its value MUST be a list of {content_count} JSON objects.
    Each object in the list should represent one email ad variation.
    Assign unique "Ad Name" for each variation (e.g., "Email_DemandCapture_Ver_1", "Email_DemandCapture_Ver_2", ...).

    {{
      "email_ads": [
        // Example for one variation (repeat {content_count} times in the list):
        {{
          "Ad Name": "Email_Ad_Ver_1", // Ensure this is unique for each variation
          "Funnel Stage": "Demand Capture",
          "Headline": "Generated Headline Text for Ver 1",
          "Subject Line": "Generated Subject Line Text for Ver 1",
          "Body": "Generated Email Body Text for Ver 1. Should be compelling and lead to the CTA.",
          "CTA": "Action-oriented text, e.g., '{lead_objective}' or similar, linking to {book_link}"
        }}
        // ... more variations if content_count > 1
      ]
    }}
    """
    messages = [
        {"role": "system", "content": base_system_prompt},
        {"role": "user", "content": user_prompt_content}
    ]
    return [messages] # Return a list containing this single 'messages' list
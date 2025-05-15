from typing import List, Dict, Any

def get_email_prompts_messages(url_context_sum: str, additional_context_sum: str, 
                               lead_objective: str, book_link: str, content_count: int) -> List[List[Dict[str, str]]]:
    """
    Generates a list containing a single prompt message set for generating multiple email ad variations.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter. Generate ad copy in JSON format. Ensure the JSON is valid and contains all requested fields. The output should be a single JSON object with a key 'ads' containing a list of ad variations."

    # This is a placeholder user prompt. User will edit.
    user_prompt_content = f"""
    Task: Generate {content_count} unique email ad variations.

    Company Context:
    - URL Summary: {url_context_sum if url_context_sum else "Not provided."}
    - Additional Info Summary: {additional_context_sum if additional_context_sum else "Not provided."}

    Campaign Details:
    - Funnel Stage: Demand Capture (This is fixed for emails as per spec)
    - Lead Objective: {lead_objective}
    - Booking Link (for CTA): {book_link}

    Output Format:
    Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
    The "ads" list must contain exactly {content_count} email ad objects.
    Each ad object should have a unique "Ad Name": "Email_DemandCapture_Ver_X".
    {{
      "ads": [
        // {content_count} email ad objects here, for example:
        {{
          "Ad Name": "Email_DemandCapture_Ver_1",
          "Funnel Stage": "Demand Capture",
          "Headline": "Generated Headline Text 1",
          "Subject Line": "Generated Subject Line Text 1",
          "Body": "Generated Email Body Text 1, start email with Hi [Name], use 2-3 paragraphs, embed {book_link} naturally in body.",
          "CTA": "Action-oriented text for variation 1, e.g., '{lead_objective}' or similar"
        }},
        {{
          "Ad Name": "Email_DemandCapture_Ver_2",
          "Funnel Stage": "Demand Capture",
          "Headline": "Generated Headline Text 2",
          "Subject Line": "Generated Subject Line Text 2",
          "Body": "Generated Email Body Text 2, start email with Hi [Name], use 2-3 paragraphs, embed {book_link} naturally in body.",
          "CTA": "Action-oriented text for variation 2, e.g., '{lead_objective}' or similar"
        }}
        // ... and so on, up to {content_count} variations
      ]
    }}
    """
    messages = [
        {"role": "system", "content": base_system_prompt},
        {"role": "user", "content": user_prompt_content}
    ]
    return [messages] # Return a list containing this single 'messages' list
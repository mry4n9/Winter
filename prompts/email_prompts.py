from typing import List, Dict, Any

def get_email_prompts_messages(url_context_sum: str, additional_context_sum: str, 
                               lead_objective: str, book_link: str, content_count: int) -> List[List[Dict[str, str]]]:
    """
    Generates a list of prompt messages for email ad copy.
    Each item in the list is a 'messages' list for one OpenAI API call.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
    all_prompts_messages: List[List[Dict[str, str]]] = []
    
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter. Generate ad copy in JSON format. Ensure the JSON is valid and contains all requested fields."

    for i in range(content_count):
        # This is a placeholder user prompt. User will edit.
        user_prompt_content = f"""
        Task: Generate one email ad variation.

        Company Context:
        - URL Summary: {url_context_sum if url_context_sum else "Not provided."}
        - Additional Info Summary: {additional_context_sum if additional_context_sum else "Not provided."}

        Campaign Details:
        - Ad Name: Email_Ad_Variation_{i+1}
        - Funnel Stage: Demand Capture (This is fixed for emails as per spec)
        - Lead Objective: {lead_objective}
        - Booking Link (for CTA): {book_link}

        Output Format:
        Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
        {{
          "Ad Name": "Email_Ad_Variation_{i+1}",
          "Funnel Stage": "Demand Capture",
          "Headline": "Generated Headline Text",
          "Subject Line": "Generated Subject Line Text",
          "Body": "Generated Email Body Text. Should be compelling and lead to the CTA.",
          "CTA": "Action-oriented text, e.g., '{lead_objective}' or similar, linking to {book_link}"
        }}
        """
        messages = [
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": user_prompt_content}
        ]
        all_prompts_messages.append(messages)
    return all_prompts_messages
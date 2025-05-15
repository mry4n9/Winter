from typing import List, Dict, Any

def get_linkedin_prompts_messages(url_context_sum: str, additional_context_sum: str, lead_magnet_sum: str,
                                  learn_more_link: str, magnet_link: str, book_link: str, 
                                  lead_objective: str, content_count: int) -> List[List[Dict[str, str]]]:
    """
    Generates a list of prompt messages for LinkedIn ad copy.
    One prompt per funnel stage, each asking for 'content_count' variations.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
    all_prompts_messages: List[List[Dict[str, str]]] = []
    
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter specializing in LinkedIn ads. Generate ad copy in JSON format. Ensure the JSON is valid and contains all requested fields."

    # Determine CTA for Demand Capture based on lead_objective
    demand_capture_cta = "Register" if "Demo" in lead_objective else "Request"

    funnel_stages_config = {
        "Brand Awareness": {
            "cta_button": "Learn More",
            "destination": learn_more_link,
            "primary_context": f"URL Summary: {url_context_sum if url_context_sum else 'N/A'}\nAdditional Context: {additional_context_sum if additional_context_sum else 'N/A'}",
            "secondary_context": ""
        },
        "Demand Gen": {
            "cta_button": "Download",
            "destination": magnet_link,
            "primary_context": f"Lead Magnet Summary: {lead_magnet_sum if lead_magnet_sum else 'N/A'}",
            "secondary_context": f"URL Summary: {url_context_sum if url_context_sum else 'N/A'}\nAdditional Context: {additional_context_sum if additional_context_sum else 'N/A'}"
        },
        "Demand Capture": {
            "cta_button": demand_capture_cta,
            "destination": book_link,
            "primary_context": f"Lead Objective: {lead_objective}",
            "secondary_context": f"URL Summary: {url_context_sum if url_context_sum else 'N/A'}\nAdditional Context: {additional_context_sum if additional_context_sum else 'N/A'}"
        }
    }

    for stage_name, config in funnel_stages_config.items():
        # This is a placeholder user prompt. User will edit.
        user_prompt_content = f"""
        Task: Generate {content_count} unique LinkedIn ad variations for the '{stage_name}' funnel stage.

        Company Context:
        - Primary Context for this ad: {config['primary_context']}
        - Supporting Context: {config['secondary_context']}

        Campaign Details for all variations in this batch:
        - Funnel Stage: {stage_name}
        - Destination Link: {config['destination']}
        - CTA Button Text: {config['cta_button']}

        Output Format:
        Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
        The root key MUST be "linkedin_ads" and its value MUST be a list of {content_count} JSON objects.
        Each object in the list should represent one LinkedIn ad variation for the '{stage_name}' stage.
        Assign unique "Ad Name" for each variation (e.g., "LinkedIn_{stage_name.replace(" ", "")}_Ver_1", ...).

        {{
          "linkedin_ads": [
            // Example for one variation (repeat {content_count} times in the list):
            {{
              "Ad Name": "LinkedIn_{stage_name.replace(" ", "")}_Ver_1", // Ensure this is unique
              "Funnel Stage": "{stage_name}",
              "Introductory Text": "Generated introductory text for variation 1.",
              "Image Copy": "Suggested text overlay or concept for variation 1 image/video.",
              "Headline": "Generated headline for variation 1.",
              "Destination": "{config['destination']}",
              "CTA Button": "{config['cta_button']}"
            }}
            // ... more variations if content_count > 1
          ]
        }}
        """
        messages = [
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": user_prompt_content}
        ]
        all_prompts_messages.append(messages)
    return all_prompts_messages
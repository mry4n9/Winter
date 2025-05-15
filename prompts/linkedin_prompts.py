from typing import List, Dict, Any

def get_linkedin_prompts_messages(url_context_sum: str, additional_context_sum: str, lead_magnet_sum: str,
                                  learn_more_link: str, magnet_link: str, book_link: str, 
                                  lead_objective: str, content_count: int) -> List[List[Dict[str, str]]]:
    """
    Generates a list of prompt messages for LinkedIn ad copy, one message set per funnel stage.
    Each message set requests 'content_count' variations for that stage.
    USER WILL MANUALLY EDIT THE PROMPT CONTENT.
    """
    all_prompts_messages: List[List[Dict[str, str]]] = []
    
    # This is a placeholder system prompt. User will edit.
    base_system_prompt = "You are an expert marketing copywriter specializing in LinkedIn ads. Generate ad copy in JSON format. Ensure the JSON is valid and contains all requested fields. The output should be a single JSON object with a key 'ads' containing a list of ad variations for the specified funnel stage."

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
        - Primary Context for this ad stage: {config['primary_context']}
        - Supporting Context: {config['secondary_context']}

        Campaign Details:
        - Funnel Stage: {stage_name}
        - Destination Link: {config['destination']}
        - CTA Button Text: {config['cta_button']}

        Output Format:
        Strictly adhere to the following JSON structure. Do NOT add any text before or after the JSON object.
        The "ads" list must contain exactly {content_count} LinkedIn ad objects for the '{stage_name}' stage.
        Each ad object should have a unique "Ad Name" like "LinkedIn_{stage_name.replace(" ", "")}_Ver_X".
        {{
          "ads": [
            // {content_count} LinkedIn ad objects here for {stage_name}, for example:
            {{
              "Ad Name": "LinkedIn_{stage_name.replace(" ", "")}_Ver_1",
              "Funnel Stage": "{stage_name}",
              "Introductory Text": "Generated introductory text for variation 1.",
              "Image Copy": "Suggested text overlay or concept for variation 1 image/video.",
              "Headline": "Generated headline for variation 1.",
              "Destination": "{config['destination']}",
              "CTA Button": "{config['cta_button']}"
            }},
            {{
              "Ad Name": "LinkedIn_{stage_name.replace(" ", "")}_Ver_2",
              "Funnel Stage": "{stage_name}",
              "Introductory Text": "Generated introductory text for variation 2.",
              "Image Copy": "Suggested text overlay or concept for variation 2 image/video.",
              "Headline": "Generated headline for variation 2.",
              "Destination": "{config['destination']}",
              "CTA Button": "{config['cta_button']}"
            }}
            // ... and so on, up to {content_count} variations for this stage
          ]
        }}
        """
        messages = [
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": user_prompt_content}
        ]
        all_prompts_messages.append(messages)
    return all_prompts_messages
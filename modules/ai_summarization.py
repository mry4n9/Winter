import streamlit as st
import openai

# This function will be cached in app.py where it's called with specific inputs
def summarize_text(text_to_summarize: str, api_key: str, model_name: str = "gpt-4.1-mini", target_chars: int = 2500) -> str:
    """
    Summarizes text using OpenAI API.
    The prompt is kept simple as per requirements and can be manually edited later.
    """
    if not text_to_summarize:
        return ""
    if not api_key:
        st.error("OpenAI API key not found. Please set it in secrets.toml.")
        return "Error: API key not configured."

    openai.api_key = api_key
    
    # Simple prompt for summarization (user will manually edit this later)
    prompt_content = f"Summarize this text to approximately {target_chars} characters: \n\n{text_to_summarize}"
    
    # Estimate max_tokens. Average token is ~4 chars.
    # Add a small buffer.
    max_tokens_for_summary = int(target_chars / 3.5) # A bit more generous than /4

    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert summarization AI."},
                {"role": "user", "content": prompt_content}
            ],
            max_tokens=max_tokens_for_summary, 
            temperature=0.3 # Lower temperature for more factual summaries
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except openai.error.AuthenticationError:
        st.error("OpenAI API Key is invalid or not authorized. Please check your secrets.toml.")
        return "Error: OpenAI Authentication Failed."
    except openai.error.RateLimitError:
        st.error("OpenAI API rate limit exceeded. Please try again later or check your plan.")
        return "Error: OpenAI Rate Limit Exceeded."
    except openai.error.InvalidRequestError as e:
        st.error(f"OpenAI Invalid Request: {e}. This might be due to excessive input length or model issues.")
        return f"Error: OpenAI Invalid Request - {e}."
    except Exception as e:
        st.error(f"An unexpected error occurred during summarization with OpenAI: {e}")
        return f"Error during summarization: {e}"
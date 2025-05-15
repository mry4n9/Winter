import streamlit as st
import openai

# This function will be cached in app.py where it's called with specific inputs
def summarize_text(text_to_summarize: str, api_key: str, model_name: str = "gpt-4.1-mini", target_chars: int = 2500) -> str:
    """
    Summarizes text using OpenAI API.
    The prompt is kept simple and can be manually edited later.
    """
    if not text_to_summarize:
        return ""
    if not api_key:
        st.error("OpenAI API key not found. Please set it in secrets.toml.")
        return "Error: API key not configured."

    try:
        client = openai.OpenAI(api_key=api_key)

        # Prompt for summarization
        prompt_content = f"Summarize this text to approximately {target_chars} characters:\n\n{text_to_summarize}"

        # Estimate max_tokens (tokens ≈ chars / 3.5)
        max_tokens_for_summary = int(target_chars / 3.5)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert summarization AI."},
                {"role": "user", "content": prompt_content}
            ],
            max_tokens=max_tokens_for_summary,
            temperature=0.3
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except openai.AuthenticationError:
        st.error("OpenAI API Key is invalid or not authorized. Please check your secrets.toml.")
        return "Error: OpenAI Authentication Failed."
    except openai.RateLimitError:
        st.error("OpenAI API rate limit exceeded. Please try again later or check your plan.")
        return "Error: OpenAI Rate Limit Exceeded."
    except openai.InvalidRequestError as e:
        st.error(f"OpenAI Invalid Request: {e}. This might be due to excessive input length or model issues.")
        return f"Error: OpenAI Invalid Request - {e}."
    except Exception as e:
        st.error(f"An unexpected error occurred during summarization with OpenAI: {e}")
        return f"Error during summarization: {e}"
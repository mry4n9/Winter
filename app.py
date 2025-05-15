import streamlit as st
import openai
import json
from io import BytesIO

# Import project modules
from modules import utils, context_extraction, ai_summarization, transparency_report, excel_processing
from prompts import email_prompts, linkedin_prompts, facebook_prompts, google_search_prompts, google_display_prompts

# --- Page Configuration ---
st.set_page_config(page_title="M Funnel Generator", layout="wide")

# --- Helper function for OpenAI API calls ---
def call_openai_for_ads(api_key: str, model_name: str, list_of_message_sets: list, channel_name: str) -> list:
    openai.api_key = api_key
    collected_ads = []
    
    progress_bar = st.progress(0)
    total_calls = len(list_of_message_sets)

    for i, messages in enumerate(list_of_message_sets):
        st.write(f"Generating ad content for {channel_name} (Prompt {i+1}/{total_calls})...")
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"} # Requires newer models
            )
            content = response.choices[0].message.content.strip()
            
            # Attempt to parse JSON
            try:
                # The entire content should be the JSON object if response_format is honored
                json_data = json.loads(content)
                
                if channel_name in ["Google Search", "Google Display"]:
                    # These channels expect a list of ads under an "ads" key in a single response
                    if "ads" in json_data and isinstance(json_data["ads"], list):
                        collected_ads.extend(json_data["ads"])
                    else:
                        st.error(f"Unexpected JSON structure for {channel_name}. Expected 'ads' list. Got: {json_data}")
                        # Add placeholder if structure is wrong to avoid breaking excel
                        if channel_name == "Google Search":
                             collected_ads.extend([{"Headline": "Error", "Description": "Error in generation"}] * 15)
                        else: # Google Display
                             collected_ads.extend([{"Headline": "Error", "Description": "Error in generation"}] * 5)

                else: # Email, LinkedIn, Facebook - one ad object per call
                    collected_ads.append(json_data)

            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON for {channel_name} (Prompt {i+1}): {e}. Response: {content}")
                # Add placeholder for this ad
                if channel_name == "Email": collected_ads.append({"Ad Name": f"Error_{i+1}", "Headline": "JSON Parse Error"})
                elif channel_name == "LinkedIn": collected_ads.append({"Ad Name": f"Error_{i+1}", "Headline": "JSON Parse Error"})
                elif channel_name == "Facebook": collected_ads.append({"Ad Name": f"Error_{i+1}", "Headline": "JSON Parse Error"})

        except openai.error.AuthenticationError:
            st.error("OpenAI API Key is invalid or not authorized. Halting ad generation.")
            return collected_ads # Stop further calls
        except openai.error.RateLimitError:
            st.error(f"OpenAI API rate limit exceeded during {channel_name} generation. Try again later.")
            # Potentially add placeholder for this ad and continue or stop
        except openai.error.InvalidRequestError as e:
             st.error(f"OpenAI Invalid Request for {channel_name} (Prompt {i+1}): {e}. This might be due to prompt issues or model limitations.")
        except Exception as e:
            st.error(f"Error calling OpenAI for {channel_name} (Prompt {i+1}): {e}")
        
        progress_bar.progress((i + 1) / total_calls)
    
    progress_bar.empty() # Clear progress bar after completion
    return collected_ads

# --- Caching for Summaries ---
@st.cache_data(show_spinner="Summarizing text...")
def get_ai_summary(_text_to_summarize, _api_key, _model_name, _cache_key_prefix="summary"):
    # _cache_key_prefix is to ensure different summaries have different cache keys
    # The actual parameters used by summarize_text are passed directly
    return ai_summarization.summarize_text(_text_to_summarize, _api_key, _model_name)

# --- Streamlit Frontend ---
st.title("M Funnel Generator")

# --- Session State Initialization ---
if 'output_generated' not in st.session_state:
    st.session_state.output_generated = False
    st.session_state.docx_bytes = None
    st.session_state.xlsx_bytes = None
    st.session_state.sanitized_company_name = "report"


# --- Inputs ---
st.header("1. Extract Company Context")
company_name = st.text_input("Company Name*", key="company_name", placeholder="e.g., Danish Water")
client_url = st.text_input("Client’s Website URL", key="client_url")
additional_context_file = st.file_uploader("Upload Additional Company Context (PDF or PPTX)", type=["pdf", "pptx"], key="additional_context_file")
lead_magnet_file = st.file_uploader("Upload Lead Magnet (PDF)", type=["pdf"], key="lead_magnet_file")

st.header("2. Other Options")
lead_objective_options = ["Demo Booking", "Sales Meeting"]
lead_objective = st.selectbox("Lead Objective", options=lead_objective_options, key="lead_objective")

learn_more_link = st.text_input("Link to 'Learn More' Page", key="learn_more_link")
magnet_link = st.text_input("Link to Lead Magnet Download/Page", key="magnet_link")
book_link = st.text_input("Link to Demo Booking or Sales Meeting Page*", key="book_link")

content_count = st.slider("Content Count per Stage (Email, LinkedIn, Facebook)", min_value=1, max_value=20, value=3, key="content_count")

# --- Generate Button ---
st.markdown("---")
generate_button = st.button("🚀 Generate Ad Content & Report")
st.markdown("---")

if generate_button:
    # --- Validation ---
    if not company_name:
        st.error("Company Name is required.")
    elif not book_link: # Assuming book_link is critical for some ad types
        st.error("Link to Demo Booking or Sales Meeting Page is required.")
    else:
        st.session_state.output_generated = False # Reset on new generation
        st.session_state.docx_bytes = None
        st.session_state.xlsx_bytes = None

        # --- API Key ---
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
            if not api_key or api_key == "your_openai_api_key_here":
                st.error("OpenAI API key not configured in .streamlit/secrets.toml. Please set it up.")
                st.stop()
        except KeyError:
            st.error("OPENAI_API_KEY not found in .streamlit/secrets.toml. Please create this file and add your key.")
            st.stop()
        
        openai_model = "gpt-4.1-mini" # As specified
        st.session_state.sanitized_company_name = utils.sanitize_filename(company_name)

        with st.spinner("Processing... This may take a few minutes."):
            # --- 1. Context Extraction ---
            st.subheader("Step 1: Extracting Context")
            url_context_raw = ""
            if client_url:
                with st.spinner(f"Extracting text from URL: {client_url}..."):
                    url_context_raw = context_extraction.extract_text_from_url(client_url)
                st.info(f"URL extraction: {len(url_context_raw)} characters extracted.")
            
            additional_context_raw = ""
            if additional_context_file:
                with st.spinner(f"Extracting text from additional context file: {additional_context_file.name}..."):
                    additional_context_raw = context_extraction.extract_text_from_uploaded_file(additional_context_file)
                st.info(f"Additional context extraction: {len(additional_context_raw)} characters extracted.")

            lead_magnet_raw = ""
            if lead_magnet_file:
                with st.spinner(f"Extracting text from lead magnet file: {lead_magnet_file.name}..."):
                    lead_magnet_raw = context_extraction.extract_text_from_uploaded_file(lead_magnet_file)
                st.info(f"Lead magnet extraction: {len(lead_magnet_raw)} characters extracted.")

            # --- 2. AI Summarization ---
            st.subheader("Step 2: AI Summarization")
            url_context_sum = get_ai_summary(url_context_raw, api_key, openai_model, "url_sum") if url_context_raw else ""
            if url_context_raw: st.info(f"URL summary: {len(url_context_sum)} characters generated.")
            
            additional_context_sum = get_ai_summary(additional_context_raw, api_key, openai_model, "add_sum") if additional_context_raw else ""
            if additional_context_raw: st.info(f"Additional context summary: {len(additional_context_sum)} characters generated.")
            
            lead_magnet_sum = get_ai_summary(lead_magnet_raw, api_key, openai_model, "lm_sum") if lead_magnet_raw else ""
            if lead_magnet_raw: st.info(f"Lead magnet summary: {len(lead_magnet_sum)} characters generated.")

            # --- 3. Transparency Report (DOCX) ---
            st.subheader("Step 3: Generating Transparency Report")
            with st.spinner("Creating DOCX report..."):
                st.session_state.docx_bytes = transparency_report.create_report_docx(
                    company_name,
                    url_context_raw, url_context_sum,
                    additional_context_raw, additional_context_sum,
                    lead_magnet_raw, lead_magnet_sum
                )
            st.info("DOCX report generated.")

            # --- 4. Prepare Prompts & 5. AI Ad Generation ---
            st.subheader("Step 4 & 5: Generating Ad Content with AI")
            all_ad_data = {}

            # Email Ads
            with st.spinner("Generating Email ads..."):
                email_msg_list = email_prompts.get_email_prompts_messages(
                    url_context_sum, additional_context_sum, lead_objective, book_link, content_count
                )
                all_ad_data['Email'] = call_openai_for_ads(api_key, openai_model, email_msg_list, "Email")
            st.info(f"Generated {len(all_ad_data.get('Email', []))} Email ad variations.")

            # LinkedIn Ads
            with st.spinner("Generating LinkedIn ads..."):
                linkedin_msg_list = linkedin_prompts.get_linkedin_prompts_messages(
                    url_context_sum, additional_context_sum, lead_magnet_sum,
                    learn_more_link, magnet_link, book_link, lead_objective, content_count
                )
                all_ad_data['LinkedIn'] = call_openai_for_ads(api_key, openai_model, linkedin_msg_list, "LinkedIn")
            st.info(f"Generated {len(all_ad_data.get('LinkedIn', []))} LinkedIn ad variations.")

            # Facebook Ads
            with st.spinner("Generating Facebook ads..."):
                facebook_msg_list = facebook_prompts.get_facebook_prompts_messages(
                    url_context_sum, additional_context_sum, lead_magnet_sum,
                    learn_more_link, magnet_link, book_link, lead_objective, content_count
                )
                all_ad_data['Facebook'] = call_openai_for_ads(api_key, openai_model, facebook_msg_list, "Facebook")
            st.info(f"Generated {len(all_ad_data.get('Facebook', []))} Facebook ad variations.")

            # Google Search Ads
            with st.spinner("Generating Google Search ads..."):
                gsearch_msg_list = google_search_prompts.get_google_search_prompts_messages(
                    url_context_sum, additional_context_sum
                )
                all_ad_data['Google Search'] = call_openai_for_ads(api_key, openai_model, gsearch_msg_list, "Google Search")
            st.info(f"Generated {len(all_ad_data.get('Google Search', []))} Google Search ad components.")
            
            # Google Display Ads
            with st.spinner("Generating Google Display ads..."):
                gdisplay_msg_list = google_display_prompts.get_google_display_prompts_messages(
                    url_context_sum, additional_context_sum
                )
                all_ad_data['Google Display'] = call_openai_for_ads(api_key, openai_model, gdisplay_msg_list, "Google Display")
            st.info(f"Generated {len(all_ad_data.get('Google Display', []))} Google Display ad components.")

            # --- 6. Excel Report (XLSX) ---
            st.subheader("Step 6: Generating Excel Report")
            with st.spinner("Creating XLSX report..."):
                st.session_state.xlsx_bytes = excel_processing.create_excel_report(all_ad_data)
            st.info("XLSX report generated.")
            
            st.session_state.output_generated = True
            st.success("All content generated successfully!")

# --- Download Buttons ---
if st.session_state.output_generated:
    st.header("3. Download Outputs")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.docx_bytes:
            st.download_button(
                label="Download AI Transparency Report (DOCX)",
                data=st.session_state.docx_bytes,
                file_name=f"{st.session_state.sanitized_company_name}_ai_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    with col2:
        if st.session_state.xlsx_bytes:
            st.download_button(
                label="Download Ad Content (XLSX)",
                data=st.session_state.xlsx_bytes,
                file_name=f"{st.session_state.sanitized_company_name}_lead.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --- Footer ---
st.markdown("---")
st.markdown("Made by M. Version 0.7")
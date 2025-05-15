import streamlit as st
import openai
import json
from io import BytesIO
import time # For potential delay in clearing progress

# Import project modules
from modules import utils, context_extraction, ai_summarization, transparency_report, excel_processing
from prompts import email_prompts, linkedin_prompts, facebook_prompts, google_search_prompts, google_display_prompts

# --- Page Configuration ---
st.set_page_config(page_title="M Funnel Generator", layout="wide")

# --- Helper function for OpenAI API calls ---
def call_openai_for_ads(api_key: str, model_name: str, list_of_message_sets: list, channel_name: str) -> list:
    openai.api_key = api_key
    collected_ads = []
    
    # Use st.empty() for dynamic progress updates for each channel
    progress_placeholder = st.empty()

    total_api_calls = len(list_of_message_sets)
    
    for i, messages in enumerate(list_of_message_sets):
        # Update progress text for the current API call
        progress_text = f"Generating ad content for {channel_name} (API Call {i+1}/{total_api_calls})..."
        if total_api_calls > 0: # Avoid division by zero if list is empty
             progress_placeholder.progress((i) / total_api_calls, text=progress_text)
        else:
            progress_placeholder.info(f"No API calls needed for {channel_name}.")


        try:
            response = openai.OpenAI(api_key=api_key).chat.completions.create(
            model=model_name,
            messages=messages,
            response_format="json"
        )
            content = response.choices[0].message.content.strip()
            
            try:
                json_data = json.loads(content)
                
                # Handle different JSON structures based on channel
                if channel_name == "Email":
                    if "email_ads" in json_data and isinstance(json_data["email_ads"], list):
                        collected_ads.extend(json_data["email_ads"])
                    else:
                        st.error(f"Unexpected JSON for Email. Expected 'email_ads' list. Got: {json_data}")
                        collected_ads.append({"Ad Name": f"Error_Structure_Email", "Headline": "JSON Structure Error"})
                
                elif channel_name == "LinkedIn":
                    if "linkedin_ads" in json_data and isinstance(json_data["linkedin_ads"], list):
                        collected_ads.extend(json_data["linkedin_ads"])
                    else:
                        st.error(f"Unexpected JSON for LinkedIn. Expected 'linkedin_ads' list. Got: {json_data}")
                        collected_ads.append({"Ad Name": f"Error_Structure_LinkedIn", "Headline": "JSON Structure Error"})

                elif channel_name == "Facebook":
                    if "facebook_ads" in json_data and isinstance(json_data["facebook_ads"], list):
                        collected_ads.extend(json_data["facebook_ads"])
                    else:
                        st.error(f"Unexpected JSON for Facebook. Expected 'facebook_ads' list. Got: {json_data}")
                        collected_ads.append({"Ad Name": f"Error_Structure_Facebook", "Headline": "JSON Structure Error"})

                elif channel_name in ["Google Search", "Google Display"]:
                    if "ads" in json_data and isinstance(json_data["ads"], list):
                        collected_ads.extend(json_data["ads"])
                    else:
                        st.error(f"Unexpected JSON for {channel_name}. Expected 'ads' list. Got: {json_data}")
                        error_headline = "Error_GS_Structure" if channel_name == "Google Search" else "Error_GD_Structure"
                        count = 15 if channel_name == "Google Search" else 5
                        collected_ads.extend([{"Headline": error_headline, "Description": "JSON Structure Error"}] * count)
                else:
                    st.warning(f"Unknown channel type '{channel_name}' in ad generation response handling.")
                    # Fallback: assume it's a single ad object if structure is unknown
                    collected_ads.append(json_data)

            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON for {channel_name} (API Call {i+1}): {e}. Response: {content}")
                collected_ads.append({"Ad Name": f"Error_JSON_Parse_{channel_name}_{i+1}", "Headline": "JSON Parse Error"})

        except openai.error.AuthenticationError:
            st.error("OpenAI API Key is invalid or not authorized. Halting ad generation for this channel.")
            progress_placeholder.empty()
            return collected_ads # Stop further calls for this channel
        except openai.error.RateLimitError:
            st.error(f"OpenAI API rate limit exceeded for {channel_name} (API Call {i+1}). Try again later.")
            collected_ads.append({"Ad Name": f"Error_RateLimit_{channel_name}_{i+1}", "Headline": "Rate Limit Error"})
        except openai.error.InvalidRequestError as e:
             st.error(f"OpenAI Invalid Request for {channel_name} (API Call {i+1}): {e}.")
             collected_ads.append({"Ad Name": f"Error_InvalidRequest_{channel_name}_{i+1}", "Headline": "Invalid Request Error"})
        except Exception as e:
            st.error(f"Error calling OpenAI for {channel_name} (API Call {i+1}): {e}")
            collected_ads.append({"Ad Name": f"Error_Generic_{channel_name}_{i+1}", "Headline": "Generic OpenAI Error"})
    
    if total_api_calls > 0:
        progress_placeholder.progress(1.0, text=f"{channel_name} ad generation complete.")
        # Optionally clear the progress bar after a short delay or keep it
        # time.sleep(2) # Example delay
        # progress_placeholder.empty() 
    
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
company_name = st.text_input("Company Name*", key="company_name", placeholder="e.g., Danish Water Company")
client_url = st.text_input("Client’s Website URL", key="client_url")
additional_context_file = st.file_uploader("Upload Additional Company Context (PDF or PPTX)", type=["pdf", "pptx"], key="additional_context_file")
lead_magnet_file = st.file_uploader("Upload Lead Magnet (PDF)", type=["pdf"], key="lead_magnet_file")

st.header("2. Other Options")
lead_objective_options = ["Demo Booking", "Sales Meeting"]
lead_objective = st.selectbox("Lead Objective", options=lead_objective_options, key="lead_objective")

learn_more_link = st.text_input("Link to 'Learn More' Page", key="learn_more_link")
magnet_link = st.text_input("Link to Lead Magnet Download/Page", key="magnet_link")
book_link = st.text_input("Link to Demo Booking or Sales Meeting Page*", key="book_link")

content_count = st.slider("Content Count per Stage (Email, LinkedIn, Facebook)", min_value=1, max_value=20, value=10, key="content_count")

# --- Generate Button ---
st.markdown("---")
generate_button = st.button("🚀 Generate Ad Content & Report")
st.markdown("---")

# Placeholder for overall progress bar and status messages
overall_progress_bar = st.empty()
status_messages_area = st.container() # Use a container for multiple messages

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
    
    openai_model = "gpt-4.1-mini" 
    st.session_state.sanitized_company_name = utils.sanitize_filename(company_name)

    # Overall progress tracking
    # Adjusted total steps: Extraction(1), Summaries(1), Report(1), Ad Gen (5 channels, but fewer API calls)(1), Excel(1) = 5 main stages
    total_main_stages = 5 
    current_main_stage = 0
    
    def update_overall_progress(message=""):
        current_main_stage += 1
        progress_percentage = current_main_stage / total_main_stages
        overall_progress_bar.progress(progress_percentage, text=f"Overall Progress: {message}")

    with status_messages_area: # Log messages within this container
        st.info("Starting generation process...")

    update_overall_progress("Extracting Context...")
    # --- 1. Context Extraction ---
    with status_messages_area: st.write("🔄 Step 1: Extracting Context...")
    url_context_raw = ""
    if client_url:
        with st.spinner(f"Extracting text from URL: {client_url}..."):
            url_context_raw = context_extraction.extract_text_from_url(client_url)
        with status_messages_area: st.write(f"✔️ URL extraction: {len(url_context_raw)} chars.")
    
    additional_context_raw = ""
    if additional_context_file:
        with st.spinner(f"Extracting text from additional context file..."):
            additional_context_raw = context_extraction.extract_text_from_uploaded_file(additional_context_file)
        with status_messages_area: st.write(f"✔️ Additional context: {len(additional_context_raw)} chars.")

    lead_magnet_raw = ""
    if lead_magnet_file:
        with st.spinner(f"Extracting text from lead magnet file..."):
            lead_magnet_raw = context_extraction.extract_text_from_uploaded_file(lead_magnet_file)
        with status_messages_area: st.write(f"✔️ Lead magnet: {len(lead_magnet_raw)} chars.")
    
    update_overall_progress("AI Summarization...")
    # --- 2. AI Summarization ---
    with status_messages_area: st.write("🔄 Step 2: AI Summarization...")
    url_context_sum = get_ai_summary(url_context_raw, api_key, openai_model, "url_sum") if url_context_raw else ""
    if url_context_raw: 
        with status_messages_area: st.write(f"✔️ URL summary: {len(url_context_sum)} chars.")
    
    additional_context_sum = get_ai_summary(additional_context_raw, api_key, openai_model, "add_sum") if additional_context_raw else ""
    if additional_context_raw: 
        with status_messages_area: st.write(f"✔️ Additional context summary: {len(additional_context_sum)} chars.")
    
    lead_magnet_sum = get_ai_summary(lead_magnet_raw, api_key, openai_model, "lm_sum") if lead_magnet_raw else ""
    if lead_magnet_raw: 
        with status_messages_area: st.write(f"✔️ Lead magnet summary: {len(lead_magnet_sum)} chars.")

    update_overall_progress("Generating Transparency Report...")
    # --- 3. Transparency Report (DOCX) ---
    with status_messages_area: st.write("🔄 Step 3: Generating Transparency Report (DOCX)...")
    with st.spinner("Creating DOCX report..."):
        st.session_state.docx_bytes = transparency_report.create_report_docx(
            company_name, url_context_raw, url_context_sum,
            additional_context_raw, additional_context_sum,
            lead_magnet_raw, lead_magnet_sum
        )
    with status_messages_area: st.write("✔️ DOCX report generated.")

    update_overall_progress("Generating Ad Content...")
    # --- 4. Prepare Prompts & 5. AI Ad Generation ---
    with status_messages_area: st.write("🔄 Step 4 & 5: Generating Ad Content with AI...")
    all_ad_data = {}

    # Email Ads
    email_msg_list = email_prompts.get_email_prompts_messages(
        url_context_sum, additional_context_sum, lead_objective, book_link, content_count
    )
    all_ad_data['Email'] = call_openai_for_ads(api_key, openai_model, email_msg_list, "Email")
    with status_messages_area: st.write(f"✔️ Generated {len(all_ad_data.get('Email', []))} Email ad variations.")

    # LinkedIn Ads
    linkedin_msg_list = linkedin_prompts.get_linkedin_prompts_messages(
        url_context_sum, additional_context_sum, lead_magnet_sum,
        learn_more_link, magnet_link, book_link, lead_objective, content_count
    )
    all_ad_data['LinkedIn'] = call_openai_for_ads(api_key, openai_model, linkedin_msg_list, "LinkedIn")
    with status_messages_area: st.write(f"✔️ Generated {len(all_ad_data.get('LinkedIn', []))} LinkedIn ad variations.")

    # Facebook Ads
    facebook_msg_list = facebook_prompts.get_facebook_prompts_messages(
        url_context_sum, additional_context_sum, lead_magnet_sum,
        learn_more_link, magnet_link, book_link, lead_objective, content_count
    )
    all_ad_data['Facebook'] = call_openai_for_ads(api_key, openai_model, facebook_msg_list, "Facebook")
    with status_messages_area: st.write(f"✔️ Generated {len(all_ad_data.get('Facebook', []))} Facebook ad variations.")

    # Google Search Ads
    gsearch_msg_list = google_search_prompts.get_google_search_prompts_messages(
        url_context_sum, additional_context_sum
    )
    all_ad_data['Google Search'] = call_openai_for_ads(api_key, openai_model, gsearch_msg_list, "Google Search")
    with status_messages_area: st.write(f"✔️ Generated {len(all_ad_data.get('Google Search', []))} Google Search ad components.")
    
    # Google Display Ads
    gdisplay_msg_list = google_display_prompts.get_google_display_prompts_messages(
        url_context_sum, additional_context_sum
    )
    all_ad_data['Google Display'] = call_openai_for_ads(api_key, openai_model, gdisplay_msg_list, "Google Display")
    with status_messages_area: st.write(f"✔️ Generated {len(all_ad_data.get('Google Display', []))} Google Display ad components.")

    update_overall_progress("Generating Excel Report...")
    # --- 6. Excel Report (XLSX) ---
    with status_messages_area: st.write("🔄 Step 6: Generating Excel Report (XLSX)...")
    with st.spinner("Creating XLSX report..."):
        st.session_state.xlsx_bytes = excel_processing.create_excel_report(all_ad_data)
    with status_messages_area: st.write("✔️ XLSX report generated.")
    
    st.session_state.output_generated = True
    overall_progress_bar.success("✅ All content generated successfully!")
    with status_messages_area: st.success("All steps completed!")


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
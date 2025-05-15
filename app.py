import streamlit as st
from openai import OpenAI
import json
from io import BytesIO

# Import project modules
from modules import utils, context_extraction, ai_summarization, transparency_report, excel_processing
from prompts import email_prompts, linkedin_prompts, facebook_prompts, google_search_prompts, google_display_prompts

# --- Page Configuration ---
st.set_page_config(page_title="M Funnel Generator", layout="wide")

# --- Helper function for OpenAI API calls ---
def call_openai_for_ads(api_key: str, model_name: str, list_of_message_sets: list, channel_name: str, current_content_count: int) -> list:
    # openai.api_key = api_key # Old way
    client = OpenAI(api_key=api_key) # New: Initialize client
    collected_ads = []
    
    # Progress bar for API calls within this specific channel generation
    # total_calls is len(list_of_message_sets), which is 1 for Email, 3 for LI/FB, 1 for GSearch/GDisplay
    total_calls = len(list_of_message_sets)
    # Create a unique key for the progress bar if it's inside a loop or might be re-created
    progress_bar_key = f"progress_bar_{channel_name}_{st.session_state.get('run_id', 0)}"
    progress_bar_container = st.empty() # Placeholder for progress bar

    for i, messages in enumerate(list_of_message_sets):
        # Update progress message for the specific call being made
        progress_text = f"Generating ad content for {channel_name} (API Call {i+1}/{total_calls})..."
        if total_calls > 0:
             progress_bar_container.progress((i) / total_calls, text=progress_text) # Show progress before the call
        else:
             progress_bar_container.progress(0, text=progress_text)


        try:
            # response = openai.ChatCompletion.create( # Old way
            response = client.chat.completions.create( # New way
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"} # Requires newer models
            )
            content = response.choices[0].message.content.strip()
            
            try:
                json_data = json.loads(content)
                
                if "ads" in json_data and isinstance(json_data["ads"], list):
                    collected_ads.extend(json_data["ads"])
                else:
                    st.error(f"Unexpected JSON structure for {channel_name} (API Call {i+1}). Expected 'ads' list. Got: {content[:300]}...")
                    # Add placeholder(s) if structure is wrong
                    num_placeholders_to_add = 1 # Default to one error entry for the failed call
                    if channel_name in ["Email", "LinkedIn", "Facebook"]:
                        # For these, one API call was supposed to generate 'current_content_count' ads
                        # If the structure is wrong, we add 'current_content_count' error entries
                        # or a single one representing the batch failure.
                        # Let's add one error entry representing the failed batch for simplicity.
                        pass # One placeholder is fine.

                    error_ad_name = f"StructError_{channel_name}_Call_{i+1}"
                    if channel_name == "Email":
                        collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Demand Capture", "Headline": "Generation Error", "Subject Line": "", "Body": "", "CTA": ""})
                    elif channel_name == "LinkedIn":
                        collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Error", "Introductory Text": "Generation Error", "Image Copy": "", "Headline": "", "Destination": "", "CTA Button": ""})
                    elif channel_name == "Facebook":
                        collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Error", "Primary Text": "Generation Error", "Image Copy": "", "Headline": "", "Link Description": "", "Destination": "", "CTA Button": ""})
                    elif channel_name == "Google Search":
                         collected_ads.extend([{"Headline": "StructError", "Description": "JSON Structure Error"}] * 15)
                    elif channel_name == "Google Display":
                         collected_ads.extend([{"Headline": "StructError", "Description": "JSON Structure Error"}] * 5)

            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON for {channel_name} (API Call {i+1}): {e}. Response: {content[:300]}...")
                error_ad_name = f"JSONError_{channel_name}_Call_{i+1}"
                if channel_name == "Email": collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Demand Capture", "Headline": "JSON Parse Error", "Subject Line": "", "Body": "", "CTA": ""})
                elif channel_name == "LinkedIn": collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Error", "Introductory Text": "JSON Parse Error", "Image Copy": "", "Headline": "", "Destination": "", "CTA Button": ""})
                elif channel_name == "Facebook": collected_ads.append({"Ad Name": error_ad_name, "Funnel Stage": "Error", "Primary Text": "JSON Parse Error", "Image Copy": "", "Headline": "", "Link Description": "", "Destination": "", "CTA Button": ""})
                elif channel_name == "Google Search": collected_ads.extend([{"Headline": "JSONError", "Description": "JSON Parse Error"}] * 15)
                elif channel_name == "Google Display": collected_ads.extend([{"Headline": "JSONError", "Description": "JSON Parse Error"}] * 5)

        except openai.AuthenticationError: # openai.error.AuthenticationError old
            st.error("OpenAI API Key is invalid or not authorized. Halting ad generation for this channel.")
            # Add a clear error marker for this channel's batch
            collected_ads.append({"Ad Name": f"AuthError_{channel_name}", "Headline": "OpenAI Auth Failed"})
            break # Stop further calls for this channel
        except openai.RateLimitError: # openai.error.RateLimitError old
            st.error(f"OpenAI API rate limit exceeded during {channel_name} generation (API Call {i+1}). Try again later.")
            collected_ads.append({"Ad Name": f"RateLimitError_{channel_name}", "Headline": "Rate Limit Exceeded"})
            # Optionally break or continue with placeholders for remaining calls in this channel
        except openai.APIConnectionError as e: # New error type to consider
            st.error(f"OpenAI API connection error for {channel_name} (API Call {i+1}): {e}")
            collected_ads.append({"Ad Name": f"ConnectionError_{channel_name}", "Headline": "API Connection Error"})
        except openai.APIStatusError as e: # New error type for non-200 responses
            st.error(f"OpenAI API error for {channel_name} (API Call {i+1}): Status {e.status_code}, Response: {e.response}")
            collected_ads.append({"Ad Name": f"APIStatusError_{channel_name}", "Headline": f"API Error {e.status_code}"})
        except openai.BadRequestError as e: # openai.error.InvalidRequestError old, now BadRequestError
             st.error(f"OpenAI Invalid Request for {channel_name} (API Call {i+1}): {e}. This might be due to prompt issues or model limitations.")
             collected_ads.append({"Ad Name": f"InvalidRequest_{channel_name}", "Headline": "Invalid Request to OpenAI"})
        except Exception as e:
            st.error(f"An unexpected error occurred calling OpenAI for {channel_name} (API Call {i+1}): {e}")
            collected_ads.append({"Ad Name": f"UnexpectedError_{channel_name}", "Headline": "Unexpected OpenAI Error"})
        
        if total_calls > 0:
            progress_bar_container.progress((i + 1) / total_calls, text=f"{channel_name} (API Call {i+1}/{total_calls}) Complete")
    
    progress_bar_container.empty() # Clear progress bar after completion for this channel
    return collected_ads

# --- Caching for Summaries ---
@st.cache_data(show_spinner="Summarizing text...")
def get_ai_summary(_text_to_summarize, _api_key, _model_name, _cache_key_prefix="summary"):
    return ai_summarization.summarize_text(_text_to_summarize, _api_key, _model_name)

# --- Streamlit Frontend ---
st.title("M Funnel Generator")

# --- Session State Initialization ---
if 'output_generated' not in st.session_state:
    st.session_state.output_generated = False
    st.session_state.docx_bytes = None
    st.session_state.xlsx_bytes = None
    st.session_state.sanitized_company_name = "report"
if 'run_id' not in st.session_state: # For unique progress bar keys if needed
    st.session_state.run_id = 0


# --- Inputs ---
st.header("1. Extract Company Context")
company_name = st.text_input("Company Name*", key="company_name", placeholder="e.g., Danish Water Corp")
client_url = st.text_input("Client’s Website URL", key="client_url")
additional_context_file = st.file_uploader("Upload Additional Company Context (PDF or PPTX)", type=["pdf", "pptx"], key="additional_context_file")
lead_magnet_file = st.file_uploader("Upload Lead Magnet (PDF)", type=["pdf"], key="lead_magnet_file")

st.header("2. Other Options")
lead_objective_options = ["Demo Booking", "Sales Meeting"]
lead_objective = st.selectbox("Lead Objective", options=lead_objective_options, key="lead_objective")

learn_more_link = st.text_input("Link to 'Learn More' Page", key="learn_more_link")
magnet_link = st.text_input("Link to Lead Magnet Download/Page", key="magnet_link")
book_link = st.text_input("Link to Demo Booking or Sales Meeting Page*", key="book_link")

content_count_input = st.slider("Content Count per Stage (Email, LinkedIn, Facebook)", min_value=1, max_value=20, value=3, key="content_count")

# --- Generate Button ---
st.markdown("---")
generate_button = st.button("🚀 Generate Ad Content & Report")
st.markdown("---")

if generate_button:
    st.session_state.run_id += 1 # Increment run_id for unique keys
    # --- Validation ---
    if not company_name:
        st.error("Company Name is required.")
    elif not book_link: 
        st.error("Link to Demo Booking or Sales Meeting Page is required.")
    else:
        st.session_state.output_generated = False 
        st.session_state.docx_bytes = None
        st.session_state.xlsx_bytes = None

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

        # Main progress status for the whole generation process
        main_progress_text = "Starting generation process..."
        main_progress_bar = st.progress(0, text=main_progress_text)
        total_steps = 6 # Extraction, Summarization, DOCX, Email, LI, FB, GSearch, GDisplay, XLSX (approx)
        current_step = 0

        def update_main_progress(step_increment, text):
            nonlocal current_step
            current_step += step_increment
            main_progress_bar.progress(current_step / total_steps, text=text)

        with st.spinner("Overall process running... please wait."): # General spinner
            # --- 1. Context Extraction ---
            update_main_progress(0, "Step 1: Extracting Context...") # Initial text for step 1
            st.subheader("Step 1: Extracting Context") # Keep subheaders for clarity
            url_context_raw = ""
            if client_url:
                with st.spinner(f"Extracting text from URL: {client_url}..."): # Specific spinner
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
            update_main_progress(1, "Step 1: Context Extraction Complete.")

            # --- 2. AI Summarization ---
            update_main_progress(0, "Step 2: AI Summarization...")
            st.subheader("Step 2: AI Summarization")
            url_context_sum = get_ai_summary(url_context_raw, api_key, openai_model, f"url_sum_{st.session_state.run_id}") if url_context_raw else ""
            if url_context_raw: st.info(f"URL summary: {len(url_context_sum)} characters generated.")
            
            additional_context_sum = get_ai_summary(additional_context_raw, api_key, openai_model, f"add_sum_{st.session_state.run_id}") if additional_context_raw else ""
            if additional_context_raw: st.info(f"Additional context summary: {len(additional_context_sum)} characters generated.")
            
            lead_magnet_sum = get_ai_summary(lead_magnet_raw, api_key, openai_model, f"lm_sum_{st.session_state.run_id}") if lead_magnet_raw else ""
            if lead_magnet_raw: st.info(f"Lead magnet summary: {len(lead_magnet_sum)} characters generated.")
            update_main_progress(1, "Step 2: AI Summarization Complete.")

            # --- 3. Transparency Report (DOCX) ---
            update_main_progress(0, "Step 3: Generating Transparency Report...")
            st.subheader("Step 3: Generating Transparency Report")
            with st.spinner("Creating DOCX report..."):
                st.session_state.docx_bytes = transparency_report.create_report_docx(
                    company_name,
                    url_context_raw, url_context_sum,
                    additional_context_raw, additional_context_sum,
                    lead_magnet_raw, lead_magnet_sum
                )
            st.info("DOCX report generated.")
            update_main_progress(1, "Step 3: Transparency Report Complete.")

            # --- 4. Prepare Prompts & 5. AI Ad Generation ---
            update_main_progress(0, "Step 4 & 5: Generating Ad Content with AI...")
            st.subheader("Step 4 & 5: Generating Ad Content with AI")
            all_ad_data = {}

            # Email Ads
            st.write("Processing Email ads...") # Main status update
            email_msg_list = email_prompts.get_email_prompts_messages(
                url_context_sum, additional_context_sum, lead_objective, book_link, content_count_input
            )
            all_ad_data['Email'] = call_openai_for_ads(api_key, openai_model, email_msg_list, "Email", content_count_input)
            st.info(f"Generated {len(all_ad_data.get('Email', []))} Email ad variations.")

            # LinkedIn Ads
            st.write("Processing LinkedIn ads...")
            linkedin_msg_list = linkedin_prompts.get_linkedin_prompts_messages(
                url_context_sum, additional_context_sum, lead_magnet_sum,
                learn_more_link, magnet_link, book_link, lead_objective, content_count_input
            )
            all_ad_data['LinkedIn'] = call_openai_for_ads(api_key, openai_model, linkedin_msg_list, "LinkedIn", content_count_input)
            st.info(f"Generated {len(all_ad_data.get('LinkedIn', []))} LinkedIn ad variations.")

            # Facebook Ads
            st.write("Processing Facebook ads...")
            facebook_msg_list = facebook_prompts.get_facebook_prompts_messages(
                url_context_sum, additional_context_sum, lead_magnet_sum,
                learn_more_link, magnet_link, book_link, lead_objective, content_count_input
            )
            all_ad_data['Facebook'] = call_openai_for_ads(api_key, openai_model, facebook_msg_list, "Facebook", content_count_input)
            st.info(f"Generated {len(all_ad_data.get('Facebook', []))} Facebook ad variations.")
            update_main_progress(1, "Step 4 & 5: Email, LinkedIn, Facebook Ads Complete.")

            # Google Search Ads
            update_main_progress(0, "Step 4 & 5: Generating Google Search Ads...")
            st.write("Processing Google Search ads...")
            gsearch_msg_list = google_search_prompts.get_google_search_prompts_messages(
                url_context_sum, additional_context_sum
            )
            # For Google Search, content_count is fixed (15 items from 1 API call)
            all_ad_data['Google Search'] = call_openai_for_ads(api_key, openai_model, gsearch_msg_list, "Google Search", 15) 
            st.info(f"Generated {len(all_ad_data.get('Google Search', []))} Google Search ad components.")
            
            # Google Display Ads
            update_main_progress(0, "Step 4 & 5: Generating Google Display Ads...") # Separate small progress for these
            st.write("Processing Google Display ads...")
            gdisplay_msg_list = google_display_prompts.get_google_display_prompts_messages(
                url_context_sum, additional_context_sum
            )
            # For Google Display, content_count is fixed (5 items from 1 API call)
            all_ad_data['Google Display'] = call_openai_for_ads(api_key, openai_model, gdisplay_msg_list, "Google Display", 5)
            st.info(f"Generated {len(all_ad_data.get('Google Display', []))} Google Display ad components.")
            update_main_progress(1, "Step 4 & 5: All Ad Generation Complete.")


            # --- 6. Excel Report (XLSX) ---
            update_main_progress(0, "Step 6: Generating Excel Report...")
            st.subheader("Step 6: Generating Excel Report")
            with st.spinner("Creating XLSX report..."):
                st.session_state.xlsx_bytes = excel_processing.create_excel_report(all_ad_data)
            st.info("XLSX report generated.")
            update_main_progress(1, "Step 6: Excel Report Complete.")
            
            main_progress_bar.progress(1.0, text="All content generated successfully!")
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
import streamlit as st
import streamlit.components.v1 as components
import openai
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# --- User Key Input ---
with st.sidebar:
    st.header("Configuration")
    st.markdown("Enter your OpenAI API key below.")
    st.markdown("Your key is used for this session only and is not stored or saved.")
    user_openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="You can get your key from https://platform.openai.com/account/api-keys"
    )

# --- App Logic: API Key Validation ---
if user_openai_key:
    openai.api_key = user_openai_key

    try:
        openai.models.list()
        st.sidebar.success("API Key is valid!")

        # --- Core Functionality: Transcribing Audio ---
        def transcribe_audio(audio_file_path):
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text
            except openai.OpenAIError as e:
                st.error(f"An error occurred with the OpenAI API: {e}")
                return None

        # --- New Functionality: Formatting Text based on type ---
        def format_text(raw_text, format_type, openai_model="gpt-4o"):
            prompts = {
                "Article": f"""
                You are an expert content writer. Your task is to take the following raw text from an audio transcription and format it into a well-structured, easy-to-read blog post or article.

                The article should include:
                - A catchy and descriptive title.
                - A brief introductory paragraph.
                - Multiple sections with clear and descriptive headings (using Markdown ##).
                - Bullet points or numbered lists where appropriate to improve readability.
                - A concluding summary.

                Make sure to fix any grammatical errors, add punctuation, and smooth out the language to make it sound natural and professional. Do not add any new information that is not present in the original text.

                Here is the raw text to format:
                ---
                {raw_text}
                ---

                Please provide the final formatted article.
                """,
                "Script": f"""
                You are a professional video script writer. Your task is to take the following raw text from an audio transcription and format it into a clean, easy-to-follow video script.

                The script should be broken down into clear segments, with a title and an introduction. Add some simple actions or shot suggestions in parentheses, like "(FADE IN)" or "(CUT TO: Close-up)". Keep it concise and professional.

                Here is the raw text to format:
                ---
                {raw_text}
                ---

                Please provide the final formatted video script.
                """,
                "Social Media Caption": f"""
                You are a social media expert. Your task is to take the following raw text and turn it into a concise, engaging social media caption for platforms like Instagram, Facebook, or LinkedIn.

                The caption should be short, punchy, and include 3-5 relevant hashtags. It should also have a clear call-to-action (CTA), like asking a question to encourage engagement. Do not add any new information.

                Here is the raw text to format:
                ---
                {raw_text}
                ---

                Please provide the final social media caption.
                """,
                "Summary": f"""
                You are an expert summarizer. Your task is to take the following raw text and create a concise, yet comprehensive summary.

                The summary should be no more than 3-4 sentences. Focus on the most important points and key takeaways. Do not include minor details.

                Here is the raw text to summarize:
                ---
                {raw_text}
                ---

                Please provide the final summary.
                """,
                "Amazon Review": f"""
                You are a professional product reviewer. Your task is to take the following raw text from an audio transcription and write a concise, helpful Amazon-style review.

                The review should have a title and a body. It should clearly state a star rating (from 1 to 5) and focus on the pros, cons, and a final recommendation. Use a conversational and honest tone. Do not add any new information that is not present in the original text.

                Here is the raw text to format into a review:
                ---
                {raw_text}
                ---

                Please provide the final Amazon review.
                """
            }

            selected_prompt = prompts.get(format_type, prompts["Article"])

            try:
                response = openai.chat.completions.create(
                    model=openai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful and professional writing assistant."},
                        {"role": "user", "content": selected_prompt}
                    ],
                    temperature=0.7
                )
                return response.choices[0].message.content
            except openai.OpenAIError as e:
                st.error(f"An error occurred with the OpenAI API: {e}")
                return None

        # --- Streamlit App Interface ---
        st.set_page_config(page_title="Audio-to-Article Converter", layout="centered")
        st.title("🗣️ Audio-to-Article Converter")
        st.markdown("Easily convert spoken audio into a professionally formatted article.")

        if 'transcribed_text' not in st.session_state:
            st.session_state.transcribed_text = None

        tab1, tab2 = st.tabs(["Upload an Audio File", "Record Live Audio"])

        with tab1:
            st.subheader("1. Upload an Audio File")
            uploaded_file = st.file_uploader(
                "Choose an audio file...",
                type=["mp3", "m4a", "wav"]
            )
            if uploaded_file:
                with st.spinner("Transcribing uploaded audio..."):
                    # Use a secure and simple temporary filename
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
                        temp_audio_file.write(uploaded_file.getbuffer())
                        temp_file_path = temp_audio_file.name

                    st.audio(uploaded_file, format='audio/wav')
                    transcribed_text = transcribe_audio(temp_file_path)
                    st.session_state.transcribed_text = transcribed_text
                    os.remove(temp_file_path)
                    if transcribed_text:
                        st.success("Transcription complete!")
                        st.subheader("Raw Transcription")
                        st.write(transcribed_text)

        with tab2:
            st.subheader("2. Record Live Audio")
            st.markdown("Click the button to start and stop recording. The recording will start as soon as your browser grants permission.")
            audio_bytes = audio_recorder(
                text="Start Recording",
                recording_color="#e8b62c",
                neutral_color="#6aa36f",
                icon_size="3x"
            )
            if audio_bytes:
                with st.spinner("Transcribing live audio..."):
                    temp_file_path = "temp_recorded_audio.wav"
                    with open(temp_file_path, "wb") as f:
                        f.write(audio_bytes)
                    st.audio(audio_bytes, format="audio/wav")
                    transcribed_text = transcribe_audio(temp_file_path)
                    st.session_state.transcribed_text = transcribed_text
                    os.remove(temp_file_path)
                if transcribed_text:
                    st.success("Transcription complete!")
                    st.subheader("Raw Transcription")
                    st.write(transcribed_text)

        if st.session_state.transcribed_text:
            st.markdown("---")
            st.subheader("3. Select Format and Generate")

            format_type = st.selectbox(
                "Choose your desired output format:",
                options=["Article", "Script", "Social Media Caption", "Summary", "Amazon Review"]
            )

            if st.button(f"Generate {format_type}"):
                with st.spinner(f"Generating {format_type}..."):
                    formatted_content = format_text(st.session_state.transcribed_text, format_type)
                    if formatted_content:
                        st.success(f"{format_type} generation complete!")
                        st.markdown(f"## Your Formatted {format_type}")
                        st.markdown(formatted_content)

    except openai.AuthenticationError as e:
        st.sidebar.error("Invalid API Key. Please check your key and try again.")
        st.warning("Please enter a valid OpenAI API key in the sidebar to begin.")

else:
    st.warning("Please enter your OpenAI API key in the sidebar to begin.")

st.markdown("I hope you find this tool useful! If you do consider starring this repository on GitHub, and supporting me on Ko-fi. Thank you!")

kofi_html = """
<script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script><script type='text/javascript'>kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'Q5Q11L449E');kofiwidget2.draw();</script>
"""
components.html(kofi_html, height=70, width=220)

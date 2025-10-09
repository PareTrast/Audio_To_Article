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

# --- Set API Key ---
# Check if the user has provided a key and use it.
# We will not load from .env file for public use.
openai.api_key = user_openai_key

# --- Conditional App Execution ---
if not openai.api_key:
    # If no key is provided, display an error and stop execution
    st.warning("Please enter your OpenAI API key in the sidebar to begin.")
    # The app stops here until the user provides a key
    st.stop()
else:
    # If a key is provided, continue with the rest of the application
    st.sidebar.success("API Key is valid!")

    # --- Core Functionality: Transcribing Audio ---
    def transcribe_audio(audio_file_path):
        """
        Transcribes an audio file into text using OpenAI's Whisper model.
        """
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

    # --- New Functionality: Formatting the Article ---
    def format_as_article(raw_text, openai_model="gpt-4o"):
        """
        Takes raw transcribed text and formats it into a blog post/article.
        """
        prompt = f"""
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
        """
        try:
            response = openai.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful and professional writing assistant."},
                    {"role": "user", "content": prompt}
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
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

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
        st.subheader("3. Generate a Formatted Article")

        if st.button("Generate Article from Transcription"):
            with st.spinner("Generating article..."):
                formatted_article = format_as_article(st.session_state.transcribed_text)

                if formatted_article:
                    st.success("Article generation complete!")
                    st.markdown("## Your Formatted Article")
                    st.markdown(formatted_article)

st.markdown("I hope you find this tool useful! If you do consider starring this repository on GitHub, and supporting me on Ko-fi. Thank you!")

kofi_html = """
<script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script><script type='text/javascript'>kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'Q5Q11L449E');kofiwidget2.draw();</script>
"""
components.html(kofi_html, height=70, width=220)

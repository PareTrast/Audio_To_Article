import streamlit as st
import openai
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# --- Configuration and Setup ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# Initialize session state variables
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = None

# Using tabs to separate the two different input methods
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

    # A placeholder to show a temporary message
    status_placeholder = st.empty()

    # The audio recorder widget
    audio_bytes = audio_recorder(
        text="Start Recording",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_size="3x"
    )

    if audio_bytes:
        # Clear the temporary message once recording is done
        status_placeholder.empty()

        # Show a spinner while the transcription is processing
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

# --- Article Generation Section (appears after any transcription) ---
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

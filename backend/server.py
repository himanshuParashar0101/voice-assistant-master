import os
import io
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
from openai import OpenAI
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
import requests
from dotenv import load_dotenv  # Import dotenv
load_dotenv()
app = FastAPI()

# CORS configuration (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Check if the API key is set and print it
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"OpenAI API Key is set: {api_key}")
else:
    print("OpenAI API Key is not set.")


# Set Google Cloud project ID
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
if GOOGLE_CLOUD_PROJECT:
    print(f"Google Cloud Project ID is set: {GOOGLE_CLOUD_PROJECT}")
else:
    print("Google Cloud Project ID is not set.")

# Set OpenAI model to use (GPT-4)
OPENAI_MODEL = "gpt-4o"

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive the audio file from the client
        data = await websocket.receive_bytes()
        audio_data = io.BytesIO(data)

        # Convert audio data to WAV format with 16-bit, 16kHz, mono
        audio_segment = AudioSegment.from_file(audio_data, format="webm")
        audio_segment = audio_segment.set_frame_rate(16000).set_sample_width(2).set_channels(1)
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)

        # Save the WAV file locally for Google Cloud transcription
        with open("temp_audio.wav", "wb") as f:
            f.write(wav_io.read())

        # Transcribe audio data using Google Cloud
        transcription = transcribe_google_cloud("temp_audio.wav")
        print(f"Transcribed text: {transcription}")

        # Send the transcription to the client (optional)
        await websocket.send_text(json.dumps({'type': 'text', 'content': transcription}))

        # Stream GPT-4 response and TTS audio back to the client
        await generate_response_and_audio(transcription, websocket)

    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        await websocket.close()

def transcribe_google_cloud(stream_file: str) -> str:
    """Transcribes audio from an audio file stream using Google Cloud Speech-to-Text API."""
    client = SpeechClient()

    # Read the audio file as bytes
    with open(stream_file, "rb") as f:
        audio_content = f.read()

    # Split the audio into smaller chunks (max 25,600 bytes per chunk)
    max_chunk_size = 25600  # Google Cloud limit
    stream = [
        audio_content[start: start + max_chunk_size]
        for start in range(0, len(audio_content), max_chunk_size)
    ]

    audio_requests = (
        cloud_speech_types.StreamingRecognizeRequest(audio=audio) for audio in stream
    )

    recognition_config = cloud_speech_types.RecognitionConfig(
        auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )
    
    streaming_config = cloud_speech_types.StreamingRecognitionConfig(
        config=recognition_config
    )

    config_request = cloud_speech_types.StreamingRecognizeRequest(
        recognizer=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global/recognizers/_",
        streaming_config=streaming_config,
    )

    def requests(config: cloud_speech_types.RecognitionConfig, audio: list):
        yield config
        yield from audio

    # Transcribes the audio into text
    responses_iterator = client.streaming_recognize(
        requests=requests(config_request, audio_requests)
    )

    responses = []
    transcript = ""
    for response in responses_iterator:
        responses.append(response)
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "

    return transcript.strip()

async def generate_response_and_audio(transcribed_text, websocket):
    if not transcribed_text:
        await websocket.send_text(json.dumps({'type': 'text', 'content': "I'm sorry, I didn't catch that. Could you please repeat?"}))
        return

    system_prompt = "You are a helpful AI assistant that answers questions about Earth and Mars."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcribed_text}
    ]

    try:
        # Use the new OpenAI API to generate a response
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7
        )

        # Access the response from the assistant
        assistant_response = response.choices[0].message.content
        print(f"Assistant's response: {assistant_response}")

        # Send the assistant's response text to the client
        await websocket.send_text(json.dumps({'type': 'text', 'content': assistant_response}))

        # Convert the assistant's response to speech
        await generate_speech(assistant_response, websocket)

    except Exception as e:
        print(f"Error generating response: {e}")
        await websocket.send_text(json.dumps({'type': 'text', 'content': "I'm sorry, I couldn't process your request at this time."}))

async def generate_speech(text, websocket):
    try:
        # Use OpenAI's new TTS API to generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # You can change the voice model as needed
            input=text,
        )

        # Create a BytesIO object to store the binary audio response
        audio_io = io.BytesIO()

        # Write the binary audio content directly to BytesIO
        audio_io.write(response.content)

        # Reset the buffer's position to the beginning
        audio_io.seek(0)

        # Send the generated audio as bytes to the websocket client
        await websocket.send_bytes(audio_io.getvalue())
    except Exception as e:
        print(f"Error generating speech: {e}")
        await websocket.send_text(json.dumps({'type': 'text', 'content': "Error generating speech."}))
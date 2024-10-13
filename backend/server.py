import os
import io
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv

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

# Set OpenAI model to use (GPT-4)
OPENAI_MODEL = "gpt-4o"

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted.")
    try:
        while True:  # Keep the connection open
            print("Waiting to receive audio data...")
            data = await websocket.receive_bytes()  # Receive audio data
            print("Received audio data.")

            audio_data = io.BytesIO(data)

            # Convert audio data to WAV format with 16-bit, 16kHz, mono
            try:
                audio_segment = AudioSegment.from_file(audio_data, format="webm")
                print("Audio converted to WAV format.")
            except Exception as e:
                print(f"Error converting audio: {e}")
                continue

            audio_segment = audio_segment.set_frame_rate(16000).set_sample_width(2).set_channels(1)
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            # Save the WAV file locally for transcription
            with open("temp_audio.wav", "wb") as f:
                f.write(wav_io.read())
            print("Saved audio to temp_audio.wav.")

            # Transcribe audio data locally
            transcription = transcribe_audio_local("temp_audio.wav")
            print(f"Transcribed text: {transcription}")

            # Send the transcription to the client (optional)
            await websocket.send_text(json.dumps({'type': 'text', 'content': transcription}))

            # Stream GPT-4 response and TTS audio back to the client
            await generate_response_and_audio(transcription, websocket)

    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        await websocket.close()

def transcribe_audio_local(audio_file: str) -> str:
    """Transcribes audio from a local audio file using SpeechRecognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)  # Read the entire audio file
    try:
        # Use Google Web Speech API for transcription
        transcript = recognizer.recognize_google(audio)
        return transcript
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return "Could not understand audio"
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return f"Could not request results; {e}"

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
        print("Generating response from OpenAI...")
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
        print("Generating speech from text...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Change the voice model as needed
            input=text,
        )

        # Create a BytesIO object to store the binary audio response
        audio_io = io.BytesIO()
        audio_io.write(response.content)

        # Reset the buffer's position to the beginning
        audio_io.seek(0)

        # Send the generated audio as bytes to the websocket client
        await websocket.send_bytes(audio_io.getvalue())
        print("Sent generated audio to the client.")
    except Exception as e:
        print(f"Error generating speech: {e}")
        await websocket.send_text(json.dumps({'type': 'text', 'content': "Error generating speech."}))

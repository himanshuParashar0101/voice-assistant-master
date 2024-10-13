# Web Voice Assistant

This project is a web-based voice assistant built with Python and JavaScript. It integrates OpenAI's GPT models for generating responses, Google Cloud Speech-to-Text API for real-time transcription, and gTTS for text-to-speech functionalities. Users can interact with the assistant via voice commands, and the assistant responds with synthesized speech.

## Table of Contents
- Project Structure
- Prerequisites
- Setup Instructions
  - Backend Setup
  - Frontend Setup
- How to Run the Project
- How It Works
- Important Notes
- Troubleshooting
- Acknowledgments

## Project Structure

```
WebVoiceAssistant/
├── backend/
│   ├── server.py
│   ├── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
└── README.md
```

## Prerequisites
Before setting up the project, ensure you have the following installed:

- Python 3.7 or higher
- Node.js and npm (optional, if you plan to use any Node.js packages)
- Google Cloud Account with Speech-to-Text API enabled
- OpenAI API Key
- Git (optional, for cloning the repository)

## Setup Instructions

### Backend Setup

1. Clone the Repository (Optional):
   ```bash
   git clone https://github.com/yourusername/WebVoiceAssistant.git
   cd WebVoiceAssistant/backend
   ```

2. Install Backend Dependencies:
```bash
pip install -r requirements.txt
```

3. Set Environment Variables:

OpenAI API Key:
```bash
export OPENAI_API_KEY='your-openai-api-key'  # On Windows use `set`
```

4. Google Cloud Project ID:
```bash
export GOOGLE_CLOUD_PROJECT='your-google-cloud-project-id'
```

5. Google Application Credentials:
Download your Google Cloud service account JSON key file and set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your/service-account-file.json'
```

6. Run the Backend Server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

7. Frontend Setup

Navigate to the Frontend Directory:
```bash
cd ../frontend
```

Open index.html in a Web Browser:

Use a modern browser that supports the Web Audio API and WebSockets.
Ensure the browser allows microphone access.



How to Run the Project

Start the Backend Server:

Follow the backend setup instructions to start the server.


Open the Frontend Application:

Open the index.html file in your web browser. You can also serve it using a simple HTTP server if needed.


### Interact with the Assistant:

Click the Start Recording button.
Speak a command or ask a question, e.g., "What is the weather today?" or "Tell me about Mars."
The assistant will transcribe your speech in real-time and display it.
The assistant will generate a response, display it, and play the synthesized speech.
Click the Stop Recording button to end the session.



### How It Works

1. Audio Capture and Streaming:

The frontend captures audio using the Web Audio API.
Audio data is sent to the backend via WebSockets in small chunks.


2. Real-Time Transcription:

3. The backend receives audio data and converts it to the required format.
Google Cloud Speech-to-Text API transcribes the audio in real-time.
Transcriptions (interim and final) are sent back to the frontend via WebSockets.


4. Assistant Response Generation:

5. Once a final transcription is received, the backend sends it to OpenAI's ChatCompletion API.
The assistant's response is generated and streamed back to the frontend.


6. Text-to-Speech Conversion:

The assistant's response is converted to speech using gTTS.
The synthesized speech is sent as binary data to the frontend.
The frontend plays the audio for the user.



### Important Notes
1. API Keys and Credentials

OpenAI API Key: Sign up at OpenAI to get your API key.
Google Cloud Credentials:

Enable the Speech-to-Text API in your Google Cloud project.
Create a service account and download the JSON key file.
Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your key file.



2. Dependencies
Backend dependencies are listed in backend/requirements.txt.
Install them using:
pip install -r requirements.txt
3. Audio Format Handling

The frontend captures audio in webm format with opus codec.
The backend converts it to LINEAR16 PCM format required by Google Cloud Speech-to-Text API.

4. CORS and Security

The backend server includes CORS middleware to allow cross-origin requests.
For production, update the allow_origins list with specific domains.
Use secure WebSocket connections (wss://) in production.


### Guidelines:

1. Code Quality: Write clean, maintainable code with proper structure and documentation.
2. User Experience: Emphasize smooth user engagement, allowing users to interact with the assistant as they would in natural conversations.
3. Innovation: Feel free to suggest and implement additional features that enhance functionality or user experience.
4. Testing: Ensure thorough testing is conducted to identify and fix any bugs or performance issues.

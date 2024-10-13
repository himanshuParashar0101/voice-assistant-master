    // app.js

    const recordButton = document.getElementById('recordButton');
    let isRecording = false;
    let socket;
    let mediaRecorder;
    let audioContext;

    recordButton.addEventListener('click', () => {
        if (!isRecording) {
            startRecording();
            recordButton.textContent = 'Stop Recording';
        } else {
            stopRecording();
            recordButton.textContent = 'Start Recording';
        }
        isRecording = !isRecording;
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Microphone access granted');

            socket = new WebSocket('ws://localhost:8000/ws/audio');
            socket.binaryType = 'arraybuffer';

            socket.onopen = () => {
                console.log('WebSocket connection opened');
            };

            socket.onmessage = async (event) => {
                console.log('Received message from server');
                // Handle incoming audio stream (assistant's response)
                await playAudio(event.data);
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            socket.onclose = (event) => {
                console.log('WebSocket connection closed:', event);
            };

            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorder.start(250); // Send data in chunks every 250ms
            console.log('MediaRecorder started');

            mediaRecorder.ondataavailable = (event) => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                    console.log('Sent audio chunk to server');

                    // Interrupt playback when user starts speaking
                    if (audioContext && audioContext.state !== 'closed') {
                        audioContext.close();
                        console.log('Playback interrupted by user');
                    }
                } else {
                    console.warn('WebSocket is not open. ReadyState:', socket.readyState);
                }
            };

            mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
            };
        } catch (error) {
            console.error('Error accessing microphone:', error);
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            console.log('MediaRecorder stopped');
        }
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
            console.log('WebSocket connection closed');
        }
    }

    async function playAudio(data) {
        if (audioContext) {
            audioContext.close();
            console.log('Previous audio context closed');
        }
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('Created new audio context');

        try {
            const arrayBuffer = data instanceof ArrayBuffer ? data : await data.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            console.log('Decoded audio data');

            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.start(0);
            console.log('Started audio playback');
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

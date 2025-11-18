// collector.js
// This script is meant to be embedded on a client's website.
// It uses their unique clientId to send audience data to your backend.

// !! IMPORTANT !!
// CLIENTS MUST REPLACE THIS WITH THEIR UNIQUE CLIENT ID
// You will provide this on their account page in the Admin Portal.
const CLIENT_ID = 'YOUR_CLIENT_ID_HERE'; // <--- THIS MUST BE REPLACED BY THE CLIENT

// !! IMPORTANT !!
// REPLACE WITH THE PUBLIC URL OF YOUR PYTHON BACKEND (app.py)
// If you're running locally, it's 127.0.0.1:5000.
// In production, this will be your deployed backend URL (e.g., https://your-api.com/predict_frame)
const FRAME_API_URL = 'http://127.0.0.1:5000/predict_frame';

let webcamFeed = null;
let videoStream = null;
let processingInterval = null;
let canvas = null; // Canvas for processing frames

// Function to initialize the collector
function initAudienceCollector() {
    console.log('Audience Collector Initializing...');

    // Find a designated container for the collector (optional, for client feedback)
    const container = document.getElementById('audience-collector-container');
    if (container) {
        container.innerHTML = `
            <div style="font-family: sans-serif; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9; color: #333; text-align: center;">
                <p>Audience Analytics: Camera is off. Waiting for user interaction or auto-start.</p>
            </div>
        `;
    }

    // Try to auto-start camera (can be configured based on client preference)
    // For now, let's keep it manual or based on an event
    // autoStartCamera(); // Can uncomment this if you want it to start immediately

    // Add a global function for clients to manually start/stop the collector
    window.startAudienceCamera = startAudienceCamera;
    window.stopAudienceCamera = stopAudienceCamera;

    console.log('Audience Collector Ready. Use startAudienceCamera() to activate.');
}

async function startAudienceCamera() {
    if (!CLIENT_ID || CLIENT_ID === 'YOUR_CLIENT_ID_HERE') {
        console.error('Audience Collector Error: CLIENT_ID is not set. Please configure the script with your unique ID.');
        alert('Audience Collector Error: CLIENT_ID is not set. Please contact support.');
        return;
    }
    if (videoStream) {
        console.warn('Audience Collector: Camera is already running.');
        return;
    }

    try {
        // Create a hidden video element
        webcamFeed = document.createElement('video');
        webcamFeed.style.cssText = 'display:none;'; // Keep it hidden
        webcamFeed.autoplay = true;
        webcamFeed.muted = true;
        webcamFeed.playsInline = true;
        document.body.appendChild(webcamFeed);

        videoStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
        webcamFeed.srcObject = videoStream;

        // Create a hidden canvas for processing
        canvas = document.createElement('canvas');
        canvas.style.cssText = 'display:none;';
        document.body.appendChild(canvas);

        webcamFeed.onloadedmetadata = () => {
            canvas.width = webcamFeed.videoWidth;
            canvas.height = webcamFeed.videoHeight;
            processingInterval = setInterval(processFrame, 500); // Process every 500ms
            console.log('Audience Collector: Camera started. Processing frames.');
            updateClientFeedback('Audience Analytics: Camera active.');
        };

    } catch (err) {
        console.error('Audience Collector Error accessing webcam:', err);
        updateClientFeedback('Audience Analytics: Error starting camera. Please check permissions.');
    }
}

function stopAudienceCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    if (processingInterval) {
        clearInterval(processingInterval);
        processingInterval = null;
    }
    if (webcamFeed && webcamFeed.parentNode) {
        webcamFeed.parentNode.removeChild(webcamFeed);
        webcamFeed = null;
    }
    if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
        canvas = null;
    }
    console.log('Audience Collector: Camera stopped.');
    updateClientFeedback('Audience Analytics: Camera off.');
}

async function processFrame() {
    if (!webcamFeed || webcamFeed.readyState < 3 || !canvas) return;

    const context = canvas.getContext('2d');
    context.drawImage(webcamFeed, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);

    try {
        const response = await fetch(FRAME_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_data: imageData,
                client_id: CLIENT_ID // Send the client ID with each frame
            })
        });

        if (!response.ok) {
            console.error('Audience Collector: Error sending frame to backend. Status:', response.status);
            // Consider stopping or pausing if too many errors
            return;
        }

        const data = await response.json();
        // The embedded script usually doesn't need to display predictions,
        // it just sends them. But you can log for debugging.
        // console.log('Audience Collector: Frame processed, predictions:', data.predictions);

    } catch (err) {
        console.error('Audience Collector: Error processing frame:', err);
    }
}

function updateClientFeedback(message) {
    const container = document.getElementById('audience-collector-container');
    if (container) {
        const pTag = container.querySelector('p');
        if (pTag) pTag.textContent = message;
    }
}


// Initialize when the DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAudienceCollector);
} else {
    initAudienceCollector();
}
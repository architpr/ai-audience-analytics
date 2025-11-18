# 📊 AI Audience Analytics System

## 🚀 Project Overview

This **AI Audience Analytics System** is a full-stack application designed to capture and visualize real-time demographic data (age and gender) of an audience. Leveraging client-side webcam streaming and image uploads, the system processes facial data through a robust Python Flask backend powered by deep learning models (Mediapipe for face detection, OpenCV for image processing, and a custom age/gender classifier). All collected insights are securely stored in a scalable Google Firestore database, with data meticulously isolated for each client. The system culminates in an interactive, dynamic dashboard, providing businesses with valuable, actionable intelligence to understand their audience demographics, inform marketing strategies, and optimize user experiences.

**Key Features:**

* **Real-time Live Camera Analysis:** Processes video frames from a webcam to detect faces and predict age/gender on the fly.
* **Static Image Upload:** Allows users to upload photos for batch demographic analysis.
* **Deep Learning Backend:** Utilizes a Python Flask API integrated with advanced computer vision models for accurate predictions.
* **Secure Client-Specific Data:** Employs Firebase Authentication and Firestore to ensure each client's data is isolated and protected.
* **Interactive Dashboard:** Visualizes aggregated demographic trends with dynamic charts (gender breakdown, age distribution) and key metrics.
* **Scalable Architecture:** Built on Firebase, designed to handle growing data volumes and multiple clients seamlessly.

## 🛠️ Technologies Used

**Frontend:**
* **HTML5, CSS3 (Tailwind CSS):** For modern, responsive UI.
* **JavaScript (ES6+):** Core interactivity and logic.
* **Chart.js:** For dynamic and engaging data visualizations on the dashboard.
* **Firebase SDK (Client):** User authentication (Sign Up/Login) and real-time Firestore data retrieval.

**Backend:**
* **Python 3.9+**
* **Flask:** Lightweight web framework for API endpoints.
* **Mediapipe:** For efficient and accurate face detection.
* **OpenCV-Python:** Image processing and annotation.
* **NumPy:** Numerical operations.
* **Firebase Admin SDK (Python):** Secure server-side interaction with Firestore.
* **Gunicorn:** Production-ready WSGI HTTP server for Flask.
* **Flask-CORS:** Handling Cross-Origin Resource Sharing for API requests.

**Database:**
* **Google Firestore (NoSQL):** Scalable, serverless database for storing client-specific demographic data.

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

* Python 3.9+
* `pip` (Python package installer)
* Node.js & `npm` (for Tailwind CSS setup, optional if you just use the provided CSS)
* Git
* A Google Firebase Project (configured for Authentication and Firestore)

### 1. Clone the Repository

git clone [https://github.com/architpr/ai-audience-analytics.git](https://github.com/architpr/ai-audience-analytics.git)
cd ai-audience-analytics

### 2\. Set Up Firebase

  * **Create a Firebase Project:** Go to [Firebase Console](https://console.firebase.google.com/) and create a new project.
  * **Enable Authentication:**
      * Navigate to "Build" -> "Authentication" -> "Get started".
      * Enable the "Email/Password" sign-in method.
  * **Enable Firestore Database:**
      * Navigate to "Build" -> "Firestore Database" -> "Create database".
      * Start in "production mode" (you'll set up rules below). Choose a location.
  * **Update Firestore Security Rules:**
      * In Firestore, go to the "Rules" tab.
      * Replace existing rules with:

        ```firestore
        rules_version = '2';
        service cloud.firestore {
          match /databases/{database}/documents {
            // Rules for client data
            match /clients/{clientId}/sightings/{sightingId} {
              allow read, write: if request.auth != null && request.auth.uid == clientId;
            }
            // All other collections/documents are read/write by authenticated users
            match /{document=**} {
              allow read, write: if request.auth != null;
            }
          }
        }
        ```
      * Click "Publish".
  * **Get Firebase Configuration:**
      * In Firebase Project settings (gear icon next to "Project overview"), click "Add app" -> "Web".
      * Register your app and copy the `firebaseConfig` object.

### 3\. Configure Frontend (`index.html` & `login.html`)

  * Open `index.html` and `login.html` in your code editor.
  * **Paste your `firebaseConfig`** object (from Firebase console) into both files, replacing the placeholder comments where `const firebaseConfig = { ... }` is defined. Ensure the `apiKey` and other details match your Firebase project.

### 4\. Set Up Backend (Python Flask)

  * **Create a Virtual Environment:** (Highly Recommended)

    ```bash
    python -m venv venv
    ```
  * **Activate Virtual Environment:**
      * On Windows: `.\venv\Scripts\activate`
      * On macOS/Linux: `source venv/bin/activate`
  * **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```
  * **Download ML Models:**
      * Your project uses pre-trained deep learning models. Ensure the `models` directory contains all necessary `.caffemodel`, `.prototxt`, and `.pbtxt` files.
      * (If these aren't in your repo, provide instructions or a download link here for where to get them, e.g., from OpenCV's GitHub or a Google Drive link)
  * **Run the Flask Backend:**

    ```bash
    python app.py
    ```
    The backend will typically run on `http://127.0.0.1:5000/`. Keep this terminal open.

### 5\. Run the Frontend

  * Open `login.html` directly in your web browser (e.g., `file:///D:/ML%20project/age-gender-project/login.html`).
  * Sign up for a new account (e.g., `clienta@example.com`). This will create a new user in your Firebase Authentication.
  * You will be redirected to `index.html`.

## 📈 Usage & Demonstration

  * **Sign Up / Login:** Access `login.html` in your browser. Create a new user account (e.g., `clienta@example.com`) or log in with existing credentials.
  * **Live Collector:**
      * Navigate to the "Live Collector" tab.
      * **Live Camera:** Click "Start Camera" to initiate real-time facial analysis. Observe predictions on the processed feed and "Database Status" indicating data being saved to Firestore.
      * **Upload Photo:** Upload an image containing a face. Click "Detect from Photo" to see predictions and save data.
  * **Dashboard:**
      * Click on the "Dashboard" link in the sidebar.
      * Observe the "Total Detections," "Most Seen Gender," "Most Seen Age Group" metrics, and the dynamic "Gender Breakdown" and "Age Breakdown" charts.
      * Click the refresh button to load the latest data.
  * **Multi-Client Demonstration:**
      * Logout.
      * Sign up as `clientb@example.com`.
      * Collect data via Live Camera or Upload Photo for Client B.
      * Verify in Firebase Firestore that Client B's data is isolated under their own UID.
      * Check Client B's dashboard.
      * Log back in as Client A and confirm Client A's dashboard still shows only their data, demonstrating robust data isolation.

## ☁️ Deployment (Free Tier)

This project is designed for cost-effective deployment leveraging free tiers of cloud services.

  * **Frontend (HTML/CSS/JS):**
      * Deployed via **GitHub Pages**. (Extremely reliable and truly free for static sites).
      * Your deployed frontend can be found at: [https://architpr.github.io/ai-audience-analytics/login.html](https://architpr.github.io/ai-audience-analytics/login.html)
  * **Backend (Python Flask + ML Models):**
      * Deployed via **Render.com** (Free Web Services tier).
      * *Note: Render's free tier services "spin down" after 15 minutes of inactivity. The first request after a spin-down may take 30-60 seconds to warm up.*
      * Your deployed backend API URL: `[YOUR_RENDER_BACKEND_URL_HERE]`
      * **Remember to update `UPLOAD_API_URL` and `FRAME_API_URL` in your frontend JavaScript (`index.html`, `collector.js` if separate) to point to your deployed Render backend URL.**

## 🤝 Contributing

Contributions, issues, and feature requests are welcome\! Feel free to check the [issues page](https://github.com/architpr/ai-audience-analytics/issues) on GitHub.

---

Made with ❤️ by Archit

Feel free to connect:

  * [LinkedIn](https://www.linkedin.com/in/yourprofile)
  * [GitHub](https://github.com/architpr)

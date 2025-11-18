import cv2
import numpy as np
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- Firebase Admin SDK Initialization ---
#
# !! IMPORTANT: YOU MUST UPDATE THE PATH BELOW !!
#
# 1. Go to your Firebase Console.
# 2. Navigate to Project settings (gear icon) -> Service accounts tab.
# 3. Click "Generate new private key" and download the JSON file.
# 4. Place this downloaded JSON file in a secure location within your project.
#    A common and simple approach for local development is to place it
#    in the same directory as this `app.py` file.
# 5. Replace "path/to/your/serviceAccountKey.json" with the ACTUAL path
#    to your downloaded JSON file.
#    Example if in the same directory: "your-firebase-project-id-adminsdk-xxxxx-yyyyyy.json"
#
try:
    cred = credentials.Certificate(r"D:\ML project\age-gender-project\audience-analytics-c4fcc-firebase-adminsdk-fbsvc-c0847b5685.json") # <--- REPLACE THIS STRING WITH YOUR FILE'S PATH
    initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    print("Please ensure 'serviceAccountKey.json' is correctly placed and specified in app.py.")
    print("You can download it from Firebase Console -> Project settings -> Service accounts tab.")
    exit() # Exit if Firebase fails to initialize, as the app won't function correctly.

# --- Model Loading ---
print("Loading models into memory...")

FACE_PROTO = "models/opencv_face_detector.pbtxt"
FACE_MODEL = "models/opencv_face_detector_uint8.pb"
AGE_PROTO = "models/age_deploy.prototxt"
AGE_MODEL = "models/age_net.caffemodel"
GENDER_PROTO = "models/gender_deploy.prototxt"
GENDER_MODEL = "models/gender_net.caffemodel"

AGE_BUCKETS = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
GENDER_LIST = ['Male', 'Female']

try:
    face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
    age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
    gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
    print("Models loaded successfully.")
except cv2.error as e:
    print(f"Error loading models: {e}")
    print("Please make sure the model files are in the 'models' directory.")
    exit()

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
# --- End of Model Loading ---


# --- Core Prediction Function ---
def get_face_predictions(frame):
    """
    Detects faces in an image, predicts age and gender, and draws on the image.
    Returns:
        - The frame with annotations (bounding boxes, text)
        - A list of prediction strings (e.g., "Male, (25-32)")
    """
    annotated_frame = frame.copy()
    frame_height = annotated_frame.shape[0]
    frame_width = annotated_frame.shape[1]
    
    blob = cv2.dnn.blobFromImage(annotated_frame, 1.0, (300, 300), [104, 117, 123], True, False)
    
    face_net.setInput(blob)
    detections = face_net.forward()
    
    predictions_list = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        if confidence > 0.7:
            x1 = int(detections[0, 0, i, 3] * frame_width)
            y1 = int(detections[0, 0, i, 4] * frame_height)
            x2 = int(detections[0, 0, i, 5] * frame_width)
            y2 = int(detections[0, 0, i, 6] * frame_height)
            
            padding = 20
            face = annotated_frame[max(0, y1-padding):min(y2+padding, frame_height-1),
                                   max(0, x1-padding):min(x2+padding, frame_width-1)]
            
            if face.shape[0] == 0 or face.shape[1] == 0:
                continue

            face_blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            
            gender_net.setInput(face_blob)
            gender_preds = gender_net.forward()
            gender = GENDER_LIST[gender_preds[0].argmax()]
            
            age_net.setInput(face_blob)
            age_preds = age_net.forward()
            age = AGE_BUCKETS[age_preds[0].argmax()]
            
            label = f"{gender}, {age}"
            predictions_list.append(label)
            
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            
    return annotated_frame, predictions_list


# --- Firestore Saving Function (UPDATED for multi-tenant) ---
def save_prediction_to_firestore(gender, age_range, client_id):
    """Saves the detected gender and age range to Firestore for a specific client."""
    try:
        # Save to clients/{client_id}/sightings
        doc_ref = db.collection('clients').document(client_id).collection('sightings').add({
            'gender': gender,
            'age_range': age_range,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"Prediction saved for client {client_id} (ID: {doc_ref[1].id}): Gender={gender}, Age={age_range}")
    except Exception as e:
        print(f"Error saving prediction for client {client_id} to Firestore: {e}")


# --- API Endpoint 1: File Upload (Unchanged - for single image upload) ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    in_memory_file = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)
    
    if frame is None:
        return jsonify({'error': 'Could not decode image'}), 400

    annotated_frame, predictions = get_face_predictions(frame)
    
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        'predictions': predictions,
        'annotated_image': f"data:image/jpeg;base64,{image_base64}"
    })


# --- API Endpoint 2: Live Video Frame (UPDATED for client_id and Firestore saving) ---
@app.route('/predict_frame', methods=['POST'])
def predict_frame():
    data = request.get_json()
    if not data or 'image_data' not in data:
        return jsonify({'error': 'No image data provided'}), 400

    # Extract client_id from the request data
    client_id = data.get('client_id') 
    if not client_id:
        return jsonify({'error': 'client_id is required'}), 400

    # Decode the base64 string
    try:
        image_data = data['image_data'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
    except (IndexError, base64.binascii.Error) as e:
        return jsonify({'error': f'Invalid base64 data: {e}'}), 400
    
    # Convert bytes to a numpy array
    in_memory_file = np.frombuffer(image_bytes, np.uint8)
    # Decode the array into an OpenCV image (frame)
    frame = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({'error': 'Could not decode image data'}), 400

    # Process the frame to get predictions
    annotated_frame, predictions = get_face_predictions(frame)
    
    # Save prediction to Firestore if faces were detected
    if predictions: # Only save if a face was actually detected
        # For simplicity, we'll save only the first detected face's attributes.
        # You could extend this to save multiple if needed.
        first_prediction = predictions[0]
        gender, age_range = first_prediction.split(', ') 
        save_prediction_to_firestore(gender, age_range, client_id)

    # Encode the *annotated* frame back to base64 for the frontend to display (if needed)
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Send the result back
    return jsonify({
        'predictions': predictions,
        'annotated_image': f"data:image/jpeg;base64,{image_base64}"
    })


# Run the app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)










































































































# import cv2
# import numpy as np
# import base64
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# # Initialize the Flask application
# app = Flask(__name__)
# # Enable CORS (Cross-Origin Resource Sharing) to allow
# # our frontend to communicate with this backend
# CORS(app)

# # --- Model Loading ---
# # This part is unchanged
# print("Loading models into memory...")

# FACE_PROTO = "models/opencv_face_detector.pbtxt"
# FACE_MODEL = "models/opencv_face_detector_uint8.pb"
# AGE_PROTO = "models/age_deploy.prototxt"
# AGE_MODEL = "models/age_net.caffemodel"
# GENDER_PROTO = "models/gender_deploy.prototxt"
# GENDER_MODEL = "models/gender_net.caffemodel"

# AGE_BUCKETS = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
# GENDER_LIST = ['Male', 'Female']

# try:
#     face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
#     age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
#     gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
#     print("Models loaded successfully.")
# except cv2.error as e:
#     print(f"Error loading models: {e}")
#     print("Please make sure the model files are in the 'models' directory.")
#     exit()

# MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
# # --- End of Model Loading ---


# # --- Core Prediction Function (Unchanged) ---
# # This function is used by BOTH endpoints
# def get_face_predictions(frame):
#     """
#     Detects faces in an image, predicts age and gender, and draws on the image.
#     Returns:
#         - The frame with annotations (bounding boxes, text)
#         - A list of prediction strings (e.g., "Male, (25-32)")
#     """
#     annotated_frame = frame.copy()
#     frame_height = annotated_frame.shape[0]
#     frame_width = annotated_frame.shape[1]
    
#     blob = cv2.dnn.blobFromImage(annotated_frame, 1.0, (300, 300), [104, 117, 123], True, False)
    
#     face_net.setInput(blob)
#     detections = face_net.forward()
    
#     predictions_list = []

#     for i in range(detections.shape[2]):
#         confidence = detections[0, 0, i, 2]
        
#         if confidence > 0.7:
#             x1 = int(detections[0, 0, i, 3] * frame_width)
#             y1 = int(detections[0, 0, i, 4] * frame_height)
#             x2 = int(detections[0, 0, i, 5] * frame_width)
#             y2 = int(detections[0, 0, i, 6] * frame_height)
            
#             padding = 20
#             face = annotated_frame[max(0, y1-padding):min(y2+padding, frame_height-1),
#                                    max(0, x1-padding):min(x2+padding, frame_width-1)]
            
#             if face.shape[0] == 0 or face.shape[1] == 0:
#                 continue

#             face_blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            
#             gender_net.setInput(face_blob)
#             gender_preds = gender_net.forward()
#             gender = GENDER_LIST[gender_preds[0].argmax()]
            
#             age_net.setInput(face_blob)
#             age_preds = age_net.forward()
#             age = AGE_BUCKETS[age_preds[0].argmax()]
            
#             label = f"{gender}, {age}"
#             predictions_list.append(label)
            
#             cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            
#     return annotated_frame, predictions_list


# # --- API Endpoint 1: File Upload (Unchanged) ---
# @app.route('/predict', methods=['POST'])
# def predict():
#     if 'image' not in request.files:
#         return jsonify({'error': 'No image file provided'}), 400
        
#     file = request.files['image']
#     in_memory_file = np.frombuffer(file.read(), np.uint8)
#     frame = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)
    
#     if frame is None:
#         return jsonify({'error': 'Could not decode image'}), 400

#     annotated_frame, predictions = get_face_predictions(frame)
    
#     _, buffer = cv2.imencode('.jpg', annotated_frame)
#     image_base64 = base64.b64encode(buffer).decode('utf-8')
    
#     return jsonify({
#         'predictions': predictions,
#         'annotated_image': f"data:image/jpeg;base64,{image_base64}"
#     })

# # --- API Endpoint 2: Live Video Frame (NEW) ---
# @app.route('/predict_frame', methods=['POST'])
# def predict_frame():
#     data = request.get_json()
#     if not data or 'image_data' not in data:
#         return jsonify({'error': 'No image data provided'}), 400

# # --- ADD THESE LINES FOR client_id ---
#     client_id = data.get('client_id') 
#     if not client_id:
#         return jsonify({'error': 'client_id is required'}), 400

#     # Decode the base64 string
#     # The string comes as 'data:image/jpeg;base64,....'
#     # We need to split off the header part
#     try:
#         image_data = data['image_data'].split(',')[1]
#         image_bytes = base64.b64decode(image_data)
#     except (IndexError, base64.binascii.Error) as e:
#         return jsonify({'error': f'Invalid base64 data: {e}'}), 400
    
#     # Convert bytes to a numpy array
#     in_memory_file = np.frombuffer(image_bytes, np.uint8)
#     # Decode the array into an OpenCV image (frame)
#     frame = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)

#     if frame is None:
#         return jsonify({'error': 'Could not decode image data'}), 400

#     # Process the frame using the *same* function
#     annotated_frame, predictions = get_face_predictions(frame)
    
#     # Encode the *annotated* frame back to base64
#     _, buffer = cv2.imencode('.jpg', annotated_frame)
#     image_base64 = base64.b64encode(buffer).decode('utf-8')
    
#     # Send the result back
#     return jsonify({
#         'predictions': predictions,
#         'annotated_image': f"data:image/jpeg;base64,{image_base64}"
#     })


# # Run the app
# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000, debug=True)
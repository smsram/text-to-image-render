from flask import Flask
import base64
import requests
import threading
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from flask_cors import CORS  # Import CORS
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# List of API keys
api_keys = [
    "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"
]

# Variable to keep track of the current API key index
current_api_index = 0

# Create a lock to ensure thread safety when updating the current_api_index
index_lock = threading.Lock()

# Create a ThreadPoolExecutor to handle requests concurrently
executor = ThreadPoolExecutor(max_workers=5)  # Set number of workers based on how many concurrent requests you want to handle

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate-image", methods=["POST"])
def generate_image():
    global current_api_index  # Declare global to modify the index
    
    # Get the prompt from the POST request
    prompt = request.json.get("prompt")
    
    # Get the current API key from the list using a thread-safe method
    with index_lock:  # Ensure only one thread modifies the current_api_index at a time
        api_key = api_keys[current_api_index]
        current_api_index = (current_api_index + 1) % len(api_keys)  # Update the index after fetching the current API key
    
    # The model URL
    model_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
    
    # Send the request to Hugging Face API
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "inputs": prompt
    }

    # Use ThreadPoolExecutor to handle the API request concurrently
    def api_request():
        response = requests.post(model_url, headers=headers, json=payload)
        if response.status_code == 200:
            # The response should contain the image in binary format
            img_data = response.content
            img_io = BytesIO(img_data)
            img_io.seek(0)
            base64_image = base64.b64encode(img_io.getvalue()).decode("utf-8")
            return base64_image
        else:
            return None

    # Submit the API request to the thread pool
    future = executor.submit(api_request)

    # Wait for the result (the image data)
    base64_image = future.result()

    if base64_image:
        return jsonify({"image": base64_image})
    else:
        return jsonify({"error": "Failed to generate image"})

if __name__ == "__main__":
    import os  # Import os module
from flask import Flask  # Import Flask module
from multiprocessing import set_start_method  # Import set_start_method

set_start_method("spawn")  # Set the start method to "spawn"

app = Flask(__name__)  # Create a Flask app instance

port = int(os.getenv("PORT", 8080))  # Retrieve the port from the environment variable or use 8080 as default
print(f"Starting server on port {port}...")  # Debugging print
app.run(host="0.0.0.0", port=port, debug=True, threaded=True)

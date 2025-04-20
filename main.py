from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import numpy as np
import cv2
import os
import uuid
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'thermal_analyzer_secret_key'

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
DEMO_IMAGE_PATH = os.path.join('static', 'demo', 'gray8-grayscale.jpg')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# App config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state
user_images = {}
active_image_id = "demo"
is_fahrenheit = True

# Load demo image once
demo_gray16_image = cv2.imread(DEMO_IMAGE_PATH, cv2.IMREAD_ANYDEPTH)
demo_gray8_image = cv2.normalize(demo_gray16_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Utils
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_active_image_path():
    if active_image_id == "demo":
        return DEMO_IMAGE_PATH
    elif active_image_id in user_images:
        return user_images[active_image_id]['path']
    return DEMO_IMAGE_PATH

def process_and_store_image(file, filename):
    global user_images

    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    # Read grayscale 16-bit or fallback to 8-bit
    gray16_image = cv2.imread(file_path, cv2.IMREAD_ANYDEPTH)
    if gray16_image is None:
        gray16_image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

    if gray16_image is None:
        raise ValueError("Unable to read image in grayscale.")

    # Normalize for display
    gray8_image = cv2.normalize(gray16_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    display_path = os.path.join(UPLOAD_FOLDER, f"display_{unique_filename}")
    cv2.imwrite(display_path, gray8_image)

    # Store
    image_id = f"img_{len(user_images) + 1}"
    user_images[image_id] = {
        'path': display_path,
        'original_path': file_path,
        'gray16_image': gray16_image,
        'gray8_image': gray8_image,
        'filename': filename
    }

    return image_id

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                           active_image_id=active_image_id, 
                           active_image_path=get_active_image_path())

@app.route('/upload', methods=['POST'])
def upload_file():
    global active_image_id

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        try:
            image_id = process_and_store_image(file, file.filename)
            active_image_id = image_id
            flash(f'Successfully uploaded and processed {file.filename}')
        except Exception as e:
            flash(f'Error processing image: {str(e)}')
    else:
        flash('Invalid file type. Please upload a JPG, PNG, or TIFF image.')
    return redirect(url_for('index'))

@app.route('/switch_to_demo', methods=['POST'])
def switch_to_demo():
    global active_image_id
    active_image_id = "demo"
    flash('Switched to demo image')
    return redirect(url_for('index'))

@app.route('/switch_to_image/<image_id>', methods=['POST'])
def switch_to_image(image_id):
    global active_image_id
    if image_id in user_images or image_id == "demo":
        active_image_id = image_id
        flash(f'Switched to {user_images.get(image_id, {}).get("filename", "demo image")}')
    return redirect(url_for('index'))

@app.route('/get_temp', methods=['POST'])
def get_temp():
    global is_fahrenheit, active_image_id
    data = request.json
    x, y = int(data['x']), int(data['y'])
    image_id = data.get('image_id', active_image_id)

    if image_id == "demo":
        gray16_image = demo_gray16_image
    elif image_id in user_images:
        gray16_image = user_images[image_id]['gray16_image']
    else:
        return jsonify({"temperature": "Image not found"})

    if 0 <= y < gray16_image.shape[0] and 0 <= x < gray16_image.shape[1]:
        temp = float(gray16_image[y, x])
        unit = "°F" if is_fahrenheit else "°C"
        temp = (temp * 9 / 5) + 32 if is_fahrenheit else temp
        return jsonify({
            "temperature": f"{temp:.1f} {unit}",
            "raw_value": f"{gray16_image[y, x]}"
        })
    return jsonify({"temperature": "Out of bounds"})

@app.route('/toggle_unit', methods=['POST'])
def toggle_unit():
    global is_fahrenheit
    is_fahrenheit = not is_fahrenheit
    return jsonify({
        "status": "toggled",
        "unit": "Fahrenheit" if is_fahrenheit else "Celsius"
    })

@app.route('/get_active_image')
def get_active_image():
    if active_image_id == "demo":
        return jsonify({
            "id": "demo",
            "path": DEMO_IMAGE_PATH,
            "filename": "Demo Image"
        })
    elif active_image_id in user_images:
        return jsonify({
            "id": active_image_id,
            "path": user_images[active_image_id]["path"],
            "filename": user_images[active_image_id].get("filename", "Uploaded Image")
        })
    return jsonify({"error": "No active image"}), 404

@app.route('/get_uploaded_images')
def get_uploaded_images():
    images = [{
        "id": "demo",
        "path": DEMO_IMAGE_PATH,
        "filename": "Demo Image"
    }]
    for img_id, data in user_images.items():
        images.append({
            "id": img_id,
            "path": data["path"],
            "filename": data.get("filename", "Uploaded Image")
        })
    return jsonify({"images": images})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

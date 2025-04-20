from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import numpy as np
import cv2
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'thermal_analyzer_secret_key'  # For flash messages
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'tif', 'tiff'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize with default demo image
demo_image_path = "static/demo/gray8-grayscale.jpg"
demo_gray16_image = cv2.imread(demo_image_path, cv2.IMREAD_ANYDEPTH)
demo_gray8_image = cv2.normalize(demo_gray16_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Store user uploaded image data
user_images = {}

# Mode: Celsius (False) or Fahrenheit (True)
is_fahrenheit = True
active_image_id = "demo"  # Default to demo image

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html', 
                          active_image_id=active_image_id, 
                          active_image_path=get_active_image_path())

def get_active_image_path():
    if active_image_id == "demo":
        return demo_image_path
    elif active_image_id in user_images:
        return user_images[active_image_id]['path']
    return demo_image_path

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
        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Generate unique ID for this upload
        image_id = f"img_{len(user_images) + 1}"
        
        # Process the grayscale image
        try:
            gray16_image = cv2.imread(file_path, cv2.IMREAD_ANYDEPTH)
            if gray16_image is None:
                # Try reading as regular image if ANYDEPTH fails
                gray16_image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                
            if gray16_image is None:
                flash('Failed to read image as grayscale')
                return redirect(url_for('index'))
                
            gray8_image = cv2.normalize(gray16_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            
            # Save normalized image for display
            display_path = os.path.join(app.config['UPLOAD_FOLDER'], f"display_{unique_filename}")
            cv2.imwrite(display_path, gray8_image)
            
            # Store the processed images
            user_images[image_id] = {
                'path': display_path,  # Use the normalized image for display
                'original_path': file_path,
                'gray16_image': gray16_image,
                'gray8_image': gray8_image,
                'filename': file.filename
            }
            
            # Set as active image
            active_image_id = image_id
            
            # Flash success message
            flash(f'Successfully uploaded and processed {file.filename}')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error processing image: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a JPG, PNG, or TIFF file.')
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
        if image_id == "demo":
            flash('Switched to demo image')
        else:
            filename = user_images[image_id].get('filename', 'uploaded image')
            flash(f'Switched to {filename}')
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
        temp = float(gray16_image[y, x])  # Convert to float to avoid int arithmetic
        if is_fahrenheit:
            temp = (temp * 9 / 5) + 32
            unit = "°F"
        else:
            unit = "°C"
        return jsonify({"temperature": f"{temp:.1f} {unit}", "raw_value": f"{gray16_image[y, x]}"})
    else:
        return jsonify({"temperature": "Out of bounds"})

@app.route('/toggle_unit', methods=['POST'])
def toggle_unit():
    global is_fahrenheit
    is_fahrenheit = not is_fahrenheit
    unit = "Fahrenheit" if is_fahrenheit else "Celsius"
    return jsonify({"status": "toggled", "unit": unit})

@app.route('/get_active_image')
def get_active_image():
    if active_image_id == "demo":
        return jsonify({
            "id": "demo",
            "path": demo_image_path,
            "filename": "Demo Image"
        })
    elif active_image_id in user_images:
        return jsonify({
            "id": active_image_id,
            "path": user_images[active_image_id]["path"],
            "filename": user_images[active_image_id].get("filename", "Uploaded Image")
        })
    else:
        return jsonify({"error": "No active image"}), 404

@app.route('/get_uploaded_images')
def get_uploaded_images():
    images = [{"id": "demo", "path": demo_image_path, "filename": "Demo Image"}]
    for img_id, img_data in user_images.items():
        images.append({
            "id": img_id,
            "path": img_data["path"],
            "filename": img_data.get("filename", "Uploaded Image")
        })
    return jsonify({"images": images})

if __name__ == '__main__':
    app.run(debug=True)
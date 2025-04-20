from flask import Flask, render_template, jsonify, request
import numpy as np
import cv2

app = Flask(__name__)

# Load the image once when the server starts
gray16_image = cv2.imread("static/gray8-grayscale.jpg", cv2.IMREAD_ANYDEPTH)
gray8_image = cv2.normalize(gray16_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Mode: Celsius (False) or Fahrenheit (True)
is_fahrenheit = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_temp', methods=['POST'])
def get_temp():
    global is_fahrenheit
    data = request.json
    x, y = int(data['x']), int(data['y'])

    if 0 <= y < gray16_image.shape[0] and 0 <= x < gray16_image.shape[1]:
        temp = gray16_image[y, x]
        if is_fahrenheit:
            temp = (temp * 9 / 5) + 32
            unit = "Fahrenheit"
        else:
            unit = "Celsius"
        return jsonify({"temperature": f"{temp:.1f} {unit}"})
    else:
        return jsonify({"temperature": "Out of bounds"})

@app.route('/toggle_unit', methods=['POST'])
def toggle_unit():
    global is_fahrenheit
    is_fahrenheit = not is_fahrenheit
    return jsonify({"status": "toggled"})

if __name__ == '__main__':
    app.run(debug=True)

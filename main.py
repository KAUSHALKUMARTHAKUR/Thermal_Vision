import numpy as np
import cv2

# Function to handle mouse events
def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # Clear previously displayed text
        gray8_temp_display = gray8_image.copy()
        gray16_temp_display = gray16_image.copy()

        # Get the temperature value from the image
        pixel_flame_gray16 = gray16_image[y, x]

        # Convert temperature from Celsius to Fahrenheit
        pixel_flame_gray16_fahrenheit = (pixel_flame_gray16 * 9 / 5) + 32

        # Display the temperature value on both images
        cv2.putText(gray8_temp_display, "{0:.1f} Fahrenheit".format(pixel_flame_gray16_fahrenheit), (x-80, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(gray16_temp_display, "{0:.1f} Fahrenheit".format(pixel_flame_gray16_fahrenheit), (x-80, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (65535, 65535, 65535), 1)

        # Display the images
        cv2.imshow('8-bit Grayscale Image', gray8_temp_display)
        cv2.imshow('16-bit Grayscale Image', gray16_temp_display)

# Read the image
gray16_image = cv2.imread(r"C:\Users\kaush\Downloads\Thermal_Vision\028.jpg", cv2.IMREAD_ANYDEPTH)

# Create an 8-bit grayscale image
gray8_image = np.zeros((120,160), dtype=np.uint8)

# Normalize the 16-bit image to 8-bit
gray8_image = cv2.normalize(gray16_image, gray8_image, 0, 255, cv2.NORM_MINMAX)
gray8_image = np.uint8(gray8_image)

# Create windows to display images
cv2.namedWindow('8-bit Grayscale Image')
cv2.namedWindow('16-bit Grayscale Image')

# Set the mouse callback function
cv2.setMouseCallback('8-bit Grayscale Image', mouse_event)
cv2.setMouseCallback('16-bit Grayscale Image', mouse_event)

# Display the images
cv2.imshow('8-bit Grayscale Image', gray8_image)
cv2.imshow('16-bit Grayscale Image', gray16_image)

cv2.waitKey(0)
cv2.destroyAllWindows()

import numpy as np
import cv2

is_fahrenheit = True

def mouse_event(event, x, y, flags, param):
    global is_fahrenheit

    if event == cv2.EVENT_MOUSEMOVE:
        
        gray8_temp_display = gray8_image.copy()
        gray16_temp_display = gray16_image.copy()

        pixel_flame_gray16 = gray16_image[y, x]

        
        if is_fahrenheit:
            temperature = (pixel_flame_gray16 * 9 / 5) + 32
            unit = "Fahrenheit"
        else:
            temperature = pixel_flame_gray16
            unit = "Celsius"

        
        cv2.putText(gray8_temp_display, "{0:.1f} {1}".format(temperature, unit), (x-80, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(gray16_temp_display, "{0:.1f} {1}".format(temperature, unit), (x-80, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (65535, 65535, 65535), 1)

       
        cv2.imshow('8-bit Grayscale Image', gray8_temp_display)
        cv2.imshow('16-bit Grayscale Image', gray16_temp_display)

    elif event == cv2.EVENT_LBUTTONDOWN:
        
        is_fahrenheit = not is_fahrenheit

gray16_image = cv2.imread(r"C:\Users\kaush\Downloads\Project1\gray8-grayscale.jpg", cv2.IMREAD_ANYDEPTH)

gray8_image = np.zeros(gray16_image.shape, dtype=np.uint8)
gray8_image = cv2.normalize(gray16_image, gray8_image, 0, 255, cv2.NORM_MINMAX)
gray8_image = np.uint8(gray8_image)


cv2.namedWindow('8-bit Grayscale Image')
cv2.namedWindow('16-bit Grayscale Image')


cv2.setMouseCallback('8-bit Grayscale Image', mouse_event)
cv2.setMouseCallback('16-bit Grayscale Image', mouse_event)


cv2.imshow('8-bit Grayscale Image', gray8_image)
cv2.imshow('16-bit Grayscale Image', gray16_image)

cv2.waitKey(0)
cv2.destroyAllWindows()

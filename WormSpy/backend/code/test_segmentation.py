import cv2
import EasyPySpin
import numpy as np

cap = EasyPySpin.VideoCapture(0)

while (cap.isOpened()):
    # Read a frame from the video capture
    success, frame = cap.read()
    resolution = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if frame.dtype != np.uint8: #check if frame is 8 bit and grayscale and convert if not
        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    blurred_frame = cv2.GaussianBlur(frame, (33, 33), 99)
    thresh = cv2.adaptiveThreshold(blurred_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 99, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    eroded_image = cv2.erode(thresh, kernel, iterations=3)
    processed_frame = cv2.dilate(eroded_image, kernel, iterations=1)

    # Convert the grayscale frame to a color frame
    color_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # Display the frame
    cv2.imshow("Frame", frame)
    cv2.imshow("Processed Frame", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS, cross_origin
import cv2

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
cap = cv2.VideoCapture(0)









# Status indicators to be altered with get requests. 
TRACKING_ENABLED = False
AUTOFOCUS_ENABLED = False
RECORDING_ENABLED = False

@app.route("/")
@cross_origin()
def home():
    return "Hello, Flask!"

@app.route('/video_feed', methods=['POST'])
@cross_origin()
def video_feed():
    # Open the video capture
    cap = cv2.VideoCapture(0)

    def gen():
        # with Connection.open_serial_port("COM4") as connection:
        #     device_list = connection.detect_devices()
        while True:
            # Read a frame from the video capture
            success, frame = cap.read()

            # Check if the frame was successfully read
            if success:
                # Resize the image to be 256x256
                frame = cv2.resize(frame, None, fx=0.25, fy=0.25)
                
                # Encode the frame in JPEG format
                ret, jpeg = cv2.imencode('.jpg', frame)
                
                # Yield the encoded frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                # If the frame was not successfully read, yield a blank frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n\r\n')

    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)

       
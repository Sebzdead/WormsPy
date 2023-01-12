from flask import Flask, request, Response, jsonify, make_response, json
from flask_cors import CORS, cross_origin
import EasyPySpin
import cv2
from dlclive import DLCLive, Processor
import math
from zaber_motion import Library, Units
from zaber_motion.binary import Connection, device
import numpy as np

app = Flask(__name__)
CORS(app, origins=['http://localhost:4200'])
app.config['CORS_HEADERS'] = 'Content-Type'

Library.enable_device_db_store()

# python -m flask run --host=127.0.0.1

# PREFERENCES, these change how the code will act in aesthetic ways
LOG_SENT_COMMANDS = True  # whether or not to print to console when a command is sent to zaber
SENT_COMMAND_PRECISION = 4  # places after the decimal to include in logged commands
PRE_CODE = "A-"  # a string put before all logged messages

# COMMONLY USED CONFIGURATION
# CURRENT_HEIGHT = 4  #millimeters height of camera
TRACKING_MODE = "simpleToCenter"  # the mode for how the camera should track, default is "simpleToCenter"
COM_PORT = "COM4"  # which com port to connect to for the zaber connection, format "COM#"
CONNECTED_TO_ZABER = True  # whether or not the program should try to connect to the zaber (False for debugging)

# SET UP CONFIGURATION -- config to be changed more rarely
# BASE_HEIGHT = 1  #millimeters camera is up
TOTAL_MM_X = 1.3125  # total width of the FOV in mm
TOTAL_MM_Y = 1.05  # total height of the FOV in mm

ZABER_ORIENTATION_X = 1  # whether the x direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_Y = 1  # whether the y direction of the zaber is inverted from the video feed (-1 if they are inverted)

TOTAL_PIXELS_X = 256  # pixels across of the video feed
TOTAL_PIXELS_Y = 256  # pixels across of the video feed

# UNIT CONVERSIONS
MM_MST = 20997  # millimeters per microstep
MM_TOT = 50.8  # total millimeters that the zaber can extend

# Zaber device boundaries
MAXIMUM_DEVICE_POSITION = 1066667
MINIMUM_DEVICE_POSITION = 0

# Global Variables for recording
start_recording = False
stop_recording = False
start_recording_fl = False
stop_recording_fl = False

settings = {
    "resolution": (256, 256),
    "fps": 10,
    "filepath": 'D:\WormSpy_video\Tracking',
    "filename": 'default.avi',
    "resolution_fl": (1024, 1024),
    "fps_fl": 10,
    "filepath_fl": 'D:\WormSpy_video\Calcium',
    "filename_fl": 'default_fluorescent'
}

# Autofocus settings
af_enabled = False

# Intial Camera Settings
leftCam = None
rightCam = None
serialPort = 'COM4'

is_tracking = False

@app.route("/")
@cross_origin()
def home():
    return "Hello, Flask! Why don't you work?"

@cross_origin()
@app.route('/video_feed')
def video_feed():
  global leftCam
  # Open the video capture
  # cap = EasyPySpin.VideoCapture(2)
  print(leftCam)
  cap = EasyPySpin.VideoCapture(leftCam)
  if not cap.isOpened():
      print("Camera can't open\nexit")
      return -1

  dlc_proc = Processor()
  dlc_live = DLCLive('DLC_models', processor=dlc_proc, display=False)
  
  def gen():
    global start_recording, stop_recording, settings, is_tracking, serialPort
    is_recording = False
    # buff = []
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter()
    with Connection.open_serial_port(serialPort) as connection:
    # with Connection.open_serial_port("COM4") as connection:
        device_list = connection.detect_devices()
        firstIt = True
        while (cap.isOpened()):
            # Read a frame from the video capture
            success, frame = cap.read()
            # Check if the frame was successfully read
            if success:
                # Resize the image to be 256x256
                img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)
                if firstIt:
                  dlc_live.init_inference(img_show)
                  firstIt = False
                poseArr = dlc_live.get_pose(img_show)
                posArr = poseArr[:, [0, 1]]
                posArr =  [list( map(lambda x: int(abs(x)), i) ) for i in posArr]

                # frame = draw_skeleton(frame, posArr, settings["resolution"][0])
                
                if start_recording:
                  print("Start Recording")
                  # out.open('output.avi', fourcc, 10.0, (1024,1024), isColor=False)
                  out.open(settings["filepath"] + settings["filename"], fourcc, float(settings["fps"]), settings["resolution"], isColor=False)
                  start_recording = False
                  is_recording = True
                if is_recording:
                  # print("Recording Frame")
                  frame = cv2.resize(frame, settings["resolution"])
                  out.write(frame)
                if stop_recording:
                  print("Stopped Recording")
                  out.release()
                  is_recording = False
                  stop_recording = False
                nerveringX = poseArr[2, 0]
                nerveringY = poseArr[2, 1]
                if is_tracking:
                  trackWorm((nerveringX, nerveringY), device_list)
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

@cross_origin()
@app.route('/video_feed_fluorescent')
def video_feed_fluorescent():
  global rightCam
  # Open the video capture
  # cap = EasyPySpin.VideoCapture(2)
  cap = EasyPySpin.VideoCapture(rightCam)
  if not cap.isOpened():
      print("Camera can't open\nexit")
      return -1
  
  def gen():
    global start_recording_fl, stop_recording_fl, settings, is_tracking, serialPort
    is_recording = False
    # buff = []
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter()
    while (cap.isOpened()):
        # Read a frame from the video capture
        success, frame = cap.read()
        # Check if the frame was successfully read
        if success:
            if start_recording_fl:
              print("Start Fluorescent Recording")
              # out.open('output.avi', fourcc, 10.0, (1024,1024), isColor=False)
              out.open(settings["filepath_fl"] + settings["filename_fl"], fourcc, float(settings["fps_fl"]), settings["resolution_fl"], isColor=False)
              start_recording_fl = False
              is_recording = True
            if is_recording:
              # print("Recording Frame")
              frame = cv2.resize(frame, settings["resolution_fl"])
              out.write(frame)
            if stop_recording_fl:
              print("Stopped Fluorescent Recording")
              out.release()
              is_recording = False
              stop_recording_fl = False
            
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

@cross_origin()
@app.route("/start_recording", methods=['POST'])
def start_recording():
    global start_recording, start_recording_fl, settings
    # Update the settings with the data from the request body
    settings["filepath"] = request.json["filepath"]
    settings["filename"] = request.json["filename"]
    settings["fps"] = request.json["fps"]
    settings["resolution"] = (request.json["resolution"], request.json["resolution"])
    settings["filepath_fl"] = request.json["filepath_fl"]
    settings["filename_fl"] = request.json["filename_fl"]
    settings["fps_fl"] = request.json["fps_fl"]
    settings["resolution_fl"] = (request.json["resolution_fl"], request.json["resolution_fl"])
    # Set the recording flag to True
    start_recording = True
    start_recording_fl = True
    # return jsonify({"message": "Recording started"})
    return str(settings)


@cross_origin()
@app.route("/stop_recording", methods=['POST'])
def stop_recording():
    global stop_recording, stop_recording_fl
    # Release the video writer and set the recording flag to False
    stop_recording = True
    stop_recording_fl = True
    # Attempt at fixing CORS error
    return jsonify({"message": "Recording stopped"})


@cross_origin()
@app.route("/camera_settings", methods=['POST'])
def camera_settings():
    global leftCam, rightCam, serialPort
    # Release the video writer and set the recording flag to False
    leftCam = request.json['leftCam']
    rightCam = request.json['rightCam']
    serialPort = request.json['serialInput']
    
    # Attempt at fixing CORS error
    return jsonify({"message": "Recording stopped"})


@cross_origin()
@app.route("/toggle_tracking", methods=['POST'])
def toggle_tracking():
    global is_tracking
    is_tracking = request.json['is_tracking'] == "True"
    return str(is_tracking)


@cross_origin()
@app.route("/toggle_af", methods=['POST'])
def toggle_af():
    global af_enabled
    af_enabled = request.json['af_enabled'] == "True"
    return str(af_enabled)


def autofocus(image, threshold=20):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    abs_sobelx = cv2.convertScaleAbs(sobelx)
    focus_measure = cv2.Laplacian(abs_sobelx, cv2.CV_64F).var()
    return focus_measure > threshold

def simpleToCenter(centroidX, centroidY):
  # calculate the percent the position is from the edge of the frame
  percentX = float(centroidX) / float(TOTAL_PIXELS_X)
  percentY = float(centroidY) / float(TOTAL_PIXELS_Y)

  # millimeters the position is from the edge
  millisX = percentX * TOTAL_MM_X
  millisY = percentY * TOTAL_MM_Y

  # millimeters the stage needs to move to catch up to the worm's position
  millisMoveX = ZABER_ORIENTATION_X * (millisX - TOTAL_MM_X/2)
  millisMoveY = ZABER_ORIENTATION_Y * (millisY - TOTAL_MM_Y/2)

  return millisMoveX, millisMoveY, millisMoveX, millisMoveY

def trackWorm(input, device_list):
	# check if the input is NaN float value and return if so
  if math.isnan(input[0]):
    return 0, 0

	# convert pixels to millimeters
  inpX = input[0]
  inpY = input[1]

	# create master list value that will contain [command move x, command move y, relative worm position x, relative worm position y]
	# relative worm position is relative to the (0, 0) of the video feed
  # master = [0, 0, 0, 0]
  master = simpleToCenter(inpX, inpY)

	# convert the millimeters back to microsteps
  xCmdAmt = master[0] * MM_MST
  yCmdAmt = master[1] * MM_MST

  # determine device from list
  deviceX: device = device_list[0]
  deviceY: device = device_list[1]

  # get current device location
  deviceXPos = deviceX.get_position(unit = Units.NATIVE)
  deviceYPos = deviceY.get_position(unit = Units.NATIVE)

  # move device if the bounds of the device are not exceeded
  if (deviceXPos + xCmdAmt/10 < MAXIMUM_DEVICE_POSITION 
      or deviceXPos + xCmdAmt/10 > MINIMUM_DEVICE_POSITION
      or deviceYPos + xCmdAmt/10 < MAXIMUM_DEVICE_POSITION 
      or deviceYPos + xCmdAmt/10 > MINIMUM_DEVICE_POSITION):
    deviceX.move_relative(xCmdAmt/10, Units.NATIVE)
    deviceY.move_relative(yCmdAmt/10, Units.NATIVE)
  return 0, 0
    
	


def save_video(buff): 
  fourcc = cv2.VideoWriter_fourcc(*'XVID')
  out = cv2.VideoWriter('WebCam.avi',fourcc, 10.0, (256, 256))
  for i, frame in enumerate(buff):
    out.write(frame)
  out.release()
  
def draw_skeleton(frame, posArr, resolution):
  factor = resolution / 256
  posArr = map((lambda x: x * factor), posArr)
  # Line and circle attributes
  linecolor = (0, 0, 0)
  lineThickness = 2
  circleThickness = -1
  circleRadius = 2
  
  # Colors of the different worm parts
  noseTipColor = (0, 0, 255)
  pharynxColor = (0, 128, 255)
  nerveRingColor = (0, 255, 255)
  midbody1Color = (0, 255, 0)
  midbody2Color = (255, 0, 0)
  midbody3Color = (255, 0, 255)
  tailBaseColor = (0, 0, 255)
  tailTipColor = (255, 0, 0)
  # confArr = poseArr[:, 2]
  # Overlay the tracking data onto the image
  # line from nose tip to pharynx 
  cv2.line(frame, posArr[0], posArr[1], linecolor, lineThickness)
  # line from pharynx to nerve_ring
  cv2.line(frame, posArr[1], posArr[2], linecolor, lineThickness)
  # line from nerve ring to midbody1
  cv2.line(frame, posArr[2], posArr[3], linecolor, lineThickness)
  # line from midbody1 to midbody2
  cv2.line(frame, posArr[3], posArr[4], linecolor, lineThickness)
  # line from midbody2 to midbody3
  cv2.line(frame, posArr[4], posArr[5], linecolor, lineThickness)
  # line from midbody3 to tail_base
  cv2.line(frame, posArr[5], posArr[6], linecolor, lineThickness)
  # line from tail_base to tail_tip
  cv2.line(frame, posArr[6], posArr[7], linecolor, lineThickness)
  
  # draw circles on top of each worm part
  cv2.circle(frame, posArr[0], circleRadius, noseTipColor, circleThickness)
  cv2.circle(frame, posArr[1], circleRadius, pharynxColor, circleThickness)
  cv2.circle(frame, posArr[2], circleRadius, nerveRingColor, circleThickness)
  cv2.circle(frame, posArr[3], circleRadius, midbody1Color, circleThickness)
  cv2.circle(frame, posArr[4], circleRadius, midbody2Color, circleThickness)
  cv2.circle(frame, posArr[5], circleRadius, midbody3Color, circleThickness)
  cv2.circle(frame, posArr[6], circleRadius, tailBaseColor, circleThickness)
  cv2.circle(frame, posArr[7], circleRadius, tailTipColor, circleThickness)

  return frame


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)

       
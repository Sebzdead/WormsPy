import cv2
import math
import time
import copy
import pytz
import queue
import pygame
import pathlib
import threading
import EasyPySpin
import numpy as np
from datetime import datetime
from pathlib import Path
from threading import Lock, Thread
from zaber_motion import Library, Units
from plot_worm_path import plot_worm_path
from flask_cors import CORS, cross_origin
from skimage.filters import threshold_yen
from skimage.measure import label, regionprops
from zaber_motion.ascii import Connection, Device
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

app = Flask(__name__, template_folder='production\\templates',
            static_url_path='/static',
            static_folder='production\\static')
CORS(app, origins=['http://localhost:4200', 'http://localhost:5000'])
app.config['CORS_HEADERS'] = 'Content-Type'

# Start the Flask app locally on host IP address 127.0.0.1 for testing
# python -m flask run --host=127.0.0.1

# SET UP CONFIGURATION
XYmotorport = 'COM6' # Will vary depending on the computer
Zmotorport = 'COM3' # Will vary depending on the computer
TOTAL_MM_X = 1.92  # total width of the FOV in mm (measure)
TOTAL_MM_Y = 1.2  # total height of the FOV in mm (measure)
MM_MST = 20997  # millimeters per microstep
# Zaber device boundaries
MAXIMUM_DEVICE_XY_POSITION = 1066667 # initialized, wil be updated by the motors
MAXIMUM_DEVICE_Z_POSITION = 209974 # may vary if using different motors
MINIMUM_DEVICE_POSITION = 0
ZABER_ORIENTATION_X = 1 # whether the x direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_Y = -1 # whether the y direction of the zaber is inverted from the video feed (-1 if they are inverted)
hist_frame = np.zeros((1200, 1920, 1), dtype=np.uint8) #change to match frame size of the right camera feed (y,x,1)

# settings for the recording
FPS = 10 # Brightfield value: MUST MANUALLY CHANGE :( depending on camera model you could detect it from the camera
timeZone = pytz.timezone("US/Eastern")
settings = {
    "filepath": str(pathlib.Path.home() / 'WormSpy_video'),
    "filename": 'default',
    "use_avi_l": True, # Set to True if you want to record the left camera as a compressed avi file, False if you want to record as uncompressed tiff files
    "use_avi_r": True, # Set to True if you want to record the right camera as a compressed avi file, False if you want to record as uncompressed tiff files
}

# DLC Live Settings:
# from dlclive import DLCLive, Processor
# dlc_proc = Processor() # Import the DLC NN model
dlc_live = None # remove this line if using DLC
# dlc_live = DLCLive(r'C:\Users\User\Documents\WormSpy\DLC_models/3-node',
#                    processor=dlc_proc, display=False)

# Global Variables (leave alone)
stop_stream = False
is_recording = False
start_recording = False
stop_recording = False
start_recording_r = False
stop_recording_r = False
af_enabled = False
start_af = False
heatmap_enabled = False
track_algorithm = 0
is_tracking = False
nodeIndex = 0
mutex = Lock()
isManualEnabled = False
hist_max = 0
leftCam = None # leave as None, will be set by the user in the UI
rightCam = None # leave as None, will be set by the user in the UI
frame_queue_left = queue.Queue() # Initialize the queue
frame_queue_right = queue.Queue() # Initialize the queue 
Library.enable_device_db_store() # Initialize the device database for Zaber communication

def tiff_writer(project_path, frame_queue):
    while True:
        dt, frame = frame_queue.get()
        if frame is None:
            break
        frame_name = f"frame_{dt}.tiff"
        cv2.imwrite(str(project_path / frame_name), frame)

# Add route to serve Angular app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@cross_origin()
def serve_angular(path):
    if path and Path(app.static_folder + '/' + path).exists():
        return send_from_directory(app.static_folder, path)
    return render_template('index.html')

@cross_origin()
@app.route('/video_feed')
def video_feed():
    global leftCam
    # Open the video capture
    cap = EasyPySpin.VideoCapture(leftCam)
    resolution_l = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    initial_coords = [(resolution_l[0]/2), resolution_l[1]/2] # INITIALIZE IN CENTER OF FRAME
    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1
    if stop_stream:
        cap.release()
    # function to generate a stream of image frames for the tracking video feed
    def gen():
        global xMotor, yMotor, zMotor, start_recording, stop_recording, settings, is_tracking, serialPort, start_af, stop_stream, nodeIndex, track_algorithm, is_recording, MAXIMUM_DEVICE_XY_POSITION, MAXIMUM_DEVICE_Z_POSITION
        start_af = False
        start_recording = False
        stop_recording = False
        is_recording = False
        factor = 2 # Downsample factor change as desired
        xPos = 0
        yPos = 0
        with Connection.open_serial_port(XYmotorport) as connection:
            with Connection.open_serial_port(Zmotorport) as connection2:
                connection.enable_alerts()
                connection2.enable_alerts()
                horizontal_motors = connection.detect_devices()
                vertical_motor = connection2.detect_devices()
                print("Found devices on " + XYmotorport.format(len(horizontal_motors)))
                print("Found devices on " + Zmotorport.format(len(vertical_motor)))
                device_X = horizontal_motors[0]
                device_Y = horizontal_motors[1]
                device_Z = vertical_motor[0]
                xMotor = device_X.get_axis(1)
                yMotor = device_Y.get_axis(1)
                zMotor = device_Z.get_axis(1)
                MAXIMUM_DEVICE_XY_POSITION = device_X.settings.get("limit.max")
                MAXIMUM_DEVICE_Z_POSITION = device_Z.settings.get("limit.max")
                firstIt = True
                while (cap.isOpened()):
                    success, frame = cap.read() # Read a frame from the video capture
                    calculated_worm_coords = initial_coords
                    if success:
                        if frame.dtype != np.uint8: #check if frame is 8 bit and grayscale and convert if not
                            display_frame_l = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                        else:
                            display_frame_l = frame
                        if len(display_frame_l.shape) == 3:
                            display_frame_l = cv2.cvtColor(display_frame_l, cv2.COLOR_BGR2GRAY)
                        frame_downsample = cv2.resize(display_frame_l, (display_frame_l.shape[1] // factor, display_frame_l.shape[0] // factor), interpolation=cv2.INTER_AREA)
                        xPos = xMotor.get_position(unit=Units.LENGTH_MICROMETRES)
                        yPos = yMotor.get_position(unit=Units.LENGTH_MICROMETRES)
                        if is_tracking: ### BUTTON HAS BEEN PRESSED
                            if track_algorithm == 0: ### BRIGHT BACKGROUND THRESHOLDING
                                processed_frame = Thresh_Light_Background(frame_downsample)
                                worm_coords = find_worm_cms(processed_frame, factor, initial_coords)
                            elif track_algorithm == 1: ### FLUORESCENT THRESHOLDING
                                processed_frame = Thresh_Fluorescent_Marker(frame_downsample)
                                worm_coords = find_worm_cms(processed_frame, factor, initial_coords)
                            elif track_algorithm == 2: ### DEEP LAB CUT TRACKING
                                height, width = frame_downsample.shape
                                downsample_size = (int(height), int(width))
                                poseArr = DLC_tracking(dlc_live,firstIt,frame_downsample,downsample_size, factor)
                                posArr = poseArr[:, [0, 1]]
                                worm_coords = (posArr[nodeIndex, 0] , posArr[nodeIndex, 1])
                            calculated_worm_coords = (worm_coords[0] , worm_coords[1])
                            # MUTEX POSITION 1
                            if not mutex.locked():
                                # returns microsteps
                                trackWorm(
                                (calculated_worm_coords[0], calculated_worm_coords[1]), xMotor, yMotor, xPos, yPos, resolution_l) # TRACKING FUNCTION
                        # Reinitialize file recording
                        if start_recording:
                            print("Start Left Recording")
                            start_recording = False
                            is_recording = True
                            dt = datetime.now(tz=timeZone)
                            dtstr = dt.strftime("%d-%m-%Y_%H-%M")
                            folder_name = settings["filename"] + '_' + dtstr
                            if settings["use_avi_l"]:
                                # initialize video writer
                                fourcc_l = cv2.VideoWriter_fourcc(*'XVID')
                                parent_path: pathlib.Path = filepathToDirectory(settings["filepath"]) / folder_name
                                if not parent_path.exists(): 
                                    parent_path.mkdir(parents=True, exist_ok=False)
                                video_writer_l = cv2.VideoWriter(str(parent_path / (folder_name + "_L.avi")), fourcc_l, FPS, (display_frame_l.shape[1], display_frame_l.shape[0]), isColor=False)
                            else:
                                tiff_folder: pathlib.Path = filepathToDirectory(settings["filepath"]) / folder_name / 'leftcam_tiffs'
                                if not tiff_folder.exists(): 
                                    tiff_folder.mkdir(parents=True, exist_ok=False)
                                # Start the writer thread
                                writer_thread_l = Thread(target=tiff_writer, args=(tiff_folder, frame_queue_left))
                                writer_thread_l.start()
                            dtype = [('timestamp', 'U26'), ('X_position', 'f8'), ('Y_position', 'f8')]
                            csvDump = np.zeros(0, dtype=dtype)
                        if is_recording:
                            time = datetime.now(tz=timeZone)
                            dt = time.strftime("%H-%M-%S.%f")
                            csvDump = np.append(csvDump, np.array([(dt, xPos, yPos)], dtype=dtype))
                            if settings["use_avi_l"]:
                                video_writer_l.write(display_frame_l)
                            else:
                                frame_queue_left.put((dt, frame))  # Add frame to queue instead of writing directly
                        if stop_recording:
                            print("Stopped Left Recording")
                            if settings["use_avi_l"]:
                                video_writer_l.release()
                            else:
                                frame_queue_left.put((None, None))
                                writer_thread_l.join()
                            csv_file = settings["filename"] + ".csv"
                            csv_file_path = pathlib.Path(settings["filepath"]) / folder_name / csv_file
                            header = "timestamp,X_position,Y_position"  # Add header
                            np.savetxt(str(csv_file_path), csvDump, delimiter=",", header=header, comments="", fmt='%s,%f,%f')
                            plot_worm_path(csv_file_path) # creates a plot of the worm path in the same directory as the csv file
                            is_recording = False
                            stop_recording = False
                        # Change color to rgb from gray to allow for the coloring of circles
                        display_frame_l = cv2.cvtColor(display_frame_l, cv2.COLOR_GRAY2RGB)
                        # draw CMS position on frame as green circle
                        cv2.circle(display_frame_l, (int(calculated_worm_coords[0]), int(calculated_worm_coords[1])), 9, (0, 255, 0), -1)
                        # add skeleton overlay to image for DLC
                        #frame = draw_skeleton(frame, posArr)
                        ret, jpeg = cv2.imencode('.png', display_frame_l)
                        # Yield the encoded frame
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    else:
                        # If the frame was not successfully read, yield a "blank frame
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@cross_origin()
@app.route('/video_feed_fluorescent')
def video_feed_fluorescent():
    global rightCam, stop_stream
    cap2 = EasyPySpin.VideoCapture(rightCam)
    # Check if the camera is opened successfully
    if not cap2.isOpened():
        print("Camera can't open\nexit")
        return -1
    if stop_stream:
        cap2.release()
    def gen():
        global heatmap_enabled, start_recording_r, stop_recording_r, settings, is_tracking, serialPort, hist_frame, hist_max, latest_frame
        is_recording = False
        while (cap2.isOpened()):
            success, frame = cap2.read()
            if success:
                if frame.dtype != np.uint8: #check if frame is 8 bit and grayscale and convert if not
                    display_frame_r = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                else:
                    display_frame_r = frame
                if len(display_frame_r.shape) == 3:
                    record_frame_r = cv2.cvtColor(display_frame_r, cv2.COLOR_BGR2GRAY)
                else:
                    record_frame_r = display_frame_r
                if heatmap_enabled == True: # Apply the jet color map to the frame
                    display_frame_r = cv2.applyColorMap(display_frame_r, cv2.COLORMAP_JET) # Apply the jet color map to the frame
                hist_frame = copy.copy(display_frame_r) #histogram frame
                hist_max = np.max(frame) # max value of the frame
                latest_frame = display_frame_r.copy()
                if start_recording_r:
                    print("Start Right Recording")
                    start_recording_r = False
                    is_recording = True
                    dt = datetime.now(tz=timeZone)
                    dtstr = dt.strftime("%d-%m-%Y_%H-%M")
                    folder_name = settings["filename"] + '_' + dtstr
                    if settings["use_avi_r"]:
                        fourcc_r = cv2.VideoWriter_fourcc(*'XVID')
                        parent_path: pathlib.Path = filepathToDirectory(settings["filepath"]) / folder_name
                        if not parent_path.exists(): 
                            parent_path.mkdir(parents=True, exist_ok=False)
                        video_writer_r = cv2.VideoWriter(str(parent_path / (folder_name + "_R.avi")), fourcc_r, FPS, (record_frame_r.shape[1], record_frame_r.shape[0]), isColor=False)
                    else:
                        tiff_folder: pathlib.Path = filepathToDirectory(settings["filepath"]) / folder_name / 'rightcam_tiffs'
                        if not tiff_folder.exists(): 
                            tiff_folder.mkdir(parents=True, exist_ok=False)
                        # Start the writer thread
                        writer_thread_r = Thread(target=tiff_writer, args=(tiff_folder, frame_queue_right))
                        writer_thread_r.start()
                if is_recording:
                    time = datetime.now(tz=timeZone)
                    dt = time.strftime("%H-%M-%S.%f")
                    if settings["use_avi_r"]:
                        video_writer_r.write(record_frame_r)
                    else:
                        frame_queue_right.put((dt, frame))  # Add frame to queue instead of writing directly
                if stop_recording_r:
                    print("Stopped Right Recording")
                    is_recording = False
                    stop_recording_r = False
                    if settings["use_avi_r"]:
                        video_writer_r.release()
                    else:
                        frame_queue_right.put((None, None))  # Signal the writer thread to stop
                        writer_thread_r.join()  # Wait for the writer thread to finish
                ret, jpeg = cv2.imencode('.png', display_frame_r)
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                # If the frame was not successfully read, yield a blank frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@cross_origin()
@app.route("/get_hist")
def get_hist():
    def gen():
        global hist_frame
        current_frame = np.zeros((1200, 1920, 1), dtype=np.uint8)
        first = True
        while True: 
            if first:
                first = False
            if hist_frame is not None:
                current_frame = hist_frame
            current_frame = hist_frame
            if current_frame is not None:
                hist_size = 256
                hist_w = 512
                hist_h = 400
                bin_w = int(round(hist_w / hist_size))
                hist = cv2.calcHist(current_frame, [0], None, [hist_size], (0, 256), accumulate=False)
                norm_hist = cv2.normalize(hist, hist, 0, hist_h, cv2.NORM_MINMAX)
                histImage = np.zeros((hist_h, hist_w, 3), dtype=np.uint8)
                for i in range(1, hist_size):
                    cv2.line(histImage, (bin_w * (i - 1), hist_h - int(norm_hist[i - 1])),
                             (bin_w * (i), hist_h - int(norm_hist[i])), (0, 255, 0), thickness=2)
                ret, image_data = cv2.imencode('.png', histImage)
                png = image_data.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + png + b'\r\n')
            else:
                # If the frame was not successfully read, yield a blank frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@cross_origin()
@app.route('/stream_max')
def stream_max():
    def gen():
        global hist_max
        yield str(hist_max)
    return Response(gen(), mimetype='text/plain')

@cross_origin()
@app.route("/start_recording", methods=['POST'])
def start_record():
    global start_recording, start_recording_r, settings
    # Update the settings with the data from the request body
    try:
        settings["filepath"] = request.json["filepath"]
        settings["filename"] = request.json["filename"]
        settings['use_avi_l'] = request.json['use_avi_left']
        settings['use_avi_r'] = request.json['use_avi_right']
    except KeyError as e:
        settings['use_avi_l'] = True
        settings['use_avi_r'] = True
        print("Using previous or default filepath and filename of this session for this recording.\nTo avoid this, please set the filepath and filename in the UI and start the recording via the UI.")
    
    # Set the recording flag to True
    start_recording = True
    start_recording_r = True
    # return jsonify({"message": "Recording started"})
    return str(settings)

@cross_origin()
@app.route("/stop_recording", methods=['POST'])
def stop_record():
    global stop_recording, stop_recording_r
    # Stop the recording of both video feeds
    stop_recording = True
    stop_recording_r = True
    return jsonify({"message": "Recording stopped"})

@cross_origin()
@app.route("/toggle_heatmap", methods=['POST']) ##################### FIX THIS
def heatmap():
    global heatmap_enable, heatmap_enabled
    heatmap_enabled = request.json['heatmap_enabled'] == "True"
    return str(heatmap_enabled)

@cross_origin()
@app.route("/stop_live_stream", methods=['POST'])
def stop_live_stream():
    global stop_stream
    # Stop both video feeds
    stop_stream = True
    return jsonify({"message": "Streams stopped"})

@cross_origin()
@app.route("/camera_settings", methods=['POST']) 
def camera_settings():
    global leftCam, rightCam, serialPort
    # Set the camera settings before starting the video feeds
    leftCam = request.json['leftCam']
    rightCam = request.json['rightCam']
    serialPort = request.json['serialInput']
    return jsonify({"message": "Recording stopped"})

@cross_origin()
@app.route("/node_index", methods=['POST'])
def node_index():
    global nodeIndex
    # Set the camera settings before starting the video feeds
    nodeIndex = request.json['index']
    return jsonify({f"message": "NodeIndex Recieved: {nodeIndex}"})

@cross_origin()
@app.route("/toggle_tracking", methods=['POST'])
def toggle_tracking():
    global is_tracking, track_algorithm
    is_tracking = request.json['is_tracking'] == "True"
    track_algorithm = int(request.json['tracking_algorithm'])
    return str(is_tracking)

@cross_origin()
@app.route("/toggle_af", methods=['POST'])
def toggle_af():
    global af_enabled
    af_request = request.json['af_enabled'] == "True"
    if af_request and not af_enabled:
        start_autofocus()
    elif not af_request and af_enabled:
        stop_autofocus()
    return str(af_enabled)

@cross_origin()
@app.route("/toggle_manual", methods=['POST'])
def toggle_manual():
    global isManualEnabled
    manual_mode = request.json['toggle_manual'] == "True"
    if isManualEnabled and not manual_mode: # Turning off manual mode
        isManualEnabled = False
    elif not isManualEnabled and manual_mode: # Turning on manual mode and starting controller
        isManualEnabled = True
        start_controller()
    return str(manual_mode)

@cross_origin()
@app.route("/move_to_center", methods=['POST'])
def move_to_center():
    global xMotor, yMotor
    xMax = xMotor.settings.get("limit.max")
    yMax = yMotor.settings.get("limit.max")
    midX = xMax / 2
    midY = yMax / 2
    xMotor.move_absolute(midX, unit=Units.NATIVE, wait_until_idle=False)
    yMotor.move_absolute(midY, unit=Units.NATIVE, wait_until_idle=False)
    return jsonify({"message": "Moved to center"})

def calculate_focus_metric(frame):
    """
    Calculate a focus metric using the variance of the Laplacian.
    A higher variance indicates a sharper image.
    """
    laplacian = cv2.Laplacian(frame, cv2.CV_64F)
    return laplacian.var()

class PIDController:
    def __init__(self, kp, ki, kd, setpoint):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.integral = 0.0
        self.prev_error = 0.0

    def compute(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.prev_error = error
        return output

def continuous_autofocus(optimal_z, optimal_focus_metric, frame_interval=0.2):
    """
    Continuously adjusts the zMotor based on the focus metric from the latest frame.
    Updates at most 5 times per second.
    """
    global af_enabled, zMotor, latest_frame
    pid = PIDController(kp=0.001, ki=0, kd=0.001, setpoint=optimal_focus_metric)
    current_z = optimal_z
    while af_enabled:
        start_time = time.time()
        if latest_frame is None:
            time.sleep(frame_interval)
            continue
        metric = calculate_focus_metric(latest_frame)
        adjustment = pid.compute(metric, frame_interval)
        max_step = 20  # Maximum z movement per iteration (adjust as needed)
        adjustment = max(-max_step, min(max_step, adjustment))
        new_z = current_z + adjustment
        print("Focus metric:", metric, "Adjustment:", adjustment, "New z:", new_z)
        try:
            zMotor.move_absolute(new_z, unit=Units.NATIVE, wait_until_idle=True)
        except Exception as e:
            print("Autofocus: Error moving zMotor:", e)
        current_z = new_z
        elapsed = time.time() - start_time
        if elapsed < frame_interval:
            time.sleep(frame_interval - elapsed)
    print("Autofocus stopped.")

def start_autofocus():
    """
    Initializes autofocus by capturing the current frame and zMotor position,
    then starting the continuous autofocus loop in a daemon thread.
    """
    global af_enabled, zMotor, latest_frame, af_thread
    if latest_frame is None:
        print("No frame available to initialize autofocus.")
        return
    optimal_z = zMotor.get_position(unit=Units.NATIVE)
    optimal_focus_metric = calculate_focus_metric(latest_frame)
    print("Autofocus started with optimal_z =", optimal_z, "and optimal_focus_metric =", optimal_focus_metric)
    af_enabled = True
    af_thread = threading.Thread(target=continuous_autofocus, args=(optimal_z, optimal_focus_metric))
    af_thread.daemon = True
    af_thread.start()

def stop_autofocus():
    """
    Stops the continuous autofocus.
    """
    global af_enabled
    af_enabled = False
    print("Stopping autofocus...")

def smoothing(worm_coords, previous_worm_coords): # exponential smoothing function. Alpha determines how much smoothing is desirable.
    alpha = 0.7
    new_stage_x = previous_worm_coords[0] * alpha + worm_coords[0] * (1 - alpha)  
    new_stage_y = previous_worm_coords[1] * alpha + worm_coords[1] * (1 - alpha)
    # print new smoothed coords
    print("X: " + str(new_stage_x) + " Y: " + str(new_stage_y))
    return (new_stage_x, new_stage_y)

def simpleToCenter(centroidX, centroidY, resolution):
    # calculate the percent the position is from the edge of the frame
    percentX = float(centroidX) / float(resolution[0])
    percentY = float(centroidY) / float(resolution[1])
    # millimeters the position is from the edge
    millisX = percentX * TOTAL_MM_X
    millisY = percentY * TOTAL_MM_Y
    # millimeters the stage needs to move to catch up to the worm's position
    millisMoveX = ZABER_ORIENTATION_X * (millisX - TOTAL_MM_X/2)
    millisMoveY = ZABER_ORIENTATION_Y * (millisY - TOTAL_MM_Y/2)
    return millisMoveX, millisMoveY 

def trackWorm(input, deviceX: Device, deviceY: Device, deviceXPos, deviceYPos, resolution):
    global MAXIMUM_DEVICE_XY_POSITION, MINIMUM_DEVICE_POSITION
    # check if the input is NaN float value and return if so  
    if math.isnan(input[0]):
        return 0, 0
    # relative worm position is relative to the (0, 0) of the video feed
    master = simpleToCenter(input[0], input[1], resolution)
    # convert the millimeters back to microsteps
    xCmdAmt = master[0] * MM_MST
    yCmdAmt = master[1] * MM_MST

    # move device if the bounds of the device are not exceeded
    if (deviceXPos + xCmdAmt < MAXIMUM_DEVICE_XY_POSITION
    or deviceXPos + xCmdAmt > MINIMUM_DEVICE_POSITION
    or deviceYPos + yCmdAmt < MAXIMUM_DEVICE_XY_POSITION
    or deviceYPos + yCmdAmt > MINIMUM_DEVICE_POSITION):
        # move the device to the new position.
        x_data =int(xCmdAmt/5)
        y_data =int(yCmdAmt/5)
        deviceX.generic_command_no_response(f'move rel {x_data} 10000 5')
        deviceY.generic_command_no_response(f'move rel {y_data} 10000 5')
    return (deviceXPos + xCmdAmt), (deviceYPos + yCmdAmt)#, xCmdAmt, yCmdAmt

def Thresh_Light_Background(frame):
    blurred_frame = cv2.GaussianBlur(frame, (33, 33), 99)
    thresh = cv2.adaptiveThreshold(blurred_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 99, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    eroded_image = cv2.erode(thresh, kernel, iterations=3)
    processed_frame = cv2.dilate(eroded_image, kernel, iterations=1)
    return processed_frame

def Thresh_Fluorescent_Marker(frame):
    inv_gamma = 1.5
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    gamma = cv2.LUT(frame, table)
    # Apply Gaussian blur to the frame
    blurred_frame = cv2.GaussianBlur(gamma, (1, 1), 11)
    # Apply Yen's thresholding
    thresh = threshold_yen(blurred_frame)
    # Create a binary image by applying the threshold
    processed_frame = blurred_frame > thresh
    processed_frame = processed_frame.astype(np.uint8) * 255
    return processed_frame

def find_worm_cms(processed_frame, factor, initial_coords):
    labeled_image = label(processed_frame)  #scans binary image and groups connected pixels with the value 1 into labeled regions
    regions = regionprops(labeled_image) #calculates properties of the labelled region, returns a list of regionProperties objects, each corresponding to properties of one of the labelled regions.
    regions_by_area = sorted(regions, key=lambda x: x.area, reverse=True)
    if regions_by_area:
        coords = regions_by_area[0].centroid
    else:
        coords = initial_coords  # center of FOV
    coords = (round(coords[1]), round(coords[0])) # flip x and y coordinates to match the video feed
    coords = (coords[0] * factor, coords[1] * factor)
    return coords

def DLC_tracking(dlc_live,firstIt,frame,new_size,factor): ## DLC TRACKING FUNCTION, SHOULD WORK IF VARIABLES ARE SET CORRECTLY
    # Resize the image
    img_tracking = cv2.resize(frame, new_size, interpolation = cv2.INTER_AREA)
    if firstIt: 
        dlc_live.init_inference(img_tracking)
        firstIt = False
    poseArr = dlc_live.get_pose(img_tracking)
    # rescale the pose array to the original image size
    poseArr = poseArr * factor
    return poseArr

def draw_skeleton(frame, posArr): ### DLC SKELETON DRAWING FUNCTION EDIT AS NEEDED
    # Line and circle attributes
    linecolor = (0, 0, 0)
    lineThickness = 2
    circleThickness = -1
    circleRadius = 5

    # Colors of the different worm parts
    noseTipColor = (0, 0, 255)
    pharynxColor = (0, 128, 255)
    nerveRingColor = (0, 255, 255)
    # Overlay the tracking data onto the image
    # line from nose tip to pharynx
    cv2.line(frame, posArr[0], posArr[1], linecolor, lineThickness)
    # line from pharynx to nerve_ring
    cv2.line(frame, posArr[1], posArr[2], linecolor, lineThickness)

    # draw circles on top of each worm part
    cv2.circle(frame, posArr[0], circleRadius, noseTipColor, circleThickness)
    cv2.circle(frame, posArr[1], circleRadius, pharynxColor, circleThickness)
    cv2.circle(frame, posArr[2], circleRadius, nerveRingColor, circleThickness)
    return frame

def filepathToDirectory(str_path: str):
    # global record_path
    path = pathlib.Path(str_path)
    if not path.exists():
        path.mkdir(parents=True)
    return path

def start_controller():
    # Check if any joystick is connected
    pygame.init()
    pygame.joystick.init()
    global isManualEnabled, xMotor, yMotor, zMotor, is_tracking, is_recording, MAXIMUM_DEVICE_XY_POSITION, MAXIMUM_DEVICE_Z_POSITION
    # Track last button state to detect button press (not held down)
    last_x_button_state = False
    
    if pygame.joystick.get_count() > 0:
        # Get the first joystick
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        # Get the number of axes
        num_axes = joystick.get_numaxes()

        # Check if the joystick has at least 2 axes
        if num_axes >= 2:
            sticks_good = True
            print("Joystick count: ", pygame.joystick.get_count())
            print("Joystick axes: ", joystick.get_numaxes())
            print("Joystick buttons: ", joystick.get_numbuttons())
        else:
            print("Joystick does not have enough axes")
    else:
        print("No joystick connected.")
        sticks_good = False
        
    try: 
        while isManualEnabled:
            
            pygame.event.pump()

            xPos = xMotor.get_position(unit=Units.NATIVE)
            yPos = yMotor.get_position(unit=Units.NATIVE)
            zPos = zMotor.get_position(unit=Units.NATIVE)

            if sticks_good == True:
                input_x = joystick.get_axis(0)
                input_y = joystick.get_axis(1)
                input_z = joystick.get_axis(3)
                x_data = int(input_x * 2000)
                y_data = int(input_y * 2000) * -1
                z_data = int(input_z * 100)
                    
            # Check X button (button 2) for tracking toggle
            if joystick.get_numbuttons() > 2:  # Make sure X button exists
                current_x_button_state = joystick.get_button(2)
                
                # Detect rising edge for X button
                if current_x_button_state and not last_x_button_state:
                    # Toggle tracking state
                    is_tracking = not is_tracking
                    print(f"X button pressed: {'Enabling' if is_tracking else 'Disabling'} tracking")
                
                # Update last X button state
                last_x_button_state = current_x_button_state

            if ((xPos + x_data < MAXIMUM_DEVICE_XY_POSITION
            or xPos + x_data > MINIMUM_DEVICE_POSITION) and input_x != 0):
                mutex.acquire(blocking=True, timeout=-1)
                xMotor.generic_command_no_response(f'move rel {x_data} 10000 5')
                mutex.release()

            if ((yPos + y_data < MAXIMUM_DEVICE_XY_POSITION
            or yPos + y_data > MINIMUM_DEVICE_POSITION) and input_y != 0):
                mutex.acquire(blocking=True, timeout=-1)
                yMotor.generic_command_no_response(f'move rel {y_data} 10000 5')
                mutex.release()

            if ((zPos + z_data < MAXIMUM_DEVICE_Z_POSITION
            or zPos + z_data > MINIMUM_DEVICE_POSITION) and input_z != 0):
                zMotor.generic_command_no_response(f'move rel {z_data} 10000 5')

    except KeyboardInterrupt:
        print("Exiting...")
        mutex.release()
        pygame.quit()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
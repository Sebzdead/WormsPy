import sys
import os
import cv2
import numpy as np
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QComboBox, QLineEdit, QSpinBox, QButtonGroup, QRadioButton,
                             QGroupBox, QCheckBox, QFileDialog, QSizePolicy, QFrame)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal, QUrl
import qdarkstyle
from flask import Response
from app import (app, video_feed, video_feed_fluorescent, get_hist, stream_max,
                toggle_tracking, toggle_heatmap, toggle_autofocus, toggle_manual,
                move_to_center, start_record, stop_record, camera_settings, node_index)

class CameraThread(QThread):
    """Thread for capturing camera feed without blocking UI"""
    image_update = pyqtSignal(np.ndarray)
    
    def __init__(self, feed_url):
        super().__init__()
        self.feed_url = feed_url
        self.running = True
        
    def run(self):
        cap = cv2.VideoCapture(self.feed_url)
        while self.running:
            ret, frame = cap.read()
            if ret:
                self.image_update.emit(frame)
            time.sleep(0.03)  # ~30 FPS
        cap.release()
    
    def stop(self):
        self.running = False

class VideoSurface(QLabel):
    """Custom QLabel to display video feed with proper resizing"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setMinimumSize(480, 320)
        
    def update_frame(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qt_image).scaled(self.size(), Qt.KeepAspectRatio))

class HistogramDisplay(QLabel):
    """Label to display histogram"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setMinimumSize(400, 200)
        self.setMaximumHeight(200)
        
    def update_histogram(self, frame):
        self.setPixmap(QPixmap.fromImage(frame).scaled(self.size(), Qt.KeepAspectRatio))

class WormsPyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Application state
        self.is_live_feed_enabled = False
        self.is_recording = False
        self.is_tracking_enabled = False
        self.is_autofocus_enabled = False
        self.heatmap_on = False
        self.manual_enabled = False
        
        # Camera settings
        self.left_camera = "0"  # Default camera 0
        self.right_camera = "1"  # Default camera 1
        self.api_url = "http://127.0.0.1:5000"
        self.node_index_value = 0
        self.track_algorithm = 0
        
        # Recording settings
        self.recording_settings = {
            "filepath": os.path.expanduser("~/WormSpy_video"),
            "filename": "Project_1",
            "use_avi_left": False,
            "use_avi_right": False,
        }
        
        # Initialize UI
        self.init_ui()
        
        # Initialize timers for histogram updates
        self.hist_timer = QTimer()
        self.hist_timer.timeout.connect(self.update_histogram_max)
        
    def init_ui(self):
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Title
        title_label = QLabel("WormsPy")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Video feeds layout
        feeds_layout = QHBoxLayout()
        
        # Left video feed
        self.left_video = VideoSurface()
        feeds_layout.addWidget(self.left_video, 1)
        
        # Right video feed
        self.right_video = VideoSurface()
        feeds_layout.addWidget(self.right_video, 1)
        
        main_layout.addLayout(feeds_layout, 3)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Camera settings group
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QGridLayout()
        
        # Left camera selection
        camera_layout.addWidget(QLabel("Left Camera:"), 0, 0)
        self.left_camera_combo = QComboBox()
        self.left_camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2", "Camera 3"])
        camera_layout.addWidget(self.left_camera_combo, 0, 1)
        
        # Right camera selection
        camera_layout.addWidget(QLabel("Right Camera:"), 1, 0)
        self.right_camera_combo = QComboBox()
        self.right_camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2", "Camera 3"])
        self.right_camera_combo.setCurrentIndex(1)  # Default to camera 1
        camera_layout.addWidget(self.right_camera_combo, 1, 1)
        
        # DLC Node Index
        camera_layout.addWidget(QLabel("DLC Node Index:"), 2, 0)
        self.node_index_spinbox = QSpinBox()
        self.node_index_spinbox.setRange(0, 2)
        self.node_index_spinbox.valueChanged.connect(self.send_node_index)
        camera_layout.addWidget(self.node_index_spinbox, 2, 1)
        
        # Start/Stop feed button
        self.feed_button = QPushButton("Start Live Feed")
        self.feed_button.clicked.connect(self.toggle_live_feed)
        camera_layout.addWidget(self.feed_button, 3, 0, 1, 2)
        
        camera_group.setLayout(camera_layout)
        controls_layout.addWidget(camera_group)
        
        # Tracking settings group
        tracking_group = QGroupBox("Tracking Settings")
        tracking_layout = QGridLayout()
        
        # Tracking algorithm selection
        tracking_layout.addWidget(QLabel("Algorithm:"), 0, 0)
        self.tracking_combo = QComboBox()
        self.tracking_combo.addItems([
            "Threshold Bright Tracking",
            "Fluorescent Marker Tracking",
            "DeepLabCut Tracking"
        ])
        tracking_layout.addWidget(self.tracking_combo, 0, 1)
        
        # Toggle tracking button
        self.tracking_button = QPushButton("Enable Tracking")
        self.tracking_button.clicked.connect(self.toggle_tracking)
        tracking_layout.addWidget(self.tracking_button, 1, 0, 1, 2)
        
        # Toggle autofocus button
        self.autofocus_button = QPushButton("Enable FocusLock")
        self.autofocus_button.clicked.connect(self.toggle_autofocus)
        tracking_layout.addWidget(self.autofocus_button, 2, 0, 1, 2)
        
        # Toggle heatmap button
        self.heatmap_button = QPushButton("Enable Heatmap")
        self.heatmap_button.clicked.connect(self.toggle_heatmap)
        tracking_layout.addWidget(self.heatmap_button, 3, 0, 1, 2)
        
        tracking_group.setLayout(tracking_layout)
        controls_layout.addWidget(tracking_group)
        
        # Control settings group
        control_group = QGroupBox("Motor Control")
        control_layout = QVBoxLayout()
        
        # Toggle manual mode button
        self.manual_button = QPushButton("Enable Manual Mode")
        self.manual_button.clicked.connect(self.toggle_manual_mode)
        control_layout.addWidget(self.manual_button)
        
        # Center position button
        self.center_button = QPushButton("Center")
        self.center_button.clicked.connect(self.move_to_center)
        control_layout.addWidget(self.center_button)
        
        control_group.setLayout(control_layout)
        controls_layout.addWidget(control_group)
        
        # Recording settings group
        recording_group = QGroupBox("Recording Settings")
        recording_layout = QGridLayout()
        
        # Directory path
        recording_layout.addWidget(QLabel("Directory:"), 0, 0)
        self.directory_edit = QLineEdit(self.recording_settings["filepath"])
        recording_layout.addWidget(self.directory_edit, 0, 1)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        recording_layout.addWidget(self.browse_button, 0, 2)
        
        # Filename
        recording_layout.addWidget(QLabel("Filename:"), 1, 0)
        self.filename_edit = QLineEdit(self.recording_settings["filename"])
        recording_layout.addWidget(self.filename_edit, 1, 1, 1, 2)
        
        # File type options
        recording_layout.addWidget(QLabel("Left File Type:"), 2, 0)
        self.left_filetype_group = QButtonGroup()
        left_avi_radio = QRadioButton("AVI")
        left_avi_radio.setChecked(True)
        left_tiff_radio = QRadioButton("TIFF")
        self.left_filetype_group.addButton(left_avi_radio, 1)
        self.left_filetype_group.addButton(left_tiff_radio, 0)
        left_type_layout = QHBoxLayout()
        left_type_layout.addWidget(left_avi_radio)
        left_type_layout.addWidget(left_tiff_radio)
        recording_layout.addLayout(left_type_layout, 2, 1, 1, 2)
        
        recording_layout.addWidget(QLabel("Right File Type:"), 3, 0)
        self.right_filetype_group = QButtonGroup()
        right_avi_radio = QRadioButton("AVI")
        right_avi_radio.setChecked(True)
        right_tiff_radio = QRadioButton("TIFF")
        self.right_filetype_group.addButton(right_avi_radio, 1)
        self.right_filetype_group.addButton(right_tiff_radio, 0)
        right_type_layout = QHBoxLayout()
        right_type_layout.addWidget(right_avi_radio)
        right_type_layout.addWidget(right_tiff_radio)
        recording_layout.addLayout(right_type_layout, 3, 1, 1, 2)
        
        # Recording button
        self.recording_button = QPushButton("Start Recording")
        self.recording_button.clicked.connect(self.toggle_recording)
        recording_layout.addWidget(self.recording_button, 4, 0, 1, 3)
        
        recording_group.setLayout(recording_layout)
        controls_layout.addWidget(recording_group)
        
        main_layout.addLayout(controls_layout, 1)
        
        # Histogram section
        histogram_layout = QHBoxLayout()
        
        # Histogram display
        self.histogram_display = HistogramDisplay()
        histogram_layout.addWidget(self.histogram_display, 3)
        
        # Histogram max value
        self.hist_max_label = QLabel("Max Value: 0")
        self.hist_max_label.setAlignment(Qt.AlignCenter)
        histogram_layout.addWidget(self.hist_max_label, 1)
        
        main_layout.addLayout(histogram_layout, 1)
        
        self.setCentralWidget(main_widget)
        self.setWindowTitle("WormsPy")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        
        # Disable buttons initially
        self.update_ui_state()
        
    def update_ui_state(self):
        """Update UI elements based on current state"""
        # Enable/disable based on live feed state
        feed_active = self.is_live_feed_enabled
        self.left_camera_combo.setEnabled(not feed_active)
        self.right_camera_combo.setEnabled(not feed_active)
        self.node_index_spinbox.setEnabled(not feed_active)
        self.feed_button.setText("Stop Live Feed" if feed_active else "Start Live Feed")
        
        # Controls that require live feed
        self.tracking_button.setEnabled(feed_active)
        self.tracking_button.setText("Disable Tracking" if self.is_tracking_enabled else "Enable Tracking")
        
        self.autofocus_button.setEnabled(feed_active)
        self.autofocus_button.setText("Disable FocusLock" if self.is_autofocus_enabled else "Enable FocusLock")
        
        self.heatmap_button.setEnabled(feed_active)
        self.heatmap_button.setText("Disable Heatmap" if self.heatmap_on else "Enable Heatmap")
        
        self.manual_button.setEnabled(feed_active)
        self.manual_button.setText("Disable Manual Mode" if self.manual_enabled else "Enable Manual Mode")
        
        self.center_button.setEnabled(feed_active)
        
        # Recording controls
        self.recording_button.setEnabled(feed_active)
        self.recording_button.setText("Stop Recording" if self.is_recording else "Start Recording")
        
        self.directory_edit.setEnabled(feed_active and not self.is_recording)
        self.filename_edit.setEnabled(feed_active and not self.is_recording)
        self.browse_button.setEnabled(feed_active and not self.is_recording)
        
        for button in self.left_filetype_group.buttons():
            button.setEnabled(feed_active and not self.is_recording)
        for button in self.right_filetype_group.buttons():
            button.setEnabled(feed_active and not self.is_recording)
    
    def toggle_live_feed(self):
        """Start or stop the camera feeds"""
        if not self.is_live_feed_enabled:
            # Start the feeds
            self.left_camera = str(self.left_camera_combo.currentIndex())
            self.right_camera = str(self.right_camera_combo.currentIndex())
            
            # Send camera settings to backend
            camera_settings_data = {
                "leftCam": int(self.left_camera),
                "rightCam": int(self.right_camera),
                "serialInput": "COM4"  # Default value, could be made configurable
            }
            
            # Start feed in backend
            app.test_client().post('/camera_settings', json=camera_settings_data)
            
            # Start video capture threads
            self.left_feed_url = f"{self.api_url}/video_feed"
            self.right_feed_url = f"{self.api_url}/video_feed_fluorescent"
            self.histogram_url = f"{self.api_url}/get_hist"
            
            # Initialize video update threads for feeds
            self.init_video_threads()
            
            # Start histogram update timer
            self.hist_timer.start(500)  # Update every 500ms
            
            self.is_live_feed_enabled = True
        else:
            # Stop the feeds
            self.stop_video_threads()
            app.test_client().post('/stop_live_stream', json={})
            self.hist_timer.stop()
            self.is_live_feed_enabled = False
        
        self.update_ui_state()
    
    def init_video_threads(self):
        """Initialize and start the video capture threads"""
        # Start left camera thread
        # Note: In a real implementation, you would need to create a proper 
        # capture method that works with the Flask streams
        
        self.left_thread = VideoThread(self.left_feed_url)
        self.left_thread.frame_updated.connect(self.update_left_frame)
        self.left_thread.start()
        
        self.right_thread = VideoThread(self.right_feed_url)
        self.right_thread.frame_updated.connect(self.update_right_frame)
        self.right_thread.start()
        
        self.hist_thread = VideoThread(self.histogram_url)
        self.hist_thread.frame_updated.connect(self.update_histogram)
        self.hist_thread.start()
    
    def stop_video_threads(self):
        """Stop and clean up video threads"""
        if hasattr(self, 'left_thread'):
            self.left_thread.stop()
            self.left_thread.wait()
        
        if hasattr(self, 'right_thread'):
            self.right_thread.stop()
            self.right_thread.wait()
            
        if hasattr(self, 'hist_thread'):
            self.hist_thread.stop()
            self.hist_thread.wait()
    
    @pyqtSlot(np.ndarray)
    def update_left_frame(self, frame):
        """Update the left video feed with a new frame"""
        self.left_video.update_frame(frame)
    
    @pyqtSlot(np.ndarray)
    def update_right_frame(self, frame):
        """Update the right video feed with a new frame"""
        self.right_video.update_frame(frame)
    
    @pyqtSlot(np.ndarray)
    def update_histogram(self, frame):
        """Update the histogram display"""
        self.histogram_display.update_histogram(frame)
    
    def update_histogram_max(self):
        """Update the histogram max value display"""
        try:
            response = app.test_client().get('/stream_max')
            max_value = response.data.decode('utf-8')
            self.hist_max_label.setText(f"Max Value: {max_value}")
        except Exception as e:
            print(f"Error getting histogram max: {e}")
    
    def toggle_tracking(self):
        """Enable or disable worm tracking"""
        self.is_tracking_enabled = not self.is_tracking_enabled
        
        # Get current algorithm selection
        self.track_algorithm = self.tracking_combo.currentIndex()
        
        # Send to backend
        app.test_client().post('/toggle_tracking', json={
            "is_tracking": "True" if self.is_tracking_enabled else "False",
            "tracking_algorithm": self.track_algorithm
        })
        
        self.update_ui_state()
    
    def toggle_heatmap(self):
        """Toggle heatmap visualization for the right camera"""
        self.heatmap_on = not self.heatmap_on
        
        # Send to backend
        app.test_client().post('/toggle_heatmap', json={
            "heatmap_enabled": "True" if self.heatmap_on else "False"
        })
        
        self.update_ui_state()
    
    def toggle_autofocus(self):
        """Toggle autofocus functionality"""
        self.is_autofocus_enabled = not self.is_autofocus_enabled
        
        # Send to backend
        app.test_client().post('/toggle_af', json={
            "af_enabled": "True" if self.is_autofocus_enabled else "False"
        })
        
        self.update_ui_state()
    
    def toggle_manual_mode(self):
        """Toggle manual control mode"""
        self.manual_enabled = not self.manual_enabled
        
        # Send to backend
        app.test_client().post('/toggle_manual', json={
            "toggle_manual": "True" if self.manual_enabled else "False"
        })
        
        self.update_ui_state()
    
    def move_to_center(self):
        """Move the motors to center position"""
        app.test_client().post('/move_to_center', json={})
    
    def send_node_index(self):
        """Send the current node index to the backend"""
        self.node_index_value = self.node_index_spinbox.value()
        
        # Send to backend
        app.test_client().post('/node_index', json={
            "index": self.node_index_value
        })
    
    def browse_directory(self):
        """Open directory browser for recording path"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.directory_edit.text(),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.directory_edit.setText(directory)
    
    def toggle_recording(self):
        """Start or stop recording from both cameras"""
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            # Update recording settings
            self.recording_settings["filepath"] = self.directory_edit.text()
            self.recording_settings["filename"] = self.filename_edit.text()
            self.recording_settings["use_avi_left"] = self.left_filetype_group.checkedId() == 1
            self.recording_settings["use_avi_right"] = self.right_filetype_group.checkedId() == 1
            
            # Start recording
            app.test_client().post('/start_recording', json=self.recording_settings)
        else:
            # Stop recording
            app.test_client().post('/stop_recording', json={})
        
        self.update_ui_state()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop video threads if active
        self.stop_video_threads()
        
        # Stop live feed in backend if active
        if self.is_live_feed_enabled:
            app.test_client().post('/stop_live_stream', json={})
        
        # Stop recording if active
        if self.is_recording:
            app.test_client().post('/stop_recording', json={})
        
        event.accept()


class VideoThread(QThread):
    """Thread class for handling video streams from Flask backend"""
    frame_updated = pyqtSignal(np.ndarray)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
        
        # Get the flask app route based on URL
        if '/video_feed' in url:
            self.flask_func = video_feed
        elif '/video_feed_fluorescent' in url:
            self.flask_func = video_feed_fluorescent
        elif '/get_hist' in url:
            self.flask_func = get_hist
            
    def run(self):
        """Main thread loop to fetch frames"""
        try:
            # Instead of trying to parse the Flask multipart response
            # we'll use OpenCV's VideoCapture for camera access directly
            if hasattr(self, 'flask_func'):
                if self.flask_func.__name__ == 'video_feed':
                    cap = cv2.VideoCapture(0) # Left camera
                elif self.flask_func.__name__ == 'video_feed_fluorescent':
                    cap = cv2.VideoCapture(1) # Right camera
                elif self.flask_func.__name__ == 'get_hist':
                    # For histogram, we'll generate it from the right camera feed
                    cap = cv2.VideoCapture(1)
                
                while self.running:
                    ret, frame = cap.read()
                    if ret:
                        # Process frame based on type
                        if self.flask_func.__name__ == 'video_feed':
                            # Process left camera frame
                            if len(frame.shape) == 2:  # If grayscale
                                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                            self.frame_updated.emit(frame)
                            
                        elif self.flask_func.__name__ == 'video_feed_fluorescent':
                            # Process right camera frame - apply heatmap if enabled
                            if self.flask_func.__globals__['heatmap_enabled']:
                                frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
                            elif len(frame.shape) == 2:  # If grayscale
                                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                            self.frame_updated.emit(frame)
                            
                        elif self.flask_func.__name__ == 'get_hist':
                            # Generate histogram from frame
                            if len(frame.shape) > 2:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            else:
                                gray = frame
                                
                            hist_size = 256
                            hist_w = 512
                            hist_h = 200
                            bin_w = int(round(hist_w / hist_size))
                            hist = cv2.calcHist([gray], [0], None, [hist_size], (0, 256))
                            norm_hist = cv2.normalize(hist, hist, 0, hist_h, cv2.NORM_MINMAX)
                            
                            histImage = np.zeros((hist_h, hist_w, 3), dtype=np.uint8)
                            for i in range(1, hist_size):
                                cv2.line(histImage, (bin_w * (i - 1), hist_h - int(norm_hist[i - 1])),
                                        (bin_w * (i), hist_h - int(norm_hist[i])), (0, 255, 0), thickness=2)
                            
                            self.frame_updated.emit(histImage)
                        
                    time.sleep(0.05)  # ~20 FPS
                
                cap.release()
                
        except Exception as e:
            print(f"Error in video thread: {e}")
    
    def stop(self):
        """Stop the thread"""
        self.running = False


def run_flask():
    """Run the Flask server in a separate thread"""
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start PyQt application
    app_qt = QApplication(sys.argv)
    app_qt.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = WormsPyApp()
    window.show()
    sys.exit(app_qt.exec_())
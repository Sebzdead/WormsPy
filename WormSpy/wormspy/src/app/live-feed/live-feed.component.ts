import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-live-feed',
  templateUrl: './live-feed.component.html',
  styleUrls: ['./live-feed.component.scss'],
})
export class LiveFeedComponent implements OnInit {
  // Flag to indicate if the live feed is currently being displayed
  public isLiveFeedEnabled: boolean = false;

  // Flag to indicate if the live feed is currently being recorded
  public isRecording: boolean = false;

  // Flag to indicate if the live feed is currently being tracked
  public isTrackingEnabled: boolean = false;

  // Flag to indicate if the live feed's autofocus is currently enabled
  public isAutofocusEnabled: boolean = false;

  // URL to reach the API
  public apiUrl: string = 'http://127.0.0.1:5000';

  // the current image from the live feed
  public liveFeedUrlNormal!: string;
  public liveFeedUrlFluorescent!: string;

  private recordingSettings = {
    filepath: 'D:\\WormSpy_video\\Tracking\\',
    filename: 'Tracking_Video.avi',
    resolution: 256,
    fps: 10,
    filepath_fl: 'D:\\WormSpy_video\\Calcium\\',
    filename_fl: 'Tracking_Video_Fluorescent.avi',
    resolution_fl: 256,
    fps_fl: 10,
  };

  // Serial Port
  serialInput = new FormControl('COM4');

  // Camera selection
  leftCamera = '3';
  rightCamera = '4';

  // left recording settings
  leftFilename = new FormControl('Tracking_Video.avi');
  leftFPS = new FormControl(10.0);
  leftResolution = new FormControl(256);

  // right recording settings
  rightFilename = new FormControl('Tracking_Video_Fluorescent.avi');
  rightFPS = new FormControl(10.0);
  rightResolution = new FormControl(1024);

  constructor(private http: HttpClient) {}

  ngOnInit(): void {}

  // Method to toggle the live feed on or off
  public toggleLiveFeed(): void {
    this.isLiveFeedEnabled = !this.isLiveFeedEnabled;

    const postSettings = {
      leftCam: this.selectToCamera(this.leftCamera),
      rightCam: this.selectToCamera(this.rightCamera),
      serialInput: this.serialInput.value,
    };

    if (this.isLiveFeedEnabled) {
      this.serialInput.disable();
      this.http
        .post(this.apiUrl + '/camera_settings', postSettings)
        .subscribe((data) => {
          this.liveFeedUrlNormal = this.apiUrl + '/video_feed';
          this.liveFeedUrlFluorescent = this.apiUrl + '/video_feed_fluorescent';
        });
    } else {
      this.serialInput.enable();
      this.liveFeedUrlNormal = '';
      this.liveFeedUrlFluorescent = '';
    }
  }

  // Method to start or stop recording the live feed
  public toggleRecording(): void {
    this.isRecording = !this.isRecording;
    
    if (this.isRecording) {
      // Disable input fields
      this.leftFPS.disable();
      this.leftResolution.disable();
      this.leftFilename.disable();
      this.rightFPS.disable();
      this.rightResolution.disable();
      this.rightFilename.disable();
      
      // Update Settings 
      this.recordingSettings.filename = this.leftFilename.value;
      this.recordingSettings.fps = this.leftFPS.value;
      this.recordingSettings.resolution = this.leftResolution.value;
      this.recordingSettings.filename_fl = this.rightFilename.value;
      this.recordingSettings.fps_fl = this.rightFPS.value;
      this.recordingSettings.resolution_fl = this.rightResolution.value;
      
      // Send settings to API and initiate video recording
      this.http
        .post(this.apiUrl + '/start_recording', this.recordingSettings)
        .subscribe((data) => {});
      
    } else {
      // Terminate video recording
      this.http
        .post(this.apiUrl + '/stop_recording', {})
        .subscribe((data) => {});
      
      // Renable input fields
      this.leftFPS.enable();
      this.leftResolution.enable();
      this.leftFilename.enable();
      this.rightFPS.enable();
      this.rightResolution.enable();
      this.rightFilename.enable();
    }
  }

  // Method to enable or disable tracking in the live feed
  public toggleTracking(): void {
    this.isTrackingEnabled = !this.isTrackingEnabled;
    if (this.isTrackingEnabled) {
      this.http
        .post(this.apiUrl + '/toggle_tracking', { af_enabled: 'True' })
        .subscribe((data) => {});
    } else {
      this.http
        .post(this.apiUrl + '/toggle_tracking', { af_enabled: 'False' })
        .subscribe((data) => {});
    }
  }

  // Method to enable or disable autofocus in the live feed
  public toggleAutofocus(): void {
    this.isAutofocusEnabled = !this.isAutofocusEnabled;
    // this.http.post(this.liveFeedUrlNormal, {autofocus: this.isAutofocusEnabled})
  }

  selectDirectoryLeft(files: any) {
    this.recordingSettings.filepath = files;
  }
  selectDirectoryRight(files: any) {
    this.recordingSettings.filepath_fl = files;
  }

  selectToCamera(inp: string) {
    if (inp == '4') {
      return 3;
    } else if (inp == '3') {
      return 2;
    } else if (inp == '2') {
      return 1;
    } else {
      return 0;
    }
  }
}

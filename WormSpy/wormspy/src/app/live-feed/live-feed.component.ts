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
    filepath: 'path/to/save/video/to',
    filename: 'filename.avi',
    resolution: '256x256',
    fps: 10,
  };

  // Serial Port
  serialInput = new FormControl('COM4');

  // Camera selection
  leftCamera = '3';
  rightCamera = '4';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {}

  // Method to toggle the live feed on or off
  public toggleLiveFeed(): void {
    // this.http.post(this.liveFeedUrlNormal, {serial_port: this.serialInput})
    this.isLiveFeedEnabled = !this.isLiveFeedEnabled;

    const postSettings = {
      leftCam: this.selectToCamera(this.leftCamera),
      rightCam: this.selectToCamera(this.rightCamera),
      serialInput: this.serialInput.value,
    };
    this.http
      .post(this.apiUrl + '/camera_settings', postSettings)
      .subscribe((data) => {});
    this.liveFeedUrlNormal = this.apiUrl + '/video_feed';
  }

  // Method to start or stop recording the live feed
  public toggleRecording(): void {
    this.isRecording = !this.isRecording;
    if (this.isRecording) {
      this.http
        .post(this.apiUrl + '/start_recording', this.recordingSettings)
        .subscribe((data) => {});
    } else {
      this.http
        .post(this.apiUrl + '/stop_recording', {})
        .subscribe((data) => {});
    }
  }

  // Method to enable or disable tracking in the live feed
  public toggleTracking(): void {
    this.isTrackingEnabled = !this.isTrackingEnabled;
    this.http
      .post(this.apiUrl + '/start_recording', this.recordingSettings)
      .subscribe((data) => {});
  }

  // Method to enable or disable autofocus in the live feed
  public toggleAutofocus(): void {
    this.isAutofocusEnabled = !this.isAutofocusEnabled;
    // this.http.post(this.liveFeedUrlNormal, {autofocus: this.isAutofocusEnabled})
  }

  selectDirectory(files: any) {
    this.recordingSettings.filepath = files;
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

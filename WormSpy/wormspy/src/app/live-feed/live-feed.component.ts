import { Component, OnInit } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { SocketService } from '../socket/socket.service';

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

  public heatmapOn: boolean = false;

  public manualEnabled = false;

  // Flag to indicate if the live feed is currently being tracked
  public isTrackingEnabled: boolean = false;

  // Flag to indicate if the live feed's autofocus is currently enabled
  public isAutofocusEnabled: boolean = false;

  // URL to reach the API
  public apiUrl: string = 'http://127.0.0.1:5000';

  // the current image from the live feed
  public liveFeedUrlLeft!: string;
  public liveFeedUrlRight!: string;

  // the current histogram from the live feed flourescent
  public liveFeedUrlHistogram!: string;

  public hist_max_feed!: string;

  // array range values
  indexMin = 0;
  indexMax = 2;

  // settings to change file paths
  private recordingSettings = {
    filepath: 'D:\\WormSpy_video\\',
    filename: 'Tracking_Video',
    use_avi_left: 0,
    use_avi_right: 0,
    // resolution: 256,
    // fps: 10.0,
    // filepath_fl: 'D:\\WormSpy_video\\Calcium',
    // filename_fl: 'Tracking_Video_Fluorescent',
    // resolution_fl: 1024,
    // fps_fl: 10.0,
  };

  // Serial Port
  serialInput = new FormControl('COM4');
  nodeIndex = new FormControl('0', [
    Validators.min(this.indexMin),
    Validators.max(this.indexMax),
  ]);

  // Camera selection
  leftCamera = '1';
  rightCamera = '2';

  // // left recording settings
  // leftFilename = new FormControl('Tracking_Video');
  // leftFPS = new FormControl(10.0);
  // leftResolution = new FormControl(1024);

  // right recording settings
  folder = new FormControl('D:\\WormSpy_Video\\');
  filename = new FormControl('Project_1');
  // rightFPS = new FormControl(10.0);
  // rightResolution = new FormControl(1024);

  // flouresctent camera settings
  // flourFPS = new FormControl(10.0);
  // flourExposure = new FormControl(10000);
  // flourGain = new FormControl(0);

  //tracking settings
  trackingAlgorithm = 0;

  //avi settings
  useAviLeft = 1;
  useAviRight = 1;

  //hist
  hist_max = '0';

  constructor(private http: HttpClient, private sockService: SocketService) {}

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
        .subscribe(() => {
          this.liveFeedUrlLeft = this.apiUrl + '/video_feed';
          this.liveFeedUrlRight = this.apiUrl + '/video_feed_fluorescent';
          this.liveFeedUrlHistogram = this.apiUrl + '/get_hist';
          this.hist_max_feed = this.apiUrl + '/stream_max';
          this.callHistMax();
        });
      // this.sockService.get_hist().subscribe((data: string) => {
      //   this.liveFeedUrlHistogram = data;
      // });
    } else {
      this.serialInput.enable();
      this.liveFeedUrlLeft = '';
      this.liveFeedUrlRight = '';
      this.liveFeedUrlHistogram = '';
      this.http.post(this.apiUrl + '/stop_live_stream', {}).subscribe(() => {});
    }

    // this.liveFeedUrlNormal = "https://cdn.wallpapersafari.com/84/92/C9qAjh.jpg";
    // this.liveFeedUrlFluorescent = "https://cdn.wallpapersafari.com/84/92/C9qAjh.jpg";
  }
  public callHistMax() {
    this.http
      .get(this.hist_max_feed, { responseType: 'text' })
      .subscribe((data: string) => {
        this.hist_max = data;
      });
  }
  // Method to start or stop recording the live feed
  public toggleRecording(): void {
    this.isRecording = !this.isRecording;

    if (this.isRecording) {
      // Disable input fields
      // this.leftFPS.disable();
      // this.leftResolution.disable();
      // this.leftFilename.disable();
      // this.rightFPS.disable();
      // this.rightResolution.disable();
      this.filename.disable();

      // Update Settings
      // this.recordingSettings.filename = this.leftFilename.value;
      // this.recordingSettings.fps = this.leftFPS.value;
      // this.recordingSettings.resolution = this.leftResolution.value;
      this.recordingSettings.filepath = this.folder.value;
      this.recordingSettings.filename = this.filename.value;
      this.recordingSettings.use_avi_left = this.useAviLeft;
      this.recordingSettings.use_avi_right = this.useAviRight;
      // this.recordingSettings.fps_fl = this.rightFPS.value;
      // this.recordingSettings.resolution_fl = this.rightResolution.value;

      // Send settings to API and initiate video recording
      this.http
        .post(this.apiUrl + '/start_recording', this.recordingSettings)
        .subscribe(() => {});
    } else {
      // Terminate video recording
      this.http.post(this.apiUrl + '/stop_recording', {}).subscribe(() => {});

      // Renable input fields
      // this.leftFPS.enable();
      // this.leftResolution.enable();
      // this.leftFilename.enable();
      // this.rightFPS.enable();
      // this.rightResolution.enable();
      this.filename.enable();
    }
  }

  // public updateFlourSettings(): void {
  // const postSettings = {
  //   exposure: this.flourExposure.value,
  //   gain: this.flourGain.value,
  //   fps: this.flourFPS.value,
  // };
  // this.http
  //   .post(this.apiUrl + '/flour_settings', postSettings)
  //   .subscribe((data) => {});
  // }
  public toggleHeatmap(): void {
    this.heatmapOn = !this.heatmapOn;
    if (this.heatmapOn) {
      this.http
        .post(this.apiUrl + '/toggle_heatmap', { heatmap_enabled: 'True' })
        .subscribe(() => {});
    } else {
      this.http
        .post(this.apiUrl + '/toggle_heatmap', { heatmap_enabled: 'False' })
        .subscribe(() => {});
    }
  }
  // Method to enable or disable tracking in the live feed
  public toggleTracking(): void {
    this.isTrackingEnabled = !this.isTrackingEnabled;
    if (this.isTrackingEnabled) {
      this.http
        .post(this.apiUrl + '/toggle_tracking', {
          is_tracking: 'True',
          tracking_algorithm: this.trackingAlgorithm,
        })
        .subscribe(() => {});
    } else {
      this.http
        .post(this.apiUrl + '/toggle_tracking', {
          is_tracking: 'False',
          tracking_algorithm: this.trackingAlgorithm,
        })
        .subscribe(() => {});
    }
  }

  // Method to enable or disable tracking in the live feed
  public sendNodeIndex(): void {
    if (!(this.nodeIndex.value === '')) {
      if (this.nodeIndex.value != null) {
        let index = parseInt(this.nodeIndex.value);
        if (parseInt(this.nodeIndex.value) == 0) {
          index = 0;
        }
        if (index > this.indexMax) {
          index = this.indexMax;
        } else if (index < this.indexMin) {
          index = this.indexMin;
        }
        this.http
          .post(this.apiUrl + '/node_index', { index: index })
          .subscribe(() => {});
      }
    }
  }

  // Method to enable or disable autofocus in the live feed
  public toggleAutofocus(): void {
    if (!this.isAutofocusEnabled) {
      this.http
        .post(this.apiUrl + '/toggle_af', { af_enabled: 'True' })
        .subscribe(() => {});
    } else {
      this.http
        .post(this.apiUrl + '/toggle_af', { af_enabled: 'False' })
        .subscribe(() => {});
    }
    this.isAutofocusEnabled = !this.isAutofocusEnabled;
  }

  public toggleManualMode(): void {
    this.manualEnabled = !this.manualEnabled;
    if (this.manualEnabled) {
      this.http
        .post(this.apiUrl + '/toggle_manual', { toggle_manual: 'True' })
        .subscribe(() => {});
    } else {
      this.http
        .post(this.apiUrl + '/toggle_manual', { toggle_manual: 'False' })
        .subscribe(() => {});
    }
  }

  public moveToCenter(): void {
    this.http.post(this.apiUrl + '/move_to_center', {}).subscribe(() => {});
  }

  // selectDirectoryLeft(files: any) {
  //   this.recordingSettings.filepath = files;
  // }
  // selectDirectoryRight(files: any) {
  //   this.recordingSettings.filepath_fl = files;
  // }

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

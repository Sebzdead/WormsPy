import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-live-feed',
  templateUrl: './live-feed.component.html',
  styleUrls: ['./live-feed.component.scss']
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

  // The current magnification level of the live feed
  public magnification: number = 1;

  // the current image from the live feed
  public liveFeedUrl!: string;

  serialInput = new FormControl();

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    this.serialInput.setValue('COM4')
    this.liveFeedUrl = 'http://192.168.169.108:5000/video_feed'
  }

  // Method to toggle the live feed on or off
  public toggleLiveFeed(): void {
    this.http.post(this.liveFeedUrl, {serial_port: this.serialInput})
    this.isLiveFeedEnabled = !this.isLiveFeedEnabled;
  }

  // Method to start or stop recording the live feed
  public toggleRecording(): void {
    this.isRecording = !this.isRecording;
    this.http.post(this.liveFeedUrl, {recording: this.isRecording})
  }

  // Method to enable or disable tracking in the live feed
  public toggleTracking(): void {
    this.isTrackingEnabled = !this.isTrackingEnabled;
    this.http.post(this.liveFeedUrl, {tracking: this.isTrackingEnabled})
  }

  // Method to enable or disable autofocus in the live feed
  public toggleAutofocus(): void {
    this.isAutofocusEnabled = !this.isAutofocusEnabled;
    this.http.post(this.liveFeedUrl, {autofocus: this.isAutofocusEnabled})
  }

  // Method to increase the magnification of the live feed
  public increaseMagnification(): void {
    this.magnification++;
  }

  // Method to decrease the magnification of the live feed
  public decreaseMagnification(): void {
    this.magnification--;
  }

}

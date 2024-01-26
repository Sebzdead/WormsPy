import { Injectable } from '@angular/core';
// import * as io from 'socket.io-client';
import { Observable } from 'rxjs';
import { io } from 'socket.io-client'; // Import the 'io' function from 'socket.io-client'

@Injectable({
  providedIn: 'root'
})
export class SocketService {

  // private socket;

  constructor() {
    // this.socket = io('http://localhost:5000');
  }

  // public get_hist(): Observable<string> {
  //   // receive image data from server and return it as an observable
  //   return new Observable((observer) => {
  //     this.socket.on('get_hist', (data) => {
  //       let arrayBufferView = new Uint8Array(data['image_data']);
  //       let blob = new Blob([arrayBufferView], { type: "image/jpeg" });
  //       let urlCreator = window.URL || window.webkitURL;
  //       let imageUrl = urlCreator.createObjectURL(blob);
  //       observer.next(imageUrl);
  //     });
  //   });
  // }
}
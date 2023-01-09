import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private http: HttpClient) { }

  getLiveFeed(): Observable<Blob> {
    const image = this.http.get('http://192.168.169.108:5000/livefeed.png', { responseType: 'blob' });
    return image;
  }
}

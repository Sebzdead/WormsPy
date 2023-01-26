# WormSpy

WormSpy is a software for controlling an open source tracking fluorescence microscope. It is designed to utilize two cameras, shifted to different wavelengths to allow simultaneous tracking and behavioural measurements with high magnification calcium imaging. Due to the flexible nature of the setup, other applications are possible.

<br/>
<br/>

![](Demo.gif)

## Getting started with WormSpy
### Minimum requirements
Minimum requirements to use WormSpy:
- 2x Spinnaker compatible cameras
- XY Zaber motor stage 
- Z Zaber motor stage that can be conrolled with binary commands
- A CUDA capable NVidia GPU (Preferrably with TensorCores)

Spinnaker cameras can be replaced with any OpenCV compatible cameras, although EasyPySpin will have to be replaced with OpenCV.

### Getting started with WormSpy
1. Miniconda / Anaconda 
2. `conda create --name wormspy --file requirements.txt`
3. Ensure only the required two cameras are connected to the computer.
3. Run StartWormSpy.bat
4. Identify the serial port for the XY motors and the serial port for the Z motor. 
If all three motors are connected via the same serial port, you will have to modify the `video_feed()` function in `app.py`. 

## Developers Notes
More information for those interested in adapting WormSpy for their use case.

### Frontend 
The frontend of WormSpy was developed using Angular (HTML/SCSS/TS). To make adjustments the frontend, the installation of NodeJs is required. Run `npm install` in the `wormspy` folder after initially downloading the files. Adjustments to the frontend can be made in the live-feed component found in `wormspy/src/app/live-feed`. 

To continue using flask as a web server and maintain `StartWormSpy.bat` as an easy launch option, follow these steps:
1. Use `ng build` to create new production files in the `wormspy/dist` folder. 
2. Place the `index.html` file into the `production/template` folder. 
3. Place all other files found in the dist folder into the `production/static` folder. 
4. In the `index.html` file, edit all import statements following this template: `<src>/<href>="{{url_for('static', filename='<filename>.js')}}"`

### Backend
WormSpy uses a Python Flask webserver to communicate with the frontend. A combination of the OpenCV and EasyPySpin libraries are used to communicate with the cameras. The Zaber Motion **Binary** library is used to control the Zaber motors. The Deep Lab Cut Live library is used to identify _C. elegans_ in the live feed. 

The `video_feed()` function 

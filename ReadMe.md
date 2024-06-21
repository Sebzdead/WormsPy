# WormsPy

WormsPy is a software for controlling an open source tracking fluorescence microscope. It is designed to utilize two cameras, shifted to different wavelengths to allow simultaneous tracking and behavioural measurements with epifluorescence imaging. The dual recording approach using the same light path allows the user to align the images in post and make inferences about how neural activity affects behaviour and how the animal's interactions with its environment affect neural activity. While WormsPy was developed for calcium imaging in head sensory and interneurons in C. elegans, its modular design and low cost allows it to be iterated on by other researchers and find applications in new fields

Example of a worm expressing pansensory GCaMP being tracked using WormsPy
![](media/WormsPy3.gif)

Example with Brightfield and Fluorescent videos side by side: (worm is expressing GCaMP3 via the myo-3 promoter, for expression in body-wall musculature.)
![](media/Demo2.gif)

Example with various drosophila larvae expressing jGCaMP8f in muscle tissue courtesy of the Ohyama lab at MGill.
![](media/drosophila.gif)

## Getting started with WormsPy
WormSpy allows you to track the movements of a single animal whilst ensuring it always stays in focus. It also allows you to simultaneously record both video feeds. The left video feed is recorded as a compressed .avi file whilst the right video feed is recorded as a series of uncompressed 16-bit .tiff files to enable further feature extraction.

### Minimum requirements
Minimum requirements to use WormSpy:
- 2x Spinnaker compatible cameras
- XY Zaber motor stage (Controlled with Binary Commands) 
- Z Zaber motor stage (Controlled with Binary Commands)
- A CUDA capable NVidia GPU (Preferrably with Tensor Cores)

Spinnaker cameras can be replaced with any OpenCV compatible cameras, although EasyPySpin will have to be replaced with OpenCV.
See Build Guide for more information

### Getting started with WormsPy
1. Miniconda / Anaconda 
2. `conda create --name wormspy --file requirements.txt`
3. Ensure only the required two cameras are connected to the computer.
4. Identify the serial port for the XY motors and the serial port for the Z motor. 
If all three motors are connected via the same serial port, you will have to modify the `video_feed()` function in `app.py` such that only one serial port is open. 
5. Open the ZaberLauncher application, which acts as an intermediary messenger to the motors.
6. Run StartWormSpy.bat
7. In your browser visit `localhost:5000`

## Developer's Notes
More information for those interested in adapting WormSpy for their use case.

### Frontend 
The frontend of WormsPy was developed using Angular (HTML/SCSS/TS). To make adjustments the frontend, the installation of NodeJs is required. Run `npm install` in the `wormspy` folder after initially downloading the files. Adjustments to the frontend can be made in the live-feed component found in `wormspy/src/app/live-feed`. 

To continue using flask as a web server and maintain `StartWormSpy.bat` as an easy launch option, follow these steps:
1. Use `ng build --configuration production --deploy-url static/` to create new production files in the `wormspy/dist` folder. 
2. Place the `index.html` file into the `production/template` folder. 
3. Place all other files found in the dist folder into the `production/static` folder. Ignore assets unless those have been updated.
<!-- 4. In the `index.html` file, edit all import statements following this template: `<src>/<href>="{{url_for('static', filename='<filename>.js')}}"` -->

### Backend
WormSpy uses a Python Flask web server (`app.py`) to communicate with the frontend. A combination of the OpenCV and EasyPySpin libraries are used to communicate with the cameras. The Zaber Motion **Binary** library is used to control the Zaber motors. The DeepLabCut (DLC) Live library is used to identify _C. elegans_ in the live feed. 

If you would like to train and use your own DLC model, place your model in the `DLC_models` folder and replace the `skeleton` folder in the `DLCLive` function of the `video_feed` method.

For more detailed programmatical information about WormSpy, refer to the inline comments found in `app.py`.  

## License
WormSpy was developed by Sebastian Wittekindt and Lennard Wittekindt at McGill University. Funded by the Canadian Institute for Health Research.

Provided as open source software under the MIT license, view the [license](LICENSE.TXT) for details.

## WormsPy Dual Camera Build Guide
For a full build guide please see our publication: (FORTHCOMING)

## Features
WormsPy was designed for calcium imaging in head sensory and interneurons in C. elegans. However, many applications are possible by changing the filter sets and objectives and with some slight tweaks to the software.
The basic design of WormsPy includes:
1. Dual video feeds
2. Manual mode: Use a joystick to manually track animals. This also immensly helps with acquisition to begin tracking and recording and to manually find and maintain the focus.
3. Three tracking modes, brightfield thresholding, epifluorescent marker tracking and DeepLabCut markerless pose estimation using a pretrained CNN.
4. FocusLock, which counteracts focal drift once the desired focus has been found.
5. Set your desired directory and project name. When recording, the software will write the left camera as a compressed .avi file using fourcc ‘MJPG’ and the right camera as an uncompressed 16bit .tif folder, as well as a .csv of motor commands to a new folder with the desired project name and directory.

See the demonstration video here: https://youtu.be/mhyYDpziSE8

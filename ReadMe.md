# WormsPy

WormsPy is a software for controlling an open source tracking fluorescence microscope. It is designed to utilize two cameras, shifted to different wavelengths to allow simultaneous tracking and behavioural measurements with epifluorescence imaging. The dual recording approach using the same light path allows the user to align the images in post and make inferences about how neural activity affects behaviour and how the animal's interactions with its environment affect neural activity. While WormsPy was developed for calcium imaging in head sensory and interneurons in C. elegans, its modular design and low cost allows it to be iterated on by other researchers and find applications in new fields.

Example of a worm expressing pansensory GCaMP being tracked using WormsPy
![](media/WormsPy3.gif)

Example with Brightfield and Fluorescent videos side by side: (worm is expressing GCaMP3 via the myo-3 promoter, for expression in body-wall musculature.)
![](media/Demo2.gif)

Frame-synced recordings and stage position allow for sophisticated offline analysis
![](VideoFigure.gif)

Example with various drosophila larvae expressing jGCaMP8f in muscle tissue courtesy of the Ohyama lab at McGill.
![](media/drosophila.gif)

## Features:
WormsPy was designed for calcium imaging in head sensory and interneurons in C. elegans. However, many applications are possible by changing the filter sets and objectives and with some slight tweaks to the software.
The basic design of WormsPy includes:
1. Dual video feeds, brightfield and calcium imaging, but other setups are also possible
2. Manual mode: Use a joystick to manually track animals. This is immensly helpful with acquisition to begin tracking and recording and to manually find and maintain the focus.
3. Three tracking modes: brightfield thresholding, epifluorescent marker tracking and DeepLabCut markerless pose estimation using a pretrained CNN.
5. Frame-synced recording: Set your desired directory and project name. When recording, the software will write the left camera as a compressed .avi file using fourcc ‘MJPG’ and the right camera as an uncompressed 16bit .tif folder to capture the maximum dynamic range of cell activity
6. Worm Traces: Recordings also output a timestamped .csv that tracks motor position, allowing the animals path to be traced and compared with the corresponding video frames.
7. Closed loop optogenetic stimulation: (forthcoming)

See the demonstration video here: https://youtu.be/mhyYDpziSE8

## Building the WormsPy imaging platform:
For a full build guide please see our publication: (FORTHCOMING)

### Minimum requirements:
Minimum requirements to use WormSpy:
- 2x Spinnaker compatible cameras or any cameras compatible with opencv-python
- XY Zaber motor stage (Controlled with ASCII Commands) 
- Z Zaber motor stage (Controlled with ASCII Commands)
- if using DLC, a CUDA capable NVidia GPU (Preferrably with Tensor Cores)
- any modern CPU, though Intel architectures have better performance
- any dual stick controller compatible with PyGame

### Getting started with WormsPy:
1. Clone the repository, we recommend downloading the zip and extracting to desired location.
2. We recommend using MiniConda for environment management: https://docs.anaconda.com/miniconda/miniconda-install/
3. Add anaconda to System Path Variables
4. Open Anaconda prompt and run `conda init`
5. Open Anaconda prompt, cd to the WormsPy directory
6. Run `conda create --name wormspy python=3.8.15`
7. Run `conda activate wormspy`
8. Run `pip install -r requirements.txt`
9. Install the Zaber Launcher application: https://www.zaber.com/software#pos-download
10. Set up your motor connections using ZaberLauncher, note down COM port # for your motors and maximum position index
11. Open the file `WormsPy/backend/code/app.py` and adjust COM ports as well as other settings as needed
12. Adjust your camera settings as desired using the camera's native software (SpinView for Teledyne cameras)
13. Double click StartWormsPy.bat
14. In your browser visit `localhost:5000`
15. Enjoy WormsPy!

## Developer's Notes:
More information for those interested in adapting WormSpy for their use case.

### Frontend:
The frontend of WormsPy was developed using Angular (HTML/SCSS/TS). To make adjustments the frontend, the installation of NodeJs is required. Run `npm install` in the `wormspy` folder after initially downloading the files. Adjustments to the frontend can be made in the live-feed component found in `wormspy/src/app/live-feed`. 

To continue using flask as a web server and maintain `StartWormSpy.bat` as an easy launch option, follow these steps:
1. Use `ng build --configuration production --deploy-url static/` to create new production files in the `wormspy/dist` folder. 
2. Place the `index.html` file into the `production/template` folder. 
3. Place all other files found in the dist folder into the `production/static` folder. Ignore assets unless those have been updated.
<!-- 4. In the `index.html` file, edit all import statements following this template: `<src>/<href>="{{url_for('static', filename='<filename>.js')}}"` -->

### Backend:
WormSpy uses a Python Flask web server (`app.py`) to communicate with the frontend. A combination of the OpenCV and EasyPySpin libraries are used to communicate with the cameras. The Zaber Motion **ASCII** library is used to control the Zaber motors via the Zaber_messenger_router(), which is why the Zaberlauncher application must be open for WormsPy to work. There is an optional DeepLabCut (DLC) Live tracking option available. To activate, uncomment the code that loads in the pretrained model in lines #87-92. 

If you would like to train and use your own DLC model, place your model in the `DLC_models` folder and replace the `skeleton` folder in the `DLCLive` function of the `video_feed` method.

For more detailed programmatical information about WormSpy, refer to the inline comments found in `app.py`.  

## License:
WormSpy was developed by Sebastian Wittekindt and Lennard Wittekindt at McGill University. Funded by the Canadian Institute for Health Research.

Provided as open source software under the MIT license, view the [license](LICENSE.TXT) for details.
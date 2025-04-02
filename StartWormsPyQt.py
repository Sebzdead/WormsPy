#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    """
    Main entry point for WormsPy PyQt application
    Checks for required dependencies and launches the application
    """
    try:
        # Try importing required packages
        import PyQt5
        import numpy
        import cv2
        import qdarkstyle
        import EasyPySpin
        
        # Determine the path to the backend code
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, "WormSpy", "backend", "code", "wormspy_pyqt.py")
        
        # Launch the PyQt application
        print("Starting WormsPy PyQt application...")
        subprocess.run([sys.executable, app_path])
        
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("Please install all required packages by running:")
        print("pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
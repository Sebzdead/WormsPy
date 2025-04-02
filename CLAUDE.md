# WormsPy Development Guidelines

## Build/Run/Test Commands
- Install dependencies: `pip install -r requirements.txt`
- Launch application: Double-click `StartWormsPy.bat` or run Python backend directly with `python WormSpy/backend/code/app.py`
- Run tests: `python -m unittest WormSpy/backend/code/test_segmentation.py`
- Build frontend: `cd wormspy && npm install && ng build --configuration production --deploy-url static/`

## Code Style Guidelines
- **Python:** Follow PEP 8 style guide with 4-space indentation
- **Imports:** Group standard library, third-party, and local imports with one blank line between groups
- **Naming:** snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Types:** Type annotations encouraged for function parameters and return values
- **Error handling:** Use try/except blocks with specific exception types
- **Comments:** Docstrings for functions/classes, inline comments for complex logic
- **Frontend:** Follow Angular style guide for TypeScript, SCSS, and HTML
- **Testing:** Write tests for new features and bug fixes

## Project Structure
- Backend: Flask-based Python with OpenCV and EasyPySpin for camera control
- Frontend: Angular (TS/HTML/SCSS) for UI components
- Hardware control: Zaber Motion for motor control, DeepLabCut for tracking
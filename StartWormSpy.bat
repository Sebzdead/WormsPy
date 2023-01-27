@ECHO OFF
ECHO Please ensure that all serial ports are closed and that only the required two cameras are connected. 
ECHO Press any key to continue
pause > nul
CALL activate wormspy
ECHO WormSpy will be reachable at http://localhost:5000
CALL python app.py
CALL deactivate

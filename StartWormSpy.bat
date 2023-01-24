@ECHO OFF
ECHO 'Please ensure that all serial ports are closed and that only the required two cameras are connected.' 
ECHO 'Press any key to continue'
pause > nul
CALL conda activate wormspy
ECHO 'WormSpy will be reachable at http://localhost:5000'
CALL python -m flask run --host=127.0.0.1
CALL conda deactivate
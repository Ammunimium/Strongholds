@echo on
echo dependency installer
echo installing dependencies
python -m pip install discord-rpc raylib==5.5.0.0 websocket-client opencv-python
echo finished
timeout /t 2 /nobreak >nul
echo closing
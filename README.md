# Autoclicker
This autoclicker was originally created for Battlefield 6, where it helps with fast and repeated interactions such as quickly entering vehicles before other players. AutoClicker is a lightweight desktop utility for automating mouse clicks with a simple and compact interface. It supports customizable hotkeys, click delay settings, always-on-top behavior, and saving your preferences between launches.

# Interface Overview
The application window includes the following controls and status indicators:
- Start/Stop hotkey: sets the key used to start or stop clicking.
- Exit hotkey: sets the key used to immediately close the application.
- Min. delay (sec): defines the minimum interval between clicks.
- Max. delay (sec): defines the maximum interval between clicks.
- Always on top: keeps the window above other windows.
- Save settings: stores the current configuration for the next launch.
- Status: shows whether the auto clicker is running or stopped.
- Clicks: displays the total number of performed clicks.
- Time elapsed: shows how long the clicking session has been running.

# Build with PyInstaller
You can build a standalone Windows executable with PyInstaller using the following command:
```
pyinstaller --onefile --noconsole --clean --strip --windowed --hidden-import=customtkinter --hidden-import=pynput --hidden-import=darkdetect --upx-dir=PATH_TO_UPX --name=AutoClicker autoclicker.py
```
Command parameters
`--onefile`: packs everything into a single executable file.

`--noconsole`: hides the console window when the app starts.

`--clean`: removes temporary build files before building.

`--strip`: removes unnecessary symbols to reduce the final binary size.

`--windowed`: builds a GUI application without a console window.

`--hidden-import=customtkinter`: includes customtkinter, which PyInstaller may not detect automatically.

`--hidden-import=pynput`: includes pynput for keyboard/mouse input handling.

`--hidden-import=darkdetect`: includes darkdetect, used for theme detection.

`--upx-dir=PATH_TO_UPX`: tells PyInstaller where to find UPX for additional executable compression. This parameter is optional and can be removed if UPX is not installed or not needed.

`--name=AutoClicker`: sets the output executable name.

`autoclicker.py`: the main application script.

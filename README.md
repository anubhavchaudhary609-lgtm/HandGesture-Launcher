# ✋ HandGesture Launcher

### Control Your Windows PC Using Hand Gestures

A Python-based desktop application that uses real-time computer vision and hand gesture recognition to launch and control Windows applications through simple finger movements.

Instead of manually opening applications, simply show a gesture to your webcam and let HandGesture Launcher do the work.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![Testing](https://img.shields.io/badge/Testing-Pytest-brightgreen)

---

## 📸 Application Screenshots

### Dashboard Overview
![Dashboard](assets/screenshots/dashboard-overview.png)

### Real-Time Hand Gesture Detection
![Gesture Detection](assets/screenshots/gesture-detection.png)

### Application Settings
![Settings](assets/screenshots/settings.png)

---

## 1. Project Overview

HandGesture Launcher is a desktop automation application that allows users to launch Windows applications using hand gestures detected through a webcam.

The application uses MediaPipe for hand landmark detection and OpenCV for camera processing. It counts extended fingers and maps recognized gestures to user-selected applications.

The system includes gesture stabilization, cooldown management, customizable application mappings, and a graphical user interface.

**The application is not hard-coded to specific programs.** Chrome, Spotify, VS Code, and other applications are only example mappings that users can modify.

## 2. Key Features

- Real-time hand detection using a webcam.
- Finger counting from 0 to 5.
- Gesture-based application launching.
- Configurable gesture-to-application mappings.
- Gesture stability detection to prevent accidental launches.
- Cooldown mechanism to avoid repeated application launches.
- Custom desktop interface using CustomTkinter.
- JSON-based configuration persistence.
- Adjustable gesture sensitivity settings.
- Windows startup integration.
- Automated testing using Pytest.
- Fist Gesture Control: Close the previously launched application using a closed-fist gesture (0 fingers).
- Application Management: Launch and close applications through intuitive hand gestures.

## How to Use

1. Run the application using `python main.py`.
2. Open the Dashboard and start the camera.
3. Show your hand in front of the webcam.
4. Hold a finger gesture steady until it is detected.
5. The application assigned to that gesture will launch.
6. Use the Settings panel to change gesture-to-application mappings.
7. Turn off the camera when you finish.

**Note:** If the fist gesture is implemented to close the previously launched application, add that instruction here. Otherwise, don't claim it as an existing feature.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| OpenCV | Webcam access and image processing |
| MediaPipe | Hand landmark detection |
| CustomTkinter | Desktop graphical interface |
| JSON | Configuration storage |
| Pytest | Automated testing |
| PyInstaller | Windows executable generation |

## 4. Requirements

- Windows 10 or Windows 11.
- Python version compatible with the installed MediaPipe dependency.
- Working webcam.
- Git (for cloning the repository).

**Note:** Python 3.10 and 3.11 are recommended in the original project documentation. Verify compatibility with your installed dependency versions before selecting a Python version.

## 5. Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/anubhavchaudhary609-lgtm/HandGesture-Launcher.git
```

### Step 2: Navigate to the project directory

```bash
cd HandGesture-Launcher
```

### Step 3: Create a virtual environment

```bash
python -m venv .venv
```

### Step 4: Activate the environment

For Windows:

```bash
.venv\Scripts\activate
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

## 6. Running the Application

Start the application using:

```bash
python main.py
```

The main window opens with the Dashboard interface.

### How to use

1. Launch HandGesture Launcher.
2. Click **Start Detection**.
3. Allow webcam access.
4. Show your hand in front of the camera.
5. Raise the desired number of fingers.
6. Hold the gesture until it becomes stable.
7. The assigned application launches automatically.

The application supports finger-count gestures from 0 to 5.

## 7. Gesture Mapping

Users can assign different applications to different finger-count gestures.

Open:

**Settings → Gesture Mappings**

Example configuration:

| Gesture | Assigned Application |
|---|---|
| 1 Finger | Google Chrome |
| 2 Fingers | Visual Studio Code |
| 3 Fingers | Spotify |
| 4 Fingers | WhatsApp |
| 5 Fingers | Calculator |

These are example mappings and can be customized.

### Available operations

- Add a new application.
- Edit an existing mapping.
- Remove an application.
- Browse for executable files.
- Reset mappings to defaults.

Supported application paths include `.exe`, `.lnk`, `.bat`, and `.cmd` files.

Configuration is stored locally:

**Windows:**
```text
%APPDATA%\HandGestureLauncher\config.json
```

**Linux/macOS:**
```text
~/.handgesture_launcher/config.json
```

## 8. Gesture Sensitivity Settings

Users can customize gesture recognition behaviour through the Settings interface.

| Setting | Description |
|---|---|
| Stability (Frames) | Number of consecutive frames required to confirm a gesture. |
| Cooldown (Seconds) | Minimum interval between application launches. |
| Detection Confidence | Minimum confidence threshold for hand detection. |
| Require Neutral Gesture | Requires a zero-finger gesture between repeated launches. |
| Mirror Webcam Preview | Mirrors the webcam preview. |
| Draw Hand Landmarks | Displays detected hand landmarks on the webcam preview. |

These settings provide greater control over gesture recognition and help reduce accidental launches.

## 9. Start with Windows

The application provides a Windows startup option.

Navigate to:

**Settings → Startup**

Enable:

**Start HandGesture Launcher with Windows**

The application registers a per-user startup entry in the Windows Registry.

Registry location:

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

Disabling the option removes the startup entry.

No administrator privileges are required for this per-user registration.

## 10. Project Architecture

The project follows a modular architecture in which different components handle camera operations, gesture recognition, application launching, configuration management, and the graphical interface.

| Module | Responsibility |
|---|---|
| camera.py | Webcam access and device discovery |
| gesture_detector.py | MediaPipe hand detection and finger counting |
| gesture_manager.py | Gesture stability and cooldown management |
| app_launcher.py | Application launching |
| config_manager.py | JSON configuration management |
| startup_manager.py | Windows startup integration |
| gui/app.py | Main application window |
| gui/dashboard.py | Dashboard and webcam preview |
| gui/settings.py | Application settings and mappings |
| gui/application_dialog.py | Add/Edit application dialog |

## 11. Project Structure

```text
HandGestureLauncher/
│
├── main.py
├── build.py
├── requirements.txt
├── pytest.ini
├── README.md
│
├── assets/
│   └── screenshots/
│       ├── dashboard-overview.png
│       ├── gesture-detection.png
│       └── settings.png
│
├── config/
│
├── src/
│   ├── camera.py
│   ├── gesture_detector.py
│   ├── gesture_manager.py
│   ├── app_launcher.py
│   ├── config_manager.py
│   ├── startup_manager.py
│   │
│   └── gui/
│       ├── app.py
│       ├── dashboard.py
│       ├── settings.py
│       └── application_dialog.py
│
└── tests/
    ├── test_app_launcher.py
    ├── test_config_manager.py
    ├── test_gesture_detector.py
    └── test_gesture_manager.py
```

## 12. Running Tests

The project includes automated tests for its core functionality.

Tests cover:

- Application launching.
- Configuration management.
- Gesture detection.
- Gesture management.

Run the test suite using:

```bash
python -m pytest -q
```

The tests for core logic do not require an active webcam.

## 13. Building a Windows Executable

The project includes a build script for generating a standalone Windows executable using PyInstaller.

Run:

```bash
pip install -r requirements.txt
python build.py
```

The generated executable is expected at:

```text
dist/HandGestureLauncher.exe
```

The executable can be distributed to Windows users without requiring them to install Python separately, subject to successful packaging and testing.

## 14. Troubleshooting

| Problem | Possible Solution |
|---|---|
| Webcam cannot be opened | Close other applications using the camera and check Windows camera permissions. |
| Slow detection | Adjust detection confidence and camera resolution. |
| Incorrect finger count | Improve lighting and keep your palm clearly visible. |
| Repeated application launches | Increase stability frames or cooldown duration. |
| Application not found | Update the application path through Settings. |
| Multiple hands detected | Show only one hand clearly to the webcam. |

## 15. Privacy and Security

- Webcam frames are processed locally on the user's machine.
- No webcam footage is intentionally uploaded to an external server.
- Application mappings are stored locally.
- Users explicitly select the applications they want to launch.
- Configuration is maintained within the user's profile.

## 16. Future Improvements

Potential future enhancements include:

- Support for additional hand gestures.
- Custom gesture creation.
- Improved gesture recognition accuracy.
- More desktop automation controls.
- Enhanced application customization.
- Additional accessibility features.

---

## Developer

**Anubhav Chaudhary**

B.Tech Computer Science Student

Developed as an independent Python desktop application project.

---

⭐ If you find this project interesting, consider starring the repository!

**GitHub Repository:**  
https://github.com/anubhavchaudhary609-lgtm/HandGesture-Launcher
# 🎵 ProjectM Python SDL2 Frontend

This is a Python implementation of projectM's [frontend-sdl-cpp](https://github.com/projectM-visualizer/frontend-sdl-cpp).

The core components of the application will:
- Handle SDL rendering window
- Initialize projectM using a custom wrapper
- Capture SDL audio and route PCM data to projectM
- Listen for SDL mouse/keyboard/gamepad/window events for user controlled actions and window focus mgmt (if using Raspberry Pi lite OS evdev is used to monitor keyboard/mouse events)

## 🔉 Example Use Cases
The obvious purpose for this is to have visualizations react to sound.  That said there are various use cases for implementation.
- React to system audio
- React to ambient sound using a microphone

## 🖼️ Screenshots
![ProjectMAR Screenshot 1](https://github.com/kholbrook1303/RPI5-Bookworm-ProjectM-Audio-Receiver/blob/main/resources/preview1.png)
![ProjectMAR Screenshot 2](https://github.com/kholbrook1303/RPI5-Bookworm-ProjectM-Audio-Receiver/blob/main/resources/preview2.png)
![ProjectMAR Screenshot 3](https://github.com/kholbrook1303/RPI5-Bookworm-ProjectM-Audio-Receiver/blob/main/resources/preview3.png)
![ProjectMAR Screenshot 4](https://github.com/kholbrook1303/RPI5-Bookworm-ProjectM-Audio-Receiver/blob/main/resources/preview4.png)

## 🔩 Requirements:
- Build of libprojectM
- Python v3.9+
- Windows/Mac/Linux
  - Windows support requires GLEW

# ⚙️ Installing instructions
First you will need to build the latest release of [libprojectM](https://github.com/projectM-visualizer/projectm/blob/master/BUILDING.md).  These include instructions for each OS.

Once complete you will need to pull down this repository.  In the root of the repository there is a requirements.txt for which you can install the python dependencies:
```
python -m pip install -r requirements.txt
```

Once the requirements are in place, edit the projectMSDL.properties to adjust your configurations.  Specifically take note of the DLL references and ensure they point to the appropriate DLLs.  If you DLL path is included in the system env path variables you do not need to include this.  If they are not found you will need to specify their location.
```
# Path to the required dynamic libraries.
# GLEW: The OpenGL Extension Wrangler Library (Required for Windows).
# projectM: The main projectM library.
# projectM-Playlist: The projectM playlist library.
projectM.projectMGlewLib = <DLL_PATH>\glew32.dll
projectM.projectMLib = <DLL_PATH>\projectM-4.dll
projectM.projectMPlaylistLib = <DLL_PATH>\projectM-4-Playlist.dll
```

You will also need to specify the location for the presets and textures.  Ensure that the projectM.presetPath and projectM.texturePath include the location for these.  To obtain sets of textures and presets, see below.

# 🌌 General Presets and Textures:
Textures:
- [Base Milkdrop texture pack](https://github.com/projectM-visualizer/presets-milkdrop-texture-pack) - Recommended for
  use with _any_ preset pack!

Presets:
- [Cream of the Crop Pack](https://github.com/projectM-visualizer/presets-cream-of-the-crop) - A collection of about 10K
  presets compiled by Jason Fletcher. Currently, projectM's default preset pack.
- [Classic projectM Presets](https://github.com/projectM-visualizer/presets-projectm-classic) - A bit over 4K presets
  shipped with previous versions of projectM.
- [Milkdrop 2 Presets](https://github.com/projectM-visualizer/presets-milkdrop-original) - The original preset
  collection shipped with Milkdrop and Winamp.
- [En D Presets](https://github.com/projectM-visualizer/presets-en-d) - About 50 presets created by "En D".

# 🖦 Input Event Handling Guide

This document describes how keyboard, controller, and window input events are handled in the application.

---

## ⌨️ Keyboard Input

Handles key presses, with support for modifier keys like **Ctrl**.

### Modifier Support
- `Ctrl` (either left or right) enables certain shortcut actions when combined with other keys.

### Key Bindings

| Key            | With Ctrl? | Action                                  |
|----------------|------------|-----------------------------------------|
| `F`            | ✅         | Toggle fullscreen mode                  |
| `N`            | ❌         | Load **next preset**                    |
| `P`            | ❌         | Load **previous preset**                |
| `Q`            | ✅         | **Exit** the application                |
| `Y`            | ✅         | Toggle **playlist shuffle** mode        |
| `Delete`       | ❌         | **Delete** current preset               |
| `Space`        | ❌         | Toggle **preset lock**                  |
| `Escape`       | ❌         | Toggle fullscreen mode                  |
| `Arrow Up`     | ❌         | Increase **beat sensitivity** (+0.1)    |
| `Arrow Down`   | ❌         | Decrease **beat sensitivity** (−0.1)    |

---

## 🎮 Controller Axis Input (Desktop OS only)

Handles analog stick and trigger inputs. Uses a **deadzone threshold** to avoid accidental movements.

### Axis Bindings

| Axis                          | Condition       | Action                          |
|-------------------------------|------------------|----------------------------------|
| Left Stick X / Trigger Left   | Left / Pressed   | Load **previous preset**         |
| Left Stick X / Trigger Right  | Right / Pressed  | Load **next preset**             |
| Left Stick Y                  | Up               | Increase **beat sensitivity** (+0.1) |
| Left Stick Y                  | Down             | Decrease **beat sensitivity** (−0.1) |

---

## 🎮 Controller Button Input (Desktop OS only)

Handles digital controller buttons such as D-Pad and stick clicks.

### Button Bindings

| Button                           | Action                        |
|----------------------------------|-------------------------------|
| Left Stick Click / Right Stick Click | Toggle **preset lock**      |
| D-Pad Up                         | Increase **beat sensitivity** (+0.1) |
| D-Pad Down                       | Decrease **beat sensitivity** (−0.1) |
| D-Pad Left                       | Load **previous preset**      |
| D-Pad Right                      | Load **next preset**          |

---

## 🗔 Window Events

Handles SDL window-related system events.

### Window Event Bindings

| Event Type                                | Action                                |
|-------------------------------------------|----------------------------------------|
| `SDL_WINDOWEVENT_CLOSE`                   | Exit the application                   |
| `SDL_WINDOWEVENT_RESIZED` / `SIZE_CHANGED`| Update internal rendering dimensions   |
| `SDL_WINDOWEVENT_HIDDEN` / `MINIMIZED`    | Restore and show the window           |
| `SDL_WINDOWEVENT_FOCUS_LOST`              | Log focus loss                         |
| `SDL_WINDOWEVENT_FOCUS_GAINED`            | Log focus gain                         |
# Stream Deck Mini Robot Controller

A ROS2-aware Python project for controlling a robot GUI using an Elgato Stream Deck Mini.

Based on the Python Elgato Stream Deck library:
https://github.com/abcminiuser/python-elgato-streamdeck#python-elgato-stream-deck-library

## Project structure

```
assistance_stream_deck_keyboard/
├── README.md
├── config.yaml
├── icons/
│   ├── backward_key.png
│   ├── enter_key.png
│   ├── forward_key.png
│   ├── play_key.png
│   ├── read_state.png
│   └── stop_key.png
├── run.sh
├── main.py
├── pyproject.toml
├── requirements.txt
├── examples/
│   ├── device_information.py
│   ├── basic_usage.py
│   ├── pedal.py
│   ├── streamdeck_info.py
│   ├── tiled_image.py
│   └── animated_images.py
├── src/
│   └── streamdeck_control.py
```

## What this project does

- Detects your Elgato Stream Deck Mini
- Displays a configured icon on each Stream Deck key
- Publishes ROS2 string messages to the topic `/events_stearmdeck`
- Supports configurable button labels, topic names, and icon files via `config.yaml`

## Installation

1. Create or activate your Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

> ROS2 itself is not installed via pip. If you want ROS2 publishing, install ROS2 separately and ensure `rclpy` is available in your Python environment.

## Running the controller

Run the project from the repository root:

```bash
python3 main.py
```

Alternatively, launch the controller with the bundled shell helper:

```bash
./run.sh
```

If you want to run via the package entry point after installing the package, use:

```bash
python3 -m streamdeck_control
```

## Configuration

Edit `config.yaml` to change button labels, topic name, message payloads, or icon file paths.

Example:

```yaml
topic: /events_stearmdeck
keys:
  - label: Play
    message: e_move_robot_automatically
    icon: icons/play_key.png
  - label: Back
    message: e_gui_back
    icon: icons/backward_key.png
  - label: Stop
    message: e_stop_robot_motion
    icon: icons/stop_key.png
  - label: Ready
    message: e_gui_ready
    icon: icons/read_state.png
  - label: Forward
    message: e_gui_forward
    icon: icons/forward_key.png
  - label: Enter
    message: e_gui_enter
    icon: icons/enter_key.png
```

## Default key descriptions

- `Play`: Starts automatic robot movement or playback mode.
- `Back`: Sends a GUI back / previous-screen command.
- `Stop`: Stops robot motion immediately.
- `Ready`: Marks the system as ready and updates the GUI state.
- `Forward`: Sends a GUI forward / next-screen command.
- `Enter`: Confirms the current selection or executes the active command.

## Notes

- If `rclpy` is unavailable, the controller still runs and prints messages to the terminal.
- Key icons are loaded relative to the repository root.
- The `icons/` directory should contain PNG files that are square or near-square for best results.

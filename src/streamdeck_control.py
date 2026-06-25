import os
import sys
import time

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("Missing dependency: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

import yaml

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")

# Try to import ROS2 (rclpy).
ros_enabled = False
rclpy = None
ros_node = None
ros_publisher = None
ROSString = None
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String as ROSString
    ros_enabled = True
except Exception:
    ros_enabled = False

# Default configuration values.
CONFIG = {
    'topic': '/events_stearmdeck',
    'keys': [
        {'label': 'Play', 'message': 'e_move_robot_automatically', 'icon': 'icons/play_key.png'},
        {'label': 'Back', 'message': 'e_gui_back', 'icon': 'icons/backward_key.png'},
        {'label': 'Stop', 'message': 'e_stop_robot_motion', 'icon': 'icons/stop_key.png'},
        {'label': 'Ready', 'message': 'e_gui_ready', 'icon': 'icons/read_state.png'},
        {'label': 'Forward', 'message': 'e_gui_forward', 'icon': 'icons/forward_key.png'},
        {'label': 'Enter', 'message': 'e_gui_enter', 'icon': 'icons/enter_key.png'},
    ]
}
BUTTON_CONFIG = []
BUTTON_LABELS = []

# Button appearance settings.
FONT_SIZE = 14
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (20, 20, 20)
PRESSED_COLOR = (0, 130, 200)


def load_configuration():
    """Load the button configuration from config.yaml."""
    global CONFIG, BUTTON_CONFIG, BUTTON_LABELS
    try:
        with open(CONFIG_PATH, "r") as fh:
            cfg = yaml.safe_load(fh)
            if cfg:
                CONFIG.update(cfg)
    except FileNotFoundError:
        pass

    BUTTON_CONFIG = CONFIG.get('keys', [])
    BUTTON_LABELS = [k.get('label', f"Key {i}") for i, k in enumerate(BUTTON_CONFIG)]


def get_button_config(key_index):
    if key_index < len(BUTTON_CONFIG):
        return BUTTON_CONFIG[key_index]
    return {'label': f"Key {key_index}", 'message': None, 'icon': None}


def resolve_icon_path(icon_file):
    if not icon_file:
        return None

    if os.path.isabs(icon_file) and os.path.exists(icon_file):
        return icon_file

    candidates = [
        os.path.join(PROJECT_ROOT, icon_file),
        os.path.join(SCRIPT_DIR, icon_file),
        os.path.join(PROJECT_ROOT, 'icons', os.path.basename(icon_file)),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def create_button_image(deck, key_index, pressed=False):
    """Create an image for the Stream Deck key with optional icon support."""
    key_cfg = get_button_config(key_index)
    label = key_cfg.get('label', f"Key {key_index}")
    icon_file = key_cfg.get('icon')

    width, height = deck.key_image_format()["size"]
    bg_color = PRESSED_COLOR if pressed else BACKGROUND_COLOR
    image = Image.new("RGBA", (width, height), (*bg_color, 255))
    draw = ImageDraw.Draw(image)

    icon_image = None
    icon_path = resolve_icon_path(icon_file)
    if icon_path:
        try:
            icon_image = Image.open(icon_path).convert("RGBA")
        except Exception:
            icon_image = None

    if icon_image:
        max_icon_width = int(width * 0.7)
        max_icon_height = int(height * 0.7)
        icon_image = ImageOps.contain(icon_image, (max_icon_width, max_icon_height))
        position = ((width - icon_image.width) // 2, (height - icon_image.height) // 2)
        image.paste(icon_image, position, icon_image)
    else:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        try:
            text_width, text_height = draw.textsize(label, font=font)
        except AttributeError:
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

        draw.text(
            ((width - text_width) / 2, (height - text_height) / 2),
            label,
            font=font,
            fill=TEXT_COLOR,
        )

    return image.convert("RGB")


def perform_robot_command(message):
    """Publish the configured command string to ROS2 or log it if ROS2 is unavailable."""
    if message is None:
        return

    if ros_enabled and ros_publisher is not None and ros_node is not None:
        msg = ROSString()
        msg.data = message
        ros_publisher.publish(msg)
        ros_node.get_logger().info(f"Published: {message}")
    else:
        print(f"[StreamDeck] (no-ROS) Command: {message}")


def handle_key_action(key_index, state):
    button_cfg = get_button_config(key_index)
    label = button_cfg.get('label', f"Key {key_index}")
    message = button_cfg.get('message')
    action = "pressed" if state else "released"
    print(f"Key {key_index} ({label}) {action}")

    if state:
        perform_robot_command(message)


def key_change_callback(deck, key, state):
    handle_key_action(key, state)
    image = create_button_image(deck, key, pressed=state)
    deck.set_key_image(key, PILHelper.to_native_format(deck, image))


def setup_deck(deck):
    deck.reset()
    deck.set_key_callback(key_change_callback)

    for key in range(deck.key_count()):
        image = create_button_image(deck, key)
        deck.set_key_image(key, PILHelper.to_native_format(deck, image))

    print("Stream Deck Mini is ready. Press a button to send commands.")


def initialize_ros():
    global ros_node, ros_publisher, ros_enabled
    if not ros_enabled:
        return

    try:
        rclpy.init()

        class MinimalNode(Node):
            def __init__(self):
                super().__init__("streamdeck_publisher")

        ros_node = MinimalNode()
        ros_publisher = ros_node.create_publisher(
            ROSString,
            CONFIG.get('topic', '/events_stearmdeck'),
            10,
        )
        print(f"ROS2 support enabled: publishing to {CONFIG.get('topic')}")
    except Exception as exc:
        print("Failed to initialize rclpy. Continuing without ROS. Error:", exc)
        ros_enabled = False


def cleanup_ros():
    if ros_enabled and ros_node is not None:
        try:
            ros_node.destroy_node()
            rclpy.shutdown()
        except Exception:
            pass


def main():
    load_configuration()
    initialize_ros()

    streamdecks = DeviceManager().enumerate()
    if not streamdecks:
        print("No Stream Deck devices found. Make sure the Stream Deck Mini is connected.")
        return 1

    deck = streamdecks[0]
    print(f"Found Stream Deck: {deck.deck_type()} ({deck.key_count()} keys)")

    deck_opened = False
    try:
        deck.open()
        deck_opened = True
        setup_deck(deck)

        while True:
            if ros_enabled and ros_node is not None:
                rclpy.spin_once(ros_node, timeout_sec=0.1)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting and resetting Stream Deck...")
    except Exception as exc:
        print("Stream Deck error:", exc)
    finally:
        cleanup_ros()
        if deck_opened:
            try:
                deck.reset()
            except Exception:
                pass
            try:
                deck.close()
            except Exception:
                pass

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

import os
import sys
import json

# Allow local imports
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(ROOT)

from tools.detect_text import DetectText   # <-- your new tool
from vision.vision import capture_fullscreen


def print_header(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_detect_text():
    print_header("TEST: detect_text tool")

    tool = DetectText()

    print("Taking screenshot…")
    screen = capture_fullscreen()
    if screen is None:
        print("ERROR: capture_fullscreen returned None")
        return

    result = tool.run("")

    print("\nDetected text results:")
    print(json.dumps(result, indent=2))

    if "debug_image" in result:
        print("Debug image saved at:", result["debug_image"])
    else:
        print("No debug overlay generated.")


def main():
    print_header("STARTING TEXT DETECTION TEST")
    test_detect_text()


if __name__ == "__main__":
    main()

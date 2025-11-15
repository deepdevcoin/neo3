import os
import sys
import json
import cv2

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(ROOT)

from vision.vision import capture_fullscreen, detect_all_templates, TEMPLATES


# Where to save overlays
DEBUG_DIR = os.path.join(ROOT, "debug_outputs_all")
os.makedirs(DEBUG_DIR, exist_ok=True)


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print_header("DETECTING ALL UI TEMPLATES ON SCREEN")

    print("Total templates loaded:", len(TEMPLATES))
    print(json.dumps(list(TEMPLATES.keys()), indent=2))

    # Capture full screen
    screen = capture_fullscreen()

    # Detect everything
    print("\nRunning multi-template detection...\n")
    hits = detect_all_templates(screen)

    if not hits:
        print("NO TEMPLATES DETECTED.")
        return

    print("Detected templates:")
    print(json.dumps(hits, indent=2))

    # Draw overlays for ALL detections
    dbg = screen.copy()

    for key, info in hits.items():
        x, y = info["x"], info["y"]
        score = info["score"]

        cv2.circle(dbg, (x, y), 20, (0, 255, 0), 3)
        cv2.putText(dbg, f"{key} ({score})", (x + 25, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Save result
    save_path = os.path.join(DEBUG_DIR, "all_templates_detected.png")
    cv2.imwrite(save_path, dbg)

    print("\nSaved detection overlay here:")
    print(save_path)


if __name__ == "__main__":
    main()

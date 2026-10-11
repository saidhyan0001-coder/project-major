"""Capture one AprilTag observation and submit it to the hotel API.

This is based on the detection approach in the MIT-licensed sample repository:
https://github.com/saidhyan0001-coder/aprila-tag
That repository points to Kazuhito00/AprilTag-Detection-Python-Sample, which uses
OpenCV and pupil-apriltags. This helper does not control a robot or store images.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def report_observation(api_url: str, token: str, payload: dict[str, str | int | float]) -> dict[str, object]:
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/v1/apriltag/observations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result: dict[str, object] = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Verification API rejected the report ({exc.code}): {body}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Could not reach the verification API; no verification was recorded.") from exc
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an intended hotel room using a camera AprilTag observation.")
    parser.add_argument("--room", required=True, help="Configured room number (not inferred from tag ID)")
    parser.add_argument("--floor", required=True, help="Configured floor identifier")
    parser.add_argument("--device", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--family", default="tag36h11")
    parser.add_argument("--api-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()

    api_token = os.getenv("APRILTAG_REPORT_TOKEN")
    if not api_token:
        parser.error("Set APRILTAG_REPORT_TOKEN in the camera process environment.")

    try:
        import cv2
        from pupil_apriltags import Detector
    except ImportError as exc:
        print(
            "Camera dependencies missing. Install them with: "
            "python -m pip install -r apriltag-requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    capture = cv2.VideoCapture(args.device)
    if not capture.isOpened():
        print(f"Could not open camera device {args.device}.", file=sys.stderr)
        return 2
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    detector = Detector(families=args.family, nthreads=1, quad_decimate=2.0)

    print("Camera active. Show one room marker; press q to cancel. No timeout means no verification.")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("Camera frame unavailable; verification not recorded.", file=sys.stderr)
                return 2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detections = detector.detect(gray)
            for detection in detections:
                if float(detection.decision_margin) < 35.0:
                    continue
                family = detection.tag_family.decode("ascii")
                payload: dict[str, str | int | float] = {
                    "room_number": args.room,
                    "floor_id": args.floor,
                    "observed_family": family,
                    "observed_tag_id": int(detection.tag_id),
                    "decision_margin": float(detection.decision_margin),
                }
                result = report_observation(args.api_url, api_token, payload)
                print(json.dumps(result))
                return 0 if result.get("verified") is True else 1
            cv2.imshow("Hotel room tag verification (q to cancel)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Cancelled; no verification recorded.")
                return 1
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())

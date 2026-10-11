# Raspberry Pi deployment handoff

This is an installation guide, not a claim that the app or camera has been run on a Raspberry Pi. Test the actual Pi model, 64-bit OS image, camera, and network before production. Use Raspberry Pi OS 64-bit based on Debian Bookworm (or another currently supported 64-bit Debian release), Python 3.11+, Node 20.19+/22.12+, and npm 10+. Vite frontend and FastAPI backend should run as separate services/processes; do not assume Gemini inference runs locally.

## Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git libglib2.0-0 libgl1
python3 --version
node --version
npm --version
```

Use an official NodeSource or Node.js installation if the OS package version is below the supported Vite version. Do not install the camera dependencies unless a camera is connected.

## Checkout and configure

```bash
git clone https://github.com/saidhyan0001-coder/project-major.git
cd project-major
bash setup.sh
source .venv/bin/activate
nano .env
```

Set `APP_ENV=production`, a production `DATABASE_URL`, `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, an available `GEMINI_MODEL`, unique random `STAFF_API_TOKEN` and `APRILTAG_REPORT_TOKEN`, and exact allowed `CORS_ORIGINS`. Never expose these values in a frontend variable. For a public guest website, host the API on a managed backend platform with HTTPS rather than exposing a home Pi directly; use VPN/reverse proxy/firewall policy if the Pi hosts the backend.

## Start and verify local services

For a local demo:

```bash
source .venv/bin/activate
npm run db:migrate
npm run dev
```

For production, use separate process supervision (systemd/container), bind the backend behind a TLS reverse proxy, and serve the built frontend using a static host. `npm run dev` is not a production service manager. Put `.env` in a restricted location and use a non-root service account.

## Optional camera-based AprilTag detection

The user's `aprila-tag` repository contains a submodule referencing a Python sample that documents OpenCV + `pupil-apriltags`. Install optional packages only on a camera-capable system:

```bash
source .venv/bin/activate
python -m pip install -r apriltag-requirements.txt
export APRILTAG_REPORT_TOKEN='same secret as backend camera reporter setting'
python tools/apriltag_camera.py --room 204 --floor 2 --device 0 --api-url https://api.example.org
```

Register the actual printed tag against the correct room/floor through the staff portal first. The numeric tag ID must not be used as a room number. Verify camera device with `v4l2-ctl --list-devices` (install `v4l-utils` if needed). If the ID/family/mapping does not match or decision margin is below 35, API result is not verified. This checker only reports a room-marker observation; it does not use ROS, navigate, deliver an order, or control motors.

## Backups/operations

Use PostgreSQL with encrypted, scheduled, tested backups for production. Back up the database before every migration and test restoration. Monitor `/api/v1/health`, `/api/v1/ready`, API errors, latency, database usage, and provider quota. Rotate exposed Gemini/staff/camera credentials immediately. Raspberry Pi compatibility, camera behavior, thermals, SD-card longevity, and production reliability remain unverified until tested on the target hardware.

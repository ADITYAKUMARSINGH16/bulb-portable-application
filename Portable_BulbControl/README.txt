# Portable Bulb Control

This folder contains the portable version of the Bulb Control application. No Python installation is required.

## Contents
- `BulbControl.exe`: The main application for controlling your WiZ lights.
- `FindBulb.exe`: A utility to scan your network and find WiZ bulbs.
- `config.json`: Configuration file storing your settings (IP, area, etc.).

## How to Use
1. **Find your Bulb**: Run `FindBulb.exe` and click "Scan Network". If found, click the bulb to copy its IP address.
2. **Control your Bulb**: Run `BulbControl.exe`. Paste the IP address if it's not already set.
3. **Configuration**: Your settings are saved in `config.json` automatically.

## Troubleshooting
- Ensure you are connected to the same Wi-Fi network as your bulbs.
- If the app doesn't open, try running it as Administrator.

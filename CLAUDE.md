# Project Overview

Custom smart lightswitch firmware for Raspberry Pi Pico W. Runs MicroPython to detect button presses and communicate with Home Assistant.
Works in tandem with the ha-smart-switches add-on project (separate repository).

## Architecture

- **Platform**: Raspberry Pi Pico W with MicroPython runtime
- **Entry point**: main.py → app/start.py
- **Main loop**: Polls WiFi, HTTP request queue, and API server

## Key Components

- **app/board/** - Hardware abstraction layer
  - Supports 7+ layouts (V3-V9) with different GPIO pin mappings
  - Layout V9: 10 buttons (on, off, 1-8) with RGB LEDs
  - BasicButtonBoard, DialBoard, NeopixelBoard classes
  - Long-press detection (1.5s) and multi-button combos

- **app/wifi/** - WiFi connectivity with auto-reconnect (30s backoff)

- **app/requestqueue/** - Non-blocking HTTP request manager
  - Uses select.poll() for async socket handling
  - 5-second timeout per request
  - POST to ha-smart-switches backend at {ip}:8124/api/press

- **app/config/** - Manages config.json (WiFi, HA IP, layout, GitHub token)

- **app/api/** - Local HTTP server on port 80 with /info endpoint

- **app/otaupdate/** - GitHub-based firmware OTA updates

## Integration with ha-smart-switches

When button pressed → POST to HA add-on /api/press → add-on looks up configured script/scene → executes via HA API → LED feedback

## Development

- Written using MicroPython for Raspberry Pi Pico W
- Uses MicroPico VSCode extension for deployment
- Use an indent size of four spaces
- Check out README.md for basic information

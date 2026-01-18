# ShigureCafePlugin

A MCDReforged plugin for synchronizing whitelist and chat messages with ShigureCafeBackend.

## Features

- **Whitelist Synchronization**: Periodically fetches the whitelist from the ShigureCafe backend and updates the local `whitelist.json` file.
- **Chat Synchronization**: Real-time two-way chat synchronization between Minecraft and ShigureCafe using WebSockets.
- **Manual Control**: Command to manually trigger whitelist synchronization.

## Requirements

- [MCDReforged](https://github.com/MCDReforged/MCDReforged) >= 2.0.0
- Python dependencies:
  - `websocket-client`
  - `requests`

You can install the dependencies using:
```bash
pip install -r requirements.txt
```

## Configuration

The plugin generates a configuration file in the MCDR data folder. Default values:

| Key | Description | Default |
|-----|-------------|---------|
| `whitelist_api_url` | URL for the whitelist API | `http://localhost:8080/api/v1/minecraft/whitelist` |
| `chat_ws_url` | URL for the chat WebSocket | `ws://localhost:8080/ws/minecraft/chat` |
| `api_key` | Secret key for authentication | `shigure-cafe-secret-key` |
| `interval` | Whitelist sync interval (seconds) | `300` |

## Commands

- `!!cafe whitelist sync`: Manually trigger a whitelist synchronization.

## Installation

1. Place `ShigureCafePlugin-v1.0.0.mcdr` into your MCDR `plugins` folder.
2. Install the required Python dependencies.
3. Start MCDR.
4. Configure the plugin by editing the generated config file in the `config` directory.
5. Reload the plugin.

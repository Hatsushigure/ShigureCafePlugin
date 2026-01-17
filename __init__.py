from mcdreforged.api.all import *
from ShigureCafePlugin import whitelist_sync, message_sync

# Default Configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8080/api/v1/minecraft/whitelist",
    "chat_sync_url": "http://localhost:8080/api/v1/minecraft/message-sync",
    "api_key": "shigure-cafe-secret-key",
    "interval": 60,
    "chat_sync_interval": 1,
    "whitelist_file": "whitelist.json"
}

config = DEFAULT_CONFIG

def load_config(server: PluginServerInterface):
    global config
    config = server.load_config_simple(target_class=dict, default_config=DEFAULT_CONFIG)
    server.logger.info(f'Config loaded: {config}')

def on_load(server: PluginServerInterface, old):
    load_config(server)
    whitelist_sync.whitelist_loop(server, config)
    message_sync.chat_sync_loop(server, config)

def on_info(server: PluginServerInterface, info: Info):
    message_sync.on_info(server, info)
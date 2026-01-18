import threading
from mcdreforged.api.all import *
from . import whitelist_sync, message_sync

# Global state
config = {}
chat_client = None
stop_event = threading.Event()

# Default Configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8080/api/v1/minecraft/whitelist",
    "chat_ws_url": "ws://localhost:8080/ws/minecraft/chat",
    "api_key": "shigure-cafe-secret-key",
    "interval": 300,
    "whitelist_file": "whitelist.json"
}

def load_config(server: PluginServerInterface):
    global config
    config = server.load_config_simple(default_config=DEFAULT_CONFIG, in_data_folder=True)
    server.logger.info(f'Config loaded: {config}')

def on_load(server: PluginServerInterface, old):
    global chat_client, stop_event
    load_config(server)
    register_commands(server)
    
    stop_event.clear()
    whitelist_sync.whitelist_loop(server, config, stop_event)
    chat_client = message_sync.chat_sync_loop(server, config)

def on_unload(server: PluginServerInterface):
    global chat_client, stop_event
    server.logger.info('Unloading ShigureCafePlugin...')
    
    # Stop whitelist sync loop
    stop_event.set()
    
    # Stop chat sync websocket client
    if chat_client:
        chat_client.stop()
        chat_client = None

def register_commands(server: PluginServerInterface):
    server.register_command(
        Literal('!!cafe').then(
            Literal('whitelist').then(
                Literal('sync').runs(lambda src: manual_whitelist_sync(src))
            )
        )
    )

def manual_whitelist_sync(src: CommandSource):
    server = src.get_server()
    src.reply('§b[ShigureCafe]§r 正在手动触发白名单同步...')
    try:
        whitelist_sync.sync_whitelist(server, config)
        src.reply('§b[ShigureCafe]§r 白名单同步完成！')
    except Exception as e:
        src.reply(f'§b[ShigureCafe]§c 白名单同步失败: {e}')

def on_info(server: PluginServerInterface, info: Info):
    message_sync.on_info(server, info)
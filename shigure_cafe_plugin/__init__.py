from mcdreforged.api.all import *
from . import whitelist_sync, message_sync

# Default Configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8080/api/v1/minecraft/whitelist",
    "chat_ws_url": "ws://localhost:8080/ws/minecraft/chat",
    "api_key": "shigure-cafe-secret-key",
    "interval": 300,
    "whitelist_file": "whitelist.json"
}

config = DEFAULT_CONFIG

def load_config(server: PluginServerInterface):
    global config
    config = server.load_config_simple(target_class=dict, default_config=DEFAULT_CONFIG)
    server.logger.info(f'Config loaded: {config}')

def on_load(server: PluginServerInterface, old):
    load_config(server)
    register_commands(server)
    whitelist_sync.whitelist_loop(server, config)
    message_sync.chat_sync_loop(server, config)

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
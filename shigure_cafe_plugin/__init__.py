import time
from mcdreforged.api.command import Literal
from mcdreforged.api.types import CommandSource, Info, PluginServerInterface
from mcdreforged.api.rtext import RText, RColor, RTextList
from .chat_sync import Message, ChatSyncClient
from .whitelist_sync import WhitelistSyncClient

# Global state
config = {}
chat_client: ChatSyncClient | None = None
whitelist_client: WhitelistSyncClient | None = None

# Default Configuration
DEFAULT_CONFIG = {
    "whitelist_api_url": "http://localhost:8080/api/v1/minecraft/whitelist",
    "chat_ws_url": "ws://localhost:8080/ws/minecraft/chat",
    "api_key": "shigure-cafe-secret-key",
    "interval": 300
}

def load_config(server: PluginServerInterface):
    global config
    config: dict = server.load_config_simple(default_config=DEFAULT_CONFIG, in_data_folder=True) # type: ignore
    server.logger.info(f'Config loaded: {config}')

def on_load(server: PluginServerInterface, old):
    global chat_client, stop_event
    load_config(server)
    register_commands(server)
    
    whitelist_client = WhitelistSyncClient(server, config)
    chat_client = ChatSyncClient(server, config)
    whitelist_client.run() # type: ignore
    chat_client.run() # type: ignore

def on_unload(server: PluginServerInterface):
    server.logger.info('Unloading ShigureCafePlugin...')
    
    # Stop chat sync websocket client
    if chat_client:
        chat_client.stop()
    if whitelist_client:
        whitelist_client.stop()

def register_commands(server: PluginServerInterface):
    server.register_command(
        Literal('!!cafe').then(
            Literal('whitelist').then(
                Literal('sync').runs(lambda src: manual_whitelist_sync(src))
            )
        )
    )

def manual_whitelist_sync(src: CommandSource):
    prefix = RText('[ShigureCafe]', color=RColor.aqua)
    if (whitelist_client is None):
        src.reply(RTextList(prefix, RText(' 白名单同步客户端未初始化！', color=RColor.red)))
        return
    src.reply(RTextList(prefix, ' 正在手动触发白名单同步...'))
    try:
        whitelist_client.sync_whitelist()
        src.reply(RTextList(prefix, ' 白名单同步完成！'))
    except Exception as e:
        src.reply(RTextList(prefix, RText(f' 白名单同步失败: {e}', color=RColor.red)))

def on_user_info(server: PluginServerInterface, info: Info):
    if (chat_client is None):
        return
    if (info.player is None) or (info.content is None):
        return
    chat_client.add_message(
        Message(
            info.player,
            info.content,
            int(round(time.time() * 1000))
            )
        )
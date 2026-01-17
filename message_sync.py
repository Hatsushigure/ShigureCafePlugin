import json
import time
import requests
import threading
from mcdreforged.api.all import *

message_queue = []
queue_lock = threading.Lock()
last_timestamp = int(time.time() * 1000)

@new_thread('ShigureCafeChatSync')
def chat_sync_loop(server: PluginServerInterface, config: dict):
    global last_timestamp
    while True:
        if not server.is_plugin_loaded('shigure_cafe_plugin'):
            break
            
        try:
            with queue_lock:
                messages_to_send = list(message_queue)
                message_queue.clear()
            
            payload = {
                "messages": messages_to_send,
                "lastTimestamp": last_timestamp
            }
            
            headers = {
                "X-API-KEY": config.get('api_key'),
                "Content-Type": "application/json"
            }
            
            url = config.get('chat_sync_url')
            if url:
                resp = requests.post(url, json=payload, headers=headers, timeout=5)
                
                if resp.status_code == 200:
                    new_messages = resp.json()
                    
                    for msg in new_messages:
                        name = msg.get('name')
                        content = msg.get('message')
                        ts = msg.get('timestamp')
                        
                        if ts > last_timestamp:
                            last_timestamp = ts
                        
                        tellraw_obj = [
                            {"text": f"<{name}> ", "color": "white"},
                            {"text": content, "color": "white"}
                        ]
                        server.execute(f'tellraw @a {json.dumps(tellraw_obj)}')
        except Exception as e:
            server.logger.error(f"Error in chat sync: {e}")
            
        time.sleep(config.get('chat_sync_interval', 1))

def on_info(server: PluginServerInterface, info: Info):
    global last_timestamp
    if not server.is_server_startup():
        return

    if info.is_user:
        name = info.player
    elif info.is_from_server:
        if "tellraw" in info.content:
            return
        name = "Server"
    else:
        return

    if not info.content:
        return

    with queue_lock:
        ts = int(time.time() * 1000)
        message_queue.append({
            "name": name,
            "message": info.content,
            "timestamp": ts
        })
        last_timestamp = ts

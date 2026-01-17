import json
import time
import threading
from mcdreforged.api.all import *

# Try to import websocket, if not found, we will log error later in the loop
try:
    import websocket
except ImportError:
    websocket = None

message_queue = []
queue_lock = threading.Lock()

class ChatSyncClient:
    def __init__(self, server: PluginServerInterface, config: dict):
        self.server = server
        self.config = config
        self.ws = None
        self.running = True
        self.reconnect_delay = 1
        self.send_thread = None

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            name = msg.get('name')
            content = msg.get('message')
            
            # Don't echo back messages from server that we might have just sent 
            # (though the backend should handle this, it's safer to have some check if needed)
            
            tellraw_obj = [
                {"text": f"<{name}> ", "color": "white"},
                {"text": content, "color": "white"}
            ]
            self.server.execute(f'tellraw @a {json.dumps(tellraw_obj)}')
        except Exception as e:
            self.server.logger.error(f"Error processing received message: {e}")

    def on_error(self, ws, error):
        self.server.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.server.logger.info(f"WebSocket connection closed: {close_status_code} {close_msg}")

    def on_open(self, ws):
        self.server.logger.info("WebSocket connection established")
        self.reconnect_delay = 1
        
        # Start a thread to send messages from queue if not already running
        if self.send_thread is None or not self.send_thread.is_alive():
            self.send_thread = threading.Thread(target=self.send_loop, daemon=True)
            self.send_thread.start()

    def send_loop(self):
        self.server.logger.info("WebSocket send loop started")
        while self.running and self.ws:
            try:
                with queue_lock:
                    if message_queue:
                        messages_to_send = list(message_queue)
                        message_queue.clear()
                    else:
                        messages_to_send = []
                
                for msg in messages_to_send:
                    if self.ws and self.ws.sock and self.ws.sock.connected:
                        self.ws.send(json.dumps(msg))
                    else:
                        # Put back to queue if connection lost
                        with queue_lock:
                            message_queue.insert(0, msg)
                        break
                
                time.sleep(0.1)
            except Exception as e:
                self.server.logger.error(f"Error in WebSocket send loop: {e}")
                time.sleep(1)

    def run(self):
        if websocket is None:
            self.server.logger.error("websocket-client is not installed. Please run 'pip install websocket-client'")
            return

        ws_url = self.config.get('chat_ws_url')
        if not ws_url:
            self.server.logger.error("chat_ws_url not configured")
            return

        api_key = self.config.get('api_key')
        headers = {"X-API-KEY": api_key}

        while self.running:
            try:
                self.server.logger.info(f"Connecting to WebSocket: {ws_url}")
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    header=headers,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                self.server.logger.error(f"WebSocket run error: {e}")
            
            if self.running:
                self.server.logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

def chat_sync_loop(server: PluginServerInterface, config: dict):
    client = ChatSyncClient(server, config)
    # Use MCDR's new_thread decorator style via manual thread creation to keep client reference if needed
    thread = threading.Thread(target=client.run, name='ShigureCafeChatSync', daemon=True)
    thread.start()

def on_info(server: PluginServerInterface, info: Info):
    if not server.is_server_startup():
        return

    if info.is_user:
        name = info.player
    elif info.is_from_server:
        # Ignore messages sent by the plugin itself (tellraw)
        if "tellraw" in info.content:
            return
        # Basic server info patterns can be filtered here if needed
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
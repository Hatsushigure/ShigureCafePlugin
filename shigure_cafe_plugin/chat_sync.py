import json
import time
import threading
import websocket
import dataclasses
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.types import PluginServerInterface

queue_lock = threading.Lock()

@dataclasses.dataclass(frozen=True, slots=True)
class Message:
    name: str
    message: str
    timestamp: int

class ChatSyncClient:
    def __init__(self, server: PluginServerInterface, config: dict):
        self.message_queue: list[Message] = []
        self.sent_messages: set[Message] = set()
        self.server = server
        self.config = config
        self.running = True
        self.reconnect_delay = 1
        api_key = str(self.config['api_key'])
        ws_url: str = str(self.config['chat_ws_url'])
        headers = {"X-API-KEY": api_key}
        self.ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
            )

    def add_message(self, message: Message):
        with queue_lock:
            self.message_queue.append(message)

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            msg = Message(
                msg['name'],
                msg['message'],
                msg['timestamp']
                )

            if (msg not in self.sent_messages):
                self.server.broadcast(f'<{msg.name}> {msg.message}')
            self.sent_messages.clear()
        except Exception as e:
            self.server.logger.error(f"Error processing received message: {e}")

    def on_error(self, ws, error):
        self.server.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.server.logger.info(f"WebSocket connection closed: {close_status_code} {close_msg}")

    def on_open(self, ws):
        self.server.logger.info("WebSocket connection established")
        self.reconnect_delay = 1
        
        # Start a thread to send messages from queue
        self.send_loop() # type: ignore

    @new_thread('ShigureCafeChatSendLoop')
    def send_loop(self):
        self.server.logger.info("WebSocket send loop started")
        while self.running and self.ws:
            try:
                with queue_lock:
                    if self.message_queue:
                        messages_to_send = self.message_queue.copy()
                        self.message_queue.clear()
                    else:
                        messages_to_send = []
                
                for msg in messages_to_send:
                    if self.ws and self.ws.sock and self.ws.sock.connected:
                        self.ws.send(json.dumps(dataclasses.asdict(msg)))
                        self.sent_messages.add(msg)
                    else:
                        with queue_lock:
                            self.message_queue.insert(0, msg)
                        break
                
                time.sleep(0.1)
            except Exception as e:
                self.server.logger.error(f"Error in WebSocket send loop: {e}")
                time.sleep(1)

    @new_thread('ShigureCafeChatSync')
    def run(self):        
        while self.running:
            try:
                self.server.logger.info(f"Connecting to WebSocket: {self.ws.url}")
                self.ws.run_forever()
            except Exception as e:
                self.server.logger.error(f"WebSocket run error: {e}")
            
            self.server.logger.info(f"Reconnecting in {self.reconnect_delay}s...")
            time.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
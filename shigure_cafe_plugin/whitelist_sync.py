import json
import os
import time
import requests
import threading
from mcdreforged.api.all import *

def sync_whitelist(server: PluginServerInterface, config: dict):
    url = config.get('api_url')
    # Get the server's working directory from MCDR config
    mcdr_config = server.get_mcdr_config()
    server_dir = mcdr_config.get('working_directory', 'server')
    whitelist_path = os.path.join(server_dir, 'whitelist.json')
    
    try:
        headers = {
            "X-API-KEY": config.get('api_key')
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            server.logger.warning(f'Failed to fetch whitelist. Status: {resp.status_code}, Body: {resp.text}')
            return

        remote_whitelist = resp.json()
        
        local_whitelist = []
        if os.path.exists(whitelist_path):
            try:
                with open(whitelist_path, 'r', encoding='utf-8') as f:
                    local_whitelist = json.load(f)
            except Exception as e:
                server.logger.warning(f'Failed to read local whitelist: {e}')
        
        remote_set = {(entry.get('uuid'), entry.get('name')) for entry in remote_whitelist}
        local_set = {(entry.get('uuid'), entry.get('name')) for entry in local_whitelist}
        
        if remote_set != local_set:
            server.logger.info(f'Whitelist change detected. Updating...')
            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(remote_whitelist, f, indent=4)
            
            if server.is_server_startup():
                server.execute('whitelist reload')
                server.logger.info('Executed "whitelist reload"')
                
    except Exception as e:
        server.logger.error(f'Error syncing whitelist: {e}')

@new_thread('ShigureCafeWhitelistSync')
def whitelist_loop(server: PluginServerInterface, config: dict, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            sync_whitelist(server, config)
        except Exception as e:
             server.logger.error(f"Error in whitelist loop: {e}")
        
        # Wait for interval or until stop_event is set
        stop_event.wait(config.get('interval', 300))

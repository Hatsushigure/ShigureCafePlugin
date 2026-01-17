import json
import os
import time
import requests
from mcdreforged.api.all import *

# Default Configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8080/api/v1/minecraft/whitelist",
    "api_key": "shigure-cafe-secret-key",
    "interval": 60,
    "whitelist_file": "whitelist.json"
}

config = DEFAULT_CONFIG

def load_config(server: PluginServerInterface):
    global config
    config = server.load_config_simple(target_class=dict, default_config=DEFAULT_CONFIG)
    server.logger.info(f'Config loaded: {config}')

def sync_whitelist(server: PluginServerInterface):
    url = config.get('api_url')
    whitelist_path = config.get('whitelist_file')
    
    # Resolve whitelist path relative to server root if not absolute
    if not os.path.isabs(whitelist_path):
        # In MCDR, current working directory is usually the server root
        pass 

    try:
        # Fetch from API
        # server.logger.debug(f'Fetching whitelist from {url}')
        headers = {
            "X-API-KEY": config.get('api_key')
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            server.logger.warning(f'Failed to fetch whitelist. Status: {resp.status_code}, Body: {resp.text}')
            return

        remote_whitelist = resp.json() # List of {uuid, name}
        
        # Read local
        local_whitelist = []
        if os.path.exists(whitelist_path):
            try:
                with open(whitelist_path, 'r', encoding='utf-8') as f:
                    local_whitelist = json.load(f)
            except Exception as e:
                server.logger.warning(f'Failed to read local whitelist: {e}')
                # If read fails, we assume empty or corrupt, so we might want to overwrite if we have good data
        
        # Compare
        # Using sets of tuples to compare content (ignoring order)
        # We assume the structure is consistently [{"uuid": "...", "name": "..."}]
        
        remote_set = {(entry.get('uuid'), entry.get('name')) for entry in remote_whitelist}
        local_set = {(entry.get('uuid'), entry.get('name')) for entry in local_whitelist}
        
        if remote_set != local_set:
            server.logger.info(f'Whitelist change detected (Remote: {len(remote_set)}, Local: {len(local_set)}). Updating...')
            
            # Write new whitelist
            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(remote_whitelist, f, indent=4)
            
            # Reload if server is running
            if server.is_server_startup():
                server.execute('whitelist reload')
                server.logger.info('Executed "whitelist reload"')
            else:
                server.logger.info('Server not started, skipped "whitelist reload"')
                
    except requests.RequestException as e:
        server.logger.warning(f'Network error fetching whitelist: {e}')
    except Exception as e:
        server.logger.error(f'Unexpected error syncing whitelist: {e}')

@new_thread('ShigureCafeWhitelistSync')
def loop_task(server: PluginServerInterface):
    while True:
        if server.is_plugin_loaded('shigure_cafe_plugin'): # Safety check
            try:
                sync_whitelist(server)
            except Exception as e:
                 server.logger.error(f"Critical error in sync loop: {e}")
        
        time.sleep(config.get('interval', 60))

def on_load(server: PluginServerInterface, old):
    load_config(server)
    
    # Start the loop
    loop_task(server)

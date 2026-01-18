import json
import os
import time
import requests
from mcdreforged.api.all import *

def sync_whitelist(server: PluginServerInterface, config: dict):
    url = config.get('api_url')
    whitelist_path = config.get('whitelist_file')
    
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
def whitelist_loop(server: PluginServerInterface, config: dict):
    while True:
        if not server.is_plugin_loaded('shigure_cafe_plugin'):
            break
        try:
            sync_whitelist(server, config)
        except Exception as e:
             server.logger.error(f"Error in whitelist loop: {e}")
        time.sleep(config.get('interval', 60))

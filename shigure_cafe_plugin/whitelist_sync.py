import dataclasses
import json
import pathlib
import requests
import time
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.types import PluginServerInterface

@dataclasses.dataclass(frozen=True, slots=True)
class PlayerInfo:
    uuid: str
    name: str

Whitelist = set[PlayerInfo]

class WhitelistSyncClient:
    def __init__(self, server: PluginServerInterface, config: dict):
        self.server = server
        self.whitelist_url: str = str(config['whitelist_api_url'])
        self.whitelist_path = pathlib.Path(
            server.get_mcdr_config().get('working_directory', 'server')
            ) / 'whitelist.json'
        self.api_key: str = str(config['api_key'])
        self.sync_interval: int = int(config['interval'])
        self.running = False

    def sync_whitelist(self):
        try:
            headers = {"X-API-KEY": self.api_key}
            resp = requests.get(self.whitelist_url, headers=headers)

            if resp.status_code != 200:
                self.server.logger.warning(f'Failed to fetch whitelist: {resp.status_code}\n{resp.text}')
                return
        except Exception as e:
            self.server.logger.error(f'Error fetching whitelist: {e}')
            return
        
        try:
            remote_whitelist_json = resp.json()
            remote_whitelist: Whitelist = set(
                PlayerInfo(
                    entry['uuid'],
                    entry['name']
                    ) for entry in remote_whitelist_json
                )
        except Exception as e:
            self.server.logger.error(f'Error parsing remote whitelist: {e}')
            return
        
        try:
            local_whitelist: Whitelist = set()
            with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    content = '[]'
                local_whitelist_json = json.loads(content)
                local_whitelist = set(
                    PlayerInfo(
                        entry['uuid'],
                        entry['name']
                            ) for entry in local_whitelist_json
                        )
        except Exception as e:
            self.server.logger.error(f'Failed to read local whitelist: {e}')
            return

        if (remote_whitelist != local_whitelist):
            self.server.logger.info(f'Whitelist change detected. Updating...')
            try:
                with open(self.whitelist_path, 'w', encoding='utf-8') as f:
                    json.dump(remote_whitelist_json, f, indent=4)
            except Exception as e:
                self.server.logger.error(f'Failed to write local whitelist: {e}')
                return
            
            if self.server.is_server_running():
                self.server.execute('whitelist reload')
                self.server.logger.info('Executed "whitelist reload"')

    @new_thread('ShigureCafeWhitelistSync')
    def run(self) -> None:
        self.running = True
        while self.running:
            self.sync_whitelist()
            time.sleep(self.sync_interval)

    def stop(self) -> None:
        self.running = False

import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "ZTNA"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        default_config = {
            "agent_id": "default-agent",
            "tpm_enabled": True,
            "backend_url": "http://localhost:8000",
            "reporting_interval": 300,
            "device_name": os.getenv("COMPUTERNAME", "unknown")
        }

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception:
            pass

        return default_config

    def get(self):
        return ConfigObject(self.config)

    def update(self, key, value):
        self.config[key] = value
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

class ConfigObject:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, item):
        return self._data.get(item, None)

    def __setattr__(self, key, value):
        if key == "_data":
            super().__setattr__(key, value)
        else:
            self._data[key] = value


config_manager = ConfigManager()

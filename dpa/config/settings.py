import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "ZTNA"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        # Load from file if exists
        file_config = {}
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
        except Exception:
            pass

        # Environment variable takes precedence over file config
        backend_url = os.getenv("DPA_BACKEND_URL") or file_config.get("backend_url", "http://localhost:8000")
        
        default_config = {
            "agent_id": "default-agent",
            "tpm_enabled": os.getenv("DPA_TPM_ENABLED", "true").lower() == "true" if "DPA_TPM_ENABLED" in os.environ else file_config.get("tpm_enabled", True),
            "backend_url": backend_url,
            "reporting_interval": int(os.getenv("DPA_REPORTING_INTERVAL", file_config.get("reporting_interval", 300))),
            "device_name": os.getenv("COMPUTERNAME", file_config.get("device_name", "unknown"))
        }

        # Only write default config if file doesn't exist
        if not self.config_file.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception:
                pass

        return default_config

    def get(self):
        config_obj = ConfigObject(self.config)
        # Attach config_dir to the config object so it's accessible
        config_obj.config_dir = self.config_dir
        return config_obj

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

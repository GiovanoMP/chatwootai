from pathlib import Path
import yaml

class CrewConfig:
    def __init__(self, domain: str):
        self.domain = domain
        self._load_config()

    def _load_config(self):
        config_path = Path(f"config/domains/{self.domain}/crew_config.yaml")
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

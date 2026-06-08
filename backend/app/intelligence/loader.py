import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IntelligenceLoader:
    def __init__(self):
        self.data = {
            "services": {},
            "technologies": {},
            "vulnerabilities": {}
        }
        self._load_all()

    def _load_all(self):
        base_path = Path(__file__).resolve().parent.parent.parent.parent / "argus-intelligence"
        
        if not base_path.exists():
            logger.warning(f"Intelligence base path not found at {base_path}")
            return

        for category in ["services", "technologies", "vulnerabilities"]:
            cat_path = base_path / category
            if not cat_path.exists():
                continue
                
            for json_file in cat_path.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        content = json.load(f)
                        # Use the filename without extension as the key
                        key = json_file.stem.lower()
                        self.data[category][key] = content
                except Exception as e:
                    logger.error(f"Failed to load {json_file}: {e}")

    def load_all(self):
        return self.data

    def get_service(self, name: str):
        return self.data["services"].get(name.lower())

    def get_technology(self, name: str):
        return self.data["technologies"].get(name.lower())

    def get_vulnerability(self, name: str):
        return self.data["vulnerabilities"].get(name.lower())

# Singleton instance for caching
loader_instance = IntelligenceLoader()

def load_all():
    return loader_instance.load_all()

def get_service(name: str):
    return loader_instance.get_service(name)

def get_technology(name: str):
    return loader_instance.get_technology(name)

def get_vulnerability(name: str):
    return loader_instance.get_vulnerability(name)

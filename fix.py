import os

# 1. Fix loader.py
loader_path = "backend/app/intelligence/loader.py"
with open(loader_path, "r") as f:
    content = f.read()

if "def get_intelligence_loader():" not in content:
    content += "\n\ndef get_intelligence_loader():\n    return loader_instance\n"
    with open(loader_path, "w") as f:
        f.write(content)

# 2. Fix intelligence.py
router_path = "backend/app/routers/intelligence.py"
with open(router_path, "r") as f:
    content = f.read()

content = content.replace("loader._cache", "loader.data")
with open(router_path, "w") as f:
    f.write(content)

# 3. Fix main.py
main_path = "backend/app/main.py"
with open(main_path, "r") as f:
    content = f.read()

content = content.replace("loader._cache", "loader.data")
with open(main_path, "w") as f:
    f.write(content)

# 4. Fix docker-compose.yml
compose_path = "docker-compose.yml"
with open(compose_path, "r") as f:
    content = f.read()

new_content = ""
for line in content.splitlines():
    new_content += line + "\n"
    if line.strip() == "- ./backend:/app":
        # Check if it already has the mount
        if "- ./argus-intelligence:/argus-intelligence" not in content:
            # We add it just below the backend mount
            new_content += "      - ./argus-intelligence:/argus-intelligence\n"

# A bit hacky, let's do a proper replace
content = content.replace("- ./backend:/app", "- ./backend:/app\n      - ./argus-intelligence:/argus-intelligence")
# Since we replaced all occurrences, and both api and worker have it, it mounts for both.

with open(compose_path, "w") as f:
    f.write(content)

print("Fixes applied.")

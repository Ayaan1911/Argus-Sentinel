import os

httpx_code = """import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting httpx scan for {target}")
    # Fix 1: Hardened httpx command with user-agent, threads, timeout, retries, redirects, and explicit match-codes
    command = [
        "/usr/local/bin/httpx", 
        "-u", target, 
        "-json", 
        "-silent", 
        "-title", 
        "-web-server",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "-retries", "2",
        "-timeout", "10",
        "-follow-redirects",
        "-mc", "200,201,301,302,303,307,308,401,403,404,500,502,503"
    ]
    findings = []
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        code = proc.returncode
        stdout = stdout.decode('utf-8', errors='replace')
        stderr = stderr.decode('utf-8', errors='replace')
        
        logger.info(f"httpx stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"httpx stderr: {stderr[:500]}")
            
        if code == -1 or not stdout:
            logger.warning(f"HTTPX failed to run or timed out: {stderr}")
            return findings
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        logger.warning("HTTPX timed out")
        return findings
    except Exception as e:
        logger.warning(f"HTTPX failed to execute: {e}")
        return findings

    for line in stdout.strip().split('\\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            # Fix 1.3: Tag WAF/CDN challenged hosts
            status_code = data.get("status_code", 0)
            waf_note = ""
            if status_code in [401, 403, 503]:
                waf_note = " (WAF/CDN protected - may require further evasion)"
                data["waf_detected"] = True

            findings.append({
                "source": "httpx",
                "type": "technology",
                "title": f"Live Host: {data.get('url', '')}{waf_note}",
                "raw_data": data
            })
        except:
            pass
            
    logger.info(f"httpx found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"httpx returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
"""

with open("backend/app/scanners/httpx.py", "w") as f:
    f.write(httpx_code)

docker_compose_code = """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: argus
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./argus-intelligence:/argus-intelligence
    env_file:
      - .env
    depends_on:
      - db
      - redis

  worker:
    build:
      context: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
      - ./argus-intelligence:/argus-intelligence
    env_file:
      - .env
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
"""

with open("docker-compose.yml", "w") as f:
    f.write(docker_compose_code)

env_content = """DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/argus
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
"""

env_example_content = """DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dbname
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=production
"""

with open(".env", "w") as f:
    f.write(env_content)

with open(".env.example", "w") as f:
    f.write(env_example_content)

# Setup gitignore
gitignore_content = """
# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Node
node_modules/
.npm
"""
if not os.path.exists(".gitignore"):
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
else:
    with open(".gitignore", "a") as f:
        f.write("\n.env\n")
        
print("Updated httpx.py, docker-compose.yml, .env, and .gitignore")

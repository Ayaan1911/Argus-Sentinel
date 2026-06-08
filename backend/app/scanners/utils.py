import asyncio
import re

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def run_cmd(cmd: str, timeout: int = 300):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, strip_ansi(stdout.decode('utf-8', errors='replace')), strip_ansi(stderr.decode('utf-8', errors='replace'))
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        return -1, "", "Timeout exceeded"
    except Exception as e:
        return -1, "", str(e)

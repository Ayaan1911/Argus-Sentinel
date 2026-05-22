import tempfile
import subprocess
import os

subdomains = ['academy-cdn.hackthebox.com', 'hackthebox.com']

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    for s in subdomains:
        f.write(s + '\n')
    tmp_path = f.name

print("tmp_path:", tmp_path)
with open(tmp_path, 'r') as tf:
    print("Contents:", tf.read())

cmd = [
    '/root/go/bin/httpx',
    '-l', tmp_path,
    '-silent',
    '-status-code',
    '-title',
    '-tech-detect',
    '-follow-redirects',
    '-json',
    '-timeout', '10',
    '-retries', '1',
]

proc = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", proc.returncode)
print("Stdout length:", len(proc.stdout))
print("Stderr:", proc.stderr)
print("Stdout snippet:", proc.stdout[:200])

os.unlink(tmp_path)

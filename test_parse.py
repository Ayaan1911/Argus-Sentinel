import json

def _parse_httpx_line(line: str):
    try:
        data = json.loads(line)
        raw_host = data.get('input', data.get('url', ''))
        host = (
            raw_host
            .replace('https://', '')
            .replace('http://', '')
            .split('/')[0]
            .split(':')[0]
            .lower()
            .strip()
        )
        if not host:
            return None

        technologies = data.get('tech', data.get('technologies', [])) or []
        if isinstance(technologies, list):
            tech_names = []
            for t in technologies:
                if isinstance(t, str):
                    tech_names.append(t)
                elif isinstance(t, dict):
                    tech_names.append(t.get('name', str(t)))
            technologies = tech_names

        return host, {
            'is_alive': True,
            'status_code': data.get('status-code') or data.get('status_code'),
            'title': (data.get('title') or '').strip(),
            'technologies': technologies,
        }
    except Exception as e:
        return f"Error: {e}"

line = '{"timestamp":"2026-05-21T18:56:01.005499921Z","port":"443","url":"https://hackthebox.com","input":"hackthebox.com","status_code":302,"tech":["Cloudflare","HSTS","HTTP/3"]}'
print(_parse_httpx_line(line))

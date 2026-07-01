FROM python:3.11-slim

WORKDIR /app

# Install wget, unzip, curl, git (git required by nuclei template downloader)
RUN apt-get update && apt-get install -y wget unzip curl nmap git ca-certificates && rm -rf /var/lib/apt/lists/*

# Install subfinder
RUN wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -O /tmp/subfinder.zip && \
    unzip -q /tmp/subfinder.zip subfinder -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/subfinder && \
    rm /tmp/subfinder.zip

# Install ProjectDiscovery httpx (NOT pip httpx)
RUN wget -q https://github.com/projectdiscovery/httpx/releases/download/v1.6.5/httpx_1.6.5_linux_amd64.zip -O /tmp/httpx.zip && \
    unzip -q /tmp/httpx.zip httpx -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/httpx && \
    rm /tmp/httpx.zip

# Install nuclei
RUN rm -f /usr/local/bin/nuclei && \
    wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip -O /tmp/nuclei.zip && \
    unzip -o /tmp/nuclei.zip nuclei -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip && \
    nuclei -version

# Download nuclei templates (no -duc so templates actually download)
# HOME must be set so nuclei writes to /root/nuclei-templates
RUN HOME=/root /usr/local/bin/nuclei -update-templates -silent || true
RUN ls /root/nuclei-templates 2>/dev/null | head -5 || echo 'WARNING: nuclei-templates directory empty or missing'

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y wget unzip && \
    wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -O /tmp/subfinder.zip && \
    unzip -o /tmp/subfinder.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/subfinder && \
    rm /tmp/subfinder.zip

RUN wget https://github.com/projectdiscovery/httpx/releases/download/v1.6.5/httpx_1.6.5_linux_amd64.zip -O /tmp/httpx.zip && \
    unzip -o /tmp/httpx.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/httpx && \
    rm /tmp/httpx.zip

RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.2.4/nuclei_3.2.4_linux_amd64.zip -O /tmp/nuclei.zip && \
    unzip -o /tmp/nuclei.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip

RUN nuclei -update-templates -silent || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]

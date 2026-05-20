FROM python:3.11-slim

# Install system dependencies and tools
RUN apt-get update && apt-get install -y \
    nmap \
    wget \
    curl \
    git \
    ca-certificates \
    golang-go \
    && rm -rf /var/lib/apt/lists/*

# Install Go-based security tools
ENV GOPATH=/root/go
ENV PATH=$PATH:/root/go/bin

RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy and set permissions for start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose API port
EXPOSE 8000

CMD ["/start.sh"]

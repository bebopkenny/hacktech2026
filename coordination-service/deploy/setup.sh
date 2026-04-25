#!/bin/bash
# Run once on the Vultr VM to install Docker and start the stack.
# No GPU required — all inference goes through the K2 API.
set -e

apt-get update && apt-get install -y docker.io docker-compose git

# Clone repo (update URL to your actual remote).
# git clone https://github.com/your-org/hacktech2026.git /opt/revitvync
cd /opt/revitvync

# .env must already be on the server before running this:
#   scp .env root@<vultr-ip>:/opt/revitvync/.env
if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Copy it to /opt/revitvync/.env first."
  exit 1
fi

docker-compose up -d --build

echo ""
echo "RevitSync stack started."
echo "  Coordination service : http://$(hostname -I | awk '{print $1}'):8000"
echo "  AI layer             : http://$(hostname -I | awk '{print $1}'):8001"
echo ""
echo "Check logs: docker-compose logs -f"

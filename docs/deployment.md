# Deployment on AWS EC2 (Ubuntu 24.04)

1. **Launch** Ubuntu Server 24.04 LTS, `t3.small` or larger (2 GB RAM minimum; the frontend image build needs memory, so `t3.medium` is more comfortable), 20 GB gp3.
2. **Security group, inbound:**
   - 22 → My IP
   - 80 → My IP (shop)
   - 8080 → My IP (Kafka UI)
   - Never open 9092, 9093 or 8000.
3. **Install Docker and the Compose plugin:**
   ```bash
   sudo apt-get update && sudo apt-get install -y ca-certificates curl git
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER && newgrp docker
   ```
4. **Clone and start:**
   ```bash
   git clone https://github.com/<you>/kafka-ecommerce-demo.git && cd kafka-ecommerce-demo
   sed -i 's/\r$//' scripts/*.sh kafka/*.sh && chmod +x scripts/*.sh kafka/*.sh
   ./scripts/start.sh
   ```
   `start.sh` creates `.env` with a random `INTERNAL_API_TOKEN` if it doesn't exist. `.env` is git-ignored. Never commit it.
5. **Verify:** `./scripts/health-check.sh`, then `./scripts/test-kafka.sh`.
6. **Browse:** `http://EC2-PUBLIC-IP` (shop) and `http://EC2-PUBLIC-IP:8080` (Kafka UI).

Stop with `./scripts/stop.sh` (keeps data) or `./scripts/stop.sh --purge` (deletes the Kafka volume).
Containers use `restart: unless-stopped`, so they return after a reboot.
Your public IP changes over time. If the pages stop loading, update the security group rules.

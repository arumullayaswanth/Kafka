# Deployment on AWS EC2 (Ubuntu 24.04)

1. **Launch** Ubuntu Server 24.04 LTS, `t3.small` or larger (2 GB RAM minimum; the frontend image build needs memory, so `t3.medium` is more comfortable), 20 GB gp3.
2. **Security group, inbound:**
   - 22 → My IP
   - 80 → My IP (shop)
   - 8080 → My IP (Kafka UI)
   - Never open 9092, 9093 or 8000.
3. **Install Docker and the Compose plugin:**

**3a. Update the server and install helper tools**
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
```

**3b. Add Docker's official download source**
```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**3c. Install Docker and Docker Compose**
```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**3d. Turn Docker on, and let your user run it without `sudo`**
```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

**3e. Check it worked**
```bash
docker --version
docker compose version
docker run --rm hello-world
```
✅ You should see `Docker version ...`, `Docker Compose version v2...`, and a message starting with **"Hello from Docker!"**

❌ If you see `permission denied`, type `exit`, run the `ssh` command from Step 9 again, and repeat 10e.

---

## Part D: Get the project and start it

### Step 11: Download the project
```bash
cd ~
git clone https://github.com/arumullayaswanth/Kafka.git kafka-ecommerce-demo
cd kafka-ecommerce-demo
ls
```
✅ You should see: `README.md  backend  consumer  docker-compose.yml  docs  frontend  kafka  scripts`

### Step 12: Start everything
```bash
./scripts/start.sh
```
This single command:
1. creates the `.env` settings file, with a random secret password (`INTERNAL_API_TOKEN`)
2. builds the frontend, backend and consumer images
3. starts all 14 containers: Kafka, kafka-init, Kafka UI, backend, frontend and 9 consumers

The first time takes **5–10 minutes**, because it downloads and builds everything. Wait until the prompt comes back.

❌ If you see `Permission denied`, run `chmod +x scripts/*.sh kafka/*.sh` and try again.

### Step 13: Check that everything is running
```bash
docker compose ps
```
✅ You should see:
- `kafka` → **Up (healthy)**
- `backend` → **Up (healthy)**
- `frontend`, `kafka-ui` → **Up**
- `order-consumer-1/2/3`, `payment-consumer-1/2/3`, `notification-consumer-1/2/3` → **Up**
- `kafka-init` is missing from the list, or shows **Exited (0)**. That is correct. It runs once to create the topic, then stops.

Now run the automatic test:
```bash
./scripts/health-check.sh
./scripts/test-kafka.sh
```
✅ The last lines should say **ALL CHECKS PASSED** and **PASSED: 5 orders x 3 consumer groups, 9 consumers active.**

---

## Part E: Open it in your browser

### Step 14: Use the shop and Kafka UI
On your own computer, open a browser:

| Page | Address |
|---|---|
| 🛒 Shop | `http://YOUR-IP` |
| 📦 Orders | `http://YOUR-IP/orders` |
| 📡 Live Event Monitor | `http://YOUR-IP/dashboard` |
| 📊 Kafka UI | `http://YOUR-IP:8080` |

Use `http://`, not `https://`.


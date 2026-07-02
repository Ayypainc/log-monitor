# Standalone Log Monitoring Dashboard

This is a standalone Python web service that allows you to securely monitor multiple log folders from a web browser in real time without needing SSH.

---

## Setup & Run Instructions

### 1. Configure Directories
Open the [.env](file:///c:/janova sol/log_monitor/.env) file and edit:
*   `PORT`: The port this server runs on (defaults to `5005`).
*   `ADMIN_LOGS_PASSCODE`: A secret passcode for browser access (defaults to `admin123`).
*   `MONITORED_DIRS`: Comma-separated list of log directories in format `alias:absolute_path`.
    *   **Example (Windows)**: `MONITORED_DIRS=system_logs:C:\janova sol\logs,chatbot_logs:C:\janova sol\chatbot_rag_backend\logs`
    *   **Example (Linux Droplet)**: `MONITORED_DIRS=system_logs:/var/www/logs,chatbot_logs:/var/www/chatbot_rag_backend/logs`

### 2. Install Dependencies
Run the following commands in your server terminal or local command prompt inside the `log_monitor` directory:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Start the Server
To run the server in development mode:
```bash
python app.py
```

### 4. Running in Production on DigitalOcean Droplet
To run this background process forever (even after you close the SSH terminal), use **PM2** on your droplet:
```bash
# Start under PM2
pm2 start "python app.py" --name log-monitor

# Keep it running after droplet reboots
pm2 save
```

---

## Access the Dashboard
Once running, open your browser and go to:
`http://YOUR_DROPLET_IP:5005` (or local `http://localhost:5005`)

1. Enter your passcode.
2. Select your folder from the dropdown menu (e.g. `system_logs` or `chatbot_logs`).
3. Click any log file in the sidebar to tail, search, or download!

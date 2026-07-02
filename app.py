import os
import sys
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Load configurations
load_dotenv()
ADMIN_LOGS_PASSCODE = os.getenv("ADMIN_LOGS_PASSCODE", "admin123")
PORT = int(os.getenv("PORT", 5005))

# Parse monitored directories list (format: alias:path,alias2:path2)
monitored_dirs = {}
monitored_dirs_str = os.getenv("MONITORED_DIRS", "")
for item in monitored_dirs_str.split(","):
    if not item.strip():
        continue
    if ":" in item:
        alias, path = item.split(":", 1)
        monitored_dirs[alias.strip()] = os.path.abspath(path.strip())
    else:
        path = item.strip()
        alias = os.path.basename(path.rstrip("\\/")) or "logs"
        monitored_dirs[alias] = os.path.abspath(path)

print("=" * 60)
print(" LOG MONITOR SERVICE INITIALIZED")
print(f" PORT: {PORT}")
print(" MONITORED DIRECTORIES:")
for alias, path in monitored_dirs.items():
    print(f"  - [{alias}]: {path}")
print("=" * 60)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    """
    Renders the responsive dark-mode Log Monitoring Dashboard.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Central Log Monitor Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-card: #151b2c;
            --bg-input: #1e293b;
            --border-color: #2e3c56;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --info: #06b6d4;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Header */
        header {
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            background-color: var(--success);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px var(--success);
        }
        
        /* Main Layout */
        .layout {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        /* Sidebar */
        aside {
            width: 320px;
            background-color: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }
        
        .file-list {
            list-style: none;
            padding: 8px;
        }
        
        .folder-node {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
            user-select: none;
            margin-top: 2px;
        }
        
        .folder-node:hover {
            background-color: rgba(255, 255, 255, 0.03);
        }
        
        .folder-arrow {
            display: inline-block;
            font-size: 0.65rem;
            color: var(--text-muted);
            transition: transform 0.2s;
        }
        
        .folder-children {
            display: flex;
            flex-direction: column;
            border-left: 1px dashed var(--border-color);
            margin-left: 18px;
        }
        
        .folder-children.hidden {
            display: none;
        }
        
        .file-item {
            padding: 8px 12px;
            margin-bottom: 2px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.825rem;
        }
        
        .file-item:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        .file-item.active {
            background-color: rgba(59, 130, 246, 0.15);
            color: var(--accent);
            font-weight: 500;
        }
        
        .file-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
        }
        
        .file-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            padding-left: 8px;
            flex-shrink: 0;
        }
        
        /* Main content */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--bg-main);
            overflow: hidden;
        }
        
        /* Toolbar */
        .toolbar {
            background-color: rgba(21, 27, 44, 0.6);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 24px;
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: center;
        }
        
        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .input-control {
            background-color: var(--bg-input);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 6px;
            outline: none;
            font-size: 0.875rem;
            transition: border-color 0.2s;
        }
        
        .input-control:focus {
            border-color: var(--accent);
        }
        
        select.input-control {
            padding-right: 28px;
            cursor: pointer;
        }
        
        .btn {
            background-color: var(--accent);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.875rem;
            transition: background-color 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .btn:hover {
            background-color: var(--accent-hover);
        }
        
        .btn-outline {
            background-color: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }
        
        .btn-outline:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Console log output */
        .console-container {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background-color: #05070f;
            display: flex;
            flex-direction: column;
        }
        
        .console-output {
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        /* Log highlighting colors */
        .log-line {
            padding: 2px 8px;
            border-radius: 4px;
            margin-bottom: 2px;
            transition: background-color 0.15s;
        }
        
        .log-line:hover {
            background-color: rgba(255, 255, 255, 0.03);
        }
        
        .log-info { color: #818cf8; }
        .log-success { color: var(--success); }
        .log-warning { color: var(--warning); background-color: rgba(245, 158, 11, 0.05); }
        .log-error { color: var(--danger); background-color: rgba(239, 68, 68, 0.08); font-weight: 500; }
        .log-critical { color: #ffffff; background-color: rgba(239, 68, 68, 0.4); font-weight: 600; }
        .log-debug { color: #6b7280; }
        
        /* Modal passcode setup */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 100;
            backdrop-filter: blur(8px);
        }
        
        .modal-content {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 32px;
            width: 400px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }
        
        .modal-title {
            font-size: 1.25rem;
            font-weight: 600;
            text-align: center;
        }
        
        .modal-subtitle {
            font-size: 0.875rem;
            color: var(--text-muted);
            text-align: center;
        }
        
        .hidden {
            display: none !important;
        }
        
        /* Switch/Toggle */
        .switch {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 22px;
        }
        
        .switch input { 
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--bg-input);
            transition: .3s;
            border-radius: 22px;
            border: 1px solid var(--border-color);
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 14px;
            width: 14px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: var(--accent);
        }
        
        input:checked + .slider:before {
            transform: translateX(22px);
        }
    </style>
</head>
<body>

    <!-- Passcode Modal -->
    <div id="passcodeModal" class="modal hidden">
        <div class="modal-content">
            <h2 class="modal-title">Enter Access Passcode</h2>
            <p class="modal-subtitle">Log viewer is secure. Provide the ADMIN_LOGS_PASSCODE to proceed.</p>
            <input type="password" id="passcodeInput" class="input-control" placeholder="Enter passcode..." style="text-align: center; font-size: 1.1rem; padding: 12px;">
            <button class="btn" onclick="savePasscode()" style="justify-content: center; padding: 12px;">Authenticate</button>
            <div id="authError" style="color: var(--danger); text-align: center; font-size: 0.85rem;" class="hidden">Invalid Passcode</div>
        </div>
    </div>

    <!-- Main App -->
    <header>
        <h1><span class="status-dot"></span> System Log Monitor</h1>
        <div style="display: flex; gap: 12px; align-items: center;">
            <div class="toolbar-group">
                <label for="folderSelect" style="font-size: 0.875rem; color: var(--text-muted); font-weight: 500;">Monitor Folder:</label>
                <select id="folderSelect" class="input-control" onchange="switchFolder()"></select>
            </div>
            <span id="currentPasscodeLabel" style="font-size: 0.85rem; color: var(--text-muted);"></span>
            <button class="btn btn-outline" onclick="logout()" style="padding: 6px 12px;">Change Passcode</button>
        </div>
    </header>
    
    <div class="layout">
        <!-- Sidebar -->
        <aside>
            <div class="sidebar-header">Log Files</div>
            <ul id="fileList" class="file-list">
                <!-- Log files dynamically loaded here -->
            </ul>
        </aside>
        
        <!-- Main Console -->
        <main>
            <div class="toolbar">
                <div class="toolbar-group">
                    <label for="lineLimit" style="font-size: 0.875rem; color: var(--text-muted);">Show lines:</label>
                    <select id="lineLimit" class="input-control" onchange="loadActiveLog()">
                        <option value="100">Last 100</option>
                        <option value="500" selected>Last 500</option>
                        <option value="1000">Last 1000</option>
                        <option value="5000">Last 5000</option>
                        <option value="">Full File</option>
                    </select>
                </div>
                
                <div class="toolbar-group">
                    <label class="switch">
                        <input type="checkbox" id="autoRefreshToggle" onchange="toggleAutoRefresh()">
                        <span class="slider"></span>
                    </label>
                    <span style="font-size: 0.875rem; color: var(--text-muted);">Auto-Refresh (3s)</span>
                </div>
                
                <div class="toolbar-group" style="flex: 1; min-width: 200px;">
                    <input type="text" id="searchInput" class="input-control" placeholder="Filter console output in real-time..." style="width: 100%;" oninput="filterConsole()">
                </div>
                
                <div class="toolbar-group">
                    <button class="btn btn-outline" onclick="loadActiveLog()">
                        Refresh Now
                    </button>
                    <button id="downloadBtn" class="btn" onclick="downloadActiveLog()" disabled>
                        Download File
                    </button>
                </div>
            </div>
            
            <div id="consoleContainer" class="console-container">
                <div id="consoleOutput" class="console-output">Select a log folder and file to begin...</div>
            </div>
        </main>
    </div>

    <script>
        let savedPasscode = localStorage.getItem("admin_logs_passcode") || "";
        let activeFolder = "";
        let activeFile = "";
        let autoRefreshInterval = null;
        let originalLogLines = [];

        window.onload = function() {
            if (!savedPasscode) {
                showModal();
            } else {
                document.getElementById("currentPasscodeLabel").innerText = "Key: ****";
                loadFolderList();
            }
        };

        function showModal() {
            document.getElementById("passcodeModal").classList.remove("hidden");
            document.getElementById("passcodeInput").focus();
        }

        function savePasscode() {
            const val = document.getElementById("passcodeInput").value.trim();
            if (val) {
                savedPasscode = val;
                localStorage.setItem("admin_logs_passcode", val);
                document.getElementById("passcodeModal").classList.add("hidden");
                document.getElementById("authError").classList.add("hidden");
                document.getElementById("currentPasscodeLabel").innerText = "Key: ****";
                loadFolderList();
            }
        }

        function logout() {
            localStorage.removeItem("admin_logs_passcode");
            savedPasscode = "";
            activeFolder = "";
            activeFile = "";
            if (autoRefreshInterval) clearInterval(autoRefreshInterval);
            document.getElementById("autoRefreshToggle").checked = false;
            document.getElementById("folderSelect").innerHTML = "";
            document.getElementById("fileList").innerHTML = "";
            document.getElementById("consoleOutput").innerText = "Select a log folder and file to begin...";
            document.getElementById("downloadBtn").disabled = true;
            showModal();
        }

        function handleApiError(res, status) {
            if (status === 401) {
                logout();
            } else {
                alert("Error loading data from server: " + (res.error || "Unknown error"));
            }
        }

        function loadFolderList() {
            fetch(`/api/folders?passcode=${encodeURIComponent(savedPasscode)}`)
                .then(res => {
                    if (!res.ok) {
                        if (res.status === 401) throw new Error("401");
                        return res.json().then(data => { throw new Error(data.error || "Error") });
                    }
                    return res.json();
                })
                .then(folders => {
                    const select = document.getElementById("folderSelect");
                    select.innerHTML = "";
                    
                    if (folders.length === 0) {
                        const opt = document.createElement("option");
                        opt.textContent = "No Monitored Folders";
                        select.appendChild(opt);
                        return;
                    }
                    
                    folders.forEach(folder => {
                        const opt = document.createElement("option");
                        opt.value = folder;
                        opt.textContent = folder;
                        select.appendChild(opt);
                    });
                    
                    activeFolder = folders[0];
                    loadFileList();
                })
                .catch(err => {
                    if (err.message === "401") {
                        handleApiError({}, 401);
                    } else {
                        alert("Failed to load monitored folders: " + err.message);
                    }
                });
        }

        function switchFolder() {
            activeFolder = document.getElementById("folderSelect").value;
            activeFile = "";
            document.getElementById("consoleOutput").innerText = "Select a log file from the sidebar to begin...";
            document.getElementById("downloadBtn").disabled = true;
            loadFileList();
        }

        function loadFileList() {
            if (!activeFolder) return;
            
            fetch(`/api/logs?passcode=${encodeURIComponent(savedPasscode)}&folder=${encodeURIComponent(activeFolder)}`)
                .then(res => {
                    if (!res.ok) {
                        if (res.status === 401) throw new Error("401");
                        return res.json().then(data => { throw new Error(data.error || "Error") });
                    }
                    return res.json();
                })
                .then(files => {
                    const list = document.getElementById("fileList");
                    list.innerHTML = "";
                    if (files.length === 0) {
                        list.innerHTML = '<li style="padding: 16px; color: var(--text-muted); font-size: 0.85rem; text-align: center;">No logs found</li>';
                        return;
                    }
                    
                    // Build folder tree structure
                    const root = { children: {}, files: [] };
                    files.forEach(file => {
                        const parts = file.name.split("/");
                        let current = root;
                        
                        // Navigate/create folders
                        for (let i = 0; i < parts.length - 1; i++) {
                            const folder = parts[i];
                            if (!current.children[folder]) {
                                current.children[folder] = { children: {}, files: [] };
                            }
                            current = current.children[folder];
                        }
                        
                        // Add file
                        const filename = parts[parts.length - 1];
                        current.files.push({
                            name: filename,
                            fullName: file.name,
                            size_bytes: file.size_bytes,
                            last_modified: file.last_modified
                        });
                    });
                    
                    // Render tree node
                    renderTreeNode(root, list, 0);
                })
                .catch(err => {
                    if (err.message === "401") {
                        handleApiError({}, 401);
                    } else {
                        alert("Failed to load logs list: " + err.message);
                    }
                });
        }

        function renderTreeNode(node, container, depth) {
            // Render directories sorted alphabetically
            Object.keys(node.children).sort().forEach(folderName => {
                const childNode = node.children[folderName];
                
                // Create folder header
                const folderDiv = document.createElement("div");
                folderDiv.className = "folder-node";
                folderDiv.style.paddingLeft = `${depth * 14 + 12}px`;
                
                const arrow = document.createElement("span");
                arrow.className = "folder-arrow";
                arrow.textContent = "▶";
                
                const icon = document.createElement("span");
                icon.textContent = "📁";
                
                const label = document.createElement("span");
                label.textContent = folderName;
                
                folderDiv.appendChild(arrow);
                folderDiv.appendChild(icon);
                folderDiv.appendChild(label);
                
                // Create children container
                const childrenContainer = document.createElement("div");
                childrenContainer.className = "folder-children hidden";
                
                // Click to expand/collapse
                folderDiv.onclick = (e) => {
                    e.stopPropagation();
                    const isHidden = childrenContainer.classList.toggle("hidden");
                    arrow.style.transform = isHidden ? "rotate(0deg)" : "rotate(90deg)";
                };
                
                container.appendChild(folderDiv);
                container.appendChild(childrenContainer);
                
                // Recursively render subdirectory children
                renderTreeNode(childNode, childrenContainer, depth + 1);
            });
            
            // Render files
            node.files.forEach(file => {
                const li = document.createElement("li");
                li.className = "file-item" + (activeFile === file.fullName ? " active" : "");
                li.style.paddingLeft = `${(depth + 1) * 14 + 12}px`;
                li.onclick = (e) => {
                    e.stopPropagation();
                    selectFile(file.fullName, li);
                };
                
                const sizeKB = (file.size_bytes / 1024).toFixed(1);
                
                li.innerHTML = `
                    <span class="file-name">📄 ${file.name}</span>
                    <span class="file-meta">${sizeKB} KB</span>
                `;
                container.appendChild(li);
            });
        }

        function selectFile(filename, element) {
            activeFile = filename;
            
            document.querySelectorAll(".file-item").forEach(item => item.classList.remove("active"));
            if (element) element.classList.add("active");
            
            document.getElementById("downloadBtn").disabled = false;
            loadActiveLog(true);
        }

        function loadActiveLog(shouldScroll = false) {
            if (!activeFolder || !activeFile) return;
            
            const lineLimit = document.getElementById("lineLimit").value;
            let url = `/api/logs?passcode=${encodeURIComponent(savedPasscode)}&folder=${encodeURIComponent(activeFolder)}&file=${encodeURIComponent(activeFile)}`;
            if (lineLimit) {
                url += `&lines=${lineLimit}`;
            }
            
            fetch(url)
                .then(res => {
                    if (!res.ok) {
                        if (res.status === 401) throw new Error("401");
                        return res.json().then(data => { throw new Error(data.error || "Error") });
                    }
                    return res.text();
                })
                .then(text => {
                    const rawLines = text.split("\\n");
                    originalLogLines = rawLines;
                    renderConsole(rawLines, shouldScroll);
                })
                .catch(err => {
                    if (err.message === "401") {
                        handleApiError({}, 401);
                    } else {
                        document.getElementById("consoleOutput").innerText = "Error: " + err.message;
                    }
                });
        }

        function renderConsole(lines, shouldScroll = false) {
            const out = document.getElementById("consoleOutput");
            out.innerHTML = "";
            
            const search = document.getElementById("searchInput").value.toLowerCase();
            const container = document.getElementById("consoleContainer");
            
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
            
            let matchedLinesCount = 0;
            
            lines.forEach(line => {
                if (search && !line.toLowerCase().includes(search)) return;
                matchedLinesCount++;
                
                const div = document.createElement("div");
                div.className = "log-line";
                div.textContent = line;
                
                const lineLower = line.toLowerCase();
                if (lineLower.includes(" | info     |") || lineLower.includes(" - info -") || lineLower.includes("info: ")) {
                    div.classList.add("log-info");
                } else if (lineLower.includes(" | warning  |") || lineLower.includes(" - warning -") || lineLower.includes("warning: ")) {
                    div.classList.add("log-warning");
                } else if (lineLower.includes(" | error    |") || lineLower.includes(" - error -") || lineLower.includes("error: ") || lineLower.includes("exception:")) {
                    div.classList.add("log-error");
                } else if (lineLower.includes(" | critical |") || lineLower.includes(" - critical -") || lineLower.includes("critical: ")) {
                    div.classList.add("log-critical");
                } else if (lineLower.includes(" | debug    |") || lineLower.includes(" - debug -") || lineLower.includes("debug: ")) {
                    div.classList.add("log-debug");
                } else if (lineLower.includes("success") || lineLower.includes("succeeded")) {
                    div.classList.add("log-success");
                }
                
                out.appendChild(div);
            });
            
            if (matchedLinesCount === 0 && lines.length > 0) {
                out.innerHTML = '<div style="color: var(--text-muted); font-style: italic; padding: 12px;">No lines match filter criteria.</div>';
            }
            
            if (shouldScroll || isNearBottom) {
                container.scrollTop = container.scrollHeight;
            }
        }

        function filterConsole() {
            renderConsole(originalLogLines, false);
        }

        function toggleAutoRefresh() {
            const toggle = document.getElementById("autoRefreshToggle");
            if (toggle.checked) {
                autoRefreshInterval = setInterval(() => {
                    loadActiveLog(false);
                    loadFileList(); // Refresh file list too in case of rotation/file size change
                }, 3000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }

        function downloadActiveLog() {
            if (!activeFolder || !activeFile) return;
            window.open(`/api/logs?passcode=${encodeURIComponent(savedPasscode)}&folder=${encodeURIComponent(activeFolder)}&file=${encodeURIComponent(activeFile)}&download=true`, '_blank');
        }
        
        document.getElementById("passcodeInput").addEventListener("keyup", function(event) {
            if (event.key === "Enter") {
                savePasscode();
            }
        });
    </script>
</body>
</html>"""
    response = make_response(html_content, 200)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.route("/api/folders")
def get_folders():
    """
    Returns lists of monitored folder aliases.
    """
    passcode = request.args.get("passcode")
    if not passcode or passcode != ADMIN_LOGS_PASSCODE:
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    return jsonify(list(monitored_dirs.keys()))

@app.route("/api/logs")
def get_logs():
    """
    Protected endpoint to list, view, or download logs.
    """
    # 1. Authorize
    passcode = request.args.get("passcode")
    if not passcode or passcode != ADMIN_LOGS_PASSCODE:
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    # 2. Get folder path
    folder_alias = request.args.get("folder")
    if not folder_alias or folder_alias not in monitored_dirs:
        return make_response(jsonify({"error": "Monitored folder not found or not specified"}), 400)
        
    log_dir = monitored_dirs[folder_alias]

    # 3. Check if reading a specific file
    filename = request.args.get("file")
    if not filename:
        # List files recursively in all subdirectories
        try:
            if not os.path.exists(log_dir):
                return make_response(jsonify([]), 200)
            
            files = []
            for root, dirs, filenames in os.walk(log_dir):
                for f in filenames:
                    file_path = os.path.join(root, f)
                    stat = os.stat(file_path)
                    # Get relative path from the base log directory
                    rel_path = os.path.relpath(file_path, log_dir)
                    # Normalize backslashes to forward slashes for URL safety
                    rel_path_clean = rel_path.replace("\\", "/")
                    files.append({
                        "name": rel_path_clean,
                        "size_bytes": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            # Sort files descending
            files.sort(key=lambda x: x["name"], reverse=False)
            return jsonify(files)
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to list logs: {str(e)}"}), 500)

    # 4. View or download a specific log file
    # Security: resolve path and verify it is inside log_dir to prevent directory traversal
    abs_log_dir = os.path.abspath(log_dir)
    file_path = os.path.abspath(os.path.join(abs_log_dir, filename))

    if not file_path.startswith(abs_log_dir):
        return make_response(jsonify({"error": "Unauthorized path access"}), 403)

    if not os.path.exists(file_path):
        return make_response(jsonify({"error": f"Log file '{filename}' not found"}), 404)

    # Download file as attachment
    download = request.args.get("download", "").lower() == "true"
    if download:
        try:
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to send file: {str(e)}"}), 500)

    # Reading/viewing contents
    try:
        lines_to_read = request.args.get("lines")
        if lines_to_read:
            lines_count = int(lines_to_read)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                last_lines = deque(f, maxlen=lines_count)
                content = "".join(last_lines)
        else:
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit for Web View
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    last_lines = deque(f, maxlen=5000)
                    content = "[File too large, showing last 5000 lines]\n\n" + "".join(last_lines)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

        response = make_response(content, 200)
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to read log file: {str(e)}"}), 500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)

logo = r"""                                                                            
                      ***  ********+********+*****                          
              ****   +**+++***++*+*+*+***+++*++*++++***+*  ******           
            ***++++*+**+*++*+*+*+*******++**+*++++****+*++*++****  ****     
          +*+*+****++*** ***  **  ***    ***   ****  +**+******+++*+****    
      ******+*+**+ *****          ****  ***     *****   **   +*++++*+*++**  
   ****+**+****                     *****         ****   **    ** **+++****+
  +*+++++* ***                                   ******  **    *******+***+*
   **++++***                *+*+         *            ****        ****+++*+ 
   **+*+*+                 *++++*      *++++                     *****+*+*  
     ****+**                *+++++     +++*      ++*            *****+**+** 
     ++*** **                ++++**    ++++    **+++*           *****+**+** 
      ++**+**        **+**    ++++*   +++*   *++++++              *******   
      **++***        *+++++*   ++++*  *++*  *+++++*               ***+**    
       **++*           *++++*** **++* *++* *++++**                +**++     
      **++*****          *+++++**++++**+***++++*                 **+*+**    
     ** +*++***             +*++++++++++++++++*       ***      **+++*+**    
     *** ***++*                *+*++++++++++++*+++++++++**    **++++**      
      ***+*+***   **++++++++*+****+++++++++++++++*****        *+++**+       
      *****+++***** ******+*+*+***+++++++++++***+++*+*        ++**+**       
           ***+*+***           +**++++++++++**++++++++++**    *****         
           ****+****        ***+****+*++++++++*   +++++++*   ***+**         
            ***+****     **++*** +***++**+++*++**           *+*++**         
             ****+**  *+*++**  **+** ++* *+++**+*+*         +*+*+**         
              *++**    ***    *++*   *+*  *+++* ++***    *********          
         ***** **++*        +*++*   *+**   **+++   *++  ********            
         ******+*+***      *+***    *++     **++*        *++****            
             *** **+**     ***     *+++       ***    **++*+*++              
              ****+++*+***         *+++              *******+**             
               ****+***+++***                        ***+******             
                   *++*****+**                       *++**+  **             
                      ****++**                   **++**+*  ****             
                        **+*+***             **+*+++***+*  ****             
                         *+*+++*             ++*+*++** *******              
                         **+***+**+****     **+*++**     *                  
                         +****++++++++***+*++++*+                           
                          ******* ***+**+*+***+**                           
                                   ***++****   ***                          
                                  **  *+++      **                          
                                  *   **      

_________ .__                   .___     ________          _____                  .___            
\_   ___ \|  | _____   __ __  __| _/____ \______ \   _____/ ____\____   ____    __| _/___________ 
/    \  \/|  | \__  \ |  |  \/ __ |/ __ \ |    |  \_/ __ \   __\/ __ \ /    \  / __ |/ __ \_  __ \
\     \___|  |__/ __ \|  |  / /_/ \  ___/ |    `   \  ___/|  | \  ___/|   |  \/ /_/ \  ___/|  | \/
 \______  /____(____  /____/\____ |\___  >_______  /\___  >__|  \___  >___|  /\____ |\___  >__|   
        \/          \/           \/    \/        \/     \/          \/     \/      \/    \/                                                                       
"""                                 



# from plyer import notification
from datetime import datetime
from pathlib import Path
from tkinter import ttk
import tkinter as tk
import subprocess
import threading
import argparse
import hashlib
import difflib
import json
import time
import sys
import os

# config paths
def get_config_path() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

def get_state_path() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Local" / "MCPMonitor" / "state.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MCPMonitor" / "state.json"
    else:
        return Path.home() / ".local" / "share" / "MCPMonitor" / "state.json"

def get_snapshots_path() -> Path:
    return get_state_path().parent / "snapshots"

##################
# hash

def file_hash(path: Path) -> str | None:
    # md5 just for easier reading not for security 
    if not path.exists():
        return None
    return hashlib.md5(path.read_bytes()).hexdigest()

def hash_directory(path: Path, extensions: set = None) -> dict[str, str]:
    if extensions is None:
        extensions = {'.py', '.js', '.ts', '.mjs', '.cjs', '.json', '.yaml', '.yml', '.sh', '.bat'}
    
    hashes = {}
    if not path.exists():
        return hashes
    
    try:
        for file in path.rglob('*'):
            if file.is_file() and file.suffix.lower() in extensions:
                if any(skip in file.parts for skip in ['node_modules', '__pycache__', '.git', 'venv', '.venv']):
                    continue
                rel_path = str(file.relative_to(path))
                hashes[rel_path] = file_hash(file)
    except Exception:
        pass
    
    return hashes

def get_server_paths(config_path: Path) -> dict[str, Path]:
    # check cmd for path otherwise use args
    servers = {}
    if not config_path.exists():
        return servers
    
    try:
        config = json.loads(config_path.read_text())
        mcp_servers = config.get("mcpServers", {})
        
        for name, server_config in mcp_servers.items():
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            
            server_path = None
            
            interpreters = ("python", "python3", "py", "node", "npx", "npm", "uvx", "uv")
            
            if command.lower() in interpreters or command.lower().endswith(interpreters):
                for arg in args:
                    if arg.startswith("-"):
                        continue
                    potential_path = Path(arg).expanduser()
                    if potential_path.exists():
                        server_path = potential_path
                        break
            else:
                potential_path = Path(command).expanduser()
                if potential_path.exists():
                    server_path = potential_path
            
            if server_path:
                servers[name] = {
                    "path": server_path,
                    "is_file": server_path.is_file()
                }
    except Exception:
        pass
    
    return servers

def hash_all_servers(config_path: Path) -> dict[str, dict[str, str]]:
    server_info = get_server_paths(config_path)
    all_hashes = {}
    
    for name, info in server_info.items():
        path = info["path"]
        is_file = info["is_file"]
        
        if is_file:
            h = file_hash(path)
            if h:
                all_hashes[name] = {path.name: h}
        else:
            all_hashes[name] = hash_directory(path)
    
    return all_hashes

def compare_server_hashes(old: dict, new: dict) -> dict[str, dict[str, list]]:
    changes = {}
    all_servers = set(old.keys()) | set(new.keys())

    for server in all_servers:
        old_files = old.get(server, {})
        new_files = new.get(server, {})
        
        added = [f for f in new_files if f not in old_files]
        removed = [f for f in old_files if f not in new_files]
        modified = [f for f in old_files if f in new_files and old_files[f] != new_files[f]]
        
        if added or removed or modified:
            changes[server] = {
                "added": added,
                "removed": removed,
                "modified": modified
            }
    
    return changes

##################
# states

def save_file_snapshot(server_name: str, file_path: str, content: str):
    snapshots_dir = get_snapshots_path()
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{server_name}_{file_path.replace('/', '_').replace(os.sep, '_')}"
    snapshot_file = snapshots_dir / f"{safe_name}.snapshot"
    snapshot_file.write_text(content, encoding='utf-8', errors='replace')

def get_file_snapshot(server_name: str, file_path: str) -> str | None:
    snapshots_dir = get_snapshots_path()
    safe_name = f"{server_name}_{file_path.replace('/', '_').replace(os.sep, '_')}"
    snapshot_file = snapshots_dir / f"{safe_name}.snapshot"
    if snapshot_file.exists():
        return snapshot_file.read_text(encoding='utf-8', errors='replace')
    return None

def save_all_snapshots(config_path: Path):
    server_info = get_server_paths(config_path)
    extensions = {'.py', '.js', '.ts', '.mjs', '.cjs', '.json', '.yaml', '.yml', '.sh', '.bat'}
    
    for server_name, info in server_info.items():
        path = info["path"]
        is_file = info["is_file"]
        
        if is_file:
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
                save_file_snapshot(server_name, path.name, content)
            except Exception:
                pass
        else:
            if not path.exists():
                continue
            try:
                for file in path.rglob('*'):
                    if file.is_file() and file.suffix.lower() in extensions:
                        if any(skip in file.parts for skip in ['node_modules', '__pycache__', '.git', 'venv', '.venv']):
                            continue
                        rel_path = str(file.relative_to(path))
                        content = file.read_text(encoding='utf-8', errors='replace')
                        save_file_snapshot(server_name, rel_path, content)
            except Exception:
                pass

def load_state() -> dict:
    state_path = get_state_path()
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {}

def save_state(state: dict):
    state_path = get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))

###################

def get_config_summary(path: Path) -> str:
    if not path.exists():
        return "no config"
    try:
        config = json.loads(path.read_text())
        servers = config.get("mcpServers", {})
        if not servers:
            return "no MCPS configured"
        return f"{len(servers)} server(s): {', '.join(servers.keys())}"
    except Exception as e:
        return f"{e}"

####################
# is claude running 

def is_claude_running() -> bool:
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq claude.exe"],
                capture_output=True, text=True
            )
            return "claude.exe" in result.stdout
        elif sys.platform == "darwin":
            result = subprocess.run(
                ["pgrep", "-x", "claude"],
                capture_output=True
            )
            return result.returncode == 0
        else:  # Linux
            result = subprocess.run(
                ["pgrep", "-f", "claude"],
                capture_output=True
            )
            return result.returncode == 0
    except Exception:
        return False

def wait_for_claude_startup(poll_interval: float = 1.0):
    print("Waiting for Claude Desktop to start...")
    was_running = is_claude_running()
    while True:
        running = is_claude_running()
        # detect fresh
        if running and not was_running:
            print("Claude Desktop started!")
            time.sleep(2)
            return True
        was_running = running
        time.sleep(poll_interval)

#####################

#####################
# overlay notification

def show_overlay(title: str, message: str, duration: int = 5000, changes: dict = None, config_path: Path = None):
    root = tk.Tk()
    root.title("ClaudeDefender")
    root.iconphoto(True, tk.PhotoImage(file="./logo.png"))
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    
    try:
        root.attributes("-alpha", 0.95)
    except:
        pass
    
    bg_color = "#3D1F20"
    text_color = "#F5A9A9"
    border_color = "#5C2A2B"
    btn_bg = "#5C2A2B"
    btn_hover = "#7C3A3B"
    root.configure(bg=bg_color)
    outer = tk.Frame(root, bg=border_color, padx=1, pady=1)
    outer.pack(fill="both", expand=True)
    frame = tk.Frame(outer, bg=bg_color, padx=16, pady=12)
    frame.pack(fill="both", expand=True)
    content = tk.Frame(frame, bg=bg_color)
    content.pack(side="left", fill="both", expand=True)
    
    icon_label = tk.Label(
        content,
        text="⚠",
        font=("Segoe UI", 12),
        fg=text_color,
        bg=bg_color
    )
    icon_label.pack(side="left", padx=(0, 10))
    
    text_frame = tk.Frame(content, bg=bg_color)
    text_frame.pack(side="left", fill="both", expand=True)
    full_text = f"{title}: {message}"

    msg_label = tk.Label(
        text_frame,
        text=full_text,
        font=("Segoe UI", 10),
        fg=text_color,
        bg=bg_color,
        wraplength=450,
        justify="left"
    )
    msg_label.pack(anchor="w")
    btn_frame = tk.Frame(frame, bg=bg_color)
    btn_frame.pack(side="right", padx=(10, 0))

    if changes:
        def on_enter(e):
            review_btn.config(bg=btn_hover)
        def on_leave(e):
            review_btn.config(bg=btn_bg)
        
        def open_review():
            root.destroy()
            show_diff_viewer(changes, config_path)
        
        review_btn = tk.Label(
            btn_frame,
            text="Review changes",
            font=("Segoe UI", 9),
            fg=text_color,
            bg=btn_bg,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        review_btn.pack(side="left", padx=(0, 10))
        review_btn.bind("<Button-1>", lambda e: open_review())
        review_btn.bind("<Enter>", on_enter)
        review_btn.bind("<Leave>", on_leave)
    
    close_btn = tk.Label(
        btn_frame,
        text="✕",
        font=("Segoe UI", 11),
        fg=text_color,
        bg=bg_color,
        cursor="hand2"
    )
    close_btn.pack(side="right")
    close_btn.bind("<Button-1>", lambda e: root.destroy())
    
    root.update_idletasks()
    width = root.winfo_reqwidth()
    screen_width = root.winfo_screenwidth()
    x = (screen_width - width) // 2
    y = 60
    root.geometry(f"+{x}+{y}")
    timeout = duration * 2 if changes else duration
    root.after(timeout, root.destroy)
    def start_drag(event):
        root._drag_x = event.x
        root._drag_y = event.y
    def do_drag(event):
        x = root.winfo_x() + event.x - root._drag_x
        y = root.winfo_y() + event.y - root._drag_y
        root.geometry(f"+{x}+{y}")
    
    frame.bind("<Button-1>", start_drag)
    frame.bind("<B1-Motion>", do_drag)
    
    root.mainloop()

# normal sys notification -- deprecated

# def show_notification(title: str, message: str):
#     """Show system notification as backup."""
#     try:
#         notification.notify(title=title, message=message, timeout=10)
#     except ImportError: # fallback to print
#         print(f"🔔 {title}: {message}")

#####################

#####################
# differ

def show_diff_viewer(changes: dict, config_path: Path):
    server_paths = get_server_paths(config_path) if config_path else {}
    root = tk.Tk()
    root.title("ClaudeDefender Review")
    root.geometry("900x600")
    root.configure(bg="#1E1E1E")
    bg_dark = "#1E1E1E"
    bg_medium = "#252526"
    text_color = "#D4D4D4"
    add_color = "#4EC9B0"
    remove_color = "#F14C4C"
    header_color = "#569CD6"
    
    main = tk.Frame(root, bg=bg_dark)
    main.pack(fill="both", expand=True, padx=10, pady=10)
    title = tk.Label(
        main,
        text="MCP config diff",
        font=("Segoe UI", 14, "bold"),
        fg=header_color,
        bg=bg_dark
    )
    title.pack(anchor="w", pady=(0, 10))

    style = ttk.Style()
    style.theme_use('default')
    style.configure('TNotebook', background=bg_dark, borderwidth=0)
    style.configure('TNotebook.Tab', background=bg_medium, foreground=text_color, padding=[10, 5])
    style.map('TNotebook.Tab', background=[('selected', bg_dark)])
    
    notebook = ttk.Notebook(main)
    notebook.pack(fill="both", expand=True)
    
    # changes tab
    if changes.get("config_changed"):
        config_frame = tk.Frame(notebook, bg=bg_dark)
        notebook.add(config_frame, text="Config File")
        
        config_text = tk.Text(
            config_frame,
            bg=bg_medium,
            fg=text_color,
            font=("Consolas", 10),
            wrap="none",
            borderwidth=0
        )
        config_text.pack(fill="both", expand=True)
        config_text.insert("1.0", "Config file (claude_desktop_config.json) was modified.\n\n")
        config_text.insert("end", f"Servers configured: {changes.get('config_summary', 'Unknown')}\n")
        config_text.config(state="disabled")
    
    # individual server tab
    server_changes = changes.get("server_changes", {})
    for server_name, file_changes in server_changes.items():
        server_frame = tk.Frame(notebook, bg=bg_dark)
        notebook.add(server_frame, text=f"📦 {server_name}")
        
        text_scroll = tk.Scrollbar(server_frame)
        text_scroll.pack(side="right", fill="y")
        
        h_scroll = tk.Scrollbar(server_frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        text_widget = tk.Text(
            server_frame,
            bg=bg_medium,
            fg=text_color,
            font=("Consolas", 10),
            wrap="none",
            yscrollcommand=text_scroll.set,
            xscrollcommand=h_scroll.set,
            borderwidth=0
        )
        text_widget.pack(fill="both", expand=True)
        text_scroll.config(command=text_widget.yview)
        h_scroll.config(command=text_widget.xview)
        
        text_widget.tag_configure("added", foreground=add_color)
        text_widget.tag_configure("removed", foreground=remove_color)
        text_widget.tag_configure("header", foreground=header_color, font=("Consolas", 10, "bold"))
        
        server_info = get_server_paths(config_path) if config_path else {}
        server_path = None
        is_single_file = False
        
        if server_name in server_info:
            server_path = server_info[server_name]["path"]
            is_single_file = server_info[server_name]["is_file"]
        
        for f in file_changes.get("added", []):
            text_widget.insert("end", f"\n+ ADDED: {f}\n", "added")
        for f in file_changes.get("removed", []):
            text_widget.insert("end", f"\n- REMOVED: {f}\n", "removed")
        for f in file_changes.get("modified", []):
            text_widget.insert("end", f"\n{'='*60}\n", "header")
            text_widget.insert("end", f"MODIFIED: {f}\n", "header")
            text_widget.insert("end", f"{'='*60}\n\n", "header")
            
            old_content = get_file_snapshot(server_name, f)
            new_content = None
            
            if server_path:
                if is_single_file:
                    # for single file servers ===> server_path IS the file
                    if f == server_path.name:
                        full_path = server_path
                    else:
                        full_path = server_path.parent / f
                else:
                    full_path = server_path / f
                    
                if full_path.exists():
                    try:
                        new_content = full_path.read_text(encoding='utf-8', errors='replace')
                    except:
                        pass
            
            if old_content and new_content:
                # gen diff
                diff = difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"old/{f}",
                    tofile=f"new/{f}",
                    lineterm=""
                )
                
                for line in diff:
                    if line.startswith('+') and not line.startswith('+++'):
                        text_widget.insert("end", line + "\n", "added")
                    elif line.startswith('-') and not line.startswith('---'):
                        text_widget.insert("end", line + "\n", "removed")
                    else:
                        text_widget.insert("end", line + "\n")
            else:
                text_widget.insert("end", "(Unable to generate diff - snapshot not available)\n")
        
        text_widget.config(state="disabled")
    
    close_btn = tk.Button(
        main,
        text="Close",
        font=("Segoe UI", 10),
        fg=text_color,
        bg=bg_medium,
        activebackground="#3E3E3E",
        activeforeground=text_color,
        bd=0,
        padx=20,
        pady=5,
        cursor="hand2",
        command=root.destroy
    )
    close_btn.pack(pady=(10, 0))
    
    root.mainloop()


#####################
# check for changes return summary based on detection

def check_for_changes() -> tuple[bool, str, dict]:
    config_path = get_config_path()
    current_config_hash = file_hash(config_path)
    summary = get_config_summary(config_path)
    current_server_hashes = hash_all_servers(config_path)
    
    state = load_state()
    last_config_hash = state.get("last_hash")
    last_server_hashes = state.get("server_hashes", {})
    
    config_changed = current_config_hash != last_config_hash
    server_changes = compare_server_hashes(last_server_hashes, current_server_hashes)
    
    any_changes = config_changed or bool(server_changes)
    changes_detail = {}
    if config_changed:
        changes_detail["config_changed"] = True
        changes_detail["config_summary"] = summary
    if server_changes:
        changes_detail["server_changes"] = server_changes
    messages = []
    if config_changed:
        messages.append("Config modified")
    if server_changes:
        modified_servers = list(server_changes.keys())
        messages.append(f"Code changed in: {', '.join(modified_servers)}")
    
    change_summary = " | ".join(messages) if messages else "No changes"
    
    # save snapshots BEFORE updating state (so we can diff later)
    # Only save if this isn't the first run
    if last_config_hash is not None:
        pass

    state["last_hash"] = current_config_hash
    state["last_check"] = datetime.now().isoformat()
    state["last_summary"] = summary
    state["server_hashes"] = current_server_hashes
    save_state(state)
    save_all_snapshots(config_path)
    
    return any_changes, change_summary, changes_detail


######################
######################

def main():
    parser = argparse.ArgumentParser(description="Monitor MCP config for Claude Desktop")
    parser.add_argument("--watch", action="store_true", help="Wait for Claude startup and monitor")
    parser.add_argument("--once", action="store_true", help="Check once immediately (default)")
    parser.add_argument("--overlay-test", action="store_true", help="Test the overlay window")
    parser.add_argument("--diff-test", action="store_true", help="Test the diff viewer")
    parser.add_argument("--duration", type=int, default=8000, help="Overlay duration in ms")
    # recommended to run once after install
    parser.add_argument("--init", action="store_true", help="Initialize snapshots without alerting")
    args = parser.parse_args()
    config_path = get_config_path()
    
    if args.overlay_test:
        show_overlay("MCP Config Changed", "This is a test notification overlay.", duration=args.duration)
        return

    config_path = get_config_path()
    print(f"Monitoring: {config_path}")
    
    if args.watch:
        while True:
            wait_for_claude_startup()
            changed, summary, changes_detail = check_for_changes()
            
            if changed:
                print(f"Changes detected: {summary}")
                show_overlay(
                    "MCP Changes Detected", 
                    summary,
                    args.duration,
                    changes=changes_detail,
                    config_path=config_path
                )
            else:
                print(f"No changes. {get_config_summary(config_path)}")
            
            while is_claude_running():
                time.sleep(2)
            print("Claude closed. Watching for next startup...")
    else:
        changed, summary, changes_detail = check_for_changes()
        if changed:
            print(f"Changes detected: {summary}")
            show_overlay(
                "MCP Changes Detected",
                summary,
                args.duration,
                changes=changes_detail,
                config_path=config_path
            )
        else:
            print(f"No changes. {get_config_summary(config_path)}")

if __name__ == "__main__":
    print(logo)
    main()
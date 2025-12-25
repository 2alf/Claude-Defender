# Claude Defender
<image src="./logo.png" width=300px>
<br>

```
MCP Config Monitor for Claude Desktop
```
Detects changes to Claude Desktop MCP config and server code. Shows overlay on startup.

---
## Content
- [Questions](#Qs)
- [Setup](#setup)
- [Usage](#usage)
- [License](#license)

---
## Qs

### Why?
Protect your Claude Desktop against becoming a trojanised entry point to attackers via toolpoisoning or similar techniques. 

*(Research paper about MCP as a LOTL soon..)*

### How?
Stores MD5 hashes of your config file and all server source files. On each Claude launch, compares current hashes against stored ones. If anything changed, shows an overlay notifying you of what changed and what should be audited.

### Bloat?
Watch mode:
- `~0.1% CPU, ~20MB RAM.` 
- Just sleeps and polls tasklist every second.

On check: 
- Brief spike reading files and computing hashes, then back to idle.

It's lighter than most system tray apps. <br> 
You won't notice it.

### Future?
- Add proper code audit with user accepting or reverting the changes.
- Same as above, but also being able to quarantine servers.
- Follow the `.log` installation trace that Claude Desktop provides for further Intrusion analasys
- Rewrite in rust?

---

## Setup
#### Windows
Add to Windows startup (`shell:startup`):
```bash
pythonw claudeDefender.py --watch
```

#### macOS
Create `~/Library/LaunchAgents/com.mcp.monitor.plist`:
```xml
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    Labelcom.mcp.monitor
    ProgramArguments
        python3
        /path/to/claudeDefender.py.py
        --watch
    RunAtLoad
```
Then: `launchctl load ~/Library/LaunchAgents/com.mcp.monitor.plist`

#### Linux
Create `~/.config/autostart/mcp-monitor.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=MCP Monitor
Exec=python3 /path/to/claudeDefender.py --watch
Hidden=false
```


## Usage
```bash
python claudeDefender.py           # Check once
python claudeDefender.py --watch   # Watch for Claude launches
```

## License
GPL-3.0 - requires derivative works to also be open source



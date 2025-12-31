#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use chrono::Utc;
use tauri::{Manager, Emitter, menu::{MenuBuilder, MenuItemBuilder}, tray::{TrayIconBuilder, TrayIconEvent}};
use tauri_plugin_autostart::ManagerExt;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FileState {
    hash: String,
    last_check: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct State {
    files: HashMap<String, FileState>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FileChange {
    name: String,
    path: String,
    old_content: String,
    new_content: String,
    diff: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPServer {
    command: Option<String>,
    args: Option<Vec<String>>,
    env: Option<HashMap<String, String>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPConfig {
    #[serde(rename = "mcpServers")]
    mcp_servers: Option<HashMap<String, MCPServer>>,
}

fn get_config_path() -> PathBuf {
    if cfg!(target_os = "windows") {
        dirs::config_dir()
            .unwrap()
            .join("Claude")
            .join("claude_desktop_config.json")
    } else if cfg!(target_os = "macos") {
        dirs::home_dir()
            .unwrap()
            .join("Library/Application Support/Claude/claude_desktop_config.json")
    } else {
        dirs::config_dir()
            .unwrap()
            .join("Claude/claude_desktop_config.json")
    }
}

fn get_state_dir() -> PathBuf {
    if cfg!(target_os = "windows") {
        dirs::data_local_dir().unwrap().join("MCPMonitor")
    } else if cfg!(target_os = "macos") {
        dirs::home_dir()
            .unwrap()
            .join("Library/Application Support/MCPMonitor")
    } else {
        dirs::data_local_dir().unwrap().join("MCPMonitor")
    }
}

fn file_hash(path: &PathBuf) -> Option<String> {
    if !path.exists() {
        return None;
    }
    match fs::read(path) {
        Ok(content) => Some(format!("{:x}", md5::compute(content))),
        Err(_) => None,
    }
}

fn get_server_paths(config_path: &PathBuf) -> Vec<(String, PathBuf)> {
    if !config_path.exists() {
        return vec![];
    }

    match fs::read_to_string(config_path) {
        Ok(content) => {
            match serde_json::from_str::<MCPConfig>(&content) {
                Ok(config) => {
                    let mut paths = vec![];
                    if let Some(servers) = config.mcp_servers {
                        for (name, server) in servers {
                            if let Some(cmd) = server.command {
                                let cmd_path = PathBuf::from(&cmd);
                                if cmd_path.exists() {
                                    paths.push((format!("Server: {}", name), cmd_path));
                                }
                            }
                        }
                    }
                    paths
                }
                Err(_) => vec![],
            }
        }
        Err(_) => vec![],
    }
}

fn generate_diff(old: &str, new: &str, filename: &str) -> String {
    let old_lines: Vec<&str> = old.lines().collect();
    let new_lines: Vec<&str> = new.lines().collect();

    let mut diff = String::new();
    diff.push_str(&format!("--- {} (previous)\n", filename));
    diff.push_str(&format!("+++ {} (current)\n", filename));

    for (i, (old_line, new_line)) in old_lines.iter().zip(new_lines.iter()).enumerate() {
        if old_line != new_line {
            diff.push_str(&format!("@@ Line {} @@\n", i + 1));
            diff.push_str(&format!("-{}\n", old_line));
            diff.push_str(&format!("+{}\n", new_line));
        }
    }

    if old_lines.len() > new_lines.len() {
        diff.push_str(&format!("@@ Lines {}-{} removed @@\n", new_lines.len() + 1, old_lines.len()));
        for line in &old_lines[new_lines.len()..] {
            diff.push_str(&format!("-{}\n", line));
        }
    } else if new_lines.len() > old_lines.len() {
        diff.push_str(&format!("@@ Lines {}-{} added @@\n", old_lines.len() + 1, new_lines.len()));
        for line in &new_lines[old_lines.len()..] {
            diff.push_str(&format!("+{}\n", line));
        }
    }

    diff
}

#[tauri::command]
fn check_changes() -> Result<Vec<FileChange>, String> {
    let config_path = get_config_path();
    let state_dir = get_state_dir();
    fs::create_dir_all(&state_dir).map_err(|e| e.to_string())?;

    let state_file = state_dir.join("state.json");
    let snapshots_dir = state_dir.join("snapshots");
    fs::create_dir_all(&snapshots_dir).map_err(|e| e.to_string())?;

    let mut state: State = if state_file.exists() {
        let content = fs::read_to_string(&state_file).map_err(|e| e.to_string())?;
        serde_json::from_str(&content).unwrap_or(State {
            files: HashMap::new(),
        })
    } else {
        State {
            files: HashMap::new(),
        }
    };

    let mut changes = vec![];
    let mut files_to_check = vec![("Config".to_string(), config_path.clone())];
    files_to_check.extend(get_server_paths(&config_path));

    for (name, path) in files_to_check {
        if !path.exists() {
            continue;
        }

        let current_hash = file_hash(&path).unwrap_or_default();
        let file_key = path.to_string_lossy().to_string();
        let old_hash = state
            .files
            .get(&file_key)
            .map(|s| s.hash.clone())
            .unwrap_or_default();

        if !old_hash.is_empty() && current_hash != old_hash {
            let snapshot_path = snapshots_dir.join(format!("{}.snapshot", path.file_name().unwrap().to_string_lossy()));

            if snapshot_path.exists() {
                let old_content = fs::read_to_string(&snapshot_path).unwrap_or_default();
                let new_content = fs::read_to_string(&path).unwrap_or_default();
                let diff = generate_diff(&old_content, &new_content, &path.file_name().unwrap().to_string_lossy());

                changes.push(FileChange {
                    name: name.clone(),
                    path: file_key.clone(),
                    old_content,
                    new_content: new_content.clone(),
                    diff,
                });
            }
        }

        state.files.insert(
            file_key.clone(),
            FileState {
                hash: current_hash,
                last_check: Utc::now().to_rfc3339(),
            },
        );

        let snapshot_path = snapshots_dir.join(format!("{}.snapshot", path.file_name().unwrap().to_string_lossy()));
        if let Ok(content) = fs::read_to_string(&path) {
            let _ = fs::write(snapshot_path, content);
        }
    }

    let state_json = serde_json::to_string_pretty(&state).map_err(|e| e.to_string())?;
    fs::write(state_file, state_json).map_err(|e| e.to_string())?;

    Ok(changes)
}

#[tauri::command]
fn revert_changes(changes: Vec<FileChange>) -> Result<(), String> {
    let state_dir = get_state_dir();
    let backup_dir = state_dir.join("backups");
    fs::create_dir_all(&backup_dir).map_err(|e| e.to_string())?;

    for change in changes {
        let path = PathBuf::from(&change.path);
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S").to_string();
        let backup_path = backup_dir.join(format!(
            "{}.{}.backup",
            path.file_name().unwrap().to_string_lossy(),
            timestamp
        ));
        fs::copy(&path, &backup_path).map_err(|e| e.to_string())?;
        fs::write(&path, change.old_content).map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[tauri::command]
fn accept_changes() -> Result<(), String> {
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--minimized"]),
        ))
        .setup(|app| {
///////////////////////
// tray
            let show_item = MenuItemBuilder::with_id("show", "Show").build(app)?;
            let check_item = MenuItemBuilder::with_id("check", "Check Now").build(app)?;
            let quit_item = MenuItemBuilder::with_id("quit", "Quit").build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&show_item)
                .item(&check_item)
                .separator()
                .item(&quit_item)
                .build()?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .icon(app.default_window_icon().unwrap().clone())
                .on_menu_event(|app, event| {
                    match event.id().as_ref() {
                        "quit" => {
                            app.exit(0);
                        }
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "check" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.emit("check-now", ());
                                let _ = window.show();
                            }
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { .. } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

////////////////////////
// AUTOSTART
            let autostart = app.autolaunch();
            let _ = autostart.enable();

            if let Some(window) = app.get_webview_window("main") {
                let window_clone = window.clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        window_clone.hide().unwrap();
                        api.prevent_close();
                    }
                });

                // Check args - show window if not minimized
                let args: Vec<String> = std::env::args().collect();
                if !args.contains(&"--minimized".to_string()) {
                    let _ = window.show();
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            check_changes,
            revert_changes,
            accept_changes
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

"""
cloudflared_multi_ui_ctk_clean.py
Clean CustomTkinter version for managing multiple Cloudflared tunnels,
with robust credentials-file detection when creating tunnels.

Requirements:
pip install customtkinter pyyaml
"""

import os
import subprocess
import threading
import time
import yaml
from glob import glob
import datetime
import shutil
import re
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ================= CONFIG ===================
DEFAULT_CF_DIR = os.path.expanduser(os.path.join("~", ".cloudflared"))
DEFAULT_TEMPLATE = """# Cloudflared tunnel config
tunnel: {tunnel_name}
credentials-file: {cred_path}

ingress:
  - hostname: {hostname}
    service: http://localhost:8080
  - service: http_status:404
"""

# ================= HELPERS ===================
def ensure_cf_dir():
    os.makedirs(DEFAULT_CF_DIR, exist_ok=True)

def find_cloudflared():
    exe = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    path = shutil.which(exe)
    if path:
        return path
    alt = os.path.join(DEFAULT_CF_DIR, exe)
    return alt if os.path.exists(alt) else None

def timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")

def newest_json_after(since_ts):
    """Return the newest .json file in DEFAULT_CF_DIR with mtime >= since_ts (epoch seconds), or None."""
    files = glob(os.path.join(DEFAULT_CF_DIR, "*.json"))
    files = sorted(files, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
    for f in files:
        try:
            m = os.path.getmtime(f)
            if m >= since_ts - 1:  # small tolerance
                return f
        except Exception:
            continue
    return None

# ================= MAIN APP ==================
class CloudflaredManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        ensure_cf_dir()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Cloudflared Multi-Tunnel Manager")
        self.geometry("1100x700")

        self.cf_path = find_cloudflared()
        self.processes = {}
        self.current_cfg = None

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(self.sidebar, text="Tunnels", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        self.listbox = ctk.CTkOptionMenu(self.sidebar, values=[], command=self.select_tunnel)
        self.listbox.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(self.sidebar, text="Add New", command=self.add_new).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Edit Config", command=self.edit_selected).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Delete", fg_color="red", command=self.delete_selected).pack(padx=10, pady=5, fill="x")

        ctk.CTkLabel(self.sidebar, text="Controls", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(20, 5))
        ctk.CTkButton(self.sidebar, text="Start Selected", command=self.start_selected).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Stop Selected", command=self.stop_selected).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Start All", command=self.start_all).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Stop All", fg_color="#e74c3c", command=self.stop_all).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Refresh", command=self.refresh_list).pack(padx=10, pady=(30, 5), fill="x")

        # Main panel
        self.main = ctk.CTkFrame(self, corner_radius=10)
        self.main.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.main, text=f"Cloudflared: {self.cf_path or '(not found)'}")
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.logbox = ctk.CTkTextbox(self.main, wrap="word", font=("Consolas", 11))
        self.logbox.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)
        self.logbox.insert("end", "[INFO] Ready.\n")

        # Định nghĩa tag màu cho terminal
        self.logbox.tag_config("info", foreground="#00bcd4")        # xanh dương nhạt
        self.logbox.tag_config("success", foreground="#4caf50")     # xanh lá
        self.logbox.tag_config("warn", foreground="#ffc107")        # vàng
        self.logbox.tag_config("error", foreground="#f44336")       # đỏ
        self.logbox.tag_config("gray", foreground="#9e9e9e")        # xám

        bottom = ctk.CTkFrame(self.main)
        bottom.grid(row=2, column=0, sticky="we", padx=10, pady=8)
        ctk.CTkButton(bottom, text="Save Logs", command=self.save_logs).pack(side="left", padx=6)
        ctk.CTkButton(bottom, text="Clear Logs", command=lambda: self.logbox.delete("1.0", "end")).pack(side="left", padx=6)
        ctk.CTkButton(bottom, text="Open Config Folder", command=self.open_folder).pack(side="left", padx=6)

        self.refresh_list()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # --------------- Utility ----------------
    def append_log(self, msg, level="info", tunnel=None):
        ts = timestamp()
        prefix = f"[{ts}] "
        if tunnel:
            prefix += f"[{os.path.basename(tunnel)}] "
        line = prefix + msg + "\n"

        # --- Tự nhận diện màu dựa trên nội dung ---
        lower = msg.lower()
        tag = "info"
        if level == "error" or any(k in lower for k in ["error", "failed", "exception", "denied"]):
            tag = "error"
        elif any(k in lower for k in ["warn", "warning"]):
            tag = "warn"
        elif any(k in lower for k in ["success", "connected", "started"]):
            tag = "success"
        elif any(k in lower for k in ["stopped", "disconnected", "exit"]):
            tag = "gray"

        self.logbox.insert("end", line, tag)
        self.logbox.see("end")

    def _cfg_files(self):
        return sorted(glob(os.path.join(DEFAULT_CF_DIR, "*.yml")) + glob(os.path.join(DEFAULT_CF_DIR, "*.yaml")))

    # --------------- Tunnel Ops ----------------
    def refresh_list(self):
        files = self._cfg_files()
        names = [os.path.basename(f) for f in files]
        self.listbox.configure(values=names if names else ["(no configs)"])
        if names:
            # keep current selection if exists
            if self.current_cfg and os.path.basename(self.current_cfg) in names:
                self.listbox.set(os.path.basename(self.current_cfg))
            else:
                self.listbox.set(names[0])
                self.current_cfg = os.path.join(DEFAULT_CF_DIR, names[0])
        else:
            self.current_cfg = None
        self.append_log(f"Found {len(names)} config(s).")

    def select_tunnel(self, value):
        if value == "(no configs)":
            self.current_cfg = None
            return
        self.current_cfg = os.path.join(DEFAULT_CF_DIR, value)
        self.append_log(f"Selected {value}")

    def add_new(self):
        # prompt name
        dlg = ctk.CTkInputDialog(title="Add New Tunnel", text="Enter tunnel name:")
        name = dlg.get_input()
        if not name:
            return

        # ensure cloudflared exists
        if not self.cf_path:
            messagebox.showerror("Error", "cloudflared binary not found in PATH.")
            return

        # record timestamp before create to detect new json
        t0 = time.time()
        self.append_log(f"Creating tunnel '{name}' ...")
        cmd = [self.cf_path, "tunnel", "create", name]
        try:
            # capture both stdout and stderr text
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            out = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
            self.append_log(out)
        except subprocess.CalledProcessError as e:
            out = (e.stdout or "") + ("\n" + (e.stderr or ""))
            self.append_log(f"Error creating tunnel: {out}", level="error")
            messagebox.showerror("Error", f"Cannot create tunnel:\n{out}")
            return
        except Exception as e:
            self.append_log(f"Failed to run cloudflared create: {e}", level="error")
            messagebox.showerror("Error", f"Failed to run cloudflared: {e}")
            return

        # Try parse credentials path from output
        cred_path = None
        # pattern: Tunnel credentials written to C:\Users\...\something.json
        m = re.search(r"Tunnel credentials written to (.+?\.json)", out)
        if m:
            candidate = m.group(1).strip()
            # sometimes cloudflared prints with quotes or trailing punctuation
            candidate = candidate.strip().strip("'\"")
            if os.path.exists(candidate):
                cred_path = candidate

        # If not parsed, try using "Created tunnel <name> with id <uuid>" to build uuid.json
        if not cred_path:
            m2 = re.search(r"Created tunnel .* with id ([0-9a-fA-F\-]+)", out)
            if m2:
                uuid = m2.group(1).strip()
                candidate2 = os.path.join(DEFAULT_CF_DIR, f"{uuid}.json")
                if os.path.exists(candidate2):
                    cred_path = candidate2

        # Fallback: find newest .json file modified after t0
        if not cred_path:
            cand = newest_json_after(t0)
            if cand:
                cred_path = cand

        if not cred_path:
            self.append_log("Could not locate credentials JSON after creating tunnel.", level="error")
            messagebox.showerror("Error", "Tunnel created but credentials file (.json) not found automatically. Please run 'cloudflared tunnel create' manually or place the credentials file in the config folder.")
            return

        # create YAML config file referencing cred_path
        cfg_path = os.path.join(DEFAULT_CF_DIR, f"config_{name}.yml")
        yaml_content = DEFAULT_TEMPLATE.format(tunnel_name=name, cred_path=cred_path, hostname=f"{name}.example.com")
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            self.append_log(f"Created config {cfg_path}")
            self.refresh_list()
            # open editor so user can edit ingress etc.
            self.open_editor(cfg_path)
        except Exception as e:
            self.append_log(f"Failed to write config: {e}", level="error")
            messagebox.showerror("Error", f"Failed to write config: {e}")

    def edit_selected(self):
        cfg = self.current_cfg
        if not cfg or not os.path.exists(cfg):
            messagebox.showinfo("Info", "Select a config first.")
            return
        self.open_editor(cfg)

    def open_editor(self, cfg):
        editor = ctk.CTkToplevel(self)
        editor.title(f"Edit: {os.path.basename(cfg)}")
        editor.geometry("800x600")

        text = ctk.CTkTextbox(editor, wrap="none", font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        with open(cfg, "r", encoding="utf-8") as f:
            text.insert("1.0", f.read())

        def save_changes():
            content = text.get("1.0", "end")
            try:
                yaml.safe_load(content)
            except Exception as e:
                messagebox.showerror("YAML Error", f"Invalid YAML:\n{e}")
                return
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(content)
            self.append_log(f"Saved {os.path.basename(cfg)}")
            editor.destroy()

        btn_frame = ctk.CTkFrame(editor)
        btn_frame.pack(fill="x", pady=6)
        ctk.CTkButton(btn_frame, text="Save", command=save_changes).pack(side="right", padx=6)
        ctk.CTkButton(btn_frame, text="Cancel", command=editor.destroy).pack(side="right", padx=6)

    def delete_selected(self):
        cfg = self.current_cfg
        if not cfg:
            messagebox.showinfo("Info", "Select a config first.")
            return
        if cfg in self.processes:
            messagebox.showerror("Error", "Stop the tunnel first.")
            return
        if messagebox.askyesno("Delete", f"Delete {os.path.basename(cfg)}?"):
            os.remove(cfg)
            self.append_log(f"Deleted {cfg}")
            self.refresh_list()

    # --------------- Run / Stop ----------------
    def _run_cf(self, cfg):
        if not self.cf_path:
            self.append_log("cloudflared not found.", level="error")
            return
        cmd = [self.cf_path, "--config", cfg, "tunnel", "run"]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except Exception as e:
            self.append_log(f"Failed to start process: {e}", level="error")
            return
        self.processes[cfg] = p
        threading.Thread(target=self._reader, args=(cfg, p), daemon=True).start()
        self.append_log(f"Started {os.path.basename(cfg)}")

    def _reader(self, cfg, proc):
        try:
            for line in proc.stdout:
                self.append_log(line.rstrip("\n"), tunnel=cfg)
        except Exception as e:
            self.append_log(f"Reader error: {e}", level="error", tunnel=cfg)
        finally:
            self.append_log(f"{os.path.basename(cfg)} stopped.", tunnel=cfg)
            self.processes.pop(cfg, None)

    def start_selected(self):
        cfg = self.current_cfg
        if not cfg or not os.path.exists(cfg):
            messagebox.showinfo("Info", "Select a config first.")
            return
        if cfg in self.processes:
            messagebox.showinfo("Info", "Already running.")
            return
        self._run_cf(cfg)

    def stop_selected(self):
        cfg = self.current_cfg
        if not cfg or cfg not in self.processes:
            messagebox.showinfo("Info", "Not running.")
            return
        try:
            self.processes[cfg].terminate()
        except Exception:
            pass
        self.append_log(f"Stopped {os.path.basename(cfg)}")
        self.processes.pop(cfg, None)

    def start_all(self):
        for f in self._cfg_files():
            if f not in self.processes:
                self._run_cf(f)
        self.append_log("Started all tunnels.")

    def stop_all(self):
        for f, p in list(self.processes.items()):
            try:
                p.terminate()
            except Exception:
                pass
            self.processes.pop(f, None)
            self.append_log(f"Stopped {os.path.basename(f)}")
        self.append_log("All tunnels stopped.")

    # --------------- Misc ----------------
    def save_logs(self):
        p = filedialog.asksaveasfilename(defaultextension=".log")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.logbox.get("1.0", "end"))
            self.append_log(f"Logs saved to {p}")

    def open_folder(self):
        if os.path.exists(DEFAULT_CF_DIR):
            if os.name == "nt":
                os.startfile(DEFAULT_CF_DIR)
            else:
                subprocess.Popen(["xdg-open", DEFAULT_CF_DIR])

    def on_close(self):
        if self.processes:
            self.stop_all()
        self.destroy()

# ============= RUN ==============
if __name__ == "__main__":
    app = CloudflaredManager()
    app.mainloop()

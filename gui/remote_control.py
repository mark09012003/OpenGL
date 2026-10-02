"""Master/slave configuration window and GUI integration."""
import secrets
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from gui.theme import Theme
from network_control import (MasterClient, SlaveControlServer,
                             local_ip_address, normalize_endpoint)


class RemoteControlMixin:
    def initialize_remote_control(self):
        self.remote_server = None
        self.remote_window = None
        self.control_config = {
            "mode": "standalone", "port": 8765, "token": "",
            "slaves": [],
        }

    def configure_remote_control(self, settings, persist=False):
        config = dict(self.control_config)
        config.update(settings or {})
        config["mode"] = config.get("mode", "standalone")
        config["port"] = int(config.get("port", 8765))
        config["token"] = str(config.get("token", "")).strip()
        config["slaves"] = [str(item).strip() for item in config.get("slaves", [])
                             if str(item).strip()]
        if config["mode"] not in ("standalone", "master", "slave"):
            raise ValueError("未知的控制模式")
        if not 1024 <= config["port"] <= 65535:
            raise ValueError("連接埠必須介於 1024 到 65535")
        if config["mode"] != "standalone" and len(config["token"]) < 12:
            raise ValueError("共享密鑰至少需要 12 個字元")
        for endpoint in config["slaves"]:
            normalize_endpoint(endpoint, config["port"])

        self.stop_remote_server()
        self.control_config = config
        if config["mode"] == "slave":
            server = SlaveControlServer(
                config["port"], config["token"], self.remote_status,
                self.receive_remote_command, logger=self.logger,
            )
            server.start()
            self.remote_server = server
            self.logger.info("Slave 控制服務已啟動：http://%s:%s",
                             local_ip_address(), config["port"])
        if persist:
            full_config = self.config_manager.load()
            full_config["control"] = dict(config)
            self.config_manager.save(full_config)

    def stop_remote_server(self):
        if self.remote_server is not None:
            self.remote_server.stop()
            self.remote_server = None

    def remote_status(self):
        return {
            "state": "running" if self.is_running else "stopped",
            "name": self.window_var.get() or "未選擇遊戲視窗",
        }

    def receive_remote_command(self, command):
        def execute():
            self.logger.info("收到 Master 遠端命令：%s", command.upper())
            if command == "start":
                self.start_automation()
            else:
                self.stop_automation()
        self.ui_queue.put(execute)

    def open_remote_control(self):
        if self.remote_window and self.remote_window.winfo_exists():
            self.remote_window.lift()
            return
        window = tk.Toplevel(self.root)
        self.remote_window = window
        window.title("Master / Slave 控制")
        window.geometry("620x570")
        window.minsize(560, 500)
        window.configure(bg=Theme.BACKGROUND_PRIMARY)
        window.transient(self.root)

        content = tk.Frame(window, bg=Theme.BACKGROUND_PRIMARY)
        content.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(content, text="MASTER / SLAVE", bg=Theme.BACKGROUND_PRIMARY,
                 fg=Theme.TEXT_HIGHLIGHT, font=(Theme.FONT_FAMILY, 16, "bold")).pack(anchor="w")
        tk.Label(content, text="區域網路遠端開始與停止控制",
                 bg=Theme.BACKGROUND_PRIMARY, fg=Theme.TEXT_SECONDARY,
                 font=(Theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(2, 14))

        form = tk.Frame(content, bg=Theme.BACKGROUND_SECONDARY,
                        highlightbackground=Theme.BORDER_PRIMARY, highlightthickness=1)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        mode_var = tk.StringVar(value=self.control_config["mode"])
        port_var = tk.StringVar(value=str(self.control_config["port"]))
        token_var = tk.StringVar(value=self.control_config["token"])

        def label(text, row):
            tk.Label(form, text=text, bg=Theme.BACKGROUND_SECONDARY,
                     fg=Theme.TEXT_SECONDARY, font=(Theme.FONT_FAMILY, 9)).grid(
                         row=row, column=0, sticky="w", padx=12, pady=8)
        label("本機模式", 0)
        mode_combo = ttk.Combobox(form, textvariable=mode_var, state="readonly",
                                  values=("standalone", "master", "slave"))
        mode_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=8)
        label("Slave 連接埠", 1)
        ttk.Entry(form, textvariable=port_var).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=8)
        label("共享密鑰", 2)
        token_row = tk.Frame(form, bg=Theme.BACKGROUND_SECONDARY)
        token_row.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=8)
        token_row.columnconfigure(0, weight=1)
        ttk.Entry(token_row, textvariable=token_var, show="●").grid(row=0, column=0, sticky="ew")
        ttk.Button(token_row, text="產生", command=lambda: token_var.set(secrets.token_urlsafe(24))).grid(row=0, column=1, padx=(7, 0))

        tk.Label(content, text="Slave 位址（Master 模式，每行一台）",
                 bg=Theme.BACKGROUND_PRIMARY, fg=Theme.TEXT_SECONDARY,
                 font=(Theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(14, 5))
        slaves_text = tk.Text(content, height=5, bg=Theme.INPUT_BACKGROUND,
                              fg=Theme.INPUT_TEXT, insertbackground=Theme.INPUT_CARET,
                              relief="flat", padx=8, pady=7,
                              font=(Theme.FONT_MONO, 9))
        slaves_text.pack(fill="x")
        slaves_text.insert("1.0", "\n".join(self.control_config["slaves"]))

        status = tk.Text(content, height=8, state="disabled", bg=Theme.LOG_BACKGROUND,
                         fg=Theme.LOG_TEXT, relief="flat", padx=8, pady=7,
                         font=(Theme.FONT_MONO, 9))
        status.pack(fill="both", expand=True, pady=(14, 10))

        def show_status(lines):
            status.config(state="normal")
            status.delete("1.0", "end")
            status.insert("1.0", "\n".join(lines))
            status.config(state="disabled")

        def values():
            return {
                "mode": mode_var.get(), "port": int(port_var.get()),
                "token": token_var.get().strip(),
                "slaves": [line.strip() for line in slaves_text.get("1.0", "end").splitlines()
                            if line.strip()],
            }

        def apply():
            try:
                self.configure_remote_control(values(), persist=True)
                if self.control_config["mode"] == "slave":
                    show_status([
                        f"SLAVE ONLINE  http://{local_ip_address()}:{self.control_config['port']}",
                        "等待 Master 自動探索...",
                    ])
                else:
                    show_status([f"模式已切換：{self.control_config['mode'].upper()}"])
            except (ValueError, OSError) as exc:
                messagebox.showerror("設定失敗", str(exc), parent=window)

        def run_master(command=None):
            try:
                pending = values()
                if pending["mode"] != "master":
                    raise ValueError("請先選擇 master 模式")
                self.configure_remote_control(pending, persist=True)
            except (ValueError, OSError) as exc:
                messagebox.showerror("設定失敗", str(exc), parent=window)
                return
            endpoints = list(self.control_config["slaves"])
            show_status(["正在連線..."])

            def worker():
                client = MasterClient(self.control_config["token"])
                lines = []
                for endpoint in endpoints:
                    try:
                        if command:
                            client.command(endpoint, command)
                        result = client.status(endpoint)
                        lines.append(f"{endpoint:<28} {result.get('state', 'unknown').upper()}")
                    except (ConnectionError, ValueError) as exc:
                        lines.append(f"{endpoint:<28} ERROR  {exc}")
                self.ui_queue.put(lambda: show_status(lines or ["尚未設定 Slave 位址"]))
            threading.Thread(target=worker, name="master-command", daemon=True).start()

        def discover_slaves():
            try:
                pending = values()
                pending["mode"] = "master"
                mode_var.set("master")
                self.configure_remote_control(pending, persist=True)
            except (ValueError, OSError) as exc:
                messagebox.showerror("探索失敗", str(exc), parent=window)
                return
            show_status(["正在透過區網廣播與 ARP 尋找 Slave..."])

            def worker():
                client = MasterClient(self.control_config["token"])
                found = client.discover(self.control_config["port"])
                endpoints = sorted(found)

                def update():
                    slaves_text.delete("1.0", "end")
                    slaves_text.insert("1.0", "\n".join(endpoints))
                    self.control_config["slaves"] = endpoints
                    full_config = self.config_manager.load()
                    full_config["control"] = dict(self.control_config)
                    self.config_manager.save(full_config)
                    show_status([
                        f"{endpoint:<28} {found[endpoint].get('state', 'unknown').upper()}"
                        for endpoint in endpoints
                    ] or ["未找到 Slave；請確認防火牆、連接埠與共享密鑰"])
                self.ui_queue.put(update)
            threading.Thread(target=worker, name="master-discovery", daemon=True).start()

        buttons = tk.Frame(content, bg=Theme.BACKGROUND_PRIMARY)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="套用設定", command=apply).pack(side="left")
        ttk.Button(buttons, text="自動尋找", command=discover_slaves).pack(side="left", padx=7)
        ttk.Button(buttons, text="重新整理", command=lambda: run_master()).pack(side="left")
        ttk.Button(buttons, text="全部開始", command=lambda: run_master("start")).pack(side="right")
        ttk.Button(buttons, text="全部停止", command=lambda: run_master("stop")).pack(side="right", padx=7)

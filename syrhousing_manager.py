#!/usr/bin/env python3
"""
SyrHousing Windows Manager
A GUI application to manage the SyrHousing backend server and discovery system.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import requests
import sys
import os
from datetime import datetime
import json

class SyrHousingManager:
    def __init__(self, root):
        self.root = root
        self.root.title("SyrHousing Manager")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Process tracking
        self.backend_process = None
        self.frontend_process = None
        self.is_running = False

        # Configuration
        self.backend_port = 8000
        self.frontend_port = 5173
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Setup UI
        self.setup_ui()

        # Start status checking thread
        self.check_status_thread = threading.Thread(target=self.status_checker, daemon=True)
        self.check_status_thread.start()

        # Auto-start option
        self.auto_start = tk.BooleanVar(value=True)
        if self.auto_start.get():
            self.root.after(1000, self.start_backend)

    def setup_ui(self):
        """Setup the user interface"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🏠 SyrHousing Manager",
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # Main content frame
        content_frame = tk.Frame(self.root, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Status Frame
        status_frame = tk.LabelFrame(content_frame, text="Server Status", font=("Arial", 12, "bold"), padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Backend status
        tk.Label(status_frame, text="Backend:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.backend_status_label = tk.Label(status_frame, text="●", font=("Arial", 16), fg="gray")
        self.backend_status_label.grid(row=0, column=1, padx=5)
        self.backend_text_label = tk.Label(status_frame, text="Stopped", font=("Arial", 10))
        self.backend_text_label.grid(row=0, column=2, sticky=tk.W)

        # Frontend status
        tk.Label(status_frame, text="Frontend:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.frontend_status_label = tk.Label(status_frame, text="●", font=("Arial", 16), fg="gray")
        self.frontend_status_label.grid(row=1, column=1, padx=5)
        self.frontend_text_label = tk.Label(status_frame, text="Stopped", font=("Arial", 10))
        self.frontend_text_label.grid(row=1, column=2, sticky=tk.W)

        # Discovery scheduler
        tk.Label(status_frame, text="Discovery:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.discovery_status_label = tk.Label(status_frame, text="●", font=("Arial", 16), fg="gray")
        self.discovery_status_label.grid(row=2, column=1, padx=5)
        self.discovery_text_label = tk.Label(status_frame, text="Inactive", font=("Arial", 10))
        self.discovery_text_label.grid(row=2, column=2, sticky=tk.W)

        # Control Buttons Frame
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Backend",
            command=self.start_backend,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame,
            text="⏹ Stop Backend",
            command=self.stop_backend,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.restart_button = tk.Button(
            button_frame,
            text="🔄 Restart",
            command=self.restart_backend,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)

        # Discovery Actions Frame
        discovery_frame = tk.LabelFrame(content_frame, text="Discovery Actions", font=("Arial", 12, "bold"), padx=10, pady=10)
        discovery_frame.pack(fill=tk.X, pady=10)

        self.run_discovery_button = tk.Button(
            discovery_frame,
            text="🔍 Run Discovery Now",
            command=self.run_discovery,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.run_discovery_button.pack(side=tk.LEFT, padx=5)

        self.view_stats_button = tk.Button(
            discovery_frame,
            text="📊 View Statistics",
            command=self.view_stats,
            bg="#16a085",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.view_stats_button.pack(side=tk.LEFT, padx=5)

        # Quick Access Frame
        access_frame = tk.LabelFrame(content_frame, text="Quick Access", font=("Arial", 12, "bold"), padx=10, pady=10)
        access_frame.pack(fill=tk.X, pady=10)

        tk.Button(
            access_frame,
            text="🌐 Open API Docs",
            command=lambda: self.open_url(f"http://localhost:{self.backend_port}/docs"),
            font=("Arial", 9),
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            access_frame,
            text="💻 Open Frontend",
            command=lambda: self.open_url(f"http://localhost:{self.frontend_port}"),
            font=("Arial", 9),
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            access_frame,
            text="📁 Open Project Folder",
            command=lambda: os.startfile(self.base_dir),
            font=("Arial", 9),
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # Log Frame
        log_frame = tk.LabelFrame(content_frame, text="Server Logs", font=("Arial", 12, "bold"), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=15,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Auto-start checkbox
        auto_start_cb = tk.Checkbutton(
            content_frame,
            text="Auto-start backend on launch",
            variable=self.auto_start,
            font=("Arial", 9)
        )
        auto_start_cb.pack(anchor=tk.W)

        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, message):
        """Add message to log window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.status_bar.config(text=message)

    def start_backend(self):
        """Start the backend server"""
        if self.backend_process:
            self.log("Backend is already running")
            return

        self.log("Starting backend server...")

        try:
            # Change to backend directory and start uvicorn
            backend_dir = os.path.join(self.base_dir, "backend")

            # Start backend process
            if sys.platform == "win32":
                self.backend_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(self.backend_port)],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.backend_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(self.backend_port)],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )

            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log("Backend server started!")

            # Start log reading thread
            threading.Thread(target=self.read_backend_logs, daemon=True).start()

        except Exception as e:
            self.log(f"Error starting backend: {e}")
            messagebox.showerror("Error", f"Failed to start backend:\n{e}")

    def stop_backend(self):
        """Stop the backend server"""
        if not self.backend_process:
            self.log("Backend is not running")
            return

        self.log("Stopping backend server...")

        try:
            self.backend_process.terminate()
            self.backend_process.wait(timeout=5)
            self.backend_process = None
            self.is_running = False

            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log("Backend server stopped")

        except Exception as e:
            self.log(f"Error stopping backend: {e}")
            try:
                self.backend_process.kill()
            except:
                pass

    def restart_backend(self):
        """Restart the backend server"""
        self.log("Restarting backend...")
        self.stop_backend()
        time.sleep(2)
        self.start_backend()

    def read_backend_logs(self):
        """Read backend logs in background thread"""
        if not self.backend_process:
            return

        for line in iter(self.backend_process.stdout.readline, b''):
            if not line:
                break
            try:
                log_line = line.decode('utf-8').strip()
                if log_line:
                    self.root.after(0, self.log, log_line)
            except:
                pass

    def status_checker(self):
        """Check server status periodically"""
        while True:
            try:
                # Check backend
                try:
                    response = requests.get(f"http://localhost:{self.backend_port}/api/health", timeout=2)
                    if response.status_code == 200:
                        self.root.after(0, self.update_backend_status, True)
                    else:
                        self.root.after(0, self.update_backend_status, False)
                except:
                    self.root.after(0, self.update_backend_status, False)

                time.sleep(5)
            except:
                break

    def update_backend_status(self, is_running):
        """Update backend status indicator"""
        if is_running:
            self.backend_status_label.config(fg="green")
            self.backend_text_label.config(text=f"Running (port {self.backend_port})")
            self.discovery_status_label.config(fg="green")
            self.discovery_text_label.config(text="Active (daily at 2 AM)")
        else:
            self.backend_status_label.config(fg="red" if self.is_running else "gray")
            self.backend_text_label.config(text="Stopped")
            self.discovery_status_label.config(fg="gray")
            self.discovery_text_label.config(text="Inactive")

    def run_discovery(self):
        """Run discovery manually"""
        self.log("Starting manual discovery run...")

        def run_in_thread():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "backend.scripts.run_discovery"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                self.root.after(0, self.log, "Discovery completed!")
                self.root.after(0, self.log, result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

                if result.returncode == 0:
                    self.root.after(0, messagebox.showinfo, "Success", "Discovery run completed successfully!")
                else:
                    self.root.after(0, messagebox.showwarning, "Warning", f"Discovery completed with errors.\nCheck logs for details.")

            except subprocess.TimeoutExpired:
                self.root.after(0, self.log, "Discovery run timed out")
                self.root.after(0, messagebox.showerror, "Timeout", "Discovery run took too long and was cancelled.")
            except Exception as e:
                self.root.after(0, self.log, f"Error running discovery: {e}")
                self.root.after(0, messagebox.showerror, "Error", f"Failed to run discovery:\n{e}")

        threading.Thread(target=run_in_thread, daemon=True).start()

    def view_stats(self):
        """View discovery statistics"""
        try:
            result = subprocess.run(
                [sys.executable, "check_status.py"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            stats_window = tk.Toplevel(self.root)
            stats_window.title("Discovery Statistics")
            stats_window.geometry("500x400")

            text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD, font=("Consolas", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text.insert(tk.END, result.stdout)
            text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load statistics:\n{e}")

    def open_url(self, url):
        """Open URL in default browser"""
        import webbrowser
        webbrowser.open(url)
        self.log(f"Opening {url}")

    def on_closing(self):
        """Handle window closing"""
        if self.backend_process:
            if messagebox.askokcancel("Quit", "Backend is running. Stop it and quit?"):
                self.stop_backend()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = SyrHousingManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

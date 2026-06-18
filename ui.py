import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
import time
import datetime
from PIL import Image, ImageTk
import automate2  # Imports your existing automation script

# Ensure we are in the correct directory so images and config load properly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

class AutoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 F Automation Control Panel")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f4f6f9")
        
        self.accounts = []
        self.stop_requested = False
        self.is_running = False
        self.thread = None
        
        # Modern UI styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#f4f6f9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[15, 5], background="#e1e4e8", foreground="#333")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#0056b3")])
        
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#0056b3", foreground="white", borderwidth=0)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="#ffffff", fieldbackground="#ffffff", borderwidth=0)
        style.map('Treeview', background=[('selected', '#cce5ff')], foreground=[('selected', '#000000')])
        
        self.load_accounts()
        self.build_ui()
        self.refresh_lists()

    def load_accounts(self):
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, "r") as f:
                    self.accounts = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load accounts: {e}")
        else:
            self.accounts = []

    def save_accounts(self):
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(self.accounts, f, indent=4)

    def build_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg="#0056b3", pady=15)
        header.pack(side=tk.TOP, fill=tk.X)
        
        title_lbl = tk.Label(header, text="FanDuel AutoBot Dashboard", font=("Segoe UI", 16, "bold"), bg="#0056b3", fg="white")
        title_lbl.pack(side=tk.LEFT, padx=20)

        # --- TOOLBAR ---
        toolbar = tk.Frame(self.root, bg="#ffffff", pady=10, padx=10, relief=tk.FLAT)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        btn_font = ("Segoe UI", 10, "bold")
        
        def create_btn(parent, text, cmd, bg_col, fg_col="black"):
            btn = tk.Button(parent, text=text, command=cmd, bg=bg_col, fg=fg_col, font=btn_font, 
                            relief=tk.FLAT, padx=15, pady=5, cursor="hand2")
            # Hover effects
            btn.bind("<Enter>", lambda e: btn.config(bg="#d1d5db" if bg_col == "#e2e8f0" else bg_col))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg_col))
            return btn

        create_btn(toolbar, "📁 Upload JSON", self.upload_json, "#e2e8f0").pack(side=tk.LEFT, padx=5)
        create_btn(toolbar, "➕ Add Account", self.add_account, "#e2e8f0").pack(side=tk.LEFT, padx=5)
        create_btn(toolbar, "⚙ Settings", self.open_settings, "#ffc107").pack(side=tk.LEFT, padx=5)
        
        separator = tk.Frame(toolbar, width=2, bg="#cbd5e1")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=2)
        
        create_btn(toolbar, "▶ Run Pending", self.run_pending, "#28a745", "white").pack(side=tk.LEFT, padx=5)
        create_btn(toolbar, "▶ Run Selected", self.run_selected, "#17a2b8", "white").pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = create_btn(toolbar, "🛑 STOP EVERYTHING", self.stop_automation, "#dc3545", "white")
        self.stop_btn.config(state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=10)
        
        # Status panel
        status_frame = tk.Frame(toolbar, bg="#ffffff")
        status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.status_lbl = tk.Label(status_frame, text="🟢 Idle", fg="#28a745", font=("Segoe UI", 11, "bold"), bg="#ffffff")
        self.status_lbl.pack(side=tk.TOP, anchor=tk.E)
        
        self.warning_lbl = tk.Label(status_frame, text="", fg="#dc3545", font=("Segoe UI", 9, "bold"), bg="#ffffff")
        self.warning_lbl.pack(side=tk.BOTTOM, anchor=tk.E)

        # --- TABS ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.tab_pending = ttk.Frame(self.notebook)
        self.tab_success = ttk.Frame(self.notebook)
        self.tab_created = ttk.Frame(self.notebook)
        self.tab_failed = ttk.Frame(self.notebook)
        
        self.tab_skipped = ttk.Frame(self.notebook)
        self.tab_another_account = ttk.Frame(self.notebook)
        self.tab_service_unavailable = ttk.Frame(self.notebook)
        self.tab_unable_to_verify = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_pending, text="  ⏳ Pending  ")
        self.notebook.add(self.tab_success, text="  ✅ Success  ")
        self.notebook.add(self.tab_created, text="  🌟 Created  ")
        self.notebook.add(self.tab_failed, text="  ❌ Failed  ")
        self.notebook.add(self.tab_skipped, text="  ⏭ Skipped  ")
        self.notebook.add(self.tab_another_account, text="  👥 Another Account  ")
        self.notebook.add(self.tab_service_unavailable, text="  ⚠️ Service Unavailable  ")
        self.notebook.add(self.tab_unable_to_verify, text="  ❓ Unable to Verify  ")
        
        # --- TREEVIEWS ---
        columns_pending = ("ID", "Email", "Username", "Status")
        columns_done = ("ID", "Email", "Username", "Time Ran", "Status")
        
        self.tree_pending = self.create_treeview(self.tab_pending, columns_pending)
        self.tree_success = self.create_treeview(self.tab_success, columns_done)
        self.tree_created = self.create_treeview(self.tab_created, columns_done)
        self.tree_failed = self.create_treeview(self.tab_failed, columns_done + ("Reason",))
        self.tree_skipped = self.create_treeview(self.tab_skipped, columns_done + ("Reason",))
        self.tree_another_account = self.create_treeview(self.tab_another_account, columns_done + ("Reason",))
        self.tree_service_unavailable = self.create_treeview(self.tab_service_unavailable, columns_done + ("Reason",))
        self.tree_unable_to_verify = self.create_treeview(self.tab_unable_to_verify, columns_done + ("Reason",))

    def create_treeview(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            tree.heading(col, text=col)
            if col == "ID":
                tree.column(col, width=50, anchor=tk.CENTER)
            elif col == "Status":
                tree.column(col, width=100, anchor=tk.CENTER)
            elif col == "Time Ran":
                tree.column(col, width=150, anchor=tk.CENTER)
            elif col == "Reason":
                tree.column(col, width=300)
            else:
                tree.column(col, width=200)
            
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Alternate row colors
        tree.tag_configure('evenrow', background='#f9fafb')
        tree.tag_configure('oddrow', background='#ffffff')
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Context menu (Right-click)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="✏ Edit Account", command=lambda: self.edit_account(tree))
        menu.add_command(label="🗑 Delete Account", command=lambda: self.delete_account(tree))
        menu.add_separator()
        menu.add_command(label="▶ Run This Account", command=lambda: self.run_single(tree))
        menu.add_command(label="🖼 View Screenshot", command=lambda: self.view_screenshot(tree))
        
        def show_menu(event):
            item = tree.identify_row(event.y)
            if item:
                if item not in tree.selection():
                    tree.selection_set(item)
                menu.post(event.x_root, event.y_root)
                
        tree.bind("<Button-3>", show_menu)
        tree.bind("<Double-1>", lambda e: self.view_screenshot(tree))
        return tree

    def refresh_lists(self):
        for tree in (self.tree_pending, self.tree_success, self.tree_created, self.tree_failed, self.tree_skipped, self.tree_another_account, self.tree_service_unavailable, self.tree_unable_to_verify):
            for item in tree.get_children():
                tree.delete(item)
                
        for idx, acc in enumerate(self.accounts):
            status = "Pending"
            timestamp = acc.get("timestamp", "-")
            if acc.get("skipped"):
                status = "Skipped"
            elif acc.get("unable_to_verify"):
                status = "Unable to Verify"
            elif acc.get("we_found_another_account"):
                status = "Another Account"
            elif acc.get("service_not_available"):
                status = "Service Unavailable"
            elif acc.get("ran"):
                if acc.get("created"):
                    status = "Created"
                else:
                    status = "Success" if acc.get("success") else "Failed"
                
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            
            if status == "Pending":
                self.tree_pending.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), status], tags=(tag,))
            elif status == "Success":
                self.tree_success.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status], tags=(tag,))
            elif status == "Created":
                self.tree_created.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status], tags=(tag,))
            elif status == "Failed":
                self.tree_failed.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status, acc.get("reason", "")], tags=(tag,))
            elif status == "Skipped":
                self.tree_skipped.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status, acc.get("reason", "")], tags=(tag,))
            elif status == "Another Account":
                self.tree_another_account.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status, acc.get("reason", "")], tags=(tag,))
            elif status == "Service Unavailable":
                self.tree_service_unavailable.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status, acc.get("reason", "")], tags=(tag,))
            elif status == "Unable to Verify":
                self.tree_unable_to_verify.insert("", tk.END, values=[idx, acc.get("email", ""), acc.get("username", ""), timestamp, status, acc.get("reason", "")], tags=(tag,))

    def open_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuration Settings")
        dialog.geometry("800x600")
        
        settings = automate2.load_settings()
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab_general = ttk.Frame(notebook)
        tab_referrals = ttk.Frame(notebook)
        tab_proxies = ttk.Frame(notebook)
        
        notebook.add(tab_general, text="General")
        notebook.add(tab_referrals, text="Referrals")
        notebook.add(tab_proxies, text="Proxies")
        
        # General Tab
        tk.Label(tab_general, text="Referral Mode:", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        mode_var = tk.StringVar(value=settings.get("referral_mode", "rotate"))
        modes = [
            ("Rotate (A -> B -> C -> A)", "rotate", "Runs accounts sequentially through all enabled referrals one by one."),
            ("Sequential 60 mins (One for 60m, then next)", "sequential_60m", "Sticks to one referral for 60 minutes, then switches to the next available one."),
            ("Random Mix (Random but equal distribution)", "random_mix", "Randomly selects a referral for each account, ensuring equal usage over 24 hours."),
            ("Percentage Allocation (Based on weights)", "percentage_allocation", "Allocates accounts to referrals based on the 'percentage' value set in the Referrals tab.")
        ]
        for text, val, desc in modes:
            tk.Radiobutton(tab_general, text=text, variable=mode_var, value=val).pack(anchor=tk.W, padx=20)
            tk.Label(tab_general, text=desc, font=("Segoe UI", 8), fg="#666666").pack(anchor=tk.W, padx=40, pady=(0, 10))
            
        tk.Frame(tab_general, height=2, bg="#cbd5e1").pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(tab_general, text="Edge Browser Path:", font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))
        tk.Label(tab_general, text=r"Example: C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", font=("Segoe UI", 8), fg="#666666").pack(anchor=tk.W, padx=40)
        
        edge_path_var = tk.StringVar(value=settings.get("edge_path", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"))
        tk.Entry(tab_general, textvariable=edge_path_var, width=70).pack(anchor=tk.W, padx=40, pady=(0, 10))
            
        # Referrals Tab
        ref_text = tk.Text(tab_referrals, height=20)
        ref_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ref_str = json.dumps(settings.get("referrals", []), indent=4)
        ref_text.insert(tk.END, ref_str)
        tk.Label(tab_referrals, text="Enter Referrals: Can be complex JSON, or a simple list like ['url1', 'url2'], or just one URL per line.").pack(pady=5)
        
        # Proxies Tab
        proxy_text = tk.Text(tab_proxies, height=20)
        proxy_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        proxy_str = json.dumps(settings.get("proxies", []), indent=4)
        proxy_text.insert(tk.END, proxy_str)
        tk.Label(tab_proxies, text="Enter Proxies: Can be complex JSON, or one proxy per line (host:port:user:pass).").pack(pady=5)
        
        def save_settings_ui():
            # Process Referrals
            ref_raw = ref_text.get("1.0", tk.END).strip()
            referrals = []
            if ref_raw:
                try:
                    # Try to parse as valid JSON first
                    parsed_ref = json.loads(ref_raw)
                    if isinstance(parsed_ref, list):
                        for item in parsed_ref:
                            if isinstance(item, dict):
                                referrals.append(item)
                            elif isinstance(item, str):
                                referrals.append({"url": item, "enabled": True, "percentage": 100})
                    else:
                        raise ValueError("Referrals JSON must be a list.")
                except Exception as e:
                    if '{' in ref_raw:
                        messagebox.showerror("Error", f"Referrals format is invalid. If mixing JSON and plain text, ensure it's a valid JSON array.\nError: {e}")
                        return
                    # Fallback to simple format parsing (e.g., ['url1'] or one URL per line)
                    import re
                    clean_ref = ref_raw.strip("[]")
                    items = re.split(r'[\n,]+', clean_ref)
                    for item in items:
                        item = item.strip().strip("'\"")
                        if item:
                            referrals.append({"url": item, "enabled": True, "percentage": 100})
            
            # Process Proxies
            proxy_raw = proxy_text.get("1.0", tk.END).strip()
            proxies = []
            if proxy_raw:
                try:
                    # Try to parse as valid JSON first
                    parsed_proxy = json.loads(proxy_raw)
                    if isinstance(parsed_proxy, list):
                        for item in parsed_proxy:
                            if isinstance(item, dict):
                                proxies.append(item)
                            elif isinstance(item, str):
                                parts = item.split(':', 3)
                                if len(parts) >= 4:
                                    proxies.append({
                                        "host": parts[0].strip(),
                                        "port": parts[1].strip(),
                                        "user": parts[2].strip(),
                                        "pass": parts[3].strip(),
                                        "last_use": 0
                                    })
                                else:
                                    raise ValueError(f"Invalid proxy format: {item}")
                    else:
                        raise ValueError("Proxies JSON must be a list.")
                except Exception as e:
                    if '{' in proxy_raw:
                        messagebox.showerror("Error", f"Proxies format is invalid. If mixing JSON and plain text, ensure it's a valid JSON array.\nError: {e}")
                        return
                    # Fallback to host:port:user:pass parsing
                    lines = proxy_raw.split('\n')
                    for line in lines:
                        line = line.strip().strip("[],'\"")
                        if not line: continue
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            proxies.append({
                                "host": parts[0].strip(),
                                "port": parts[1].strip(),
                                "user": parts[2].strip(),
                                "pass": parts[3].strip(),
                                "last_use": 0
                            })
                        else:
                            messagebox.showerror("Error", f"Invalid proxy format on line:\n{line}\nExpected host:port:user:pass")
                            return
                
            settings["referrals"] = referrals
            settings["proxies"] = proxies
            settings["referral_mode"] = mode_var.get()
            settings["edge_path"] = edge_path_var.get().strip()
            
            # Clean up old keys
            if "urls" in settings:
                del settings["urls"]
            
            automate2.save_settings(settings)
            messagebox.showinfo("Success", "Settings saved successfully.")
            dialog.destroy()
            
        tk.Button(dialog, text="Save Settings", command=save_settings_ui, bg="#28a745", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

    def upload_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    new_accs = json.load(f)
                    if isinstance(new_accs, dict):
                        new_accs = [new_accs]
                    if isinstance(new_accs, list):
                        self.accounts.extend(new_accs)
                        self.save_accounts()
                        self.refresh_lists()
                        messagebox.showinfo("Success", f"Appended {len(new_accs)} accounts.")
                    else:
                        messagebox.showerror("Error", "JSON must contain a list of accounts.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def get_selected_indices(self, tree):
        selected = tree.selection()
        return [int(tree.item(item, "values")[0]) for item in selected]

    def delete_account(self, tree):
        indices = self.get_selected_indices(tree)
        if not indices: return
        if messagebox.askyesno("Confirm", f"Delete {len(indices)} account(s)?"):
            # Delete in reverse order to keep indices intact during deletion
            for idx in sorted(indices, reverse=True):
                del self.accounts[idx]
            self.save_accounts()
            self.refresh_lists()

    def add_account(self):
        self.open_editor_dialog(None)

    def edit_account(self, tree):
        indices = self.get_selected_indices(tree)
        if indices:
            self.open_editor_dialog(indices[0])

    def open_editor_dialog(self, idx):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Account" if idx is not None else "Add Account")
        dialog.geometry("650x500")
        
        fields = [
            "email", "username", "password", "firstName", "middleName", "lastName", 
            "apt", "address", "city", "province", "postcode", "phone", "month", "day", "year", "referral_url"
        ]
        entries = {}
        acc_data = self.accounts[idx] if idx is not None else automate2.DEFAULT_CONFIG.copy()
        
        # Two-column layout
        for i, field in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            tk.Label(dialog, text=field.capitalize() + ":").grid(row=row, column=col, padx=10, pady=10, sticky=tk.E)
            ent = tk.Entry(dialog, width=25)
            ent.insert(0, str(acc_data.get(field, "")))
            ent.grid(row=row, column=col+1, padx=10, pady=10)
            entries[field] = ent
            
        def save(make_pending=False):
            for field, ent in entries.items():
                acc_data[field] = ent.get()
            
            if make_pending:
                acc_data["ran"] = False
                acc_data["success"] = False
                acc_data["reason"] = ""
                
            if idx is None:
                self.accounts.append(acc_data)
            else:
                self.accounts[idx] = acc_data
                
            self.save_accounts()
            self.refresh_lists()
            dialog.destroy()
            
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=len(fields)//2 + 1, column=0, columnspan=4, pady=20)
        
        tk.Button(btn_frame, text="Save", command=lambda: save(False), width=15).pack(side=tk.LEFT, padx=10)
        if idx is not None:
            tk.Button(btn_frame, text="Save & Reset to Pending", command=lambda: save(True), width=20).pack(side=tk.LEFT, padx=10)

    def view_screenshot(self, tree):
        indices = self.get_selected_indices(tree)
        if not indices: return
        acc = self.accounts[indices[0]]
        path = acc.get("screenshot")
        
        if path and os.path.exists(path):
            top = tk.Toplevel(self.root)
            top.title(f"Screenshot - {acc.get('email')}")
            try:
                img = Image.open(path)
                # Resize to fit screen reasonably
                img.thumbnail((900, 700))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(top, image=photo)
                lbl.image = photo
                lbl.pack()
            except Exception as e:
                messagebox.showerror("Error", f"Cannot load image: {e}")
        else:
            messagebox.showinfo("Not Found", "No screenshot available for this account.")

    def stop_automation(self):
        if self.is_running:
            self.stop_requested = True
            self.status_lbl.config(text="🛑 Stopping... Killing browser...", fg="#dc3545")
            
            # Kill the browser using automate2's helper function
            automate2.kill_browser()
            
            # Trigger PyAutoGUI's Failsafe to interrupt the running script immediately
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.moveTo(0, 0)
            except Exception:
                pass

    def run_pending(self):
        indices = [i for i, acc in enumerate(self.accounts) if not acc.get("ran")]
        self.start_runner(indices)

    def run_selected(self):
        # Only run selected items from the pending tab
        indices = self.get_selected_indices(self.tree_pending)
        if indices:
            self.start_runner(indices)
        else:
            messagebox.showinfo("Info", "Select accounts from the Pending tab (Ctrl+Click to select multiple).")

    def run_single(self, tree):
        indices = self.get_selected_indices(tree)
        if indices:
            self.start_runner([indices[0]])

    def start_runner(self, indices):
        if self.is_running:
            messagebox.showwarning("Warning", "Automation is already running!")
            return
        if not indices:
            messagebox.showinfo("Info", "No accounts to run.")
            return
            
        self.is_running = True
        self.stop_requested = False
        self.stop_btn.config(state=tk.NORMAL, bg="#dc3545", cursor="hand2")
        self.warning_lbl.config(text="⚠️ DO NOT TOUCH MOUSE/KEYBOARD!")
        
        # Run in background thread to keep UI responsive
        self.thread = threading.Thread(target=self.runner_thread, args=(indices,), daemon=True)
        self.thread.start()

    def runner_thread(self, indices):
        for i, idx in enumerate(indices):
            if self.stop_requested:
                break
                
            acc = self.accounts[idx]
            email = acc.get('email', 'Unknown')
            
            self.root.after(0, lambda e=email, c=i+1, t=len(indices): 
                            self.status_lbl.config(text=f"🔄 Validating: {e} ({c}/{t})", fg="#0056b3"))
            
            current_config = automate2.DEFAULT_CONFIG.copy()
            current_config.update(acc)
            
            is_valid, val_reason = automate2.validate_account(current_config)
            if not is_valid:
                acc["ran"] = True
                acc["success"] = False
                acc["skipped"] = True
                acc["reason"] = val_reason
                acc["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_accounts()
                self.root.after(0, self.refresh_lists)
                continue
                
            settings = automate2.load_settings()
            url, proxy, wait_time = automate2.get_next_url_and_proxy(settings, current_config)
            
            if wait_time > 0:
                for remaining in range(int(wait_time), 0, -1):
                    if self.stop_requested:
                        break
                    mins, secs = divmod(remaining, 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    self.root.after(0, lambda t=time_str: self.status_lbl.config(text=f"⏳ Proxy Cooldown: {t}", fg="#f39c12"))
                    time.sleep(1)
                    
            if self.stop_requested:
                break
                
            self.root.after(0, lambda e=email, c=i+1, t=len(indices): 
                            self.status_lbl.config(text=f"🔄 Running: {e} ({c}/{t})", fg="#0056b3"))
            
            first_name = automate2.clean_special_characters(current_config.get("firstName", "first"))
            last_name = automate2.clean_special_characters(current_config.get("lastName", "last"))
            current_config["username"] = f"{last_name}{first_name}{automate2.random.randint(1000, 9999)}"
            
            try:
                is_created, status = automate2.main(current_config, url, proxy)
                success = True
                created = bool(is_created)
                
                if status == "we_found_another_account":
                    reason = "We found another account"
                    screenshot_path = automate2.take_result_screenshot("we_found_another_account")
                elif status == "service_not_available":
                    reason = "Service not available"
                    screenshot_path = automate2.take_result_screenshot("service_not_available")
                elif status == "unable_to_verify":
                    reason = "Unable to verify data"
                    screenshot_path = automate2.take_result_screenshot("unable_to_verify")
                elif status == "success_not_created":
                    reason = "Finished without creating account (standard success fallback)."
                    screenshot_path = automate2.take_result_screenshot("success")
                else:
                    reason = "Successfully completed."
                    screenshot_path = automate2.take_result_screenshot("success")
            except Exception as e:
                if self.stop_requested:
                    self.root.after(0, lambda: self.status_lbl.config(text="🛑 Stopped by User", fg="#dc3545"))
                    break
                    
                success = False
                created = False
                reason = str(e)
                screenshot_path = automate2.take_result_screenshot("error")
                
            # import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update Account State
            acc["ran"] = True
            acc["success"] = success
            acc["created"] = created
            if "Account already exist" in reason:
                acc["skipped"] = True
                acc["success"] = False # Ensure it's not marked as success
            else:
                acc["skipped"] = False
                
            acc["we_found_another_account"] = ("We found another account" in reason)
            acc["service_not_available"] = ("Service not available" in reason)
            acc["unable_to_verify"] = ("Unable to verify" in reason)
            acc["reason"] = reason
            acc["screenshot"] = screenshot_path
            acc["timestamp"] = timestamp
            
            self.save_accounts()
            self.root.after(0, self.refresh_lists)
            
            # Close browser
            automate2.kill_browser()
            
            # Wait period between accounts
            if i < len(indices) - 1 and not self.stop_requested:
                settings = automate2.load_settings()
                proxies = settings.get("proxies", [])
                if len(proxies) <= 1:
                    wait_time_minutes = 10 if success else 11
                    total_seconds = wait_time_minutes * 60
                else:
                    total_seconds = 120 # Minimum 2 minutes buffer when multiple proxies exist
                
                # Custom wait loop with countdown display
                for remaining in range(total_seconds, 0, -1):
                    if self.stop_requested:
                        break
                    
                    mins, secs = divmod(remaining, 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    self.root.after(0, lambda t=time_str: self.status_lbl.config(text=f"⏳ Waiting for next account: {t}", fg="#f39c12"))
                    time.sleep(1)

        # Cleanup after loop finishes or stops
        self.is_running = False
        self.stop_requested = False
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED, bg="#e2e8f0", cursor="arrow"))
        self.root.after(0, lambda: self.warning_lbl.config(text=""))
        self.root.after(0, lambda: self.status_lbl.config(text="🟢 Idle", fg="#28a745"))
        self.root.after(0, lambda: messagebox.showinfo("Done", "Automation queue finished or was stopped."))

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoUI(root)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from pywizlight import discovery

class BulbFinderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WiZ Bulb Scanner")
        self.geometry("400x300")
        self.resizable(False, False)

        # Style
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))

        # Header
        ttk.Label(self, text="WiZ Bulb Discovery", font=("Arial", 14, "bold")).pack(pady=10)

        # Listbox for results
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.result_list = tk.Listbox(self.list_frame, font=("Courier", 10), height=8)
        self.result_list.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.result_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_list.config(yscrollcommand=scrollbar.set)
        
        self.result_list.bind('<<ListboxSelect>>', self.on_select)

        # Status
        self.status_var = tk.StringVar(value="Click Scan to start.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="gray")
        self.status_label.pack(pady=5)

        # Buttons
        self.btn_scan = ttk.Button(self, text="Scan Network", command=self.start_scan)
        self.btn_scan.pack(pady=10, fill="x", padx=50)

        ttk.Label(self, text="(Click a bulb to copy IP)", font=("Arial", 8)).pack(pady=(0, 10))

    def start_scan(self):
        self.btn_scan.config(state="disabled")
        self.status_var.set("Scanning... please wait...")
        self.result_list.delete(0, tk.END)
        
        # Run async scan in a separate thread
        threading.Thread(target=self.run_async_scan, daemon=True).start()

    def run_async_scan(self):
        asyncio.run(self._scan_task())

    async def _scan_task(self):
        try:
            bulbs = await discovery.discover_lights(broadcast_space="255.255.255.255")
            self.after(0, self.update_results, bulbs)
        except Exception as e:
            self.after(0, self.show_error, str(e))

    def update_results(self, bulbs):
        self.btn_scan.config(state="normal")
        if not bulbs:
            self.status_var.set("No bulbs found.")
            messagebox.showinfo("Result", "No WiZ bulbs found on this network.")
        else:
            self.status_var.set(f"Found {len(bulbs)} bulb(s).")
            for bulb in bulbs:
                self.result_list.insert(tk.END, f"{bulb.ip}  [{bulb.mac}]")

    def show_error(self, msg):
        self.btn_scan.config(state="normal")
        self.status_var.set("Error during scan.")
        messagebox.showerror("Scan Error", msg)

    def on_select(self, event):
        selection = self.result_list.curselection()
        if selection:
            data = self.result_list.get(selection[0])
            ip = data.split(" ")[0] # Extract IP
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(ip)
            self.update() # Keep clipboard after closure
            
            self.status_var.set(f"Copied: {ip}")

if __name__ == "__main__":
    app = BulbFinderApp()
    app.mainloop()

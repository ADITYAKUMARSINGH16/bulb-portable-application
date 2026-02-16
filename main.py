import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import mss
import numpy as np
import colorsys
from pywizlight import wizlight, PilotBuilder

# --- CONFIGURATION & GLOBALS ---
# Stability Fix: 10fps (0.1s) to prevent WiZ packet loss
UPDATE_INTERVAL = 0.1 
DEFAULT_IP = "192.168.29.140"

class BulbController:
    """Handles the async bulb communication and screen capture in a separate thread."""
    def __init__(self, status_callback, preview_callback):
        self.running = False
        self.ip = DEFAULT_IP
        self.status_callback = status_callback
        self.preview_callback = preview_callback
        self.monitor_area = None 
        self.loop = None
        self.thread = None
        self.color_mode = "Dominant" 
        
        # Features
        self.smooth_mode = True
        self.vibrant_mode = False 
        self.brightness_scale = 1.0 
        self.last_rgb = (0, 0, 0) 

    def start(self, ip):
        if self.running: return
        self.ip = ip
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.status_callback("Starting...", "orange")

    def stop(self):
        self.running = False
        self.status_callback("Stopping...", "orange")

    def set_area(self, area):
        self.monitor_area = area

    def set_mode(self, mode):
        self.color_mode = mode

    def set_brightness(self, val):
        self.brightness_scale = val

    def set_smoothing(self, enabled):
        self.smooth_mode = enabled

    def set_vibrant(self, enabled):
        self.vibrant_mode = enabled

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._sync_task())
        self.loop.close()

    async def _sync_task(self):
        self.status_callback(f"Connecting to {self.ip}...", "blue")
        try:
            light = wizlight(self.ip)
            self.status_callback("Connected! Syncing...", "green")
            
            with mss.mss() as sct:
                while self.running:
                    # Capture Region
                    if self.monitor_area:
                        capture_region = self.monitor_area
                    else:
                        capture_region = sct.monitors[1] 

                    # Capture & Downsample
                    sct_img = sct.grab(capture_region)
                    img_array = np.array(sct_img)[::15, ::15] 

                    r, g, b = 0, 0, 0

                    if self.color_mode == "Dominant":
                        pixels = img_array.reshape(-1, 4)[:, :3]
                        
                        # --- SMART FILTERING ---
                        # Filter out gray/dark pixels to avoid matching the background
                        # Convert to simple HSV-like check
                        # Saturation approx = (max - min) / max
                        # Value = max
                        p_max = np.max(pixels, axis=1)
                        p_min = np.min(pixels, axis=1)
                        
                        # Avoid division by zero
                        with np.errstate(divide='ignore', invalid='ignore'):
                            saturation = (p_max - p_min) / p_max
                            saturation[np.isnan(saturation)] = 0
                        
                        # Filter: Keep pixels with Sat > 15% AND Val > 15%
                        mask = (saturation > 0.15) & (p_max > 40)
                        filtered_pixels = pixels[mask]
                        
                        if len(filtered_pixels) > 0:
                            # Use filtered pixels
                            target_pixels = filtered_pixels
                        else:
                            # Fallback to all pixels if scene is entirely gray
                            target_pixels = pixels

                        # Quantize
                        target_pixels = (target_pixels // 8) * 8 
                        colors, counts = np.unique(target_pixels, axis=0, return_counts=True)
                        if len(counts) > 0:
                            dominant = colors[np.argmax(counts)]
                            b, g, r = int(dominant[0]), int(dominant[1]), int(dominant[2])

                    else: # Average
                        img_squared = img_array.astype(np.float64) ** 2
                        avg_squared = np.average(np.average(img_squared, axis=0), axis=0)
                        avg_color = np.sqrt(avg_squared)
                        b, g, r = int(avg_color[0]), int(avg_color[1]), int(avg_color[2])

                    # --- SMOOTHING ---
                    if self.smooth_mode:
                        alpha = 0.4 
                        r = int(self.last_rgb[0] * (1-alpha) + r * alpha)
                        g = int(self.last_rgb[1] * (1-alpha) + g * alpha)
                        b = int(self.last_rgb[2] * (1-alpha) + b * alpha)
                        self.last_rgb = (r, g, b)
                    # -----------------

                    # --- COLOR LOGIC ---
                    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                    
                    brightness_cmd = 255
                    
                    # Black Threshold
                    if v < 0.08:
                        r, g, b = 0, 0, 0
                        brightness_cmd = 0
                    else:
                        # Saturation Boost
                        boost = 2.0 if self.vibrant_mode else 1.2
                        s = min(1.0, s * boost) 
                        
                        # Auto-boost V
                        if v > 0.15: v = 1.0
                        
                        # Apply slider scaling
                        v = v * self.brightness_scale
                        brightness_cmd = int(255 * self.brightness_scale)
                        
                        r_f, g_f, b_f = colorsys.hsv_to_rgb(h, s, v)
                        r, g, b = int(r_f*255), int(g_f*255), int(b_f*255)
                    # -------------------

                    # Update Preview
                    hex_color = f'#{r:02x}{g:02x}{b:02x}'
                    self.preview_callback(hex_color)

                    # Send to Bulb
                    # Stability Fix: Speed roughly matches update interval (100-150ms)
                    speed_ms = 150 if self.smooth_mode else 120
                    
                    await light.turn_on(
                        PilotBuilder(rgb=(r, g, b), brightness=brightness_cmd, speed=speed_ms)
                    )

                    await asyncio.sleep(UPDATE_INTERVAL)
            
            await light.turn_off()
            self.status_callback("Stopped.", "red")

        except Exception as e:
            self.status_callback(f"Error: {e}", "red")
            self.running = False


class AreaSelector(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.attributes('-alpha', 0.3)
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.configure(bg='black')
        self.state('zoomed')

        self.canvas = tk.Canvas(self, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())
        
        messagebox.showinfo("Select Area", "Drag to select area. ESC to cancel.")

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2, fill="white")

    def on_drag(self, event):
        if self.start_x is None: return 
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.start_x is None:
            self.destroy()
            return

        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        width = x2 - x1
        height = y2 - y1

        if width > 10 and height > 10:
            area = {"top": y1, "left": x1, "width": width, "height": height}
            self.callback(area)
        
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WiZ Bulb Sync - Stable")
        self.geometry("350x600")
        self.resizable(False, False)

        self.controller = BulbController(self.update_status, self.update_preview)

        # UI Components
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(main_frame, text="Bulb Control", font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="black")
        self.status_label.pack(pady=5)

        # Preview
        self.preview_frame = tk.Frame(main_frame, bg="black", height=80, width=80, relief="sunken", bd=2)
        self.preview_frame.pack(pady=5)

        # IP Address
        ttk.Label(main_frame, text="Bulb IP:").pack(anchor="w")
        self.ip_var = tk.StringVar(value=DEFAULT_IP)
        self.ip_entry = ttk.Entry(main_frame, textvariable=self.ip_var)
        self.ip_entry.pack(fill="x", pady=(0, 5))

        # Color Mode
        ttk.Label(main_frame, text="Color Logic:").pack(anchor="w")
        self.mode_var = tk.StringVar(value="Dominant")
        self.mode_combo = ttk.Combobox(main_frame, textvariable=self.mode_var, values=["Dominant", "Average"], state="readonly")
        self.mode_combo.pack(fill="x", pady=(0, 10))
        self.mode_combo.bind("<<ComboboxSelected>>", self.change_mode)

        # Brightness Slider
        ttk.Label(main_frame, text="Master Brightness:").pack(anchor="w")
        self.bright_var = tk.DoubleVar(value=1.0)
        self.bright_scale = ttk.Scale(main_frame, from_=0.0, to=1.0, variable=self.bright_var, command=self.update_brightness)
        self.bright_scale.pack(fill="x", pady=(0, 10))

        # Checkboxes
        self.smooth_var = tk.BooleanVar(value=True)
        self.smooth_chk = ttk.Checkbutton(main_frame, text="Silky Smooth Mode", variable=self.smooth_var, command=self.toggle_smooth)
        self.smooth_chk.pack(anchor="w", pady=(0, 5))

        self.vibrant_var = tk.BooleanVar(value=False)
        self.vibrant_chk = ttk.Checkbutton(main_frame, text="Vibrant Colors (Boost)", variable=self.vibrant_var, command=self.toggle_vibrant)
        self.vibrant_chk.pack(anchor="w", pady=(0, 15))

        # Buttons
        self.btn_start = ttk.Button(main_frame, text="Start Sync", command=self.toggle_sync)
        self.btn_start.pack(fill="x", pady=5)

        self.btn_area = ttk.Button(main_frame, text="Select Screen Area", command=self.select_area)
        self.btn_area.pack(fill="x", pady=5)
        
        self.btn_reset = ttk.Button(main_frame, text="Reset to Full Screen", command=self.reset_area)
        self.btn_reset.pack(fill="x", pady=5)

        self.area_label = ttk.Label(main_frame, text="Area: Full Screen", font=("Arial", 8))
        self.area_label.pack(pady=5)

        # Footer
        ttk.Label(main_frame, text="Created by Aditya Kumar Singh", font=("Arial", 7), foreground="gray").pack(side="bottom", pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def change_mode(self, event):
        self.controller.set_mode(self.mode_var.get())

    def update_brightness(self, val):
        self.controller.set_brightness(float(val))

    def toggle_smooth(self):
        self.controller.set_smoothing(self.smooth_var.get())

    def toggle_vibrant(self):
        self.controller.set_vibrant(self.vibrant_var.get())

    def toggle_sync(self):
        if self.controller.running:
            self.controller.stop()
            self.btn_start.configure(text="Start Sync")
        else:
            self.controller.start(self.ip_var.get())
            self.btn_start.configure(text="Stop Sync")

    def select_area(self):
        self.withdraw() # Hide main app
        AreaSelector(self, self.set_capture_area)
        
    def set_capture_area(self, area):
        self.deiconify() # Show main app
        self.controller.set_area(area)
        self.area_label.configure(text=f"Area: {area['width']}x{area['height']} at ({area['left']},{area['top']})")

    def reset_area(self):
        self.controller.set_area(None)
        self.area_label.configure(text="Area: Full Screen")

    def update_status(self, text, color):
        self.status_var.set(text)
        self.status_label.configure(foreground=color)

    def update_preview(self, hex_color):
        try:
            self.preview_frame.configure(bg=hex_color)
        except:
            pass

    def on_close(self):
        if self.controller.running:
            self.controller.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
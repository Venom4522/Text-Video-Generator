import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, colorchooser
import threading
import queue
import logging  # <-- THE FIX IS HERE
import main     # Import the main script logic

# --- Logger for GUI ---
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quote Video Generator")
        self.geometry("800x600")

        # --- Main Layout ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # --- Left Panel: Controls ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.grid(row=0, column=0, sticky="ew", columnspan=2, pady=(0, 10))
        
        self.generate_button = ttk.Button(controls_frame, text="Select File & Generate Videos", command=self.start_generation_thread)
        self.generate_button.pack(fill=tk.X, expand=True)

        # --- Middle Panel: Customization ---
        custom_frame = ttk.LabelFrame(main_frame, text="Customization", padding="10")
        custom_frame.grid(row=1, column=0, sticky="ns", padx=(0, 10))

        # Video Duration
        ttk.Label(custom_frame, text="Video Duration (s):").grid(row=0, column=0, sticky="w", pady=2)
        self.duration_var = tk.StringVar(value="5")
        ttk.Spinbox(custom_frame, from_=1, to=300, textvariable=self.duration_var, width=10).grid(row=0, column=1, sticky="ew", pady=2)

        # Font Size
        ttk.Label(custom_frame, text="Font Size:").grid(row=1, column=0, sticky="w", pady=2)
        self.font_size_var = tk.StringVar(value="70")
        ttk.Spinbox(custom_frame, from_=10, to=300, textvariable=self.font_size_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)

        # Text Alignment
        ttk.Label(custom_frame, text="Text Align:").grid(row=2, column=0, sticky="w", pady=2)
        self.align_var = tk.StringVar(value="center")
        ttk.Combobox(custom_frame, textvariable=self.align_var, values=["left", "center", "right"], width=10).grid(row=2, column=1, sticky="ew", pady=2)

        # Vertical Position
        ttk.Label(custom_frame, text="Vertical Pos:").grid(row=3, column=0, sticky="w", pady=2)
        self.v_pos_var = tk.StringVar(value="middle")
        ttk.Combobox(custom_frame, textvariable=self.v_pos_var, values=["top", "middle", "bottom"], width=10).grid(row=3, column=1, sticky="ew", pady=2)

        # Font Color
        self.font_color_var = tk.StringVar(value="#FFFFFF")
        ttk.Button(custom_frame, text="Font Color", command=self.pick_font_color).grid(row=4, column=0, sticky="ew", pady=5)
        self.font_color_preview = tk.Label(custom_frame, text="", bg=self.font_color_var.get(), width=4)
        self.font_color_preview.grid(row=4, column=1)

        # Background Color
        self.bg_color_var = tk.StringVar(value="#000000")
        ttk.Button(custom_frame, text="Background Color", command=self.pick_bg_color).grid(row=5, column=0, sticky="ew", pady=5)
        self.bg_color_preview = tk.Label(custom_frame, text="", bg=self.bg_color_var.get(), width=4)
        self.bg_color_preview.grid(row=5, column=1)
        
        # --- Right Panel: Logging ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=1, column=1, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, bg="#2b2b2b", fg="#d3d3d3")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # --- Setup Logging ---
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(self.queue_handler)

        self.after(100, self.poll_log_queue)

    def pick_font_color(self):
        color_code = colorchooser.askcolor(title="Choose Font Color", initialcolor=self.font_color_var.get())
        if color_code and color_code[1]:
            self.font_color_var.set(color_code[1])
            self.font_color_preview.config(bg=color_code[1])

    def pick_bg_color(self):
        color_code = colorchooser.askcolor(title="Choose Background Color", initialcolor=self.bg_color_var.get())
        if color_code and color_code[1]:
            self.bg_color_var.set(color_code[1])
            self.bg_color_preview.config(bg=color_code[1])

    def poll_log_queue(self):
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display_log_message(record)
        self.after(100, self.poll_log_queue)

    def display_log_message(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + '\n')
        self.log_area.config(state='disabled')
        self.log_area.yview(tk.END)
    
    def get_custom_config(self):
        """Gathers all settings from the GUI controls."""
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        return {
            'video': {
                'duration': int(self.duration_var.get()),
                'background_color': hex_to_rgb(self.bg_color_var.get())
            },
            'text': {
                'font_size': int(self.font_size_var.get()),
                'font_color': hex_to_rgb(self.font_color_var.get()),
                'text_align': self.align_var.get(),
                'vertical_pos': self.v_pos_var.get()
            }
        }

    def start_generation_thread(self):
        quotes_path = filedialog.askopenfilename(
            title="Select Quotes File",
            filetypes=(("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not quotes_path:
            return

        self.generate_button.config(state='disabled')
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        custom_config = self.get_custom_config()

        self.thread = threading.Thread(
            target=main.run_video_generation,
            args=(quotes_path, custom_config)
        )
        self.thread.daemon = True
        self.thread.start()
        self.after(100, self.check_thread)

    def check_thread(self):
        if self.thread.is_alive():
            self.after(100, self.check_thread)
        else:
            self.generate_button.config(state='normal')

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()


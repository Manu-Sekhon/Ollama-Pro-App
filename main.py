import customtkinter as ctk
import requests
import threading
import json
import os
import time
import psutil
try:
    from pynvml import *
    nvml_available = True
except:
    nvml_available = False

# Configuration & Theme
DATA_FILE = os.path.expanduser("~/.ollama_pro_data.json")
COLORS = {
    "bg_dark": "#0d1117",      # Github Dark
    "sidebar": "#161b22",      # Sidebar Dark
    "panel_right": "#161b22",  # Right Panel Dark
    "accent": "#58a6ff",       # Blue
    "accent_hover": "#1f6feb",
    "text_main": "#c9d1d9",
    "text_dim": "#8b949e",
    "border": "#30363d",
    "success": "#238636",
    "warning": "#d29922",
    "error": "#f85149",
    "model_llama": "#79c0ff",
    "model_gemma": "#d2a8ff",
    "model_mistral": "#ffa657"
}

class HardwareMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.running = True
        if nvml_available:
            try: nvmlInit()
            except: pass

    def get_stats(self):
        ram = psutil.virtual_memory()
        vram_total, vram_used = 0, 0
        gpu_temp = 0
        
        if nvml_available:
            try:
                handle = nvmlDeviceGetHandleByIndex(0)
                info = nvmlDeviceGetMemoryInfo(handle)
                vram_total = info.total / (1024**3)
                vram_used = info.used / (1024**3)
                gpu_temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
            except: pass
            
        return {
            "ram_p": ram.percent,
            "ram_u": ram.used / (1024**3),
            "ram_t": ram.total / (1024**3),
            "vram_u": vram_used,
            "vram_t": vram_total,
            "vram_p": (vram_used/vram_total)*100 if vram_total > 0 else 0,
            "gpu_temp": gpu_temp
        }

    def run(self):
        while self.running:
            stats = self.get_stats()
            self.callback(stats)
            time.sleep(2)

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, role, content, model_name="", color=None):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", pady=10, padx=10)
        
        self.role = role
        self.model_name = model_name
        self.color = color
        
        bg_color = COLORS["accent"] if role == "user" else COLORS["sidebar"]
        txt_color = "#ffffff" if role == "user" else COLORS["text_main"]
        border_w = 0 if role == "user" else 1
        
        self.container = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=12, 
                                 border_width=border_w, border_color=COLORS["border"])
        self.container.pack(side="right" if role == "user" else "left", padx=(50, 0) if role == "user" else (0, 50))
        
        if model_name:
            tag_frame = ctk.CTkFrame(self.container, fg_color="transparent")
            tag_frame.pack(fill="x", padx=12, pady=(8, 0))
            
            tag = ctk.CTkLabel(tag_frame, text=f"@{model_name.upper()}", 
                               font=ctk.CTkFont(size=10, weight="bold"), 
                               text_color=color if color else COLORS["accent"])
            tag.pack(side="left")

        # Enhanced Textbox for Pro Output
        self.text_display = ctk.CTkTextbox(self.container, font=ctk.CTkFont(size=14, family="DejaVu Sans Mono" if role == "assistant" else "Helvetica"), 
                                          text_color=txt_color, fg_color="transparent",
                                          wrap="word", border_width=0, width=650)
        self.text_display.pack(padx=10, pady=10)
        self.text_display.insert("1.0", content)
        self.text_display.configure(state="disabled")
        
        # Initial height sync
        self.after(50, self.adjust_height)

    def update_text(self, text):
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", text)
        self.text_display.configure(state="disabled")
        self.adjust_height()

    def adjust_height(self):
        # Improved height calculation for variable content
        content = self.text_display.get("1.0", "end-1c")
        num_lines = content.count("\n") + 1
        # Add buffer for wrapping (approximate based on width)
        wrap_buffer = len(content) // 80 
        total_lines = num_lines + wrap_buffer
        
        new_height = min(max(45, total_lines * 24), 800)
        self.text_display.configure(height=new_height)
        
        # Ensure scroll to bottom
        self.master._parent_canvas.yview_moveto(1.0)

class OllamaProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ollama Pro - Engineering Workspace")
        self.geometry("1500x950")
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.api_base = "http://localhost:11434/api"
        self.is_split_view = False
        self.inference_start_time = 0
        self.available_models = []
        
        # History Structure: [{"id": "...", "title": "...", "messages": [...]}]
        self.sessions = []
        self.current_session_id = None
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.load_data()
        self.setup_ui()
        self.start_new_chat() # Initialize empty session
        
        self.hw_monitor = HardwareMonitor(self.update_hardware_ui)
        threading.Thread(target=self.hw_monitor.run, daemon=True).start()
        
        self.load_models()
        self.after(500, self.render_history_sidebar)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    # Support legacy single-history structure or new multi-session structure
                    if "history" in data and isinstance(data["history"], list) and (not data["history"] or "role" in data["history"][0]):
                        # Migrate legacy data
                        if data["history"]:
                            self.sessions = [{"id": str(time.time()), "title": "Legacy Session", "messages": data["history"]}]
                    elif "sessions" in data:
                        self.sessions = data.get("sessions", [])
            except: self.sessions = []

    def save_data(self):
        data = {"sessions": self.sessions}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def clear_all_history(self):
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete ALL chat history?"):
            self.sessions = []
            self.save_data()
            self.start_new_chat()

    def start_new_chat(self):
        self.current_session_id = str(time.time())
        self.sessions.append({
            "id": self.current_session_id,
            "title": "New Chat",
            "messages": []
        })
        self.save_data()
        self.clear_canvas()
        self.render_history_sidebar()

    def clear_canvas(self):
        for widget in self.chat_frame_1._scroll_area.winfo_children():
            widget.destroy()
        if self.chat_frame_2:
            for widget in self.chat_frame_2._scroll_area.winfo_children():
                widget.destroy()

    def render_history_sidebar(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
            
        for session in reversed(self.sessions): # Newest first
            item_frame = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            # Session Select Button
            is_active = session["id"] == self.current_session_id
            bg = COLORS["border"] if is_active else "transparent"
            
            btn = ctk.CTkButton(item_frame, text=session["title"], anchor="w",
                                fg_color=bg, hover_color=COLORS["border"], 
                                text_color=COLORS["text_main"], height=32,
                                command=lambda s=session: self.load_session(s["id"]))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Individual Delete Button
            del_btn = ctk.CTkButton(item_frame, text="✕", width=28, height=28,
                                    fg_color="transparent", hover_color="#ef4444",
                                    text_color=COLORS["text_dim"],
                                    command=lambda s=session: self.delete_session(s["id"]))
            del_btn.pack(side="right")

    def delete_session(self, session_id):
        self.sessions = [s for s in self.sessions if s["id"] != session_id]
        self.save_data()
        
        # If we deleted the active session, start a fresh one or load another
        if session_id == self.current_session_id:
            if self.sessions:
                self.load_session(self.sessions[-1]["id"])
            else:
                self.start_new_chat()
        else:
            self.render_history_sidebar()

    def load_session(self, session_id):
        self.current_session_id = session_id
        self.clear_canvas()
        session = next((s for s in self.sessions if s["id"] == session_id), None)
        if session:
            for msg in session["messages"]:
                ChatBubble(self.chat_frame_1._scroll_area, msg["role"], msg["content"], 
                           model_name=msg.get("model", ""), color=msg.get("color"))

    def setup_ui(self):
        # LEFT PANEL
        self.left_panel = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORS["sidebar"], border_width=1, border_color=COLORS["border"])
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        
        header_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_frame.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header_frame, text="OLLAMA PRO", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["accent"]).pack(side="left")
        
        self.new_chat_btn = ctk.CTkButton(self.left_panel, text="+ New Chat", 
                                          fg_color=COLORS["accent"], text_color=COLORS["bg_dark"], font=ctk.CTkFont(weight="bold"),
                                          command=self.start_new_chat)
        self.new_chat_btn.pack(fill="x", padx=20, pady=(0, 10))

        self.clear_all_btn = ctk.CTkButton(self.left_panel, text="🗑 Clear All History", 
                                           fg_color="transparent", border_width=1, border_color="#ef4444",
                                           hover_color="#ef4444", text_color=COLORS["text_main"],
                                           command=self.clear_all_history)
        self.clear_all_btn.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(self.left_panel, text="PRIMARY ROUTING", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_dim"]).pack(padx=20, anchor="w")
        self.model_dropdown = ctk.CTkComboBox(self.left_panel, values=[], width=220, height=35, corner_radius=8, 
                                             fg_color=COLORS["bg_dark"], border_color=COLORS["border"], button_color=COLORS["border"])
        self.model_dropdown.pack(pady=(5, 10), padx=20)

        self.model_dropdown_2 = ctk.CTkComboBox(self.left_panel, values=[], width=220, height=35, corner_radius=8, 
                                               fg_color=COLORS["bg_dark"], border_color=COLORS["border"], button_color=COLORS["border"])
        self.model_dropdown_2.pack(pady=(5, 20), padx=20)
        self.model_dropdown_2.configure(state="disabled")

        ctk.CTkLabel(self.left_panel, text="CHAT HISTORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_dim"]).pack(padx=20, anchor="w")
        self.history_scroll = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # CENTER PANEL
        self.center_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=20)
        self.center_panel.grid_rowconfigure(1, weight=1)
        self.center_panel.grid_columnconfigure(0, weight=1)

        self.top_bar = ctk.CTkFrame(self.center_panel, height=60, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(15, 0))
        
        self.split_btn = ctk.CTkSwitch(self.top_bar, text="SPLIT VIEW COMPARISON", command=self.toggle_split_view, progress_color=COLORS["accent"])
        self.split_btn.pack(side="left", padx=10)
        
        self.persona_badge = ctk.CTkLabel(self.top_bar, text="PERSONA: ENGINEERING", fg_color=COLORS["border"], 
                                         corner_radius=6, padx=10, font=ctk.CTkFont(size=11, weight="bold"))
        self.persona_badge.pack(side="right", padx=10)

        self.canvas_container = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        self.canvas_container.grid(row=1, column=0, sticky="nsew", pady=15)
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        self.chat_frame_1 = self.create_chat_column(self.canvas_container, 0)
        self.chat_frame_2 = None

        self.input_container = ctk.CTkFrame(self.center_panel, height=100, fg_color="transparent")
        self.input_container.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        self.input_container.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkTextbox(self.input_container, height=80, corner_radius=12, border_width=1, 
                                         border_color=COLORS["border"], fg_color=COLORS["sidebar"], font=ctk.CTkFont(size=14))
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.user_input.bind("<Return>", self.handle_return)
        
        # Voice Button
        self.voice_btn = ctk.CTkButton(self.input_container, text="🎤", width=50, height=80, corner_radius=12,
                                       fg_color=COLORS["sidebar"], border_width=1, border_color=COLORS["border"],
                                       hover_color=COLORS["border"], text_color=COLORS["accent"],
                                       command=self.start_voice_recording)
        self.voice_btn.grid(row=0, column=1, padx=(0, 10))

        self.send_btn = ctk.CTkButton(self.input_container, text="➤", width=60, height=80, corner_radius=12, 
                                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], 
                                      text_color=COLORS["bg_dark"], command=self.send_message)
        self.send_btn.grid(row=0, column=2)

        # --- RIGHT PANEL ---
        self.right_panel = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["panel_right"], border_width=1, border_color=COLORS["border"])
        self.right_panel.grid(row=0, column=2, sticky="nsew")

        ctk.CTkLabel(self.right_panel, text="ENGINE ROOM", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text_dim"]).pack(pady=20, padx=20, anchor="w")
        self.create_gauge("SYSTEM RAM", "ram_bar", "ram_label")
        self.create_gauge("GPU VRAM", "vram_bar", "vram_label")
        
        self.stats_frame = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_dark"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.stats_frame.pack(fill="x", padx=20, pady=20)
        self.tps_label = ctk.CTkLabel(self.stats_frame, text="0.0 TPS", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"])
        self.tps_label.pack(pady=(15, 0))
        ctk.CTkLabel(self.stats_frame, text="TOKENS PER SECOND", font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"]).pack(pady=(0, 15))

        ctk.CTkLabel(self.right_panel, text="INFERENCE PARAMETERS", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_dim"]).pack(padx=20, anchor="w", pady=(20, 10))
        self.temp_slider = self.create_parameter("Temperature", 0, 1, 0.7)
        self.ctx_slider = self.create_parameter("Context Window", 2048, 32768, 4096, is_int=True)
        self.top_p_slider = self.create_parameter("Top P", 0, 1, 0.9)

    def handle_return(self, event):
        if not event.state & 0x1: # No Shift
            self.send_message()
            return "break"

    def start_voice_recording(self):
        import speech_recognition as sr
        
        def record():
            self.after(0, lambda: self.voice_btn.configure(text="🔴", fg_color="#ef4444"))
            r = sr.Recognizer()
            with sr.Microphone() as source:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                    text = r.recognize_google(audio)
                    self.after(0, lambda: self.user_input.insert("end", f" {text}"))
                except Exception as e:
                    print(f"Voice Error: {e}")
                finally:
                    self.after(0, lambda: self.voice_btn.configure(text="🎤", fg_color=COLORS["sidebar"]))
        
        threading.Thread(target=record, daemon=True).start()

    def create_chat_column(self, master, col):
        container = ctk.CTkFrame(master, fg_color=COLORS["bg_dark"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        container.grid(row=0, column=col, sticky="nsew", padx=5)
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        container._scroll_area = scroll
        return container

    def create_gauge(self, name, bar_attr, label_attr):
        frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_dim"]).pack(anchor="w")
        bar = ctk.CTkProgressBar(frame, height=8, progress_color=COLORS["accent"], fg_color=COLORS["border"])
        bar.pack(fill="x", pady=5)
        bar.set(0)
        setattr(self, bar_attr, bar)
        label = ctk.CTkLabel(frame, text="0.0 / 0.0 GB (0%)", font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"])
        label.pack(anchor="e")
        setattr(self, label_attr, label)

    def create_parameter(self, name, min_val, max_val, default, is_int=False):
        frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        val_var = ctk.DoubleVar(value=default)
        lbl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_frame.pack(fill="x")
        ctk.CTkLabel(lbl_frame, text=name, font=ctk.CTkFont(size=12), text_color=COLORS["text_main"]).pack(side="left")
        val_lbl = ctk.CTkLabel(lbl_frame, text=str(default), font=ctk.CTkFont(size=12), text_color=COLORS["accent"])
        val_lbl.pack(side="right")
        def update_lbl(v):
            if is_int: v = int(float(v))
            else: v = round(float(v), 2)
            val_lbl.configure(text=str(v))
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, variable=val_var, 
                              progress_color=COLORS["accent"], button_color=COLORS["accent"], command=update_lbl)
        slider.pack(fill="x", pady=5)
        return slider

    def render_history(self):
        for msg in self.messages:
            ChatBubble(self.chat_frame_1._scroll_area, msg["role"], msg["content"], 
                       model_name=msg.get("model", ""), color=msg.get("color"))

    def toggle_split_view(self):
        self.is_split_view = self.split_btn.get()
        if self.is_split_view:
            self.canvas_container.grid_columnconfigure(1, weight=1)
            self.chat_frame_2 = self.create_chat_column(self.canvas_container, 1)
            self.model_dropdown_2.configure(state="normal")
            self.model_dropdown_2.set(self.model_dropdown.get())
        else:
            if self.chat_frame_2:
                self.chat_frame_2.destroy()
                self.chat_frame_2 = None
            self.canvas_container.grid_columnconfigure(1, weight=0)
            self.model_dropdown_2.configure(state="disabled")

    def update_hardware_ui(self, stats):
        self.ram_bar.set(stats["ram_p"] / 100)
        self.ram_label.configure(text=f"{stats['ram_u']:.1f} / {stats['ram_t']:.1f} GB ({int(stats['ram_p'])}%)")
        if stats["vram_t"] > 0:
            self.vram_bar.set(stats["vram_p"] / 100)
            self.vram_label.configure(text=f"{stats['vram_u']:.1f} / {stats['vram_t']:.1f} GB ({int(stats['vram_p'])}%)")

    def load_models(self):
        def fetch():
            try:
                r = requests.get(f"{self.api_base}/tags", timeout=5)
                if r.status_code == 200:
                    models = [m['name'] for m in r.json().get('models', [])]
                    self.available_models = models
                    self.after(0, self.update_dropdown_models)
            except: pass
        threading.Thread(target=fetch, daemon=True).start()

    def update_dropdown_models(self):
        self.model_dropdown.configure(values=self.available_models)
        self.model_dropdown_2.configure(values=self.available_models)
        if self.available_models:
            self.model_dropdown.set(self.available_models[0])
            self.model_dropdown_2.set(self.available_models[0])

    def send_message(self):
        text = self.user_input.get("1.0", "end-1c").strip()
        model_1 = self.model_dropdown.get()
        model_2 = self.model_dropdown_2.get()
        if not text or "loading" in model_1: return
        
        self.user_input.delete("1.0", "end")
        self.inference_start_time = time.time()
        
        # Get active session
        session = next((s for s in self.sessions if s["id"] == self.current_session_id), None)
        if not session: return
        
        # Auto-title for new chats
        if session["title"] == "New Chat" and len(text) > 0:
            session["title"] = text[:25] + "..." if len(text) > 25 else text
            self.render_history_sidebar() # Update title in sidebar
        
        session["messages"].append({"role": "user", "content": text})
        
        ChatBubble(self.chat_frame_1._scroll_area, "user", text)
        if self.is_split_view:
            ChatBubble(self.chat_frame_2._scroll_area, "user", text)

        bubble_1 = ChatBubble(self.chat_frame_1._scroll_area, "assistant", "...", model_name=model_1, color=COLORS["model_llama"])
        threading.Thread(target=self.stream_response, args=(model_1, text, bubble_1, True, session), daemon=True).start()
        
        if self.is_split_view:
            bubble_2 = ChatBubble(self.chat_frame_2._scroll_area, "assistant", "...", model_name=model_2, color=COLORS["model_gemma"])
            threading.Thread(target=self.stream_response, args=(model_2, text, bubble_2, False, session), daemon=True).start()

    def stream_response(self, model, prompt, bubble, is_main, session):
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": self.temp_slider.get(),
                    "num_ctx": int(self.ctx_slider.get())
                }
            }
            r = requests.post(f"{self.api_base}/generate", json=payload, stream=True, timeout=120)
            
            full_text = ""
            tokens = 0
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("response", "")
                    full_text += content
                    tokens += 1
                    elapsed = time.time() - self.inference_start_time
                    tps = tokens / elapsed if elapsed > 0 else 0
                    if tokens % 5 == 0:
                        self.after(0, lambda t=full_text, s=tps: self.update_inference_ui(bubble, t, s))
            
            self.after(0, lambda t=full_text: bubble.update_text(t))
            if is_main:
                session["messages"].append({"role": "assistant", "content": full_text, "model": model})
                self.save_data()
        except Exception as e:
            self.after(0, lambda: bubble.update_text(f"Error: {str(e)}"))

    def update_inference_ui(self, bubble, text, tps):
        bubble.update_text(text)
        self.tps_label.configure(text=f"{tps:.1f} TPS")

if __name__ == "__main__":
    app = OllamaProApp()
    app.mainloop()

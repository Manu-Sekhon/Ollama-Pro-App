# Ollama Pro - Engineering Workspace

A high-performance, multi-model desktop interface designed for AI engineering, side-by-side model comparison, and real-time hardware monitoring.

## 🚀 Key Features

*   **Multi-Model Split View**: Toggle a split-screen canvas to prompt two different models simultaneously and compare their reasoning in real-time.
*   **Engine Room (Right Sidebar)**: 
    *   **Live Hardware Gauges**: Real-time System RAM and NVIDIA VRAM monitoring (via `pynvml`).
    *   **Inference Dashboard**: Live Tokens Per Second (TPS) tracking for performance benchmarking.
    *   **Granular Tuning**: Physical sliders for Temperature and Context Length.
*   **Intelligent History & Routing**:
    *   **Multi-Session Management**: Start new chats, auto-title sessions, and switch between past conversations in the sidebar.
    *   **Targeted Deletion**: Delete specific sessions individually with a single click.
    *   **Model-Tagged Responses**: AI bubbles are visually tagged with the specific model that generated them (e.g., `@LLAMA3`, `@GEMMA2`).
*   **Productivity Tools**:
    *   **Voice-to-Text**: Built-in 🎤 button for hands-free prompting using high-accuracy transcription.
    *   **Enter-to-Send**: Optimized input with Enter for sending and Shift+Enter for new lines.
    *   **Pro Workspace UI**: A sleek, high-contrast dark theme inspired by professional IDEs (GitHub Dark).

## 🛠 Installation & Launch

### Desktop Shortcut
You can launch the app directly using the **Ollama Pro** icon on your desktop (computer chip icon).

### Terminal Command
```bash
~/.ollama_pro_env/bin/python ~/ollama_pro.py
```

## 🚀 One-Click Install for Linux

To install **Ollama Pro** and its system dependencies on any Linux machine, run these commands in your terminal:

```bash
git clone https://github.com/Manu-Sekhon/Ollama-Pro-App.git
cd Ollama-Pro-App
chmod +x install.sh
./install.sh
```

This will automatically:
1.  Install required system libraries (`portaudio`, `alsa`).
2.  Set up a local Python virtual environment.
3.  Install all Python dependencies.
4.  Create an **Ollama Pro** shortcut on your Desktop and in your Application Menu.

## 📁 Project Structure

*   `ollama_pro.py`: Core application source code.
*   `~/.ollama_pro_env/`: Isolated Python environment with `customtkinter`, `pynvml`, and `speech_recognition`.
*   `~/.ollama_pro_data.json`: Local database storing your multi-session chat history and parameters.
*   `~/Desktop/Ollama-Pro.desktop`: Official Linux desktop entry for quick access.

## 💡 Pro Tips for Hardware

*   **RTX 2050 (4GB)**: For best performance in **Split View**, use lightweight models like `llama3.2:1b` or `phi3:mini`.
*   **VRAM Management**: Monitor the VRAM gauge in the Engine Room when switching models to avoid "Out of Memory" errors.
# Ollama-Pro-App

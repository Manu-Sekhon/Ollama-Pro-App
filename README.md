# Ollama Pro - Engineering Workspace

A high-performance, multi-model desktop interface designed for AI engineering, side-by-side model comparison, and real-time hardware monitoring.

## 🚀 Key Features

*   **Multi-Model Split View**: Toggle a split-screen canvas to prompt two different models simultaneously and compare their reasoning in real-time.
*   **Model Explorer (New)**: 
    *   **Smart Recommendations**: Automatically detects your VRAM and RAM to recommend models that will run smoothly on your hardware.
    *   **Technical Insights**: Displays parameter counts (e.g., 3.2B, 8B) and required disk space before you download.
    *   **One-Click Pull**: An expanded catalog of popular models (Llama, Mistral, Gemma, Phi, Qwen, DeepSeek) available for instant download.
    *   **Live Search**: Instantly filter the model catalog by name, tag, or capability.
*   **Engine Room (Right Sidebar)**: 
    *   **Live Hardware Gauges**: Real-time System RAM and NVIDIA VRAM monitoring (via `pynvml`).
    *   **Inference Dashboard**: Live Tokens Per Second (TPS) tracking for performance benchmarking.
    *   **Granular Tuning**: Physical sliders for Temperature and Context Length.
*   **Integrated Ollama Management**:
    *   **Auto-Server Control**: Automatically detects and starts the Ollama server on application launch.
    *   **One-Click Install**: If Ollama isn't found, the app can install it for you using the official script.
*   **Intelligent History & Routing**:
    *   **Multi-Session Management**: Start new chats, auto-title sessions, and switch between past conversations in the sidebar. **Now automatically cleans up unused "New Chat" sessions.**
    *   **Targeted Deletion**: Delete specific sessions individually with a single click.
    *   **Model-Tagged Responses**: AI bubbles are visually tagged with the specific model that generated them (e.g., `@LLAMA3`, `@GEMMA2`).
*   **Productivity Tools**:
    *   **Native Linux Scrolling**: Fully supported and optimized mousewheel scrolling across all components (chat, history, model hub).
    *   **Voice-to-Text**: Built-in 🎤 button for hands-free prompting using high-accuracy transcription.
    *   **Pro Workspace UI**: A sleek, high-contrast dark theme inspired by professional IDEs (GitHub Dark).

## 🛠 Installation

To run **Ollama Pro**, ensure you have Python 3.10+ and the required dependencies:

```bash
git clone https://github.com/Manu-Sekhon/Ollama-Pro-App.git
cd Ollama-Pro-App
chmod +x install.sh
./install.sh
```

## 📁 Project structure

*   `main.py`: Core application source code and UI logic.
*   `install.sh`: Automated setup script for Linux systems.
*   `requirements.txt`: Python library dependencies.
*   `~/.ollama_pro_data.json`: Local persistent chat history database.

## 💡 Hardware Optimization

The app is optimized for mid-range GPUs (like the RTX 2050 4GB). It will prioritize:
1.  **VRAM-Fit**: Models that fit entirely in your GPU memory for maximum speed.
2.  **RAM-Fallback**: If no GPU is detected, it suggests models based on system RAM availability.

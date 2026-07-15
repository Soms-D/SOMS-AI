# SOMS-AI

SOMS-AI is a 100% free, open-source, local-first voice assistant for desktop,
terminal, memory, system commands, and time-series forecasting. It uses Ollama
for local LLM chat by default, stores memory on your PC, and exposes GUI, TUI,
and CLI entry points from the same system controller.

## Features

| Area | Capability |
| --- | --- |
| GUI | Flet desktop chat interface with quick commands and microphone toggle. |
| TUI | Textual terminal interface with command history and status panel. |
| CLI | Scriptable and interactive command mode. |
| Local LLM | Ollama chat and vision model integration. |
| Memory | Local ChromaDB-backed memory store under `soms_memory/`. |
| Voice | Offline speech recognition, offline TTS, wake-word command handling. |
| Tools | Weather, file opening, YouTube/media, email, camera, diagnostics. |
| Forecasting | `/timesfm` status and `/timesfm demo` using TimesFM 2.5 Torch. |
| Maintenance | Self-healing, cleanup, package diagnostics, growth/evolution reports. |

## Quick Start

```bash
python3 -m venv venv
./venv/bin/pip install -U pip
./venv/bin/pip install -r requirements.txt
```

Recommended system packages on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y espeak-ng ffmpeg alsa-utils portaudio19-dev flac pulseaudio-utils
```

Optional packages:

```bash
sudo apt install -y motion imagemagick sox
```

Install Ollama from <https://ollama.com>, then pull at least one local model:

```bash
ollama pull llama3.1:8b
ollama pull llava
```

For fully offline STT, pre-download/cache a Faster Whisper model while you have
internet access, or configure a local `whisper.cpp` model path in
`soms_config.json`. By default SOMS uses `base.en` and will not send audio to an
online speech API.

## Run

```bash
./venv/bin/python main.py            # desktop GUI
./venv/bin/python main.py --tui      # terminal UI
./venv/bin/python main.py --cli      # interactive CLI
./venv/bin/python main.py --cli /info
./venv/bin/python main.py --no-wake  # disable wake-word listener
```

Normal voice mode starts with a greeting, listens for the wake word `soms`, and
then answers spoken commands. Say `soms` by itself to enter hands-free
conversation mode, or say `soms <your command>` to run one command directly.

## Auto Start

The included launcher starts SOMS from the project venv if one exists:

```bash
./start_soms.sh --gui
```

To start SOMS automatically after login with wake-word listening enabled:

```bash
mkdir -p ~/.config/systemd/user
cp soms.service ~/.config/systemd/user/soms.service
systemctl --user daemon-reload
systemctl --user enable --now soms.service
loginctl enable-linger "$USER"
```

View logs:

```bash
journalctl --user -u soms.service -f
```

## Core Commands

| Command | Description |
| --- | --- |
| `/help` | Show command manual. |
| `/info` | Live system status. |
| `/system check` | Health diagnostics. |
| `/model` | List or select Ollama models. |
| `/memory` | Memory-layer status. |
| `/forget` | Clear memory; supports `chat` or `secrets` scope. |
| `/voice` | Voice and microphone status. |
| `/camera` | Capture and describe a camera frame. |
| `/email` | Check email or configure IMAP credentials. |
| `/self-heal` | Scan logs and repair known issues. |
| `/clean` | Remove old logs, temp files, and caches. |
| `/packages` | Package manager status. |
| `/plan <goal>` | Generate an action plan. |
| `/task <name>` | Run an engineering/health task. |
| `/grow <axis>` | Improve performance, intelligence, efficiency, stability, or all. |
| `/timesfm` | Show TimesFM integration status. |
| `/timesfm demo` | Load TimesFM 2.5 and run a sample forecast. |

## TimesFM Forecasting

SOMS includes a lazy TimesFM service. The model is not loaded during startup
because first use can download large Hugging Face model weights.

The integrated demo is equivalent to:

```python
import torch
import numpy as np
import timesfm

torch.set_float32_matmul_precision("high")

model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch"
)

model.compile(
    timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        normalize_inputs=True,
        use_continuous_quantile_head=True,
        force_flip_invariance=True,
        infer_is_positive=True,
        fix_quantile_crossing=True,
    )
)

point_forecast, quantile_forecast = model.forecast(
    horizon=12,
    inputs=[
        np.linspace(0, 1, 100),
        np.sin(np.linspace(0, 20, 67)),
    ],
)
```

Run it through SOMS:

```bash
./venv/bin/python main.py --cli /timesfm
./venv/bin/python main.py --cli /timesfm demo
```

## Configuration

`soms_config.json` stores system settings, model names, voice settings, email
settings, and feature toggles. `soms_user_config.json` stores user preferences
and honorifics.

Common LLM settings:

```json
{
  "llm": {
    "host": "http://localhost:11434",
    "api_key": "",
    "default_model": "llama3.1:8b",
    "vision_model": "llava"
  },
  "voice": {
    "stt_engine": "faster-whisper",
    "tts_engine": "piper",
    "language": "en",
    "local_files_only": true,
    "whisper_model": "base.en",
    "whisper_cpp_model": "",
    "piper_model": ""
  }
}
```

## Project Layout

```text
SOMS-AI/
├── main.py                 # entry point and system controller
├── agent.py                # request router and conversation logic
├── orchestrator.py         # command coordination
├── forecasting.py          # TimesFM lazy model service
├── skills.py               # file, web, media, weather, email, camera tools
├── memory.py               # local memory layer
├── voice.py                # STT/TTS/microphone handling
├── tui.py                  # Textual interface
├── soms/
│   ├── __init__.py         # compatibility package for current flat layout
│   ├── gui.py              # Flet desktop GUI
│   └── gui_sudo.py         # sudo password prompt helper
├── requirements.txt        # pip-only Python dependencies
├── pyproject.toml          # SOMS-AI package metadata
├── start_soms.sh           # launcher script
└── timesfm/                # vendored/reference TimesFM sources
```

The codebase currently uses a flat module layout with a small `soms/`
compatibility package so imports such as `soms.agent` resolve correctly. A later
full source move can place all app modules under `soms/`, but this repair keeps
runtime behavior stable.

## Troubleshooting

No chat response:

```bash
curl -s http://localhost:11434/api/tags
ollama pull llama3.1:8b
```

No voice output:

```bash
sudo apt install -y espeak-ng
```

No speech recognition:

```bash
./venv/bin/pip install -r requirements.txt
sudo apt install -y portaudio19-dev flac pulseaudio-utils
```

If Faster Whisper says the model is missing, temporarily set
`"local_files_only": false` while online so the model can be cached, then set it
back to `true`.

TimesFM reports missing Torch:

```bash
./venv/bin/pip install -r requirements.txt
```

First `/timesfm demo` is slow because it may download the model weights.

## Privacy

SOMS is designed for private local use. Memory is stored under `soms_memory/`,
Ollama runs locally by default, and voice STT/TTS uses local engines. `/forget`
clears stored memory. Camera and email features only run when invoked or
configured.

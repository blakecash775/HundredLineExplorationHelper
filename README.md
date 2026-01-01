# The Hundred Line: Last Defense Academy - Exploration Helper

A simple overlay tool that reads your screen during exploration events and shows you the possible outcomes for each choice.

## Features

- **Auto-scan**: Continuously monitors your screen and automatically detects exploration events
- **Manual search**: Type keywords to look up specific events
- **Always-on-top**: Stays visible over your game window

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install Pillow pytesseract
```

### 2. Install Tesseract OCR

The screen reading feature requires Tesseract OCR to be installed on your system.

**Windows:**
- Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Run the installer (default path is fine)
- The tool will auto-detect common installation paths

**Other platforms:**
- macOS: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

## Usage

```bash
python hundred_line_helper.py
```

Or just run the script by double clicking if you have python set up.

### Controls

- **Start Scanning**: Begins continuous screen monitoring. When an exploration event is detected, the choices and outcomes are displayed automatically.
- **Scan Once**: Takes a single screenshot and attempts to match an event.
- **Manual Search**: Type any keywords from the event text to look it up directly.

### Tips

- Position the helper window where it won't overlap with the game's event text
- The scanner checks once per second
- If auto-detection isn't working well, use Manual Search with a few distinctive words from the event

## Event Data

The `exploration_events.json` file contains all known exploration events and their outcomes. The outcome format shows the possible results separated by `|` when there are multiple possibilities.

## Troubleshooting

**"Cannot scan - missing dependencies"**
- Make sure both Pillow and pytesseract are installed
- Make sure Tesseract OCR is installed on your system

**Events not being detected**
- Ensure the game text is clearly visible on screen
- Try using Manual Search as a fallback
- OCR works best with clear, unobstructed text

## Accuracy

I wasn't able to find an event guide with 100% accuracy, but you can easily update the json if you want.
Feel free to like file an issue on this repo too if you care that much, maybe we can get the first fully accurate store of this info.

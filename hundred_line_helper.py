"""
The Hundred Line: Last Defense Academy - Exploration Helper
Reads your screen for exploration choices and displays possible rewards.
"""

import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
import threading
import time

try:
    from PIL import ImageGrab, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Try to find Tesseract on Windows
import os
import sys

if sys.platform == 'win32':
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe'),
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            if TESSERACT_AVAILABLE:
                pytesseract.pytesseract.tesseract_cmd = path
            break


class ExplorationHelper:
    # Precomputed constants for matching
    STOPWORDS = frozenset({
        'you', 'the', 'a', 'an', 'it', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
        'and', 'but', 'if', 'or', 'because', 'until', 'while', 'this',
        'that', 'these', 'those', 'what', 'which', 'who', 'whom',
        'find', 'see', 'look', 'looks', 'looking', 'found', 'seems',
        'seem', 'might', 'maybe', 'something', 'anything', 'nothing'
    })

    DISTINCTIVE_WORDS = frozenset([
        'altar', 'statue', 'offerings', 'mummy', 'mushroom',
        'quicksand', 'spiderweb', 'beehive', 'minecart', 'dynamite',
        'revolver', 'roulette', 'gymnasium', 'pharmacy', 'oasis',
        'butterflies', 'carnivorous', 'greenhouse', 'mannequins',
        'graffiti', 'talisman', 'effigy', 'underwear', 'excavator',
        'armory', 'cassette', 'drone', 'robot', 'bomb', 'squall',
        'playground', 'vending', 'barrel', 'bridge', 'sword',
        'boxing', 'arcade', 'batting', 'invader', 'ghost'
    ])

    def __init__(self):
        self.events = []
        self.load_events()
        self.scanning = False
        self.scan_thread = None

        self.setup_gui()

    def load_events(self):
        """Load exploration events from JSON file and precompute matching data."""
        script_dir = Path(__file__).parent
        events_file = script_dir / "exploration_events.json"

        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_events = data.get('events', [])
        except FileNotFoundError:
            print(f"Warning: {events_file} not found. Using empty event list.")
            raw_events = []
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse events file: {e}")
            raw_events = []

        # Precompute matching data for each event
        self.events = []
        for event in raw_events:
            prompt_lower = event['prompt'].lower()
            words = prompt_lower.split()

            # Precompute 3-word phrases
            phrases = [' '.join(words[i:i+3]) for i in range(len(words) - 2)]

            # Precompute meaningful words (not stopwords, len > 2)
            meaningful = [w for w in words if w not in self.STOPWORDS and len(w) > 2]

            # Precompute long words (6+ chars)
            long_words = [w for w in words if len(w) >= 6]

            # Check if has distinctive word
            has_distinctive = bool(set(words) & self.DISTINCTIVE_WORDS)

            self.events.append({
                **event,
                '_prompt_lower': prompt_lower,
                '_phrases': phrases,
                '_meaningful': meaningful,
                '_meaningful_count': len(meaningful) if meaningful else 1,
                '_long_words': long_words,
                '_long_count': len(long_words) if long_words else 1,
                '_has_distinctive': has_distinctive
            })

    def setup_gui(self):
        """Set up the Tkinter GUI."""
        self.root = tk.Tk()
        self.root.title("Hundred Line Helper")
        self.root.geometry("500x600")
        self.root.configure(bg='#2b2b2b')

        # Make window always on top
        self.root.attributes('-topmost', True)

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', padding=6)
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TFrame', background='#2b2b2b')

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="The Hundred Line Helper",
            font=('Segoe UI', 16, 'bold'),
            bg='#2b2b2b',
            fg='#00ff88'
        )
        title_label.pack(pady=(0, 10))

        # Status indicator
        self.status_frame = tk.Frame(main_frame, bg='#2b2b2b')
        self.status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_dot = tk.Label(
            self.status_frame,
            text="●",
            font=('Segoe UI', 12),
            bg='#2b2b2b',
            fg='#888888'
        )
        self.status_dot.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            self.status_frame,
            text="Idle",
            font=('Segoe UI', 10),
            bg='#2b2b2b',
            fg='white'
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Control buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.scan_btn = tk.Button(
            btn_frame,
            text="Start Scanning",
            command=self.toggle_scan,
            bg='#4a4a4a',
            fg='white',
            activebackground='#5a5a5a',
            activeforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.manual_btn = tk.Button(
            btn_frame,
            text="Scan Once",
            command=self.manual_scan,
            bg='#4a4a4a',
            fg='white',
            activebackground='#5a5a5a',
            activeforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        self.manual_btn.pack(side=tk.LEFT)

        # Search frame for manual lookup
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_frame,
            text="Manual Search:",
            bg='#2b2b2b',
            fg='white',
            font=('Segoe UI', 9)
        ).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(
            search_frame,
            bg='#3a3a3a',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.search_entry.bind('<Return>', lambda e: self.search_events())

        search_btn = tk.Button(
            search_frame,
            text="Find",
            command=self.search_events,
            bg='#4a4a4a',
            fg='white',
            activebackground='#5a5a5a',
            activeforeground='white',
            relief=tk.FLAT,
            padx=10
        )
        search_btn.pack(side=tk.LEFT)

        # Results area
        results_label = tk.Label(
            main_frame,
            text="Results:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2b2b2b',
            fg='white'
        )
        results_label.pack(anchor=tk.W)

        self.results_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            height=20
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Configure text tags for colored output
        self.results_text.tag_configure('header', foreground='#00ff88', font=('Consolas', 11, 'bold'))
        self.results_text.tag_configure('choice', foreground='#ffcc00')
        self.results_text.tag_configure('outcome', foreground='#88ccff')

        # Show requirements info
        self.show_requirements_info()

    def show_requirements_info(self):
        """Display info about required dependencies."""
        self.results_text.delete(1.0, tk.END)

        messages = []

        if not PIL_AVAILABLE:
            messages.append("! Pillow not installed - Screen capture disabled")
            messages.append("  Install with: pip install Pillow")

        if not TESSERACT_AVAILABLE:
            messages.append("! pytesseract not installed - OCR disabled")
            messages.append("  Install with: pip install pytesseract")
            messages.append("  Also need Tesseract-OCR installed on system")

        if messages:
            self.results_text.insert(tk.END, "Setup Notes:\n", 'header')
            for msg in messages:
                self.results_text.insert(tk.END, msg + "\n")
            self.results_text.insert(tk.END, "\n")

        self.results_text.insert(tk.END, "Ready!\n", 'header')
        self.results_text.insert(tk.END, f"Loaded {len(self.events)} exploration events.\n\n")
        self.results_text.insert(tk.END, "Use 'Manual Search' to type keywords from an event,\n")
        self.results_text.insert(tk.END, "or 'Start Scanning' to auto-detect from screen.\n")

    def toggle_scan(self):
        """Toggle continuous scanning."""
        if self.scanning:
            self.scanning = False
            self.scan_btn.config(text="Start Scanning")
            self.status_dot.config(fg='#888888')
            self.status_label.config(text="Idle")
        else:
            if not PIL_AVAILABLE or not TESSERACT_AVAILABLE:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Cannot scan - missing dependencies!\n", 'header')
                self.results_text.insert(tk.END, "Install Pillow and pytesseract first.\n")
                return

            self.scanning = True
            self.scan_btn.config(text="Stop Scanning")
            self.status_dot.config(fg='#00ff00')
            self.status_label.config(text="Scanning...")

            self.scan_thread = threading.Thread(target=self.continuous_scan, daemon=True)
            self.scan_thread.start()

    def continuous_scan(self):
        """Continuously scan the screen for event text."""
        last_match = None

        while self.scanning:
            try:
                text = self.capture_screen_text()
                match = self.find_best_match(text)

                if match and match != last_match:
                    last_match = match
                    self.root.after(0, lambda m=match: self.display_event(m))

                time.sleep(1)  # Scan every second
            except Exception as e:
                print(f"Scan error: {e}")
                time.sleep(2)

    def manual_scan(self):
        """Perform a single screen scan."""
        if not PIL_AVAILABLE or not TESSERACT_AVAILABLE:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Cannot scan - missing dependencies!\n", 'header')
            return

        self.status_label.config(text="Scanning...")
        self.root.update()

        try:
            text = self.capture_screen_text()
            match = self.find_best_match(text)

            if match:
                self.display_event(match)
            else:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "No matching event found.\n", 'header')
                self.results_text.insert(tk.END, "\nDetected text:\n")
                self.results_text.insert(tk.END, text[:500] + "..." if len(text) > 500 else text)
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Scan error: {e}\n", 'header')

        self.status_label.config(text="Idle")

    def capture_screen_text(self):
        """Capture the screen and extract text via OCR."""
        # Capture entire screen
        screenshot = ImageGrab.grab()

        # Optimize image for faster OCR: grayscale and scale down
        screenshot = ImageOps.grayscale(screenshot)
        new_size = (screenshot.width // 2, screenshot.height // 2)
        screenshot = screenshot.resize(new_size)

        # Run OCR with optimized config
        text = pytesseract.image_to_string(screenshot, config='--psm 6')
        return text.lower()

    def find_best_match(self, screen_text):
        """Find the best matching event from the screen text using precomputed data."""
        best_match = None
        best_score = 0.0
        threshold = 0.4

        for event in self.events:
            # Method 1: Check precomputed 3-word phrases
            substring_score = 0
            for phrase in event['_phrases']:
                if phrase in screen_text:
                    substring_score = 0.8
                    break

            # Method 2: Check precomputed meaningful words
            matching_meaningful = sum(1 for w in event['_meaningful'] if w in screen_text)
            word_score = matching_meaningful / event['_meaningful_count']

            # Method 3: Check precomputed long words
            matching_long = sum(1 for w in event['_long_words'] if w in screen_text)
            long_word_score = matching_long / event['_long_count']

            # Combine scores
            score = max(substring_score, word_score * 0.7 + long_word_score * 0.3)

            # Bonus for distinctive words (precomputed flag)
            if event['_has_distinctive'] and any(w in screen_text for w in event['_prompt_lower'].split() if w in self.DISTINCTIVE_WORDS):
                score += 0.3

            if score > best_score and score >= threshold:
                best_score = score
                best_match = event

        return best_match

    def search_events(self):
        """Search events by keyword."""
        query = self.search_entry.get().lower().strip()

        if not query:
            return

        matches = []
        for event in self.events:
            if query in event['prompt'].lower():
                matches.append((1.0, event))  # Exact substring match
            else:
                # Check individual words
                query_words = query.split()
                prompt = event['prompt'].lower()
                matching = sum(1 for w in query_words if w in prompt)
                if matching > 0:
                    score = matching / len(query_words)
                    matches.append((score, event))

        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)

        self.results_text.delete(1.0, tk.END)

        if not matches:
            self.results_text.insert(tk.END, f"No events matching '{query}'\n", 'header')
            return

        self.results_text.insert(tk.END, f"Found {len(matches)} match(es):\n\n", 'header')

        for score, event in matches[:5]:  # Show top 5
            self.display_event_inline(event)
            self.results_text.insert(tk.END, "\n" + "─" * 40 + "\n\n")

    def display_event(self, event):
        """Display a single event in the results area."""
        self.results_text.delete(1.0, tk.END)
        self.display_event_inline(event)

    def display_event_inline(self, event):
        """Display event details (appends to current text)."""
        self.results_text.insert(tk.END, event['prompt'] + "\n\n", 'header')

        for i, choice in enumerate(event.get('choices', []), 1):
            self.results_text.insert(tk.END, f"  [{i}] ", 'choice')
            self.results_text.insert(tk.END, choice['text'] + "\n", 'choice')
            self.results_text.insert(tk.END, f"      → ", 'outcome')
            self.results_text.insert(tk.END, choice['outcome'] + "\n\n", 'outcome')

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    app = ExplorationHelper()
    app.run()


if __name__ == "__main__":
    main()

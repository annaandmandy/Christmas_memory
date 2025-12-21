import os
import base64
import json
import glob
from datetime import datetime
from io import BytesIO
from PIL import Image
import urllib.request
import urllib.error

# ==========================================
# CONFIGURATION
# ==========================================
# 1. Set your Claude API key in the environment
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# 2. Folder setup
INPUT_FOLDER = "photos"  # Create this folder and put your images there
OUTPUT_FILE = "rpg_memories.html"

# 3. Image Processing Settings
PIXEL_SCALE = 0.05  # Smaller number = more pixelated (0.05 is 5% of original size)
PIXEL_COLORS = 24  # Lower number = more retro palette
TARGET_PIXEL_MAX = 160  # Clamp long edge to this many pixels for consistent pixel size
UPSCALE_FACTOR = 4  # Upscale after pixelation to keep visible chunky blocks

# ==========================================
# HTML5 TEMPLATE (The Player Engine)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPG Memory Log</title>
    <style>
        :root { --bg-color: #1a1a2e; --text-color: #e94560; --box-bg: #16213e; }
        body { margin: 0; background-color: #000; font-family: 'Courier New', Courier, monospace; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; color: white; user-select: none; }
        
        /* CRT Effect */
        .scanlines { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); background-size: 100% 2px, 3px 100%; z-index: 10; mix-blend-mode: overlay; opacity: 0.6; }
        
        /* Layout */
        #game-container { width: 100%; max-width: 800px; aspect-ratio: 4/3; background: #111; border: 4px solid #444; position: relative; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.8); }
        
        /* Header */
        header { background: #0f3460; padding: 10px; border-bottom: 2px solid #fff; display: flex; justify-content: space-between; font-weight: bold; letter-spacing: 2px; font-size: 0.8rem; }
        .blink { animation: blink 1s infinite; color: red; }
        @keyframes blink { 50% { opacity: 0; } }

        /* Main Viewport */
        #viewport { flex: 1; position: relative; overflow: hidden; background: #000; display: flex; align-items: center; justify-content: center; }
        #scene-img { width: 100%; height: 100%; object-fit: contain; image-rendering: pixelated; opacity: 0; transition: opacity 0.5s; }
        
        /* Text Box */
        #dialogue-box { height: 30%; background: #0f3460; border-top: 4px solid #fff; padding: 20px; box-sizing: border-box; position: relative; }
        .corner { position: absolute; width: 10px; height: 10px; border: 2px solid #fff; }
        .tl { top: 5px; left: 5px; border-right: none; border-bottom: none; }
        .tr { top: 5px; right: 5px; border-left: none; border-bottom: none; }
        .bl { bottom: 5px; left: 5px; border-right: none; border-top: none; }
        .br { bottom: 5px; right: 5px; border-left: none; border-top: none; }
        
        #text-content { font-size: 1.05rem; line-height: 1.5; text-shadow: 2px 2px #000; min-height: 60px; }
        #meta-info { display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.7rem; color: #ffd700; }
        
        /* Controls */
        .btn-group { display: flex; gap: 10px; }
        button { background: transparent; border: 2px solid #fff; color: #fff; padding: 5px 15px; cursor: pointer; font-family: inherit; font-weight: bold; text-transform: uppercase; transition: background 0.2s; }
        button:hover { background: #e94560; }
        button:disabled { opacity: 0.3; cursor: not-allowed; }

        /* Start Screen */
        #start-screen { position: absolute; inset: 0; background: #1a1a2e; z-index: 5; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
        h1 { font-size: 3rem; color: #ffd700; text-shadow: 4px 4px #000; margin-bottom: 20px; }
        .press-start { animation: blink 1.5s infinite; margin-top: 20px; cursor: pointer; }

    </style>
</head>
<body>

    <div class="scanlines"></div>

    <div id="game-container">
        <!-- START SCREEN -->
        <div id="start-screen">
            <h1>CHRONO<br>MEMORIES</h1>
            <p>RELIVING DATA STREAM...</p>
            <div class="press-start" onclick="startGame()">[ PRESS START / TAP ]</div>
        </div>

        <!-- MAIN INTERFACE -->
        <header>
            <div><span class="blink">●</span> REC-PLAY</div>
            <div id="counter">00 / 00</div>
        </header>

        <div id="viewport">
            <img id="scene-img" src="" alt="Scene">
        </div>

        <div id="dialogue-box">
            <div class="corner tl"></div><div class="corner tr"></div>
            <div class="corner bl"></div><div class="corner br"></div>
            
            <div id="text-content"></div>
            
            <div id="meta-info">
                <span id="date-display">DATE: --/--/--</span>
                <div class="btn-group">
                    <button id="prevBtn" onclick="prevSlide()"><</button>
                    <button id="nextBtn" onclick="nextSlide()">></button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // DATA INJECTION POINT
        const memories = __DATA_PLACEHOLDER__;

        let currentIndex = 0;
        const imgEl = document.getElementById('scene-img');
        const textEl = document.getElementById('text-content');
        const countEl = document.getElementById('counter');
        const dateEl = document.getElementById('date-display');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        let typeWriterInterval;

        function startGame() {
            document.getElementById('start-screen').style.display = 'none';
            loadMemory(0);
        }

        function typeWriter(text) {
            clearInterval(typeWriterInterval);
            textEl.innerHTML = '';
            let i = 0;
            typeWriterInterval = setInterval(() => {
                if (i < text.length) {
                    textEl.innerHTML += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeWriterInterval);
                }
            }, 30);
        }

        function loadMemory(index) {
            if(index < 0 || index >= memories.length) return;
            
            currentIndex = index;
            const mem = memories[index];

            // Image
            imgEl.style.opacity = 0;
            setTimeout(() => {
                imgEl.src = mem.src;
                imgEl.onload = () => { imgEl.style.opacity = 1; };
            }, 200);

            // Text
            typeWriter(mem.caption);

            // Meta
            countEl.innerText = `${currentIndex + 1} / ${memories.length}`;
            dateEl.innerText = "DATE: " + mem.date;

            // Buttons
            prevBtn.disabled = currentIndex === 0;
            nextBtn.innerText = currentIndex === memories.length - 1 ? "FIN" : ">";
            if (currentIndex === memories.length - 1) nextBtn.disabled = true;
            else nextBtn.disabled = false;
        }

        function nextSlide() { loadMemory(currentIndex + 1); }
        function prevSlide() { loadMemory(currentIndex - 1); }

        // Keyboard support
        document.addEventListener('keydown', (e) => {
            if (e.key === "ArrowRight") nextSlide();
            if (e.key === "ArrowLeft") prevSlide();
        });
    </script>
</body>
</html>
"""

# ==========================================
# LOGIC
# ==========================================

def setup_claude():
    if not os.getenv(ANTHROPIC_API_KEY_ENV):
        print(f"ERROR: Please set {ANTHROPIC_API_KEY_ENV} in your environment.")
        exit()

def pixelate_image(image_path):

    try:
        with Image.open(image_path) as img:
            # 1. Resize down to lose detail (Mosaic effect)
            w, h = img.size
            new_w = int(w * PIXEL_SCALE)
            new_h = int(h * PIXEL_SCALE)

            # Clamp to a consistent pixel size for very large inputs
            max_edge = max(new_w, new_h)
            if max_edge > TARGET_PIXEL_MAX:
                scale = TARGET_PIXEL_MAX / max_edge
                new_w = int(new_w * scale)
                new_h = int(new_h * scale)
            
            # Ensure at least 1px
            new_w = max(1, new_w)
            new_h = max(1, new_h)

            # Resize using Nearest Neighbor (preserves sharp edges)
            img_small = img.resize((new_w, new_h), Image.Resampling.NEAREST)
            # Reduce color palette for a more pixel-art look
            img_small = img_small.convert("P", palette=Image.Palette.ADAPTIVE, colors=PIXEL_COLORS)
            
            # Upscale to keep visible chunky blocks without relying only on CSS
            up_w = max(1, new_w * UPSCALE_FACTOR)
            up_h = max(1, new_h * UPSCALE_FACTOR)
            img_small = img_small.resize((up_w, up_h), Image.Resampling.NEAREST)
            
            # Convert to base64
            buffered = BytesIO()
            img_small.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def generate_story(image_path):
    """
    Sends the ORIGINAL image to Claude for analysis.
    """
    try:
        print(f"   --> Consulting the Oracle (Claude) for {os.path.basename(image_path)}...")
        
        # Convert to a supported, size-limited format (avoid request_too_large)
        with Image.open(image_path) as img:
            if getattr(img, "format", "").upper() == "MPO":
                img.seek(0)
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Downscale large images for API limits
            max_edge = 1536
            w, h = img.size
            scale = min(1.0, max_edge / max(w, h))
            if scale < 1.0:
                new_size = (int(w * scale), int(h * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            image_payload_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        prompt = (
            "You are the narrator of a retro RPG story game. "
            "Analyze this image and write a sentences caption describing the scene "
            "as if it is a event, item, a person, or plot point. "
            "eg. Remember that winter day, you are playing with water."
            "Use retro Lovely memory tone (e.g., 'Back to that day, ...', 'Do you remember? ...', (dont always use this start)). "
            "Keep it under 40 words."
        )
        
        payload = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 80,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_payload_b64,
                            },
                        },
                    ],
                }
            ],
        }

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.getenv(ANTHROPIC_API_KEY_ENV),
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}") from e

        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
        if not text:
            raise RuntimeError("Empty response from Claude.")
        return text

    except Exception as e:
        print(f"Error generating story: {e}")
        return "The memory is too corrupted to read."

def main():
    print("--- RPG MEMORY BUILDER ---")
    setup_claude()

    # 1. Verify inputs
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Created folder '{INPUT_FOLDER}'. Please put your images there and run again.")
        return

    # 2. Find images
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(INPUT_FOLDER, ext)))
    
    if not files:
        print(f"No images found in '{INPUT_FOLDER}'.")
        return

    print(f"Found {len(files)} images. Starting batch processing...")

    # 3. Process loop
    processed_data = []

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        print(f"Processing: {filename}")
        
        # A. Pixelate
        pixel_b64 = pixelate_image(filepath)
        if not pixel_b64:
            continue

        # B. Generate Story
        story = generate_story(filepath)

        # C. Get Date (prefer EXIF DateTimeOriginal)
        creation_time = os.path.getmtime(filepath)
        date_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')
        try:
            with Image.open(filepath) as img:
                exif = img.getexif()
                exif_date = exif.get(36867) or exif.get(306)  # DateTimeOriginal or DateTime
                if exif_date:
                    date_str = datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S").strftime('%Y-%m-%d')
        except Exception:
            pass

        processed_data.append({
            "src": pixel_b64,
            "caption": story,
            "date": date_str,
            "timestamp": creation_time # Used for sorting
        })

    # 4. Sort by time
    processed_data.sort(key=lambda x: x['timestamp'])

    # 5. Clean up data for JSON injection (remove raw timestamp)
    final_data = []
    for item in processed_data:
        final_data.append({
            "src": item["src"],
            "caption": item["caption"],
            "date": item["date"]
        })

    # 6. Generate H5 (HTML) File
    print("Generating H5 Cartridge...")
    json_str = json.dumps(final_data)
    final_html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", json_str)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"SUCCESS! Memory cartridge created: {OUTPUT_FILE}")
    print("Open this file in any web browser to play.")

if __name__ == "__main__":
    main()

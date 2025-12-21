# 2025 Moment Echo

2025 Moment Echo is a small interactive collection that turns photos into playable memories: a retro RPG-style story log, a floating 3D friendship gallery, and a cozy flip-card game. It’s built to feel like a gift of moments—simple to open, easy to share, and made to celebrate friendship through tiny, repeatable rituals of looking back.

Start with: https://carrie1013.github.io/Room/3d_gallary.html

A memory-driven mini collection made of three experiences:
1) RPG Story Log
2) 3D Gallery
3) Flip Memory Game

Each part is a standalone HTML page. Open them in a browser, or host the repo on GitHub Pages.

## 1) RPG Story Log (RPG memories)
**Play:** open `RPG/rpg_memories.html`.

**Build your own story log:**
1. Put your photos in `RPG/photos/`.
2. Install Python deps:
   ```bash
   pip install pillow
   ```
3. Set your Claude API key:
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"
   ```
4. Run the builder:
   ```bash
   python RPG/rpg_memory_builder.py
   ```
5. Open the generated `RPG/rpg_memories.html`.

Notes:
- The builder pixelates images and asks Claude to generate short retro RPG captions.
- Captions are embedded into the HTML as base64 images, so it can be shared as a single file.

## 2) 3D Gallery
**Play:** open `3d_gallary.html`.

**Customize:**
- Replace images in `3d_images/`.
- Edit `friendsData` inside `3d_gallary.html` to update names, titles, and descriptions.

Notes:
- The gallery uses `three.js` via CDN, so an internet connection is required.

## 3) Flip Memory Game
**Play:** open `game/index.html`.

**Customize:**
- Provide 8 folders under `game/game_photos/` named `1` to `8`.
- Each folder should contain `a.jpg` and `b.jpg` (two photos from the same place).

Example:
```
game/game_photos/1/a.jpg
game/game_photos/1/b.jpg
...
game/game_photos/8/a.jpg
game/game_photos/8/b.jpg
```

Notes:
- The game shuffles 16 cards (8 pairs) and tracks steps + time.

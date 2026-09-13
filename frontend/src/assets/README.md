# Original demo sprite atlas

Arena uses separate original inline SVG placeholders in `js/arena-icons.js`
(shield, bow, hat, healing cross, crystal, bonus markers and ruins), following
the existing inline resource/camp icon convention. Team colors, class labels and
HP supplement the shapes. Arena does not alter or reuse this Empire sprite atlas.

`sprites.png` is a project-local RGBA PNG, 256×192 pixels (about 104 KiB).
It contains four columns and three rows of 64×64 cells:

| Row | Column 1 | Column 2 | Column 3 | Column 4 |
| --- | --- | --- | --- | --- |
| 1 | Grassland | Plains | Forest | Hills |
| 2 | Mountains | Water | Settler | Warrior |
| 3 | Scout | Archer | Spearman | City |

Created for this repository with the built-in imagegen tool. No source/reference
game art was supplied. The generated atlas was reduced with nearest-neighbor
sampling to the dimensions above, preserving alpha. No generation tools are
needed to build or run the game. This is replaceable placeholder art, covered by
the repository's MIT license to the extent rights apply.

Sprite class mappings live in `js/presentation.js`; atlas positions and pixelated
scaling live in `css/main.css`. Replacing the atlas with the same grid layout does
not require game logic changes. Faction colors are CSS overlays, not duplicate art.

## Generation prompt

Use case: stylized-concept. Asset type: original pixel-art sprite atlas for a small square-grid turn-based strategy browser game. Create ONE atlas, exactly 4 equal columns by 3 equal rows on a square image. No margins, no gutters, no labels, no text, no grid lines. Each cell is an independent square sprite. Row 1 cells left to right: grassland terrain (green grass tufts); plains terrain (golden dry grass); forest terrain (cluster of dark green pine trees over grass); hills terrain (rounded brown rocky hills over grass). Row 2: mountains terrain (gray angular peaks); water terrain (blue water with small pale wave streaks); Settler unit (human traveller with broad hat, pack and walking staff); Warrior unit (human with sword and round shield). Row 3: Scout unit (hooded green traveller with cloak); Archer unit (human with unmistakable curved bow); Spearman unit (human with tall spear and small shield); City sprite (tiny cluster of warm stone houses with red roofs and central keep). All twelve cells occupy exactly one quarter width and one third height. First six terrain cells fill their whole square edge to edge. Last six unit/city cells have genuinely transparent backgrounds, with subject centered and confined within middle 80 percent of cell. Deliberately simple low-resolution pixel art as if each sprite is drawn on a 32 by 32 pixel grid, hard edges, limited muted palette, no antialiasing, no shadows outside cells. Slight elevated view for terrain and city, readable silhouettes for units. Early desktop strategy game feel; completely original designs, do not copy Civilization or other game assets. No logos or decorative borders.

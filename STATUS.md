# Super Mario Bros. clean room: status

**Play:** https://andrewnakas.github.io/smb-cleanroom/ (repo https://github.com/andrewnakas/smb-cleanroom, `main` + `gh-pages`).
Update with `sh tools/publish.sh push "message"` (regenerates, assembles, refuses to push unless the taint scan prints
`TAINT: 0 failing`).

## What works
- **Web build**: clean ROM (`D:/n64work/smb/clean/smb.nes`) on EmulatorJS 4.2.3 + FCEUmm (`ports/ejs`). Headless Edge:
  boots to the title, Start begins a 1 player game, runs / jumps through 1-1, audio buffers carry signal.
  Keyboard, gamepad and EmulatorJS's touch pad; one tap starts game and sound; works in an iframe.
- **Round trip**: the disassembly + retail CHR assembles to PRG/CHR identical to the retail dump (dirty room only).
- **Art**: 99 of 117 pictures hand-drawn (all player frames, all common enemies, power-ups, blocks, pipes, clouds,
  hills, trees, castle, coral, cannon, axe, giant mushroom, explosion, vine), own font (40 glyphs), own score popups, own title board + nametable script,
  own palettes. The other 18 are the kept coarse grid inside the silhouette (see Next).
- **Live page checked** (headless Edge against github.io): boots, Start + run + jump work, audio carries signal.
  Without `?autostart=1` the page waits for one tap (EmulatorJS start button), which also unlocks sound.
- **Attract demo** (no input for 15 s) plays 1-1 by itself: coin pop, used block, 200 popup, goomba stomp all draw.
- **Taint**: 0 failing on ROM, site and repo.
- **For decompgames.com**: `decompgames.json`, `poster.png` (composed from our tiles, no screenshot).
- No samples and no voices in this game: **practice pack skipped**.

## Decisions (for review)
1. **Web route = clean ROM + EmulatorJS/FCEUmm.** smbvanilla (the C port) loads level data and graphics from a ROM
   at run time, so a clean ROM is needed either way; the emulator route then gives touch, gamepads and save
   states for free and is the same as the N64 / GB clean-ROM builds.
2. **Disassembly**: Xkeeper0/smb1 (doppelganger's, asm6f syntax). Retail dump on disk has header junk
   (sha1 33d23c2f…); PRG fefa1097…, CHR 394badaf… match the canonical ea343f4e… ROM.
3. **What is kept**: code, level / enemy data, text, music + sfx tables; per picture a 1-bit silhouette and a colour
   grid of at most 4x4 cells over the whole picture (a lone 8x8 tile gets one cell); the uniform value of the 4 fill
   tiles; which colour index the font uses. Title screen: board footprint, attribute rows and text lines only.
   **Not kept**: glyph shapes, title logo, score-popup numerals, palettes (all ours).
4. **Taint rule** (`games/smb/taint_report.py`, details in `docs/PLATFORM_NES.md`): 16-byte raw windows with >= 6
   distinct byte values; any decoded tile equal to a retail tile in any slot / flip; per picture, fail when >= 12
   detail pixels (retail pixels that differ from the kept-fact baseline) are > 75 % reproduced and overall agreement
   is > 90 %. **Coincidences allowed** because the kept facts imply them: uniform tiles, tiles / pixel rows with a
   single non-zero colour (= the silhouette), own glyph tiles with <= 10 set pixels, grey-only palette rows
   (6 of 46 rows: white / grey stone and snow). Currently 44 tile coincidences, all silhouette-only or uniform.
   The scan caught about 20 hand-drawn tiles that had converged on retail (boots, star, hill, pipe lip); redrawn.
5. **Palettes**: our picks; coins and ? blocks glint gold -> white instead of gold -> dark, so the "?" stays readable.
6. Title text "(c)1985 NINTENDO" is kept as text (scope: text is kept). Say if you want it replaced.
7. Repo-local git identity set to the one the sibling repos use (andre / treesixtyweather@gmail.com).

## Next
- Draw the 18 baseline pictures: hammer, spiny egg, pulley, bridge over lava, chain, bubbles, small lifts
  (mostly one-colour shapes where the silhouette already says everything).
- Headless level checks: `sh games/smb/shots.sh <name> <W,L,A> "<script>"` (dev ROM starting at any level; seen so
  far: 1-1, 1-2 intro, 1-2, 1-3, 1-4, 2-2 opening screens, all fine).
- Bowser: halves are placed by code (rear 16 px behind, 8 px lower); `python -m games.smb.bowser_view out.png` shows
  him assembled. Drawn and checked in that preview, not yet seen in the running game (needs a play to the end of x-4).
- Shells: the tables are drawn with a vertical flip; art was laid out for that but not yet seen in the running game.
- A finer title logo (letters with a drop shadow).

## For the morning
- Look at: the live page, `poster.png`, and `python -m games.smb.sheet png sheet.png` for all art at once.
- You need to supply: nothing. (ROM was found in `C:/Users/andre/Downloads`.)
- To list on decompgames.com: copy `decompgames.json` into the site's `games.json` and `poster.png` to
  `/images/super-mario-bros.png` (I did not touch that repo).

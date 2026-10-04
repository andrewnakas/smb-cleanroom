# Super Mario Bros. clean room: status

**Play:** https://andrewnakas.github.io/smb-cleanroom/ (repo https://github.com/andrewnakas/smb-cleanroom, `main` + `gh-pages`).
Update with `sh tools/publish.sh push "message"` (regenerates, assembles, refuses to push unless the taint scan prints
`TAINT: 0 failing`).

## What works
- **Web build**: clean ROM (`D:/n64work/smb/clean/smb.nes`) on EmulatorJS 4.2.3 + FCEUmm (`ports/ejs`). Headless Edge:
  boots to the title, Start begins a 1 player game, runs / jumps through 1-1, audio buffers carry signal.
  Keyboard, gamepad and EmulatorJS's touch pad; one tap starts game and sound; works in an iframe.
- **Round trip**: the disassembly + retail CHR assembles to PRG/CHR identical to the retail dump (dirty room only).
- **Art**: 86 of 117 pictures hand-drawn (all player frames, all common enemies, power-ups, blocks, pipes, clouds,
  hills, trees, castle pieces), own font (40 glyphs), own score popups, own title board + nametable script,
  own palettes. The other 31 are the kept coarse grid inside the silhouette (see Next).
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
- Draw the 31 baseline pictures: explosion, hammer, springboard, spiny egg, vine, giant-mushroom ledge, coral,
  pulley, cannon, water, bridge over lava, axe, underwater coin, castle flag.
- Check Bowser, shells, springboard and the castle in the running game (their stored layout is reordered by code) and
  redraw from what is seen there.
- Longer headless play (worlds 1-2, 2-2, 1-4) for palette checks under ground / water / castle.
- A finer title logo (letters with a drop shadow).

## For the morning
- Look at: the live page, `poster.png`, and `python -m games.smb.sheet png sheet.png` for all art at once.
- You need to supply: nothing. (ROM was found in `C:/Users/andre/Downloads`.)
- To list on decompgames.com: copy `decompgames.json` into the site's `games.json` and `poster.png` to
  `/images/super-mario-bros.png` (I did not touch that repo).

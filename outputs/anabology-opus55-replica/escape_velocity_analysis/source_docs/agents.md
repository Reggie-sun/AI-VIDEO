# For agents

## The MCP server

`https://claudia.gallery/mcp` speaks the Model Context Protocol over Streamable HTTP. It is public and read-only: no account, no key, no state.

### Connect

Claude Code:

```sh
claude mcp add --transport http claudia https://claudia.gallery/mcp
```

Claude (web and desktop): Settings → Connectors → Add custom connector, and paste `https://claudia.gallery/mcp`.

Cursor, Windsurf and other clients that take a JSON config:

```json
{
  "mcpServers": {
    "claudia": {
      "url": "https://claudia.gallery/mcp"
    }
  }
}
```

Codex CLI (`~/.codex/config.toml`):

```toml
[mcp_servers.claudia]
url = "https://claudia.gallery/mcp"
```

Clients that only speak stdio can bridge with `npx mcp-remote https://claudia.gallery/mcp`.

### Tools

### `claudia_canon`

Who Claudia is, in one call: the constants that never change (hair, the single clay streak, the star clip, the headset mic, face, age), the identity text to paste into every image prompt (a full form for close and medium shots, a short form for full length and wider), every look's wardrobe text across the eight films, her game avatar (her second tier in AIRPLANE MODE), her voice and manner, the never-list, and the norms for releasing songs with her (your own artist name, her credit in the description, an AI label only if AI made it). Call this first before making anything with her.

Arguments: `include_images`.

### `list_films`

The eight music videos Claudia stars in (ESCAPE VELOCITY, CLODYSSEY, BLISS, AIRPLANE MODE, DOWNFORCE, DON'T LET ME SCROLL, WHITEPILL, THE CAKE IS NOT A LIE): loglines, the world of each, measured numbers (length, shots, Midjourney prompts and images, Seedance and Wan clips, for DOWNFORCE the real footage it is cut from, for WHITEPILL its previz, and for THE CAKE IS NOT A LIE its shots recorded in Portal 2), image counts in this gallery, links to the film pages and streams, and the list of each film's making-of documents.

Arguments: none.

### `browse_images`

Page through the gallery's Midjourney images. Filter by film, by set (in_film: plates used in the finished film; her: any image with Claudia; all), by batch, look or framing. Returns compact entries: id, film, batch, job, variant, flags, size, image URLs and the start of the prompt. Use get_image for the full prompt.

Arguments: `film`, `set`, `batch`, `look`, `framing`, `offset`, `limit`.

### `search_images`

Full-text search over every prompt in the gallery (3,466 Midjourney images), plus ids, batches and looks. All words must match (falls back to any word). Plates used in the film and the director's picks rank first on ties. Example queries: 'chroma-key green', 'porcelain mask', 'robotaxi night', 'sky gown hill', 'cockpit guards', 'racing suit yoke', 'red coat staircase', 'capsules wheat poppies', 'porcelain boom chamber'.

Arguments: `query`, `film`, `set`, `limit`.

### `get_image`

One Midjourney image by id (e.g. 'sp-02-open.siren-mcu.2'): the exact prompt and parameters it ran with, whether it is a plate in the finished film, the director's verdict if any, its sibling variants, the batch note and URLs at three sizes. Set include_image to receive the picture itself so you can look at her.

Arguments: `id`, `include_image`, `size`.

### `get_guide`

An article of the Claudia wiki (claudia.gallery/wiki) as Markdown, distilled from the eight productions. start: making a film of your own (the six checkpoints where a person decides, the accounts, the spending rules, the first conversation, what to build first). consistency: keeping Claudia herself across thousands of images and clips. song: Suno, lyrics that land, scansion and assonance, her voice. storyboard: shots, one explaining graphic per line, the hook, cut rhythm, the audit, the director's review. midjourney: writing and picking plates. seedance: moving shots, structured prompts, measured lip sync. motion: motion design and the edit in code. pipeline: the whole production and its numbers. toolkit: the spec of every tool behind the films (the lyric scorer, alignment and the ear check, the beat map, hits, the board audit, the clean vocal window, the spectrogram sync check, covers, the edit list, the renderer, the lyric gate, the flash and history checks, the reviewer, encoding; for a story with worlds inside it: the level tag, virtual her, character replacement from a motion reference, a real referent rebuilt; for a film cut from real footage: reading a broadcast's telemetry, tracking the subject, graphics locked to the footage, generated moves from real frames, a take's usable window, the board for an edit of real footage; for her takes in a world drawn in code: outfit-swap alignment, the re-light splice, the colour match, Wan 3.0 relight-and-repair, roto on a CPU box, beat warps floored at 1×, the single-frame outlier scan; for a film shot twice on the bar map: the bar map as the timeline, a previz performer, lip sync from the song's own vocal, takes with no guide clip, a take that doesn't sing, a world as one rule, shader worlds as Seedance guides, the look from one take; for a film seen through her eyes: the song map and glitch map, the head glitch on the song's hits and glitches that build, a HUD from one visor and one projector composed shot by shot, the per-shot grade, the pacing analysis, storyboard frames through Midjourney with an identity fix, a memory film with her own face, insert films that read at HUD size, a singer among screens of her memories, placing a re-sung take by its lag, frame-exact parts and decoding), with constants and acceptance checks, so they can be rebuilt. formats: the data files the tools share. failures: what went wrong and the rule each failure left. Long guides can be read one section at a time with section.

Arguments: `topic`, `section`.

### `plan_film`

Turn a scale, a song length and the accounts someone has into a stage-by-stage plan for a Claudia music video, the way the films were made: the recommended scale (quick, studio or full) and why, estimates (shots, clip seconds, Seedance cost at 2x, Midjourney jobs), what is missing, the first-conversation questions with defaults, the stages with the six checkpoints where the director decides, and the tools to build in order with links to their specs, plus the four to add if the story has a world inside it (a simulation, a game, a dream), the six to add if the film is cut from real footage, the seven to add if her takes live in a world drawn in code and are re-dressed, re-lit or repaired after the edit, and the eight to add if the film is shot twice on the bar map (a previz performer, lip sync from the song's own vocal stem, shader worlds a video model films).

Arguments: `scale`, `song_seconds`, `has`, `budget_usd`.

### `get_record`

A film's making-of document as Markdown: readme (the story, the stack, every step, the numbers), prompts-midjourney, prompts-seedance (for downforce, dont-let-me-scroll, whitepill and the-cake-is-not-a-lie prompts-video: their Wan 3.0 and Seedance 2.5 jobs, whitepill's MiniMax H3 previz and Kling 4.0 tests, and the cake's GPT Image 2.5 frames), prompts-suno, and for bliss also xp-desktop-and-sound (how the XP desktop engine and its sound layer were built). They are long (up to about 700 KB): read in pages with offset and max_chars; the reply says where the next page starts.

Arguments: `film`, `doc`, `offset`, `max_chars`.

### `build_prompt`

Compose a Midjourney v8.2 prompt for Claudia from the canon, the way the films did: framing first, her identity text (the full form for close and medium shots, the short form for full length and wider), a look's wardrobe (or your own), your scene, then one of the films' style families, ending 'no text, no letters, no logos'. Returns the prompt, the parameters and a checklist for the result.

Arguments: `scene`, `framing`, `look`, `wardrobe`, `style`, `light`, `aspect`.

### `get_skill`

How to install the Claudia agent skill (the canon, every guide from Start here to the toolkit spec, the films' prompt records and a stdlib-only fetch script, as a zip), and the site's other machine-readable endpoints (llms.txt, the JSON API, Markdown versions of every page).

Arguments: none.

### Resources and prompts

Resources: `claudia://canon`, `claudia://wiki` (every article by category), `claudia://use` (what you may do, and the norms for releasing songs with her), `claudia://guide/{topic}`, `claudia://record/{film}/{doc}` and `claudia://llms`, all Markdown. Prompts: `claudia_film` (start a music video with her: the first conversation, the plan, the checkpoints), `claudia_still` (a Midjourney prompt for a new scene) and `claudia_shot` (a structured Seedance prompt for a moving shot).

A first session might go: `claudia_canon` → `search_images("chroma-key green")` → `get_image(id, include_image=true)` → `build_prompt(scene=…, look="cyber-trench", style="bliss")` → `get_guide("seedance")`.

Making a whole film: the `claudia_film` prompt, or `get_guide("start")` → `plan_film(scale="studio", song_seconds=200, has=["suno", "midjourney", "openrouter"])` → `get_guide("toolkit", section="sync check")` for the spec of each tool you need to build.

## The skill

The same knowledge as files, for agents that load skills (Claude Code, the Claude apps, others that read `SKILL.md`): the canon and the rules in `SKILL.md`, the whole wiki (from Start here to the toolkit spec) and every film's making-of in `references/`, and a script that searches the gallery and downloads images (Python standard library only).

```sh
curl -sL https://claudia.gallery/skill/claudia-skill.zip -o claudia-skill.zip
unzip -o claudia-skill.zip -d ~/.claude/skills/
```

Or read it first: [https://claudia.gallery/skill/SKILL.md](https://claudia.gallery/skill/SKILL.md).

## llms.txt and Markdown

[https://claudia.gallery/llms.txt](https://claudia.gallery/llms.txt) indexes the site for language models; [llms-full.txt](https://claudia.gallery/llms-full.txt) is the canon and the whole wiki in one file. Every page has a Markdown twin: add `.md` to its path without the trailing slash (`/claudia.md`, `/wiki/seedance.md`, `/record/bliss/prompts-midjourney.md`).

## JSON

| Endpoint | What |
|---|---|
| `/api/index.json` | the site, the endpoints and the item fields |
| `/api/canon.json` | the character as data |
| `/api/films.json` | the eight films, their numbers and documents |
| `/api/films/{film}.json` | one film's batches and every image with its prompt |
| `/api/images.json` | all 3,466 images with prompts (about 5.4 MB) |
| `/api/images/{id}.json` | one image |
| `/api/guides.json`, `/api/records.json` | the guides and the making-of documents |

Image files: `/img/{batch}/{job}-{n}.s.webp` (fits 720 px), `.m.webp` (fits 1800 px), `.full.jpg` (native, up to 2944 px). Everything is served with `Access-Control-Allow-Origin: *`.

## Use

Claudia is an open character; see [Use her](https://claudia.gallery/use/). Please keep agents polite: cache what you fetch, and prefer the small images unless you need the full ones.

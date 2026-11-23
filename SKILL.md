---
name: minimax-h3-drama-director
description: >-
  End-to-end live-action cinematic drama director and production pipeline for
  MiniMax-H3 (ComfyUI Ref2VA, T2VA, I2VA, FL2VA, L2VA). Combines official
  MiniMax-H3 H3-Context-IR specifications, 10 official embeddings, LightX2V 8-step
  Turbo & Krea-2 keyframe workflows, and live-action drama cinematography craft
  (Character Bible, 180-degree axis lock, motivated lighting, dual native
  Chinese/English and Vietnamese VieNeu-TTS dialogue) with a Python CLI toolkit
  for 17k+5 frame alignment, WAV padding, zero-custom-node ComfyUI JSON
  generation, visual contact-sheet QC, and -14 LUFS Vietsub mastering.
---

# MiniMax-H3 Live-Action Drama Director

## Overview

Directs and produces photorealistic live-action drama scenes, multi-shot episodes, and cinematic music videos (MVs) on **MiniMax-H3** using 100% official ComfyUI core nodes (`comfy-core >= 0.33.0`, zero custom nodes). Fuses official `MiniMax-AI/MiniMax-H3` prompt specifications, LightX2V 8-step Turbo & Krea-2 keyframe engineering, live-action cinematography grammar, dual-language dialogue support (native Chinese/English acting + Vietnamese `VieNeu-TTS` `<Audio 1>`), and strict visual Contact-Sheet QC gates to protect GPU credits.

## Dependencies

- **`uv`** (installed skill): Required to execute [h3_drama_cli.py](./scripts/h3_drama_cli.py) cleanly via `uv run` (never bare `python`).
- **`ffmpeg` / `ffprobe`**: Local media binaries required by `pad-audio`, `qc-sheet`, and `assemble`.
- **`colab-mcp`** (optional MCP server): Remote GPU transport when rendering on Google Colab A100/L4.
- **`vieneu-tts-cli.exe`** (optional local binary): Offline Vietnamese TTS engine for Vietnamese lip-sync drama (`tts-vi`).

## Progressive Disclosure References

Read ONLY the reference needed for your current step:
- **T2VA / I2VA / FL2VA / L2VA exact prompt spec:** [official_base_en.txt](./references/official_base_en.txt) (verbatim from `MiniMax-AI/MiniMax-H3`)
- **Ref2VA exact 6-section prompt spec:** [official_ref_en.txt](./references/official_ref_en.txt) (verbatim from `MiniMax-AI/MiniMax-H3`)
- **Live-action directing, Character Bible, 180° rule & dual dialogue craft:** [drama_cinematography_bible.md](./references/drama_cinematography_bible.md)
- **ComfyUI presets (480p default / 736p Hero / 8-step Turbo / Pika 6-step / Krea-2 / 10 embeddings / Colab safety):** [comfyui_colab_production.md](./references/comfyui_colab_production.md)
- **Verified 10/10 real-world prompt templates:** [couple_intimate_10s_ref2va.txt](./examples/couple_intimate_10s_ref2va.txt), [solo_action_rooftop_ref2va.txt](./examples/solo_action_rooftop_ref2va.txt)
- **All-in-One Colab Studio Notebook (Krea-2 Turbo + MiniMax-H3 + Google Drive sync):** [drama_studio_krea2_h3_colab.ipynb](./resources/drama_studio_krea2_h3_colab.ipynb)

## Quick Start

```powershell
# 1. Compute exact 17k+5 frame count for a 10s drama take
uv run .agents/skills/minimax-h3-drama-director/scripts/h3_drama_cli.py align-frames `
  --seconds 10.0 --output out/frames.json

# 2. Lint a Ref2VA prompt before spending any GPU compute
uv run .agents/skills/minimax-h3-drama-director/scripts/h3_drama_cli.py lint-prompt `
  --prompt-file scene01.txt --mode ref2va --duration 10.125 --num-images 2 --output out/lint.json

# 3. Build official 0-custom-node ComfyUI workflow JSON (default: draft_480p; hero close-up: hero_736p; fast 8-step: turbo8_768p)
uv run .agents/skills/minimax-h3-drama-director/scripts/h3_drama_cli.py build-workflow `
  --mode ref2va --preset draft_480p --prompt-file scene01.txt --seconds 10.0 `
  --images actor_a.jpg actor_b.jpg --seed 99012 --prefix drama_sc01 --output out/wf.json

# 4. Extract 8-frame QC contact sheet after rendering & inspect visually with read_file
uv run .agents/skills/minimax-h3-drama-director/scripts/h3_drama_cli.py qc-sheet `
  --video out/drama_sc01.mp4 --sheet-out out/drama_sc01_qc.png --frames 8 --output out/qc.json
```

## Utility Scripts

All commands live in [h3_drama_cli.py](./scripts/h3_drama_cli.py) (stdlib-only Python 3, invoked via `uv run`, writing structured JSON to `--output`):

| Subcommand | Purpose | Key Required Flags |
| :--- | :--- | :--- |
| `align-frames` | Snaps duration (`4–15s`) to exact `17k + 5` grid at 24fps | `--seconds`, `--output` |
| `lint-prompt` | Validates `H3-Context-IR` sections, tags, embeddings, word budget, live-action purity | `--prompt-file`, `--mode`, `--duration`, `--num-images`, `--output` |
| `tts-vi` | Synthesizes Vietnamese line via local VieNeu-TTS v3 | `--text`, `--voice`, `--wav-out`, `--output` |
| `pad-audio` | Pads audio to `48kHz` stereo aligned to `17k + 5` (`4.1–15s`) & outputs trim end | `--wav-in`, `--wav-out`, `--output` |
| `build-workflow` | Emits 0-custom-node ComfyUI API JSON (`draft_480p`, `hero_736p`, `turbo8_480p`, `turbo8_544p`, `turbo8_768p`, `l4_b2_544p`, `pika6_768p`) | `--mode`, `--preset`, `--prompt-file`, `--seconds`, `--seed`, `--prefix`, `--output` |
| `comfy-submit` | Rate-limited (`1 req/s`) ComfyUI `/prompt`, `/history`, `/view` client | `--server`, `--action`, `--output` |
| `qc-sheet` | Probes streams + computes frame-to-frame `MAD spike` temporal jump score + renders `3×2` (6f) or `4×2` (8f) QC contact sheet PNG | `--video`, `--sheet-out`, `--frames`, `--output` |
| `assemble` | Trims, optional `retime_factor` lip-sync fix & `--dissolve-frames 5` seam join, `-14 LUFS` & Vietsub SRT | `--manifest`, `--video-out`, `--output` |

## Production Workflow

### 1. Intake & Preset Lock
Confirm (or infer cleanly when user states them):
- **Mode:** `ref2va` (actor portraits + dialogue/audio), `i2va` / `fl2va` (animating a pre-generated Krea-2 keyframe), or `t2va`.
- **Render Preset:**
  - **Default:** `draft_480p` (`864×480` → `RealESRGAN_x4plus.pth` `1920×1080`, Full 20 steps, ~2–5 min/clip on A100).
  - **Opt-in Hero Close-up:** `hero_736p` (native `1280×736`, Full 20 steps, **0 upscaler**, peak skin/eye/dialogue quality).
  - **Fast 8-Step Turbo (A100 MV / Keyframe-driven):** `turbo8_768p` or `turbo8_480p` (`euler` + `simple`, `MiniMaxH3SigmaShift`).
  - **Colab L4 24GB (`52 GB RAM`, `1.94 CU/h`) Winning Production Preset:** **`l4_b2_544p`** (`FP8_scaled` + `--use-sage-attention` + Kijai `8-step v1.2` + `EasyCache(0.10, 0.25..0.85)` at `960×544` in Warm-RAM mode, **0 in-ComfyUI upscaler** → upscale to `1080p` locally via FFmpeg Lanczos + `cas=0.28` + `noise=alls=4:allf=t+u` at `0 CU`). Runs **`50–58s` (`39f`) / `70–78s` (`56f`) / `133–144s` (`107f`)** (`~5.2 CU` for a full 4:38 MV!). Fallback to `EasyCache` OFF (`B1`) only for tricky re-rolls. **Avoid `W6A8` 6-bit** (causes single-frame temporal snaps).
- **Dialogue Mode:** Native MiniMax-H3 `<d>[Chinese] / [English]</d>` (most natural whispered breath acting) OR Vietnamese `VieNeu-TTS` (`tts-vi` → `pad-audio` → `<Audio 1>: fully_copy`).

### 2. Pre-Production Bible & Shot Plan (Multi-Shot Dramas / MVs)
Read [drama_cinematography_bible.md](./references/drama_cinematography_bible.md). Before prompting:
- Lock **3–5 quantified micro-anchors** per actor (hairpins, moles, pendant necklaces, hairline, blazer/collar) in a Character Bible.
- Build a **6-column Standardized Shot Table** locking `17k + 5` durations, **180° screen-axis (`L→R` / `R→L`)**, causal **Action Chains** (`Init → Trigger → Action → Feedback → Settled End State`), **One-Move-Per-Shot camera**, motivated practical lighting, and **explicit silent-listener locks** for multi-character dialogue.

### 3. Prompt Authoring & Zero-CU Lint Gate
- Read [official_ref_en.txt](./references/official_ref_en.txt) (for `Ref2VA`) or [official_base_en.txt](./references/official_base_en.txt) (for `T2VA/I2VA/FL2VA/L2VA`).
- Write all structural sections in English; keep `<d>[Language] ...</d>` and on-screen scene text in original language.
- Run `h3_drama_cli.py lint-prompt` and fix ALL errors before building any workflow JSON.

### 4. Audio Alignment & ComfyUI Workflow Build
- If Vietnamese dialogue or locked voice ref: run `tts-vi` and `pad-audio` (never attach `<Audio 1>` without at least 1 image ref!).
- Run `h3_drama_cli.py build-workflow`. Verify zero AdaLN mismatch warnings if using pruned base checkpoints with Turbo LoRAs.

### 5. Detached Render & Mandatory Visual Contact-Sheet QC (STOP-AND-ASK GATE)
- Queue asynchronously via `comfy-submit --action submit` (or Colab detached launcher) and wait using `schedule` — NEVER block inside Colab `run_code_cell` or poll in a tight loop.
- After fetching the MP4, ALWAYS run `h3_drama_cli.py qc-sheet` (`--frames 6` for `<=7s`, `--frames 8` for `>7s`) and visually inspect the PNG via `read_file`.
- **STOP-AND-ASK RULE:** If `comfy-submit` fails (OOM, HTTP error, disconnect) OR visual QC spots ANY defect (extra fingers, face/micro-anchor drift, physics glitch, plastic smoothing, dual-mouth lip-sync bleed), **STOP immediately**, present the clickable contact sheet + video + exact finding to the user, and wait for user approval before burning additional GPU CU.

### 6. Mastering & CU Idle Alert
- Assemble approved takes via `h3_drama_cli.py assemble` (`-14 LUFS`, 48kHz stereo, optional UTF-8 Vietsub SRT).
- Whenever Colab GPU finishes a job and sits idle, explicitly remind the user so they can continue or disconnect.

## Rate Limiting

`comfy-submit` enforces a conservative **`1.0 req/s`** rate limit via `time.monotonic()` plus a cross-process file lock (`<tempdir>/h3_drama_comfy.lock`), exponential backoff (`1s, 2s, 4s`) on HTTP `429` (`RateLimitError`) and transient `5xx` errors, and surfaces full HTTP `4xx` response bodies (up to 1000 chars) on non-retriable failures.

## Common Mistakes

1. **Using `RealESRGAN_x4plus_anime_6B.pth` on live-action footage:** Turns real actors into flat cartoon shading. Always use `RealESRGAN_x4plus.pth` (`draft_480p`) or 0 upscaler (`hero_736p` / `turbo8_768p`).
2. **Loading unpruned LightX2V `fl2v_turbo_8step_v1.2_768p_comfyui_bf16` on a `pruned` base:** Crashes with AdaLN shape error `[96768, 8]`. Use Kijai's pruned-compatible LoRA or an unpruned base.
3. **Human-voice words inside `overall_soundscape:` (`voice`, `speech`, `whisper`, `chatter`, `murmur`):** H3 converts this field directly into ambient audio, spawning phantom ghost voices! Keep ONLY physical/environmental sound nouns (`rustle`, `hum`, `patter`, `soft breathing`).
4. **Pink-elephant negative phrasing (`"no pin"`, `"no glasses"`) or `@handles` outside `<d>`:** Negatively naming a removed accessory often spawns it within 1s, and stray names/`@handles` render as literal on-screen text. Describe clean positive states instead and close the cast explicitly.
5. **Omitting spoken words when driving with `<Audio 1>` or re-rolling 3–5% linear lip drift:** Always put the exact words inside `<d>...</d>` even with external audio (or H3 renders closed lips), and fix linear slow-lip drift for free via manifest `retime_factor` (e.g. `0.96`) instead of wasting GPU CU re-rolling.
6. **Trailing period on embeddings (`embedding:minimaxh3_kiss_camera.`) or `"normal"` scheduler:** Always put a space before punctuation after embeddings, use `"simple"` scheduler (`0.0e+00` match), and write `non_diegetic_music: N/A` for silence.
7. **Running `RealESRGAN_x4plus` inside ComfyUI on a 52 GB RAM Colab L4 (or forgetting `/free` between Krea-2 and H3):** Qwen3-VL (`15 GB`) + FP8 UNET (`21 GB`) + VAE (`2.7 GB`) already use `~44 GB` RAM; adding 4K RealESRGAN (`+10.7 GB`) or keeping Krea-2 (`+19 GB`) resident triggers an instant Linux OOM freeze. Always call `/free` before switching from Krea-2 to H3, and upscale `960×544 → 1080p` locally with FFmpeg (`0 CU`).
8. **Using `W6A8` 6-bit UNETs or mismatched `FL2VA` first/last scales on 1:1 MV clones:** `W6A8` causes micro frame-jumps on playback, while independently swapped `first_frame` + `last_frame` pairs of different actor heights cause mid-clip character enlargement or cross-fade dissolves. Use **`FP8_scaled`** + **single-frame scale-locked `I2VA`** as the default for MV cuts (`≤4.5s`), calibrating Krea-2 `ref_boost / ref_boost_a` by shot distance (`WS: 1.85/1.18` → `CU: 2.75/1.00`).
9. **Mentioning accessories absent from the swapped keyframe (`"wearing round glasses"`, `"black fur hat"`, `"cream knit beanie"`):** MiniMax-H3 will pop the missing accessory onto the actor mid-clip or spawn a second twin wearing it. Audit every prompt strictly against the actual swapped keyframe pixels, and reinforce real signature micro-anchors (e.g. a small mole beneath the left corner of the lower lip) on close-ups.

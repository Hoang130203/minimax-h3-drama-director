# minimax-h3-drama-director

End-to-end **live-action cinematic drama & 1:1 MV cloning agent skill** for **MiniMax-H3** (`Ref2VA`, `T2VA`, `I2VA`, `FL2VA`) + **Krea-2 Identity Edit V2** on ComfyUI (Google Colab L4 24GB / A100 80GB or local GPU).

## Highlights

- **Battle-Tested Colab L4 24GB (`52 GiB RAM`) Recipe (`l4_b2_544p`):**
  - `FP8_scaled` + `--use-sage-attention` (Ada `sm_89`) + Kijai pruned `8-step v1.2` + `EasyCache(0.10, 0.25..0.85)` in Warm-RAM mode.
  - Measured throughput: **`50–58s` (`39f`)**, **`70–78s` (`56f`)**, **`88–100s` (`73f`)**, **`133–144s` (`107f`)** (`~5.2 CU` for a complete 143-cut 4:38 full MV).
  - Avoids `W6A8` 6-bit temporal frame snaps and `RealESRGAN_x4plus` 52 GB RAM OOMs (upscales `960×544 → 1080p` locally via FFmpeg Lanczos + CAS + 35mm grain at `0 CU`).
- **TRUE 1:1 MV Cloning Protocol (Zero Mid-Clip Character Enlargement):**
  - Distance-calibrated Krea-2 Identity Edit V2 (`WS: 1.85/1.18` → `CU: 2.75/1.00`) + single-frame scale-locked `I2VA` default to eliminate mid-clip scale bloat and cross-fade dissolves.
  - Strict prompt-to-pixel purity + facial micro-anchor reinforcement.
- **Zero-Custom-Node Core CLI Toolkit ([`scripts/h3_drama_cli.py`](./scripts/h3_drama_cli.py)):**
  - `align-frames` (`17k+5` at 24fps, including short MV cuts via `--allow-short`)
  - `lint-prompt` (validates `H3-Context-IR` sections, embeddings, silent-listener rules, banned soundscape voice words, negative accessory guards)
  - `build-workflow` (`draft_480p`, `hero_736p`, `turbo8_480p`, `turbo8_544p`, `l4_b2_544p`, `turbo8_768p`, `pika6_768p`)
  - `qc-sheet` (6/8-frame contact sheet + stdlib frame-to-frame `MAD spike` temporal jump audit)
  - `tts-vi`, `pad-audio`, `comfy-submit`, `assemble` (`-14 LUFS`, 35mm grain, Vietsub SRT/ASS)

## Structure

- [`SKILL.md`](./SKILL.md) — Core skill workflow & operational rules
- [`references/official_base_en.txt`](./references/official_base_en.txt) & [`references/official_ref_en.txt`](./references/official_ref_en.txt) — Verbatim MiniMax-H3 prompt specifications
- [`references/comfyui_colab_production.md`](./references/comfyui_colab_production.md) — ComfyUI presets, AdaLN compatibility matrix, L4 benchmark & RAM laws, 10 official embeddings
- [`references/drama_cinematography_bible.md`](./references/drama_cinematography_bible.md) — Character Bible, 180° axis lock, live-action cinematography, and 1:1 MV cloning protocol
- [`scripts/h3_drama_cli.py`](./scripts/h3_drama_cli.py) — Stdlib-only Python CLI toolkit
- [`resources/drama_studio_krea2_h3_colab.ipynb`](./resources/drama_studio_krea2_h3_colab.ipynb) — All-in-one Colab studio notebook
- [`examples/`](./examples/) — Verified 10/10 Ref2VA prompt templates

## Installation as an Agent Skill

Copy or clone this repo into `.agents/skills/minimax-h3-drama-director/`:

```bash
git clone https://github.com/Hoang130203/minimax-h3-drama-director.git .agents/skills/minimax-h3-drama-director
```

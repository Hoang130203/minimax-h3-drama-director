# ComfyUI & Colab Production Engineering Reference (MiniMax-H3)

Verified against `Comfy-Org/ComfyUI` (`comfy_extras/nodes_minimax_h3.py`), `Comfy-Org/MiniMax-H3`, `lightx2v/Minimax-h3-Turbo`, `Kijai/MiniMax-H3_comfy`, `Comfy-Org/Krea-2`, and `multimodalart/h3-acceleration-arena`.

---

## 1. Zero-Custom-Node Core Architecture (`comfy-core >= 0.33.0`)

All production workflows emitted by `scripts/h3_drama_cli.py` use **100% official ComfyUI core nodes** (zero fragile custom node dependencies):
- `UNETLoader`, `CLIPLoader` (`type="minimax"`), `VAELoader` (video + audio)
- `LoraLoaderModelOnly` (for Turbo LoRAs & Realism LoRAs)
- `MiniMaxH3SigmaShift` (inputs: `model`, `shift_video`, `shift_audio`)
- `MiniMaxH3ReferenceToVideo` (`ref2va` — up to `9` images, `3` videos, `3` audios; `ref_image_size="match"`)
- `MiniMaxH3ImageToVideo` (`t2va`, `i2va`, `fl2va` — optional `first_frame` / `last_frame`)
- `MiniMaxH3AddGuide` (optional seamless continuation anchoring `5` or `22` tail frames at `frame_idx=0`)
- `MiniMaxH3LatentUpscaleWithModel` (native latent-space upscaling with `LBH-123-AI/Minimax_h3_latent_Upscaler`)
- `KSamplerSelect`, `BasicScheduler` (`scheduler="simple"`), `ManualSigmas`, `BasicGuider`, `SamplerCustomAdvanced`
- `VAEDecode`, `VAEDecodeAudio`, `CreateVideo` (`fps=24`), `SaveVideo`

> **Mathematical Scheduler Proof (`h3-acceleration-arena`):** ComfyUI's `BasicScheduler` with `scheduler="simple"` reproduces MiniMax-H3's official `MiniMaxH3Scheduler` sigma grid with **`max|dsigma| = 0.0e+00`** at NFE `4 / 5 / 8 / 10 / 20`. **NEVER** use ComfyUI's default `"normal"` scheduler for H3!

---

## 2. Resolution Grid & Frame Alignment (`17k + 5` at 24 fps)

All canvas dimensions must be multiples of `32` (`16:9` widescreen strongly recommended; avoid `9:16` under Ref2VA Turbo due to documented upper-frame ghosting in HF Discussion `#44`):

| MP | 16:9 Resolution | Use Case |
| :--- | :--- | :--- |
| `0.4 MP` | `864 × 480` | Default fast batch (`draft_480p` / `turbo8_480p` → `RealESRGAN_x4plus` 1080p) |
| `0.5 MP` | `960 × 544` | LightX2V Turbo native 0.5 MP (`turbo8_544p`) |
| `0.9 MP` | `1280 × 736` | Proven Hero live-action native (`hero_736p` / `turbo8_768p`, 0 upscaler) |
| `0.98 MP` | `1344 × 768` | Official H3 max trained 768p canvas (`pika6_768p` / `hero_736p` override) |

**Exact Frame Grid (`17k + 5`, trained range `107–362f` = `4.46s–15.08s`):**
`107f (4.46s)`, `124f (5.17s)`, `141f (5.88s)`, `158f (6.58s)`, `175f (7.29s)`, `192f (8.00s)`, `209f (8.71s)`, `226f (9.42s)`, `243f (10.125s)`, `260f (10.83s)`, `277f (11.54s)`, `362f (15.08s)`.

---

## 3. Production Preset Matrix (Full 20-Step vs 8-Step Turbo vs 6-Step Pika)

| Preset (`--preset`) | Canvas → Output | Steps / Sampler / Scheduler | Shift (`V / A`) | Est. A100 Time (6.6–10s) | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`draft_480p`** *(Default)* | `864×480` → `RealESRGAN_x4plus` `1920×1080` | `20` / `res_multistep` / `simple` | `12 / 3` | ~2–5 min | Fast multi-clip drama episodes with full 20-step acting & audio fidelity |
| **`hero_736p`** *(Opt-in Hero)* | Native `1280×736` (0 upscaler) | `20` / `res_multistep` / `simple` | `12 / 3` | ~6.5–13 min | Flagship intimate close-ups, whispered native dialogue, peak skin pores & eye catchlights |
| **`turbo8_480p`** | `864×480` → `RealESRGAN_x4plus` `1920×1080` | `8` / `euler` / `simple` | `12 / 3` | ~1–2 min | Ultra-fast MV montage, beat-cut drafts, multi-seed auditioning |
| **`turbo8_544p`** | Native `960×544` (0 upscaler) | `8` / `euler` / `simple` | `12 / 3` | ~1.5–3 min | LightX2V standard fast native preview |
| **`l4_b2_544p`** *(L4 Winner)* | Native `960×544` → local FFmpeg 1080p | `8` / `euler` / `simple` + `EasyCache(0.10)` | `12 / 3` | **50–144s on L4** *(Warm-RAM)* | **Best Colab L4 24GB production preset:** `FP8_scaled` + `--use-sage-attention` + `EasyCache(0.10, 0.25..0.85)`; zero `W6A8` jumps, zero 52GB RAM OOM! |
| **`turbo8_768p`** | Native `1280×736` / `1344×768` (0 upscaler) | `8` / `euler` / `simple` | `12 / 3` *(or `6 / 3`)* | ~2.5–5.5 min | **Best speed/quality sweet spot on A100 for Krea-2 keyframe → `I2VA/FL2VA` MV & drama!** |
| **`pika6_768p`** | Native `1344×768` (0 upscaler) | `6` / `lcm` / `ManualSigmas` | `12 / 3` | ~2–4 min | Fast 6-step alternative (official Comfy-Org sigmas: `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`) |

### CRITICAL Turbo LoRA Compatibility Rules (Binary Safetensors Header Verified!)
Verified directly by inspecting raw `.safetensors` headers via HuggingFace Range reads against `pruned_int8_convrot` (`blocks.N.adaln_proj.linear.weight -> [96768, 8]`):

| Artifact | AdaLN Tensors / Shape | Pruned Base (`[96768, 8]`) Status | Exact Settings |
| :--- | :--- | :--- | :--- |
| `lightx2v/Minimax-h3-Turbo` `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors` (`1.96 GB`) | `0` AdaLN tensors | **100% SAFE** | `8 steps`, `euler`, `simple`, `shift 12/3`, `str 1.0` |
| `Kijai/MiniMax-H3_comfy` `minimax_h3_fl2v_turbo_8step_v1.2_768p_pruned_avg_rank_24_bf16.safetensors` (`335.6 MB`) | `lora_A [2, 8]`, `lora_B [96768, 2]` | **100% SAFE (Exact Match)** | `8 steps`, `euler`, `simple`, `shift 12/3`, `str 1.0` |
| `lightx2v/Minimax-h3-Turbo` `minimax_h3_fl2v_turbo_8step_v1.2_768p_comfyui_bf16.safetensors` (`2.12 GB`) | `153` unpruned `[96768, 2688]` | **CRASHES ON PRUNED!** | Requires unpruned `minimax_h3_fl2va_int8_convrot` or `bf16` |
| `Comfy-Org/MiniMax-H3` `pika_h3_flex_ref2va_v1_bf16.safetensors` (`1.96 GB`, or Kijai `553 MB`) | `0` AdaLN tensors | **100% SAFE** | `6 steps`, `lcm`, `ManualSigmas`, `shift 12/3` |
| `fal/MiniMax-H3-Realism-People-LoRA` `h3-realism-people-t2v-i2v-r2v.safetensors` (`131 MB`) | `0` AdaLN tensors (`rank 32` QKV) | **100% SAFE (T2V/I2V/R2V)** | Trigger `r34l1sm`, `str 0.6–0.85` (avoid pairing with FL2V v1.3) |
| `WarmBloodAban/Minimax-h3_Singularity` `Minimax-h3_Singularity_ref2va_v2_pruned_int8.safetensors` (`20.97 GB`) | Base `[96768, 8]` | **PRUNED BASE (Unified T2V/I2V/R2V)** | Strong `East Asian realism` + distant-face restoration + less glossy skin; supports Full 20-step OR Turbo LoRAs |

1. **Shift Value Rules by Version:**
   - `fl2v_turbo_8step_v1.2` (`pruned` or `unpruned`): `shift_video = 12.0`, `shift_audio = 3.0`, `strength = 1.0`.
   - `fl2v_turbo_8step_v1.0` / `v1.1` (`768p`): `shift_video = 6.0`, `shift_audio = 3.0`.
   - `ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`: `shift_video = 12.0`, `shift_audio = 3.0` (community verified cleaner speech than `v1.1`).
2. **FL2VA vs Ref2VA under 8-Step Turbo:**
   - When animating a **pre-rendered photorealistic Krea-2 keyframe** (MV or single-frame drama), `FL2VA/I2VA` + Kijai `8-step v1.2` delivers sharper texture and livelier motion than `Ref2VA` Turbo.
   - When locking **2+ actors + live multi-turn dialogue or `<Audio 1>: fully_copy`**, prefer **`Ref2VA` Full 20-step** (`draft_480p` or `hero_736p`) for maximum micro-expression and audio purity, or `Ref2VA` `turbo8_768p` (`v1.0`) for rapid iterations.
3. **2-Pass Native Latent Upscaling (`LBH-123-AI/Minimax_h3_latent_Upscaler`):**
   - Pass 1 at `608×352` or `864×480` → `MiniMaxH3LatentUpscaleWithModel` (`minimax_h3_latent_upscaler_2d_conv_v1_bf16.safetensors`, `364 MB`, `-84.7%` latent MSE, `30.47 dB` PSNR; audio passes through untouched) → 3-step Refine (`ManualSigmas: "0.9035, 0.6316, 0.3158, 0.0000"`) at `1280×736` or `1920×1088` → single `VAEDecode` (zero VAE encode/decode round-trip!).

### Battle-Tested Colab L4 24GB (`52 GiB RAM`, Ada `sm_89`, `1.94 CU/h`) Benchmark & Rules
Measured directly on a 68-shot Full 4:38 MV production run (`minimax_h3_fl2v_turbo_8step_v1.2_768p_pruned_avg_rank_24_bf16.safetensors`, `--use-sage-attention`, `cut02` 107f benchmark + full Warm-RAM batch):

| Config | UNET / Res | Cold (`--cache-none`) | Warm-RAM Batch | `MAD med / spike` | Verdict |
| :--- | :--- |---:|---:|---:| :--- |
| **`B1` Pure FP8** | `fp8_scaled` `960×544` | `318s` (`18.7s/it`) | `~60–170s` | `1.51 / x1.40` | **Smooth fallback** — use for tricky re-rolls (`EasyCache` OFF). |
| **`B2` FP8 + EasyCache `0.10`** (`l4_b2_544p`) | `fp8_scaled` `960×544` | `270s` (skips 2/8) | **`50–58s` (`39f`), `70–78s` (`56f`), `88–100s` (`73f`), `133–144s` (`107f`)** | **`1.46 / x1.38`** | **WINNER** — 99.5% identical face fidelity to `B1`, 1.33× faster diffusion, `~5.2 CU` total for a full 4:38 MV! |
| `B3` W6A8 544p | `w6a8` `960×544` | `258s` (`14.9s/it`) | `~135s` | `1.95 / x1.38` | **AVOID** — 6-bit weight quantization causes occasional single-frame temporal snaps on playback. |
| `B4` W6A8 736p | `w6a8` `1280×736` | `414s` (`35.6s/it`) | `~270s` | `2.18 / x1.52` | **AVOID** — sharper stills, but visible late-clip frame snaps (`f56/f64`). |

**L4 52 GiB System RAM Survival Laws:**
- **NEVER run `RealESRGAN_x4plus` inside ComfyUI alongside MiniMax-H3 on 52 GiB RAM:** `Qwen3-VL 32B` (`15 GB`) + `FP8_scaled` (`21 GB`) + `VideoVAE` (`2.7 GB`) + OS already hold `44–45 GiB`. Adding 4K `RealESRGAN` float32 batch tensors (`+10.7 GB`) hits `52.4 GB` instant Linux OOM freeze. Always output native `960×544` from ComfyUI and upscale locally at **0 CU** with FFmpeg: `scale=1920:1080:flags=lanczos+accurate_rnd+full_chroma_int,cas=strength=0.28,noise=alls=4:allf=t+u`.
- **Mandatory `/free` handoff between Krea-2 and MiniMax-H3:** Krea-2 occupies `~19–22 GiB` RAM. Always call `POST /free` (`{"unload_models": true, "free_memory": true}`) or restart ComfyUI before loading MiniMax-H3, and guard shots `>= 124f` (or `avail < 6.5 GB`) with `/free`. Keep Warm-RAM (omit `--cache-none`) during single-UNET H3 batches to save `~120–140s` reload per clip!
- **Short MV Cut Grid (`17k + 5` below 4s):** Rapid MV cuts (`1.0–3.5s`) render cleanly under `I2VA` at `39f (1.63s)`, `56f (2.33s)`, `73f (3.04s)`, `90f (3.75s)` on L4 in `< 1.5 min` each!

---

## 4. Live-Action Realism, Keyframe Generation & Upscaling Stack

### A. Pre-Generating Non-Plastic Drama Keyframes & Character Sheets (`Krea 2 Turbo`)
- **Repo:** `Comfy-Org/Krea-2`
- **Core Files:** `krea2_turbo_int8_convrot.safetensors` (`13.49 GB`; fallback `krea2_turbo_fp8_scaled.safetensors` `13.14 GB`; 8GB GPU `krea2_turbo_nvfp4.safetensors` `7.67 GB`) + `qwen3vl_4b_fp8_scaled.safetensors` (`5.24 GB`) + `qwen_image_vae.safetensors` (`254 MB`).
- **Exact Core Node Wiring (verified from `image_krea2_turbo_t2i_int8.json`):** `UNETLoader` → optional `LoraLoaderModelOnly` → `KSampler(steps=8, cfg=1.0, sampler="euler", scheduler="simple", denoise=1.0)` with `CLIPLoader(type="krea2")`, `CLIPTextEncode`, `ConditioningZeroOut`, `EmptyLatentImage`, `VAEDecode`. (~2–4s/image on A100!).
- **Anti-Plastic Photography LoRAs (Direct HuggingFace — `Omnico/Krea2_turbo_diff_loras`):**
  - `TherealrealKrea2Max_maxArtAsian_bf16_r64.safetensors` (`459 MB`) — photorealistic East Asian cinema portraits & drama frames!
  - `analogMadnessKrea2Turbo_v4_bf16_r64.safetensors` (`459 MB`) — 35mm analog film grain & natural optics!
  - `UltraRealisticByStableYogi_Krea2 V1_dequantBF16_r64.safetensors` (`459 MB`) — ultra-realistic skin texture!
- **Style Consistency Across All Shots (`ostris/krea2_turbo_style_reference`):** Wire `krea2_style_reference.safetensors` (`1.0`) + `ModelSamplingFlux(1.15, 0.5, width, height)` + `TextEncodeQwenImageEditPlus(clip, vae, image1=style_ref, prompt)` + `FluxKontextMultiReferenceLatentMethod("index_timestep_zero")` + `CFGGuider(1.0)` + `SamplerCustomAdvanced(euler/simple/8 steps)` (0 custom nodes!).
- **Identity Restaging & Continuous Last-Frame Derivation:**
  - **`conradlocke/krea2-identity-edit` V2** (`krea2_identity_edit_v2_r64.safetensors` `457 MB` & `krea2_general_edit_v2_r64.safetensors`, `8 steps`, `CFG 1.0`, `ref_boost=2`, requires optional `lbouaraba/comfyui-krea2edit`): puts 1 real actor photo into any scene/pose/lighting (`scene=aligned, person=beside`), generates character turnarounds, or edits a locked first frame into a continuous last frame!
  - **`Comfy-Org/MiniMax-H3-Image`** (`minimax_h3_image_pruned_int8_convrot.safetensors` `20.9 GB` + `minimax_h3_image_vae_fp16.safetensors` `1.17 GB`, `6 steps`, `CFG 1.0`, `euler/simple`): native 2K–4K 0-custom-node image edit reusing the exact same `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`!

### B. Optional Live-Action Realism LoRAs (MiniMax-H3)
- **`fal/MiniMax-H3-Realism-People-LoRA`** (`h3-realism-people-t2v-i2v-r2v.safetensors`, `131 MB`, trigger word `r34l1sm`, strength `0.6–1.0`): Works on T2V, I2V, and R2V; preserves skin pores, believable gestures, film-set lighting, and native stereo audio.
- **`prithivMLmods/MiniMax-H3-Facial-Realism-CloseUp`** (`74.6 MB`, prefix `Facial Realism:`): Specialized for emotional close-up micro-expressions.

### C. Upscaling Rules for Live-Action Drama
- **STRICTLY BANNED:** `RealESRGAN_x4plus_anime_6B.pth` — flattens human skin into cel-shaded cartoon outlines!
- **Tier 1 (Default Fast Pixel Upscaler):** `RealESRGAN_x4plus.pth` (`67 MB`, `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth`).
- **Tier 2 (Native Latent Upscaler — Zero VAE Round-Trip):** `LBH-123-AI/Minimax_h3_latent_Upscaler` (`minimax_h3_latent_upscaler_2d_conv_v1_bf16.safetensors`, `364 MB`) via core ComfyUI node `MiniMaxH3LatentUpscaleWithModel` + brief refine pass.
- **Tier 3 (4K Cinema Post-Upscale):** `SeedVR2` (`3B` for 12–16GB VRAM / `7B` with `blocks_to_swap=36`, `color_correction="lab"`).

---

## 5. All 10 Official MiniMax-H3 Embeddings

Download from `Comfy-Org/MiniMax-H3/tree/main/embeddings` into `ComfyUI/models/embeddings/`.
**CRITICAL SYNTAX RULE:** Always leave a **space** after the embedding name before any period or comma (`embedding:minimaxh3_kiss_camera .` — NEVER `embedding:minimaxh3_kiss_camera.`) or ComfyUI fails to resolve the token!

| Embedding Token | Drama / MV Use Case |
| :--- | :--- |
| `embedding:minimaxh3_kiss_camera` | Romantic orbital / intimate push-in camera choreography |
| `embedding:minimaxh3_bullet_time` | Dramatic time-dilation freeze & camera arc (climax / realization) |
| `embedding:minimaxh3_four_seasons` | Continuous time-passage montage across seasons (MV / epilogue) |
| `embedding:minimaxh3_blooming_flowers` | Poetic botanical transition / romantic metaphor |
| `embedding:minimaxh3_truman_show` | Dramatic overhead / pull-back surveillance framing |
| `embedding:minimaxh3_spiral_ascent` | Ascending aerial pull-away finale |
| `embedding:minimaxh3_storm_magic` | Supernatural storm / lightning shift |
| `embedding:minimaxh3_dark_magic` | Dark fantasy energy aura |
| `embedding:minimaxh3_fire_breath` | Flame stream VFX |
| `embedding:minimaxh3_art_is_explosion` | Large-scale cinematic blast VFX |

---

## 6. Google Colab & Local GPU Operations Rules

1. **Never block `colab-mcp` `run_code_cell`:** MCP cell calls time out at 3 minutes. Always submit asynchronously (`comfy-submit --action submit`), verify Step 1 `s/it` in `/tmp/comfy_server.log`, and wait via the `schedule` tool (never a polling loop!).
2. **Never display base64 `<video>` HTML in Colab output cells:** Large outputs disconnect the `colab-mcp` WebSocket. Pull MP4s via Cloudflared tunnel or Drive instead.
3. **ComfyUI V3 `SaveVideo` Output Key:** `comfy-core >= 0.33.0` returns MP4 metadata under `history[pid]["outputs"][nid]["images"]` as well as `"videos"`/`"gifs"`. `h3_drama_cli.py comfy-submit --action fetch` handles all three automatically.
4. **CU Protection & Zero-OAuth Transfer Rules:**
   - **Zero-OAuth Batch Transfer:** Upload keyframes/manifests directly to `ComfyUI/input/` via `POST <cloudflared_url>/upload/image` (pack JSON manifests inside a 16×16 PNG `tEXt` chunk via `PngInfo` to avoid base64 paste corruption), and pull finished MP4s/JPEG QC sheets via `GET <cloudflared_url>/view?filename=...&type=output` using `curl --retry 4`.
   - **Auto-Unassign on Unattended `/goal` Completion:** Once all rendered MP4s are downloaded and verified locally, terminate ComfyUI/cloudflared and call `from google.colab import runtime; runtime.unassign()` so zero idle CU burns while the user is AFK. When interactive, explicitly alert the user if GPU sits idle.
5. **Local Offline Prompting Alternative (`ComfyUI_Qwen_H3_Prompt`):** For 100% offline local ComfyUI runs without an external agent, `chflame163/ComfyUI_Qwen_H3_Prompt` runs `Qwen3.8-27B-GGUF` + `mmproj-F16.gguf` via isolated `llama-server` and auto-unloads VRAM. Note its documented limits: Qwen3.8 GGUF cannot listen to/analyze audio or BPM, and Q2 quantization degrades long multi-shot continuity compared to frontier LLMs driving this skill directly.

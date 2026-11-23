#!/usr/bin/env python3
"""MiniMax-H3 Live-Action Drama Director CLI Toolkit.

Stdlib-only multi-command CLI for MiniMax-H3 ComfyUI production:
  - align-frames   : Compute exact 17k+5 frame count and duration (24 fps).
  - lint-prompt    : Validate H3-Context-IR structure, tags, embeddings, and pacing.
  - tts-vi         : Synthesize offline Vietnamese dialogue via VieNeu-TTS CLI.
  - pad-audio      : Pad & align dialogue WAV to 48kHz stereo on the 17k+5 grid.
  - build-workflow : Emit 0-custom-node ComfyUI API JSON (draft_480p, hero_736p,
                     turbo8_480p, turbo8_544p, turbo8_768p, pika6_768p).
  - comfy-submit   : Rate-limited ComfyUI /prompt, /history, and /view client.
  - qc-sheet       : Probe video/audio + render 6- or 8-frame contact sheet PNG.
  - assemble       : Trim, concat, -14 LUFS loudness-master, and optional Vietsub burn-in.

Run via `uv run scripts/h3_drama_cli.py <subcommand> ...`
"""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

FPS = 24
MIN_TRAINED_SEC = 4.0
MAX_TRAINED_SEC = 15.0

OFFICIAL_EMBEDDINGS = {
    "minimaxh3_art_is_explosion",
    "minimaxh3_blooming_flowers",
    "minimaxh3_bullet_time",
    "minimaxh3_dark_magic",
    "minimaxh3_fire_breath",
    "minimaxh3_four_seasons",
    "minimaxh3_kiss_camera",
    "minimaxh3_spiral_ascent",
    "minimaxh3_storm_magic",
    "minimaxh3_truman_show",
}

REF2VA_SECTIONS = [
    "subject_definitions:",
    "summary:",
    "retention_analysis:",
    "detailed_description:",
    "overall_soundscape:",
    "non_diegetic_music:",
]

BASE_SECTIONS = [
    "integrated_multimodal_description:",
    "overall_soundscape:",
    "non_diegetic_music:",
]

BANNED_LIVE_ACTION_TERMS = [
    "cel-shaded",
    "cel shaded",
    "2d anime",
    "hand-drawn linework",
    "flat anime",
    "cartoon shading",
    "8k masterpiece",
    "best quality, masterpiece",
]

RUSHED_ADVERBS = [
    "briskly",
    "hurriedly",
    "snappy",
    "frantically fast",
]

# Hypernatural H3 Max empirical guards:
# 1. Human-voice words inside overall_soundscape spawn phantom voices/reverb in H3's audio VAE.
BANNED_SOUNDSCAPE_VOICE_WORDS = [
    "voice",
    "voices",
    "vocal",
    "vocals",
    "speech",
    "words",
    "talking",
    "chatter",
    "murmur",
    "murmuring",
    "conversation",
    "muttering",
    "whisper",
    "whispered",
    "whispering",
]

# 2. Speaking verbs in a no-dialogue shot cause unprompted mouth flap / gibberish.
SILENT_SHOT_SPEAKING_VERBS = [
    "says",
    "talks",
    "explains",
    "chats",
    "asks",
    "mouths",
    "mid-conversation",
]

DEFAULT_VIENEU_EXE = (
    r"C:\Users\Admin\Project\make-video\aurora-studio\resources\vieneu\vieneu-tts-cli.exe"
)

PRESET_SPECS = {
    "draft_480p": {
        "width": 864,
        "height": 480,
        "steps": 20,
        "sampler": "res_multistep",
        "scheduler": "simple",
        "use_upscaler": True,
        "upscale_w": 1920,
        "upscale_h": 1080,
        "upscaler_model": "RealESRGAN_x4plus.pth",
        "use_turbo": False,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Default fast live-action batch preset: 864x480 -> RealESRGAN_x4plus 1080p, Full 20 steps.",
    },
    "hero_736p": {
        "width": 1280,
        "height": 736,
        "steps": 20,
        "sampler": "res_multistep",
        "scheduler": "simple",
        "use_upscaler": False,
        "use_turbo": False,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Hero live-action close-up preset: native 1280x736, Full 20 steps, 0 upscaler (max skin/eye fidelity).",
    },
    "turbo8_480p": {
        "width": 864,
        "height": 480,
        "steps": 8,
        "sampler": "euler",
        "scheduler": "simple",
        "use_upscaler": True,
        "upscale_w": 1920,
        "upscale_h": 1080,
        "upscaler_model": "RealESRGAN_x4plus.pth",
        "use_turbo": True,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Ultra-fast 8-step Turbo draft/MV preset: 864x480 -> RealESRGAN_x4plus 1080p (~2.5x faster).",
    },
    "turbo8_544p": {
        "width": 960,
        "height": 544,
        "steps": 8,
        "sampler": "euler",
        "scheduler": "simple",
        "use_upscaler": False,
        "use_turbo": True,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "LightX2V native 0.5MP 8-step Turbo preset (960x544, 0 upscaler).",
    },
    "l4_b2_544p": {
        "width": 960,
        "height": 544,
        "steps": 8,
        "sampler": "euler",
        "scheduler": "simple",
        "use_upscaler": False,
        "use_turbo": True,
        "default_unet_fl2va": "minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
        "easycache_threshold": 0.10,
        "easycache_start": 0.25,
        "easycache_end": 0.85,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Colab L4 24GB (52GB RAM) winning Warm-RAM preset: FP8_scaled + SageAttention + Kijai 8-step v1.2 + EasyCache 0.10 @ 960x544, 0 in-ComfyUI upscaler (upscale 1080p locally via FFmpeg). Avoids W6A8 jumps and 52GB RealESRGAN OOM.",
    },
    "turbo8_768p": {
        "width": 1280,
        "height": 736,
        "steps": 8,
        "sampler": "euler",
        "scheduler": "simple",
        "use_upscaler": False,
        "use_turbo": True,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Native 736p/768p 8-step Turbo cinema preset (0 upscaler; use shift_video=6.0 for FL2V v1.0/v1.1, 12.0 for FL2V v1.2 & Ref2V v1.0).",
    },
    "pika6_768p": {
        "width": 1344,
        "height": 768,
        "steps": 6,
        "sampler": "lcm",
        "scheduler": "manual",
        "manual_sigmas": "1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0",
        "use_upscaler": False,
        "use_turbo": True,
        "shift_video": 12.0,
        "shift_audio": 3.0,
        "notes": "Pika-H3-Flex 6-step LCM preset at official 1344x768 (Comfy-Org template exact sigmas).",
    },
}


class RateLimitError(Exception):
    """Raised when an HTTP endpoint returns 429 after retries."""


class CrossProcessRateLimiter:
    """File-lock-based cross-process rate limiter using time.monotonic()."""

    def __init__(self, requests_per_second=1.0, lock_name="h3_drama_comfy.lock"):
        self.delay = 1.0 / max(requests_per_second, 0.01)
        self.lock_path = Path(tempfile.gettempdir()) / lock_name
        self._last_local = 0.0

    def wait(self):
        # Cross-process advisory wait via shared timestamp file + local monotonic guard
        now_wall = time.time()
        try:
            if self.lock_path.exists():
                prev_wall = float(self.lock_path.read_text(encoding="utf-8").strip() or "0")
                wall_elapsed = now_wall - prev_wall
                if 0 <= wall_elapsed < self.delay:
                    time.sleep(self.delay - wall_elapsed)
        except (OSError, ValueError):
            pass

        mono_elapsed = time.monotonic() - self._last_local
        if mono_elapsed < self.delay:
            time.sleep(self.delay - mono_elapsed)

        self._last_local = time.monotonic()
        try:
            self.lock_path.write_text(f"{time.time():.6f}", encoding="utf-8")
        except OSError:
            pass


class ComfyClient:
    """Rate-limited stdlib HTTP client for ComfyUI /prompt, /history, and /view."""

    REQUESTS_PER_SECOND = 1.0

    def __init__(self, server_url):
        self.base_url = server_url.rstrip("/")
        self.limiter = CrossProcessRateLimiter(self.REQUESTS_PER_SECOND)

    def _request_raw(self, method, path, data=None, headers=None, timeout=60, retries=3):
        url = f"{self.base_url}{path}"
        hdrs = dict(headers or {})

        for attempt in range(retries):
            self.limiter.wait()
            try:
                req = urllib_request.Request(url, data=data, headers=hdrs, method=method)
                with urllib_request.urlopen(req, timeout=timeout) as resp:
                    return resp.read()
            except urllib_error.HTTPError as e:
                if e.code == 429:
                    wait_s = 2 ** attempt
                    print(
                        f"Rate limited (429) on {url}, retrying in {wait_s}s "
                        f"(attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        raise RateLimitError(
                            f"HTTP 429 from {url} (limit={self.REQUESTS_PER_SECOND} req/s) "
                            f"after {retries} retries."
                        ) from e
                    time.sleep(wait_s)
                    continue
                if e.code >= 500:
                    wait_s = 2 ** attempt
                    print(
                        f"Server error {e.code} on {url}, retrying in {wait_s}s "
                        f"(attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        body = e.read().decode("utf-8", errors="replace")[:1000]
                        raise RuntimeError(
                            f"HTTP {e.code} from {url} after {retries} retries: {body}"
                        ) from e
                    time.sleep(wait_s)
                    continue
                try:
                    body = e.read().decode("utf-8", errors="replace")[:1000]
                except OSError:
                    body = str(e.reason)
                raise RuntimeError(
                    f"HTTP {e.code} from {url} (rate_limit={self.REQUESTS_PER_SECOND} req/s): {body}"
                ) from e
            except urllib_error.URLError as e:
                wait_s = 2 ** attempt
                print(
                    f"Connection error on {url} ({e}), retrying in {wait_s}s "
                    f"(attempt {attempt + 1}/{retries})...",
                    file=sys.stderr,
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Failed to reach {url} after {retries} attempts: {e}"
                    ) from e
                time.sleep(wait_s)

    def submit(self, workflow_dict):
        payload = json.dumps({"prompt": workflow_dict, "client_id": str(uuid.uuid4())}).encode("utf-8")
        raw = self._request_raw(
            "POST", "/prompt", data=payload, headers={"Content-Type": "application/json"}, timeout=30
        )
        return json.loads(raw.decode("utf-8"))

    def history(self, prompt_id):
        raw = self._request_raw("GET", f"/history/{prompt_id}", timeout=30)
        return json.loads(raw.decode("utf-8"))

    def queue(self):
        raw = self._request_raw("GET", "/queue", timeout=30)
        return json.loads(raw.decode("utf-8"))

    def download_view(self, filename, subfolder="", media_type="output"):
        qs = urllib_parse.urlencode(
            {"filename": filename, "subfolder": subfolder, "type": media_type}
        )
        return self._request_raw("GET", f"/view?{qs}", timeout=180)


def write_json_output(data, output_path):
    """Writes structured JSON output to disk and prints only a concise status line."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Success! Data written to: {out}")


def align_minimax_frames(seconds, clamp_trained=True):
    """Align requested duration (seconds) to MiniMax-H3's exact 17k+5 grid at 24 fps."""
    clamped = False
    eff_sec = float(seconds)
    if clamp_trained:
        if eff_sec < MIN_TRAINED_SEC:
            eff_sec = MIN_TRAINED_SEC
            clamped = True
        elif eff_sec > MAX_TRAINED_SEC:
            eff_sec = MAX_TRAINED_SEC
            clamped = True
    raw_frames = max(5, round(eff_sec * FPS))
    aligned = raw_frames + (5 - (raw_frames % 17)) % 17
    if clamp_trained and aligned > 362:
        aligned = 362
        clamped = True
    k = (aligned - 5) // 17
    latent_t = 2 if aligned <= 5 else k * 5 + 2
    actual_sec = aligned / FPS
    return {
        "requested_seconds": float(seconds),
        "clamped": clamped,
        "frames": aligned,
        "k": k,
        "fps": FPS,
        "actual_seconds": round(actual_sec, 4),
        "formatted_ss": f"{actual_sec:.2f}",
        "video_latent_t": latent_t,
        "audio_latent_t": round(actual_sec * 40),
        "in_trained_range": 107 <= aligned <= 362,
    }


def ffprobe_media(path):
    """Probes video/audio streams using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {res.stderr.strip()}")
    return json.loads(res.stdout)


def cmd_align_frames(args):
    data = align_minimax_frames(args.seconds, clamp_trained=not args.allow_unclamped)
    write_json_output(data, args.output)


def cmd_lint_prompt(args):
    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        print(f"Error: prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)

    text = prompt_path.read_text(encoding="utf-8-sig").strip()
    lower = text.lower()
    errors = []
    warnings = []

    mode = args.mode.lower()
    sections = REF2VA_SECTIONS if mode == "ref2va" else BASE_SECTIONS

    # 1. Exact section presence & ordering
    positions = []
    for sec in sections:
        idx = text.find(sec)
        if idx < 0:
            errors.append(f"Missing required H3 section header: '{sec}'")
        else:
            positions.append((sec, idx))
    if len(positions) == len(sections):
        ordered = [p[0] for p in sorted(positions, key=lambda x: x[1])]
        if ordered != sections:
            errors.append(
                f"Sections out of order. Expected {sections}, found {ordered}."
            )

    # 2. Mode-specific header checks
    if mode == "ref2va":
        if "[reference generation]" not in lower:
            errors.append(
                "Ref2VA summary must include the '[reference generation]' tag."
            )
    elif mode == "i2va":
        if not text.startswith("For the target video, at 0.00 seconds into the target video,"):
            errors.append(
                "I2VA prompt must begin with exact official header: "
                "'For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.'"
            )
    elif mode in ("fl2va", "l2va"):
        if not text.startswith("How the reference pictures align with the target video"):
            errors.append(
                f"{mode.upper()} prompt must begin with exact official header: "
                "'How the reference pictures align with the target video — ...'"
            )

    # 3. Blank line after alignment header in keyframe modes
    if mode in ("i2va", "fl2va", "l2va"):
        lines = text.splitlines()
        if len(lines) < 3 or lines[1].strip() != "":
            errors.append(
                f"{mode.upper()} requires an empty blank line immediately after line 1 alignment instruction."
            )

    # 4. Reference tag consistency (<Picture N>, <Audio N>, <Subject N>)
    pic_nums = sorted({int(m) for m in re.findall(r"<Picture\s+(\d+)>", text)})
    if args.num_images > 0:
        expected_pics = list(range(1, args.num_images + 1))
        for p in pic_nums:
            if p < 1 or p > args.num_images:
                errors.append(
                    f"Prompt references <Picture {p}> but --num-images is {args.num_images}."
                )
        missing_pics = [p for p in expected_pics if p not in pic_nums]
        if missing_pics:
            warnings.append(
                f"Provided image(s) not referenced by <Picture N> in prompt: {missing_pics}."
            )
    elif pic_nums:
        errors.append(f"Prompt references <Picture {pic_nums}> but --num-images is 0.")

    audio_nums = sorted({int(m) for m in re.findall(r"<Audio\s+(\d+)>", text)})
    if args.has_audio and not audio_nums:
        errors.append("--has-audio set but prompt never references <Audio 1>.")
    if not args.has_audio and audio_nums:
        errors.append(f"Prompt references <Audio {audio_nums}> but --has-audio was not set.")
    if args.has_audio and args.num_images == 0:
        errors.append(
            "MiniMax-H3 cannot run standalone audio without at least 1 image or video reference!"
        )

    # 5. Embedding space-before-period check & valid embedding names
    for m in re.finditer(r"embedding:([A-Za-z0-9_]+)([.,;:!?])?", text):
        emb_name, punct = m.group(1), m.group(2)
        if punct:
            errors.append(
                f"Trailing punctuation attached to 'embedding:{emb_name}{punct}'! "
                f"ComfyUI will fail to resolve it — put a space before '{punct}'."
            )
        if emb_name not in OFFICIAL_EMBEDDINGS:
            warnings.append(
                f"Embedding '{emb_name}' is not in the 10 official MiniMax-H3 embeddings list."
            )

    # 6. Dialogue tag balance & word/syllable budget check
    open_d = len(re.findall(r"<d>", text))
    close_d = len(re.findall(r"</d>", text))
    if open_d != close_d:
        errors.append(f"Unbalanced <d>...</d> dialogue tags: {open_d} open vs {close_d} close.")

    dialogues = re.findall(r"<d>(.*?)</d>", text, flags=re.DOTALL)
    total_units = 0
    for d in dialogues:
        if not re.match(r"^\s*\[[A-Za-z\- ]+\]", d):
            warnings.append(
                f"Dialogue tag missing explicit [Language] prefix (e.g. [Chinese] or [English]): '{d[:50]}'"
            )
        cleaned = re.sub(r"^\s*\[[^\]]+\]\s*", "", d).strip()
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
        latin_words = len(re.findall(r"[A-Za-z0-9']+", cleaned))
        total_units += cjk_chars + latin_words

    if dialogues and args.duration > 0:
        units_per_sec = total_units / float(args.duration)
        if units_per_sec > 3.8:
            warnings.append(
                f"Dialogue may be rushed ({total_units} words/chars in {args.duration}s = "
                f"{units_per_sec:.2f}/s; recommended <= 3.0/s for natural drama cadence)."
            )

    # 7. Multi-character silent-listener check
    subj_nums = sorted({int(m) for m in re.findall(r"<Subject\s+(\d+)>", text)})
    if len(subj_nums) >= 2 and dialogues:
        if not any(k in lower for k in ["silent", "quietly listen", "remains silent", "listening"]):
            warnings.append(
                "2+ subjects with dialogue detected but no explicit silent-listener cue found. "
                "Add 'remains silent, listening' for the non-speaking character to prevent dual lip-sync bleed."
            )

    # 8. Live-action purity & pacing checks
    if not args.allow_stylized:
        for term in BANNED_LIVE_ACTION_TERMS:
            if term in lower:
                errors.append(
                    f"Banned stylized/buzzword term '{term}' found in live-action drama prompt."
                )
    for adv in RUSHED_ADVERBS:
        if adv in lower:
            warnings.append(
                f"Rushed motion adverb '{adv}' found — may cause unnatural sped-up drama acting."
            )

    # 9. non_diegetic_music emptiness check
    m_music = re.search(r"non_diegetic_music:\s*(.*)", text, flags=re.DOTALL)
    if m_music and not m_music.group(1).strip():
        errors.append(
            "non_diegetic_music: is empty! Explicitly write 'N/A' for silence so H3 does not invent generic BGM."
        )

    # 10. Duration bounds & anti-stiffness check
    if args.duration < MIN_TRAINED_SEC or args.duration > MAX_TRAINED_SEC:
        errors.append(
            f"Duration {args.duration}s outside MiniMax-H3 trained range ({MIN_TRAINED_SEC}-{MAX_TRAINED_SEC}s)."
        )
    elif mode == "ref2va" and args.duration < 5.0:
        warnings.append(
            "Ref2VA clips shorter than ~5s (124f) can feel stiff or slow under 8-step Turbo."
        )

    # 11. Hypernatural guard: NO human-voice words inside overall_soundscape (even with <d>!)
    m_sound = re.search(
        r"overall_soundscape:\s*(.*?)(?:\n\s*non_diegetic_music:|\Z)",
        text,
        flags=re.DOTALL,
    )
    if m_sound:
        sound_body = m_sound.group(1).lower()
        bad_voice = [
            w for w in BANNED_SOUNDSCAPE_VOICE_WORDS if re.search(rf"\b{re.escape(w)}\b", sound_body)
        ]
        if bad_voice:
            errors.append(
                f"Banned human-voice term(s) inside overall_soundscape: {bad_voice}. "
                "H3 converts overall_soundscape directly into ambient audio — use only physical/environmental "
                "sound words (rustle, hum, hiss, patter, shuffle, soft breathing)."
            )

    # 12. Hypernatural guard: NO @handles outside <d> blocks (rendered as literal on-screen text)
    outside_d = re.sub(r"<d>.*?</d>", "", text, flags=re.DOTALL)
    handles = re.findall(r"@[A-Za-z0-9_]{2,}", outside_d)
    if handles:
        errors.append(
            f"Found @handle(s) outside <d> blocks ({handles}) — MiniMax-H3 renders handles as literal on-screen text."
        )

    # 13. Hypernatural guard: silent-shot speaking verbs & external audio words check
    desc_match = re.search(
        r"(?:detailed_description|integrated_multimodal_description):\s*(.*?)(?:\n\s*overall_soundscape:|\Z)",
        text,
        flags=re.DOTALL,
    )
    desc_body = desc_match.group(1).lower() if desc_match else ""
    if not dialogues and not args.has_audio:
        bad_verbs = [
            v for v in SILENT_SHOT_SPEAKING_VERBS if re.search(rf"\b{re.escape(v)}\b", desc_body)
        ]
        if bad_verbs:
            warnings.append(
                f"No <d> dialogue present, but speaking verb(s) {bad_verbs} found in description — "
                "replace with visible silent gestures and 'lips remain closed' to avoid unprompted mouth movement."
            )
    if args.has_audio and not dialogues:
        warnings.append(
            "--has-audio is enabled without a <d> spoken-words block in prompt! The prompt never hears the audio; "
            "append the spoken words inside <d>...</d> or H3 may render closed silent lips over playing audio."
        )
    if dialogues and not re.search(r"\(S\d+\)", text):
        warnings.append(
            "Dialogue <d> block(s) found without explicit speaker IDs like (S1)/(S2) immediately before <d>."
        )

    # 14. Hypernatural guard: pink-elephant negative accessory check
    pink_elephants = re.findall(
        r"\b(?:no|without)\s+(?:pin|badge|glasses|scar|hat|earrings?|necklace|ring|tattoo|beard|mustache)\b",
        outside_d.lower(),
    )
    if pink_elephants:
        warnings.append(
            f"Negative accessory wording detected ({pink_elephants}) — H3 often spawns negatively named items! "
            "Describe the positive clean state instead (e.g., 'plain, unadorned collar')."
        )

    frame_info = align_minimax_frames(args.duration)
    result = {
        "prompt_file": str(prompt_path),
        "mode": mode,
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "char_count": len(text),
            "subjects": subj_nums,
            "pictures": pic_nums,
            "audios": audio_nums,
            "dialogue_lines": len(dialogues),
            "dialogue_units": total_units,
            "recommended_frames": frame_info["frames"],
            "actual_seconds": frame_info["actual_seconds"],
        },
    }
    write_json_output(result, args.output)
    if errors:
        print(f"Lint FAILED with {len(errors)} error(s). See {args.output}", file=sys.stderr)
        sys.exit(1)


def cmd_tts_vi(args):
    exe = Path(args.vieneu_exe or DEFAULT_VIENEU_EXE)
    if not exe.exists():
        print(f"Error: VieNeu-TTS CLI not found at {exe}", file=sys.stderr)
        sys.exit(1)

    wav_out = Path(args.wav_out)
    wav_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe), "--text", args.text, "--voice", args.voice, "--output", str(wav_out)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not wav_out.exists():
        print(
            f"Error: VieNeu-TTS failed (rc={res.returncode}): {res.stderr.strip() or res.stdout.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)

    probe = ffprobe_media(wav_out)
    dur = float(probe.get("format", {}).get("duration", 0.0))
    data = {
        "wav_out": str(wav_out),
        "voice": args.voice,
        "text": args.text,
        "raw_duration_sec": round(dur, 4),
        "size_bytes": wav_out.stat().st_size,
    }
    write_json_output(data, args.output)


def cmd_pad_audio(args):
    wav_in = Path(args.wav_in)
    if not wav_in.exists():
        print(f"Error: input audio not found: {wav_in}", file=sys.stderr)
        sys.exit(1)

    probe = ffprobe_media(wav_in)
    raw_dur = float(probe.get("format", {}).get("duration", 0.0))
    if raw_dur <= 0:
        print(f"Error: invalid audio duration ({raw_dur}s) in {wav_in}", file=sys.stderr)
        sys.exit(1)

    lead_in = float(args.lead_in)
    tail_pad = float(args.tail_pad)
    natural_end = lead_in + raw_dur + tail_pad
    if natural_end > MAX_TRAINED_SEC:
        print(
            f"Error: audio ({raw_dur:.2f}s) + padding exceeds MiniMax-H3 15.0s ceiling "
            f"({natural_end:.2f}s). Split the line into two clips <= 15s.",
            file=sys.stderr,
        )
        sys.exit(1)

    target_sec = max(4.1, natural_end)
    frame_info = align_minimax_frames(target_sec, clamp_trained=True)
    padded_dur = frame_info["actual_seconds"]
    lead_ms = int(round(lead_in * 1000))

    wav_out = Path(args.wav_out)
    wav_out.parent.mkdir(parents=True, exist_ok=True)
    af = f"adelay={lead_ms}|{lead_ms},apad=whole_dur={padded_dur:.6f}"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(wav_in),
        "-af",
        af,
        "-t",
        f"{padded_dur:.6f}",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(wav_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: ffmpeg pad-audio failed: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    out_probe = ffprobe_media(wav_out)
    verified_dur = float(out_probe.get("format", {}).get("duration", 0.0))
    data = {
        "wav_in": str(wav_in),
        "wav_out": str(wav_out),
        "raw_duration_sec": round(raw_dur, 4),
        "lead_in_sec": lead_in,
        "recommended_trim_end_sec": round(min(padded_dur, lead_in + raw_dur + 0.35), 4),
        "padded_duration_sec": round(verified_dur, 4),
        "aligned_frames": frame_info["frames"],
        "sample_rate": 48000,
        "channels": 2,
    }
    write_json_output(data, args.output)


def cmd_build_workflow(args):
    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        print(f"Error: prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)
    prompt_text = prompt_path.read_text(encoding="utf-8-sig").strip()

    preset = PRESET_SPECS[args.preset]
    mode = args.mode.lower()
    width = args.width or preset["width"]
    height = args.height or preset["height"]
    if width % 32 != 0 or height % 32 != 0:
        print(f"Error: width ({width}) and height ({height}) must be multiples of 32.", file=sys.stderr)
        sys.exit(1)

    # Hard block anime_6B upscaler in live-action mode
    upscaler_model = args.upscaler_model or preset.get("upscaler_model", "RealESRGAN_x4plus.pth")
    if preset.get("use_upscaler") and "anime" in upscaler_model.lower() and not args.allow_anime_upscaler:
        print(
            f"Error: Refusing anime upscaler '{upscaler_model}' for live-action drama! "
            "Use 'RealESRGAN_x4plus.pth' (or pass --allow-anime-upscaler only for 2D anime).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Base model checkpoint selection
    default_unet = (
        "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
        if mode == "ref2va"
        else preset.get("default_unet_fl2va", "minimax_h3_fl2va_pruned_int8_convrot.safetensors")
    )
    unet_name = args.unet or default_unet

    # Default Turbo LoRA selection when using turbo presets
    turbo_lora = args.turbo_lora
    if preset["use_turbo"] and not turbo_lora:
        if args.preset == "pika6_768p":
            turbo_lora = (
                "pika_h3_flex_ref2va_v1_bf16.safetensors"
                if mode == "ref2va"
                else "pika_h3_flex_fl2va_v1_bf16.safetensors"
            )
        elif mode == "ref2va":
            turbo_lora = "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
        else:
            # Pruned-safe Kijai v1.2 default for pruned bases!
            turbo_lora = (
                "minimax_h3_fl2v_turbo_8step_v1.2_768p_pruned_avg_rank_24_bf16.safetensors"
                if "pruned" in unet_name.lower()
                else "minimax_h3_fl2v_turbo_8step_v1.2_768p_comfyui_bf16.safetensors"
            )

    warnings = []
    # AdaLN pruned-base compatibility check (HF Discussion #62)
    if (
        turbo_lora
        and "pruned" in unet_name.lower()
        and "fl2v_turbo_8step_v1.2_768p_comfyui" in turbo_lora.lower()
        and "pruned" not in turbo_lora.lower()
    ):
        warnings.append(
            "WARNING: Official unpruned fl2v_turbo_8step_v1.2_768p_comfyui_bf16 throws AdaLN shape mismatch "
            "[96768, 8] on pruned bases! Switch to Kijai's 'minimax_h3_fl2v_turbo_8step_v1.2_768p_pruned_avg_rank_24_bf16.safetensors' "
            "or use unpruned 'minimax_h3_fl2va_int8_convrot.safetensors'."
        )

    if mode == "ref2va" and preset["use_turbo"] and height > width:
        warnings.append(
            "WARNING: Ref2VA Turbo has known upper-frame ghosting in 9:16 vertical aspect ratio (HF #44). Prefer 16:9 or Full 20-step."
        )

    frame_info = align_minimax_frames(args.seconds, clamp_trained=not getattr(args, "allow_short", False))
    steps = args.steps if args.steps is not None else preset["steps"]
    shift_video = args.shift_video if args.shift_video is not None else preset["shift_video"]
    shift_audio = args.shift_audio if args.shift_audio is not None else preset["shift_audio"]

    images = args.images or []
    if mode == "ref2va" and len(images) > 9:
        print("Error: MiniMaxH3ReferenceToVideo supports at most 9 reference images.", file=sys.stderr)
        sys.exit(1)
    if mode == "i2va" and len(images) < 1:
        print("Error: i2va mode requires at least 1 image (first_frame).", file=sys.stderr)
        sys.exit(1)
    if mode == "fl2va" and len(images) < 2:
        print("Error: fl2va mode requires 2 images (first_frame and last_frame).", file=sys.stderr)
        sys.exit(1)
    if args.audio and mode != "ref2va":
        print("Error: --audio ref is supported only in ref2va mode.", file=sys.stderr)
        sys.exit(1)
    if args.audio and len(images) == 0:
        print("Error: MiniMax-H3 requires at least 1 reference image alongside --audio.", file=sys.stderr)
        sys.exit(1)

    wf = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": unet_name, "weight_dtype": "default"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": args.clip or "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "type": "minimax",
                "device": "default",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": args.video_vae or "minimax_h3_video_vae_int8_convrot.safetensors"},
        },
        "4": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": args.audio_vae or "minimax_h3_audio_vae_fp32.safetensors"},
        },
    }

    # Model chain: UNET -> optional Turbo LoRA -> optional Realism LoRA -> optional MiniMaxH3SigmaShift
    model_ref = ["1", 0]
    if preset["use_turbo"] and turbo_lora:
        wf["5"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": model_ref,
                "lora_name": turbo_lora,
                "strength_model": float(args.turbo_strength),
            },
        }
        model_ref = ["5", 0]

    if args.realism_lora:
        wf["6"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": model_ref,
                "lora_name": args.realism_lora,
                "strength_model": float(args.realism_strength),
            },
        }
        model_ref = ["6", 0]

    if preset["use_turbo"] or shift_video != 12.0 or shift_audio != 3.0:
        wf["7"] = {
            "class_type": "MiniMaxH3SigmaShift",
            "inputs": {
                "model": model_ref,
                "shift_video": float(shift_video),
                "shift_audio": float(shift_audio),
            },
        }
        model_ref = ["7", 0]

    ec_thresh = (
        args.easycache_threshold
        if getattr(args, "easycache_threshold", None) is not None
        else preset.get("easycache_threshold")
    )
    if ec_thresh is not None and float(ec_thresh) > 0:
        wf["8"] = {
            "class_type": "EasyCache",
            "inputs": {
                "model": model_ref,
                "reuse_threshold": float(ec_thresh),
                "start_percent": float(preset.get("easycache_start", 0.25)),
                "end_percent": float(preset.get("easycache_end", 0.85)),
                "verbose": True,
            },
        }
        model_ref = ["8", 0]

    # Load reference images
    for idx, img_name in enumerate(images):
        wf[str(10 + idx)] = {
            "class_type": "LoadImage",
            "inputs": {"image": img_name},
        }

    # Optional reference audio (Ref2VA only)
    if args.audio:
        wf["19"] = {
            "class_type": "LoadAudio",
            "inputs": {"audio": args.audio},
        }

    # Conditioning & AV latent node
    if mode == "ref2va":
        cond_inputs = {
            "clip": ["2", 0],
            "vae": ["3", 0],
            "audio_vae": ["4", 0],
            "prompt": prompt_text,
            "width": width,
            "height": height,
            "length": frame_info["frames"],
            "ref_image_size": args.ref_image_size,
        }
        for idx in range(len(images)):
            cond_inputs[f"ref_images.ref_image_{idx}"] = [str(10 + idx), 0]
        if args.audio:
            cond_inputs["ref_audios.ref_audio_0"] = ["19", 0]
        wf["20"] = {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": cond_inputs}
    else:
        cond_inputs = {
            "clip": ["2", 0],
            "vae": ["3", 0],
            "prompt": prompt_text,
            "width": width,
            "height": height,
            "length": frame_info["frames"],
        }
        if mode in ("i2va", "fl2va") and len(images) >= 1:
            cond_inputs["first_frame"] = ["10", 0]
        if mode == "fl2va" and len(images) >= 2:
            cond_inputs["last_frame"] = ["11", 0]
        wf["20"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": cond_inputs}

    wf["21"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": int(args.seed)}}
    wf["22"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": preset["sampler"]}}

    if preset["scheduler"] == "manual":
        wf["23"] = {
            "class_type": "ManualSigmas",
            "inputs": {"sigmas": preset["manual_sigmas"]},
        }
    else:
        wf["23"] = {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": model_ref,
                "scheduler": preset["scheduler"],
                "steps": int(steps),
                "denoise": 1.0,
            },
        }

    wf["24"] = {
        "class_type": "BasicGuider",
        "inputs": {"model": model_ref, "conditioning": ["20", 0]},
    }
    wf["25"] = {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["21", 0],
            "guider": ["24", 0],
            "sampler": ["22", 0],
            "sigmas": ["23", 0],
            "latent_image": ["20", 1],
        },
    }
    wf["26"] = {"class_type": "VAEDecode", "inputs": {"samples": ["25", 0], "vae": ["3", 0]}}
    wf["27"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["25", 0], "vae": ["4", 0]}}

    images_out_ref = ["26", 0]
    if preset.get("use_upscaler"):
        wf["30"] = {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": upscaler_model},
        }
        wf["31"] = {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"upscale_model": ["30", 0], "image": ["26", 0]},
        }
        wf["32"] = {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["31", 0],
                "upscale_method": "lanczos",
                "width": preset["upscale_w"],
                "height": preset["upscale_h"],
                "crop": "disabled",
            },
        }
        images_out_ref = ["32", 0]

    wf["28"] = {
        "class_type": "CreateVideo",
        "inputs": {"images": images_out_ref, "audio": ["27", 0], "fps": FPS, "bit_depth": 8},
    }
    wf["29"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["28", 0],
            "filename_prefix": args.prefix,
            "format": "auto",
            "codec": "auto",
        },
    }

    payload = {
        "meta": {
            "mode": mode,
            "preset": args.preset,
            "preset_notes": preset["notes"],
            "unet": unet_name,
            "turbo_lora": turbo_lora,
            "realism_lora": args.realism_lora,
            "width": width,
            "height": height,
            "upscaled_to": (
                f"{preset['upscale_w']}x{preset['upscale_h']}" if preset.get("use_upscaler") else None
            ),
            "frames": frame_info["frames"],
            "actual_seconds": frame_info["actual_seconds"],
            "steps": steps,
            "sampler": preset["sampler"],
            "scheduler": preset["scheduler"],
            "shift_video": shift_video,
            "shift_audio": shift_audio,
            "warnings": warnings,
        },
        "workflow": wf,
    }
    write_json_output(payload, args.output)
    if warnings:
        for w in warnings:
            print(w, file=sys.stderr)


def cmd_comfy_submit(args):
    client = ComfyClient(args.server)
    try:
        if args.action == "submit":
            if not args.workflow:
                print("Error: --workflow is required for action=submit", file=sys.stderr)
                sys.exit(1)
            raw_obj = json.loads(Path(args.workflow).read_text(encoding="utf-8-sig"))
            wf = raw_obj["workflow"] if "workflow" in raw_obj else raw_obj
            resp = client.submit(wf)
            write_json_output({"action": "submit", "response": resp}, args.output)
        elif args.action == "status":
            if not args.prompt_id:
                print("Error: --prompt-id is required for action=status", file=sys.stderr)
                sys.exit(1)
            hist = client.history(args.prompt_id)
            q = client.queue()
            done = args.prompt_id in hist
            status_str = hist[args.prompt_id].get("status", {}).get("status_str") if done else "running_or_queued"
            write_json_output(
                {
                    "action": "status",
                    "prompt_id": args.prompt_id,
                    "done": done,
                    "status": status_str,
                    "queue_running": len(q.get("queue_running", [])),
                    "queue_pending": len(q.get("queue_pending", [])),
                },
                args.output,
            )
        elif args.action == "fetch":
            if not args.prompt_id or not args.video_out:
                print("Error: --prompt-id and --video-out required for action=fetch", file=sys.stderr)
                sys.exit(1)
            hist = client.history(args.prompt_id)
            if args.prompt_id not in hist:
                print(f"Error: prompt_id {args.prompt_id} not finished yet.", file=sys.stderr)
                sys.exit(1)
            item = hist[args.prompt_id]
            if item.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI execution error: {item.get('status')}")
            found = None
            for node_out in item.get("outputs", {}).values():
                for media in (
                    node_out.get("videos") or node_out.get("gifs") or node_out.get("images") or []
                ):
                    if str(media.get("filename", "")).lower().endswith((".mp4", ".webm", ".mkv")):
                        found = media
                        break
                if found:
                    break
            if not found:
                raise RuntimeError(f"No video output found in ComfyUI history for {args.prompt_id}")
            blob = client.download_view(
                found["filename"], found.get("subfolder", ""), found.get("type", "output")
            )
            dst = Path(args.video_out)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(blob)
            write_json_output(
                {
                    "action": "fetch",
                    "prompt_id": args.prompt_id,
                    "video_out": str(dst),
                    "size_bytes": len(blob),
                    "source_filename": found["filename"],
                },
                args.output,
            )
    except (RateLimitError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def measure_temporal_mad(video_path):
    """Stdlib-only frame-to-frame Mean Absolute Difference (MAD) & jump spike audit."""
    w, h = 160, 90
    frame_bytes = w * h * 3
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(video_path),
        "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or len(res.stdout) < frame_bytes * 3:
        return None
    buf = memoryview(res.stdout)
    n = len(buf) // frame_bytes
    diffs = []
    prev = buf[0:frame_bytes]
    for i in range(1, n):
        cur = buf[i * frame_bytes : (i + 1) * frame_bytes]
        s = sum(abs(a - b) for a, b in zip(cur, prev))
        diffs.append(s / frame_bytes)
        prev = cur
    sorted_d = sorted(diffs)
    med = sorted_d[len(sorted_d) // 2]
    top_ratio, top_frame = 1.0, 0
    for i in range(1, len(diffs) - 1):
        nbr = (diffs[i - 1] + diffs[i + 1]) / 2.0 + 0.15
        ratio = diffs[i] / nbr
        if ratio > top_ratio:
            top_ratio, top_frame = ratio, i + 1
    return {
        "frames_checked": n,
        "max_mad": round(max(diffs), 2),
        "med_mad": round(med, 2),
        "top_spike_ratio": round(top_ratio, 2),
        "top_spike_frame": top_frame,
        "flagged_jump": top_ratio >= 1.85,
    }


def cmd_qc_sheet(args):
    video = Path(args.video)
    if not video.exists():
        print(f"Error: video file not found: {video}", file=sys.stderr)
        sys.exit(1)

    probe = ffprobe_media(video)
    streams = probe.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(probe.get("format", {}).get("duration", 0.0))
    if dur <= 0:
        print(f"Error: invalid video duration ({dur}s)", file=sys.stderr)
        sys.exit(1)

    n_frames = int(args.frames)
    tile = "3x2" if n_frames == 6 else "4x2"
    fps_val = n_frames / max(dur, 0.5)

    sheet_out = Path(args.sheet_out)
    sheet_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vf",
        f"fps={fps_val:.4f},scale=480:-1,tile={tile}",
        "-frames:v",
        "1",
        "-update",
        "1",
        str(sheet_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not sheet_out.exists():
        print(f"Error: ffmpeg qc-sheet failed: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    data = {
        "video": str(video),
        "sheet_out": str(sheet_out),
        "sheet_size_bytes": sheet_out.stat().st_size,
        "frames_sampled": n_frames,
        "tile": tile,
        "duration_sec": round(dur, 4),
        "video_stream": {
            "codec": v_stream.get("codec_name") if v_stream else None,
            "width": v_stream.get("width") if v_stream else None,
            "height": v_stream.get("height") if v_stream else None,
            "fps": v_stream.get("r_frame_rate") if v_stream else None,
        },
        "audio_stream": {
            "codec": a_stream.get("codec_name") if a_stream else None,
            "sample_rate": a_stream.get("sample_rate") if a_stream else None,
            "channels": a_stream.get("channels") if a_stream else None,
        },
        "temporal_qc": measure_temporal_mad(video),
    }
    write_json_output(data, args.output)


def cmd_assemble(args):
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    clips = manifest.get("clips", [])
    if not clips:
        print("Error: manifest has no 'clips' entries.", file=sys.stderr)
        sys.exit(1)

    target_w = int(manifest.get("width", 1920))
    target_h = int(manifest.get("height", 1080))
    target_fps = int(manifest.get("fps", FPS))

    tmp_dir = Path(tempfile.mkdtemp(prefix="h3_assemble_"))
    try:
        norm_paths = []
        for idx, clip in enumerate(clips):
            src = Path(clip["path"])
            if not src.exists():
                raise RuntimeError(f"Clip missing: {src}")
            dst = tmp_dir / f"seg_{idx:03d}.mp4"
            cmd = ["ffmpeg", "-y"]
            if clip.get("trim_start") is not None:
                cmd += ["-ss", str(clip["trim_start"])]
            cmd += ["-i", str(src)]
            if clip.get("trim_end") is not None:
                start_v = float(clip.get("trim_start") or 0.0)
                dur_v = float(clip["trim_end"]) - start_v
                cmd += ["-t", f"{dur_v:.4f}"]
            vf_parts = []
            if clip.get("retime_factor") is not None:
                rf = float(clip["retime_factor"])
                if not (0.8 <= rf <= 1.2):
                    raise RuntimeError(f"retime_factor {rf} out of safe lip-sync drift range [0.8, 1.2]")
                vf_parts.append(f"setpts={rf:.6f}*PTS")
            vf_parts.append(
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,fps={target_fps},format=yuv420p"
            )
            vf = ",".join(vf_parts)
            cmd += [
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                "192k",
                str(dst),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Segment normalize failed ({src}): {res.stderr.strip()}")
            norm_paths.append(dst)

        merged = tmp_dir / "merged.mp4"
        dissolve_frames = int(args.dissolve_frames or 0)
        if dissolve_frames > 0 and len(norm_paths) > 1:
            # Seamless N-frame xfade + acrossfade join on one frame grid (masks ~1% zoom shift on pinned-still chunks)
            d_sec = dissolve_frames / float(target_fps)
            durs = [float(ffprobe_media(p).get("format", {}).get("duration", 0.0)) for p in norm_paths]
            inputs_cmd = []
            for p in norm_paths:
                inputs_cmd += ["-i", str(p)]
            v_filters = []
            a_filters = []
            cur_v = "[0:v]"
            cur_a = "[0:a]"
            cum_dur = durs[0]
            for i in range(1, len(norm_paths)):
                offset = max(0.05, cum_dur - d_sec)
                out_v = f"[v{i}]" if i < len(norm_paths) - 1 else "[vout]"
                out_a = f"[a{i}]" if i < len(norm_paths) - 1 else "[aout]"
                v_filters.append(
                    f"{cur_v}[{i}:v]xfade=transition=fade:duration={d_sec:.4f}:offset={offset:.4f}{out_v}"
                )
                a_filters.append(
                    f"{cur_a}[{i}:a]acrossfade=d={d_sec:.4f}:c1=tri:c2=tri{out_a}"
                )
                cur_v, cur_a = out_v, out_a
                cum_dur = offset + durs[i]
            fc = ";".join(v_filters + a_filters)
            res = subprocess.run(
                [
                    "ffmpeg", "-y", *inputs_cmd,
                    "-filter_complex", fc,
                    "-map", "[vout]", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
                    str(merged),
                ],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                raise RuntimeError(f"ffmpeg dissolve merge failed: {res.stderr.strip()}")
        else:
            list_file = tmp_dir / "concat.txt"
            list_file.write_text(
                "\n".join(f"file '{p.as_posix()}'" for p in norm_paths) + "\n", encoding="utf-8"
            )
            res = subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(merged)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                raise RuntimeError(f"ffmpeg concat failed: {res.stderr.strip()}")

        out_video = Path(args.video_out)
        out_video.parent.mkdir(parents=True, exist_ok=True)
        final_cmd = ["ffmpeg", "-y", "-i", str(merged)]
        post_vf = []
        film_grain = int(args.film_grain or 0)
        if film_grain > 0:
            # Subtle temporal 35mm film grain (Hypernatural anti-plastic-skin post trick, $0 GPU cost)
            post_vf.append(f"noise=c0s={film_grain}:c0f=t+u")
        if args.srt:
            srt_p = Path(args.srt)
            if not srt_p.exists():
                raise RuntimeError(f"SRT file not found: {srt_p}")
            # Copy SRT into tmp_dir with simple path for Windows ffmpeg subtitles filter safety
            safe_srt = tmp_dir / "subs.srt"
            safe_srt.write_text(srt_p.read_text(encoding="utf-8-sig"), encoding="utf-8")
            srt_escaped = safe_srt.as_posix().replace(":", r"\:")
            post_vf.append(
                f"subtitles='{srt_escaped}':force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=26'"
            )
        if post_vf:
            final_cmd += [
                "-vf",
                ",".join(post_vf),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
            ]
        else:
            final_cmd += ["-c:v", "copy"]

        final_cmd += [
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out_video),
        ]
        res = subprocess.run(final_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"ffmpeg final master failed: {res.stderr.strip()}")

        probe = ffprobe_media(out_video)
        dur = float(probe.get("format", {}).get("duration", 0.0))
        write_json_output(
            {
                "video_out": str(out_video),
                "clip_count": len(clips),
                "duration_sec": round(dur, 4),
                "size_bytes": out_video.stat().st_size,
                "loudness_target_lufs": -14.0,
                "vietsub_burned": bool(args.srt),
            },
            args.output,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def build_parser():
    parser = argparse.ArgumentParser(
        description="MiniMax-H3 Live-Action Drama Director CLI Toolkit"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 1. align-frames
    p1 = sub.add_parser("align-frames", help="Calculate exact 17k+5 MiniMax-H3 frames at 24fps")
    p1.add_argument("--seconds", type=float, required=True, help="Target clip duration in seconds")
    p1.add_argument(
        "--allow-unclamped",
        action="store_true",
        help="Allow frames outside 4-15s trained range (e.g. 5-frame MiniMaxH3AddGuide)",
    )
    p1.add_argument("--output", required=True, help="Output JSON path")

    # 2. lint-prompt
    p2 = sub.add_parser("lint-prompt", help="Validate H3-Context-IR prompt syntax and drama rules")
    p2.add_argument("--prompt-file", required=True, help="Path to prompt text file")
    p2.add_argument(
        "--mode",
        required=True,
        choices=["ref2va", "t2va", "i2va", "fl2va", "l2va"],
        help="MiniMax-H3 generation mode",
    )
    p2.add_argument("--duration", type=float, required=True, help="Target clip duration in seconds")
    p2.add_argument("--num-images", type=int, required=True, help="Number of reference/keyframe images")
    p2.add_argument("--has-audio", action="store_true", help="Whether <Audio 1> reference is attached")
    p2.add_argument("--allow-stylized", action="store_true", help="Skip live-action purity check")
    p2.add_argument("--output", required=True, help="Output JSON lint report path")

    # 3. tts-vi
    p3 = sub.add_parser("tts-vi", help="Synthesize Vietnamese dialogue via local VieNeu-TTS v3")
    p3.add_argument("--text", required=True, help="Vietnamese dialogue line")
    p3.add_argument("--voice", required=True, help="VieNeu-TTS voice preset name")
    p3.add_argument("--wav-out", required=True, help="Output WAV file path")
    p3.add_argument("--vieneu-exe", help="Override path to vieneu-tts-cli.exe")
    p3.add_argument("--output", required=True, help="Output JSON path")

    # 4. pad-audio
    p4 = sub.add_parser("pad-audio", help="Pad & align dialogue WAV to 48kHz stereo on 17k+5 grid")
    p4.add_argument("--wav-in", required=True, help="Input WAV/audio path")
    p4.add_argument("--wav-out", required=True, help="Output padded 48kHz stereo WAV path")
    p4.add_argument("--lead-in", type=float, default=0.15, help="Silence lead-in seconds (default 0.15)")
    p4.add_argument("--tail-pad", type=float, default=0.45, help="Minimum tail buffer seconds (default 0.45)")
    p4.add_argument("--output", required=True, help="Output JSON path")

    # 5. build-workflow
    p5 = sub.add_parser("build-workflow", help="Generate official 0-custom-node ComfyUI API workflow JSON")
    p5.add_argument(
        "--mode",
        required=True,
        choices=["ref2va", "t2va", "i2va", "fl2va"],
        help="Generation mode",
    )
    p5.add_argument(
        "--preset",
        required=True,
        choices=list(PRESET_SPECS.keys()),
        help="Quality/speed preset (default recommended: draft_480p; hero close-up: hero_736p; fast 8-step: turbo8_768p)",
    )
    p5.add_argument("--prompt-file", required=True, help="Validated prompt text file")
    p5.add_argument("--seconds", type=float, required=True, help="Target clip duration in seconds")
    p5.add_argument("--images", nargs="*", default=[], help="Reference/keyframe image filenames inside ComfyUI/input/")
    p5.add_argument("--audio", help="Optional reference audio filename inside ComfyUI/input/ (Ref2VA only)")
    p5.add_argument("--seed", type=int, required=True, help="RandomNoise seed")
    p5.add_argument("--prefix", required=True, help="SaveVideo filename_prefix")
    p5.add_argument("--steps", type=int, help="Override inference steps")
    p5.add_argument("--width", type=int, help="Override canvas width (multiple of 32)")
    p5.add_argument("--height", type=int, help="Override canvas height (multiple of 32)")
    p5.add_argument("--shift-video", type=float, help="Override video flow shift (6.0 or 12.0)")
    p5.add_argument("--shift-audio", type=float, help="Override audio flow shift (default 3.0)")
    p5.add_argument("--ref-image-size", choices=["match", "max"], default="match")
    p5.add_argument("--unet", help="Override UNETLoader checkpoint filename")
    p5.add_argument("--clip", help="Override CLIPLoader checkpoint filename")
    p5.add_argument("--video-vae", help="Override video VAELoader filename")
    p5.add_argument("--audio-vae", help="Override audio VAELoader filename")
    p5.add_argument("--turbo-lora", help="Override Turbo LoRA filename in models/loras/")
    p5.add_argument("--turbo-strength", type=float, default=1.0, help="Turbo LoRA strength (default 1.0)")
    p5.add_argument("--realism-lora", help="Optional Realism People / CloseUp LoRA filename in models/loras/")
    p5.add_argument("--realism-strength", type=float, default=0.8, help="Realism LoRA strength (default 0.8)")
    p5.add_argument("--upscaler-model", help="Override upscaler filename (must be RealESRGAN_x4plus.pth for live-action)")
    p5.add_argument("--allow-anime-upscaler", action="store_true", help="Permit anime upscaler for non-live-action")
    p5.add_argument("--easycache-threshold", type=float, help="Optional EasyCache reuse_threshold (e.g. 0.10 for L4 B2; set 0 to disable)")
    p5.add_argument("--allow-short", action="store_true", help="Allow short MV 17k+5 counts below 4s (e.g. 39f/56f/73f/90f)")
    p5.add_argument("--output", required=True, help="Output workflow JSON path")

    # 6. comfy-submit
    p6 = sub.add_parser("comfy-submit", help="Rate-limited ComfyUI submit/status/fetch client")
    p6.add_argument("--server", required=True, help="ComfyUI base URL (e.g. http://127.0.0.1:8188)")
    p6.add_argument("--action", required=True, choices=["submit", "status", "fetch"])
    p6.add_argument("--workflow", help="Workflow JSON file (required for submit)")
    p6.add_argument("--prompt-id", help="ComfyUI prompt_id (required for status/fetch)")
    p6.add_argument("--video-out", help="Output MP4 path (required for fetch)")
    p6.add_argument("--output", required=True, help="Output JSON path")

    # 7. qc-sheet
    p7 = sub.add_parser("qc-sheet", help="Probe clip streams and extract 6- or 8-frame QC contact sheet PNG")
    p7.add_argument("--video", required=True, help="Input MP4 video path")
    p7.add_argument("--sheet-out", required=True, help="Output contact sheet PNG path")
    p7.add_argument("--frames", type=int, required=True, choices=[6, 8], help="Frames in grid (6=3x2, 8=4x2)")
    p7.add_argument("--output", required=True, help="Output JSON metadata path")

    # 8. assemble
    p8 = sub.add_parser("assemble", help="Concat clips, retime drift, optional N-frame dissolve, 35mm grain, -14 LUFS & Vietsub")
    p8.add_argument("--manifest", required=True, help="JSON manifest with 'clips' array (supports trim_start/trim_end/retime_factor)")
    p8.add_argument("--video-out", required=True, help="Final output MP4 path")
    p8.add_argument("--dissolve-frames", type=int, default=0, help="Optional seamless cross-dissolve frames between chunks (e.g. 5 for pinned-still lip-sync)")
    p8.add_argument("--film-grain", type=int, default=0, help="Optional subtle 35mm film grain strength (e.g. 5-7 to remove AI skin sheen for free)")
    p8.add_argument("--srt", help="Optional UTF-8 Vietsub SRT file to burn in")
    p8.add_argument("--output", required=True, help="Output JSON report path")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "align-frames": cmd_align_frames,
        "lint-prompt": cmd_lint_prompt,
        "tts-vi": cmd_tts_vi,
        "pad-audio": cmd_pad_audio,
        "build-workflow": cmd_build_workflow,
        "comfy-submit": cmd_comfy_submit,
        "qc-sheet": cmd_qc_sheet,
        "assemble": cmd_assemble,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

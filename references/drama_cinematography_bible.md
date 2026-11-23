# Live-Action Drama Cinematography & Directing Bible (MiniMax-H3)

This reference fuses official **MiniMax-H3** narrative production principles (`h3-prompt-writing`, `3d-animation-short-generator`, `music-video-subtitle-generator`), community-proven **Singularity** prompt engineering, **Director-Style** scene craft (`ComfyUI-ShotWorkspace`), and real-world live-action drama directing rules.

---

## 1. Global Live-Action Drama Style Lock

Replace vague buzzwords (*"cinematic, 8K, masterpiece, ultra-detailed"*) with concrete optical, lighting, and material specifications:

- **Camera & Glass:** `Live-action theatrical 35mm drama photography shot on ARRI Alexa Mini LF with 50mm anamorphic prime lenses` (or `35mm spherical prime` for documentary realism, `85mm` for intimate close-ups with creamy shallow depth of field).
- **Skin & Materials:** `natural human skin pores, fine eyelashes, subtle peach fuzz, realistic cloth folds and weight, specular moisture/tears/raindrops, authentic fine 35mm film grain — strictly real-life live-action film, zero anime, zero CGI plastic smoothing, never sped up`.
- **East Asian Drama Realism Anchor (optional):** When depicting East Asian casts, explicitly anchor natural lighting and realistic East Asian facial aesthetics (`East Asian realism, natural soft practical lighting, authentic skin texture without airbrushing`).
- **Motion Cadence:** `unhurried, measured real-human motion cadence` — avoid rushed adverbs (`briskly`, `snappy`, `swiftly`, `hurriedly`) unless directing an actual fight or chase stunt!

> **Anti-Stiffness Rule (Critical for 8-Step Turbo):** Never freeze an actor with overly rigid phrasing like *"keep everything from the first frame unchanged"* or generate ultra-short `2.5–3s` (`< 100f`) Ref2VA clips. Keep narrative clips **`5–10.1s` (`124–243f`)** and write active causal motion chains so body weight and breathing stay alive.

---

## 2. Pre-Production: Character Bible & Spatial Anchor Chain

### A. Character Bible (Zero Identity Drift)
For every recurring actor (`<Subject N>`), lock **3–5 quantified physical micro-anchors** that survive angle and lighting shifts:
- **Face & Hair:** exact hair length/parting/bangs, distinctive marks (e.g., *tiny beauty mark beneath right corner of lower lip*, *delicate silver side hairpin on right temple*, *thin scar over left eyebrow*).
- **Wardrobe & Jewelry:** exact garments, collar state, and small metallic anchors (*dark tailored blazer over open-collar white shirt with thin silver vertical bar pendant necklace*).
- **Reference Role Separation:**
  - `fully_preserved`: Keep face, hair, micro-anchors, AND outfit verbatim (best for same-scene continuity).
  - `partially_preserved`: Keep face/hair/likeness strictly locked while transferring wardrobe/environment cleanly (e.g., studio portrait → rain-drenched charcoal trench coat).
  - `attribute_transfer`: Transfer ONLY lighting, camera rhythm, or motion from a reference image/video while keeping actor identity from `<Picture 1>`.

> **Reference Image Rule:** A reference picture is NOT automatically Frame 0 in `Ref2VA`! Only use `<Picture N>` as an explicit start/end keyframe in `I2VA` / `FL2VA` / `L2VA`. In `Ref2VA`, bind character portraits and clean empty location plates to `<Subject N>` inside `subject_definitions:`.

### B. 6-Column Standardized Shot Table (Multi-Shot Episodes & MVs)
Before generating prompts for a multi-shot drama or MV, plan every shot in a 6-column table:

| Shot ID | Dur (`17k+5`) | Framing & 180° Axis | Action Chain (`Init → Trigger → Action → End State`) | Dialogue & Silent-Listener Lock | Soundscape, Music & Spatial Anchor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SC01` | `10.125s` (`243f`) | MCU Two-Shot, slow push-in; `S1` left → looking right, `S2` right → looking left | `S2` lifts hand slowly → cups `S1` cheek → `S1` leans into palm → cut to tight 2-shot → foreheads touch | `S1` whispers line 1 (`S2` silent listening); `S2` murmurs line 2 (`S1` lowers eyes) | Rain on glass, soft cloth rustle, minimalist solo piano; anchor: tall rain-streaked window behind `S2` |

---

## 3. Directing Rules That Separate Cinema From "AI Slop"

### Rule 1: The 180-Degree Screen-Axis Rule
When shooting a two-person conversation across cuts:
- Lock an imaginary axis between `<Subject 1>` and `<Subject 2>`.
- Always state screen placement and gaze direction explicitly in EVERY shot:
  - Shot A: `<Subject 1> on frame-left facing slightly right toward <Subject 2>`
  - Shot B (reverse/OTS): `<Subject 2> on frame-right facing slightly left toward <Subject 1>`
- **Eyeline rule:** Frontal framing does NOT mean addressing the camera! Explicitly state whether the actor looks *slightly off-lens toward `<Subject 2>`* or *squarely into the camera lens*.

### Rule 2: Action Chains (Never Isolated Verbs)
Replace single verbs (*"she reacts"*, *"he walks over"*) with a physical causal sequence:
```text
Initial State → Trigger → Preparation → Primary Action → Contact / Momentum → Physical Feedback (hair/fabric/breath) → Final Settled State
```
- **Define the Ending State!** AI clips degrade in the last 1.5–2 seconds if the prompt runs out of visual instructions. Always specify what the frame settles onto (*"...her lips close into a quiet breath as she holds his gaze under the warm lamp light"*).

### Rule 3: Cue-Triggered Listening & Subtext (Director-Style Craft)
- **Convert emotions into observable micro-actions:** Never write *"she feels heartbroken."* Write: *"her gaze drops to the porcelain cup, throat tightening in a quiet swallow, lower lip trembling slightly before she blinks away moisture."*
- **Give speakers different tactics:** One presses gently; the other deflects or hesitates. Avoid generic routine smiling or synchronized nodding after every line.
- **Explicit Silent-Listener Lock:** Whenever `<Subject 1>` delivers a `<d>...</d>` line, explicitly state that `<Subject 2>` **remains silent, listening** (plus ONE visible listener reaction: a slight shift of eyes, a released grip, or a slow inhale). This eliminates the #1 multi-character H3 bug where both mouths move during one line!

### Rule 4: The One-Move-Per-Shot Camera Rule
Never stack 3 simultaneous camera moves (*"orbit while craning up and zooming in"*). Specify ONE clear move per shot with exact **type + direction + amplitude + speed + target**:
- `pushing slowly inward with small amplitude at slow speed` (psychological intimacy / revelation)
- `pulling smoothly backward with medium amplitude at slow speed` (isolation / environment reveal)
- `static locked-off camera` (lets subtle micro-expressions and whispered dialogue command 100% attention)
- `sweeping medium-wide arc shot orbiting smoothly with medium amplitude at normal speed` (hero reveal / stunt / romantic climax)
- `gentle handheld tracking shot following from three-quarter front` (raw emotional realism)

### Rule 5: Motivated Practical Lighting (Warm vs Cool Contrast)
Always name the **light source, direction, color temperature, and shadow falloff**:
- **Intimate Interior Drama:** `Warm amber tungsten practical table lamp from frame-left casting soft sculptural shadows across cheekbones, contrasting with cool twilight-blue rain-beaded window light from behind, rich 70:30 dark-to-light shadow ratio.`
- **Rainy Neon Noir:** `Wet concrete reflecting warm sodium streetlamps and cyan-blue skyscraper signage, crisp backlit rain streaks, subtle rim light separating dark hair from night shadows.`
- **Golden Hour Outdoor:** `Low late-afternoon golden sun grazing hair edges from back-left, soft open sky fill on face, floating warm dust motes.`

---

## 4. Dual-Mode Dialogue & Audio Mastery

### Mode A: Native MiniMax-H3 Dialogue (Best for Chinese & English Drama)
- **Syntax:** `<d>[Chinese] 别离我这么近……心跳快藏不住了。</d>` or `<d>[English] I waited by the station until the last train left.</d>`
- **Word Budget:** `10–15` English words or `10–16` Chinese syllables per **5 seconds** of speaking time. Leave `0.5–1.5s` of breath/reaction before and after speech so lines never clip or rush!
- **Physical Delivery Cues:** Direct the voice through breath and posture (*"speaks in a low, unhurried, slightly hoarse whisper with a quiet exhale"*).
- **Audio Separation:**
  - `overall_soundscape:` = diegetic room tone, rain on glass, fabric rustle, footsteps, clinking cups, breathing.
  - `non_diegetic_music:` = score audible only to the audience. **For stark dramatic tension, write `non_diegetic_music: N/A` explicitly** — never leave it blank or the model invents generic upbeat background music!

### Mode B: Vietnamese Dialogue & Locked Cast Voices (`VieNeu-TTS` + `<Audio 1>`)
MiniMax-H3 does not speak natural Vietnamese from text alone. For Vietnamese drama (or strict cross-episode voice identity):
1. Synthesize each Vietnamese line locally with `h3_drama_cli.py tts-vi` (`VieNeu-TTS v3 Turbo`).
2. Align and pad the WAV to `48kHz stereo` matching an exact `17k + 5` frame length (`4.1s–15.0s`, `0.15s` lead-in) via `h3_drama_cli.py pad-audio`.
3. Attach as `ref_audio_0` (`<Audio 1>`) alongside at least ONE image ref (H3 NEVER accepts audio alone without image/video!).
4. In `retention_analysis:`:
   - **`<Audio 1>: fully_copy`** → Preserves the exact Vietnamese speech waveform and timing while driving realistic facial lip-sync, throat/jaw movement, and matching ambient SFX!
   - **`<Audio 1>: reference`** → Clones vocal timbre/warmth from a clean `3–10s` voice sample to speak new Chinese/English `<d>...</d>` lines across multiple scenes without voice drift!
5. Post-render: Trim the tail padding cleanly to `trim_end_sec` during `assemble`.

---

## 5. Multi-Shot Continuity & Music Video (MV) Mode

When producing a **>15s continuous scene or full 3-minute MV**:
1. **Master Audio Lock (MV):** Lock the song/BGM first, split into beat-aligned `5–10s` segments (`124–243f`), and match hard cuts to downbeats/vocal phrasing.
2. **Keyframe-First Hybrid (`Krea-2 Turbo` → `H3 FL2VA/I2VA Turbo 8-step`):**
   - Generate crisp 35mm establishing & hero frames using **Krea-2 Turbo** (`8 steps`, optionally with `krea2_style_reference.safetensors` to lock lighting/color grade across all shots).
   - Animate each shot with **MiniMax-H3 FL2VA + 8-step Turbo LoRA** (`I2VA` / `FL2VA`) for punchy dynamics and 2.5× speed — OR use **`Ref2VA`** whenever 2+ specific actor faces + audio/dialogue must stay locked simultaneously!
3. **Seamless Tail-to-Head Continuation:** Use ComfyUI's built-in **`MiniMaxH3AddGuide`** node to anchor the previous clip's final `5` frames (`17*0 + 5`) at `frame_idx = 0` of the next clip for continuous long-take camera flow.

---

## 6. Production-Hardened Field Traps (Hypernatural H3 Max Empirical Lessons)

Battle-tested across hundreds of real MiniMax-H3 dialogue & lip-sync productions (`hn/h3-max-lipsync-a-still`, `hn/h3-max-dialogue`, `hn/h3-prompt-format`):

1. **NEVER Put Human-Voice Words in `overall_soundscape:` (Even With Dialogue!):**
   - H3 turns `overall_soundscape:` directly into ambient audio. Words like `voice`, `vocal`, `speech`, `words`, `talking`, `chatter`, `murmur`, `conversation`, `muttering`, or `whisper` — even as metaphors — spawn phantom ghost voices or doubled reverb!
   - Use ONLY physical/environmental sound verbs: `hum`, `hiss`, `rustle`, `shuffle`, `tick`, `patter`, `creak`, `soft breathing`. Keep ALL speech direction strictly inside `detailed_description:` / `integrated_multimodal_description:`.
2. **NEVER Put Character Names or `@handles` Outside `<d>` Blocks:**
   - MiniMax-H3 frequently renders stray proper names or `@handles` as literal on-screen text! Outside `<d>`, always use `<Subject 1>` + plain visual role (`"<Subject 1>, the woman,"`) or pronouns.
3. **Close the Cast & Only Attach Physically Present Actors:**
   - Add an explicit closed-cast clause on intimate scenes: `"Only <Subject 1> and <Subject 2> are in this shot; no one else enters, appears in the background, or speaks."` (Prevents phantom 3rd extras or cloned duplicates.)
   - NEVER attach a reference picture for someone only visible on a phone/TV screen — H3 can morph the live actor in the room into that face!
   - Set any visible TV/monitor/phone screen to a fixed state (`"switched off, solid black"` or `"a paused still"`) or H3 animates an invented person onto the screen.
4. **Lock `LEFT` / `RIGHT` Positions + `(Sn)` Speaker IDs at EVERY Spoken Line:**
   - In two-handers, state BOTH screen position and `(Sn)` before every `<d>` block (`"<Subject 1> (S1) on the LEFT, speaking softly, asks: <d>[Chinese] ...</d>"`). Names alone frequently swap lines between actors!
5. **Silent-Shot Purity (No Speaking Verbs When No `<d>` Exists):**
   - When a shot has NO spoken words, omit `(Sn)`, `<d>`, AND every speaking verb (`says`, `talks`, `explains`, `chats`, `asks`, `mouths`, `"mid-conversation"`). Write visible gestures + `"every person in frame keeps their lips closed; smiles stay closed-mouthed and silent"`.
6. **The "Pink-Elephant" Negative-Accessory Trap:**
   - Never mention a removed item negatively (`"no pin or badge"`, `"no glasses"`, `"no scar"`) — H3 often spawns the named object within 1 second! Describe the clean positive state instead (`"a plain, unadorned collar, identical from first frame to last"`), and edit unwanted accessories out of reference photos first.
   - Similarly, never carry a prop rule into a shot without that prop (otherwise H3 rolls the prop in from off-screen).
7. **External Audio Lip-Sync (`<Audio 1>`) & Long Monologue Chunks:**
   - **Always include the spoken words + `<d>` block in the prompt** even when driving from `<Audio 1>` — the text prompt never hears the audio, and omitting the words can produce a closed silent mouth over playing audio!
   - **Always isolate the voice** (mono/clean speech, zero BGM mixed into `<Audio 1>`). Pad short lines (`< 4.5s`) with silence — NEVER widen the audio window into the next speaker's line.
   - **Ban finger counting:** Never prompt `"holds up three fingers on 'Finally'"` — tie natural open-hand beats to exact words instead.
   - **Pinned-Still + 5-Frame Dissolve for Long Monologues (> 15s):** Cut long tracks at sentence pauses (`. ? !`) into `5–14s` chunks, pin the SAME still as `first_frame` AND `last_frame`, and join chunks on ONE frame grid with a **5-frame dissolve (`--dissolve-frames 5`)** to mask the ~1% zoom variance between separate renders.
8. **Fix 3–5% Linear Lip-Sync Drift for Free (Don't Re-Roll!):**
   - On ~15–20% of 10s lip-sync chunks, lips drift 3–5% slow (`200–500 ms` late by the end) with the **exact same slope across every seed**. Do NOT burn CU re-rolling! Apply `retime_factor` (e.g. `0.96`) in `assemble` manifest to adjust video PTS cleanly in `ffmpeg`.
   - Always listen to the final 1.5s of dialogue renders: H3 occasionally fills tail silence by repeating the last spoken phrase (`2/24` takes); trim cleanly if caught.
9. **Static Camera Lock Clause:**
   - MiniMax-H3 pushes in slowly by default. When a scene strictly requires a locked tripod frame, write verbatim: `"Static shot: the camera stays locked on the opening framing for the whole clip, with no zoom, push-in, pull-back, pan, or cut."`
10. **First/Last Frame Continuity, Unchanged-Element Locks & Zero-Cost Film Grain (`guide-animate-a-shot` + `h3-max-image-to-video`):**
    - **Derive last frame strictly from the locked first frame** (text edit only — never two independently generated stills, or hair & collars morph mid-shot!).
    - **Pad reference images (`256–2048 px`, aspect `0.4–2.5`), never crop**; use single clean views rather than crowded multi-panel sheets when driving tight live-action close-ups.
    - **Lock unchanged sky/lighting/background explicitly:** Unlocked, H3 can turn an overcast grey sky blue or light up dark background buildings (`"The sky stays the exact same pale overcast grey from the first frame to the last."`).
    - **Spell out exact counts & limits:** `"blinks exactly once"`, `"tips the cup a third of the way, base below her chin"`, `"walks left in profile, never turning toward the camera"`.
    - **First-person POV trap:** Give eye height/posture and express drowsiness/blinks ONLY via subtle edge darkening/vignette — **NEVER name eyelids or eyelashes** (draws lid tissue across the frame!).
    - **Idle opening trim & anti-plastic film grain:** Trim idle opening frames at native 24fps (never speed up a clip to fit), and apply subtle 35mm post film grain (`--film-grain 6` in `assemble`) to erase AI skin sheen for `$0` GPU cost!
    - **Use one seed per scene job** so any 1-line prompt tweak is a true scientific A/B test.

---

## 9. TRUE 1:1 Live-Action MV Cloning Protocol (Zero Mid-Clip Enlargement)

Proven across a complete 143-cut, 4:38 full MV clone (*"Nơi Này Có Anh"*) replacing both original leads while matching exact original camera framing, lighting, cut timing, and lossless song sync:

1. **Why `<Video 1>` `Ref2VA` Fails for MV Actor Swaps:** Feeding an original MV clip into `<Video 1>` consumes ~95%+ attention tokens and copies the original singer/actor's face pixel-for-pixel. Instead, use **2-Stage Frame-Swap → Video**:
   - **Stage 0 (Zero-CU B-Roll Filter):** Classify every scene cut first (`ffmpeg select='gt(scene,0.19)'`). Pure scenic B-roll, hands, feet, aerial drones, and back-view silhouettes (~45–50% of most MVs) have no visible faces — **keep them original** and apply matching local 1080p Lanczos + CAS + 35mm grain (`0 CU`, maximal authenticity).
   - **Stage 1 (Distance-Calibrated `Krea-2 Identity Edit V2`):** Swap actor keyframes at `960×544` (`8 steps`, `CFG 1.0`, `source_image = orig_frame` `aligned`, `source_image_b = actor_ref` `beside`). Calibrate `ref_boost` / `ref_boost_a` strictly by shot scale so distant bodies never bloat and reference outfits (blazers/uniforms) never bleed in:
     - **`CU` (Close-up):** `ref_boost = 2.75`, `ref_boost_a = 1.00`
     - **`MCU` (Medium close-up):** `ref_boost = 2.55`, `ref_boost_a = 1.00`
     - **`MS` (Medium 2-shot):** `ref_boost = 2.30`, `ref_boost_a = 1.08`
     - **`WS` (Wide / full-body):** `ref_boost = 1.85`, `ref_boost_a = 1.18`
     - For **2-person `MF` shots**, run 2 sequential passes (Male first → Female second), explicitly stating `"Keep the other person 100% untouched"` and `"NEVER copy blazer/suit from the reference photo; preserve exact outfit, figure height, and single-person count"`.
     - **Mandatory Keyframe QC Gate:** Visually inspect a compact before/after contact sheet of EVERY swapped frame BEFORE running MiniMax-H3. Catch & fix outfit bleed, gender-swap mixups, double-person ghosts, or cropped heads at `25s/frame` instead of wasting GPU minutes on bad videos.
   - **Stage 2 (Single-Frame Scale-Locked `I2VA` Default):**
     - **Default to Single-Frame `I2VA`** for all standard MV cuts (`≤ 4.5s`) and constant-framing actions (even wide running-to-hug shots!). Independently swapped `first_frame` + `last_frame` `FL2VA` pairs often differ by 10–25% in character height, forcing MiniMax-H3 to artificially zoom/enlarge the actor mid-clip or insert a double-exposure cross-fade dissolve.
     - Reserve **`FL2VA` (`first_frame` + `last_frame`)** ONLY for true multi-beat blocking changes (e.g., optical rack-focus pull or 8-second vertical crane tilt) where both frames are visually verified to share identical actor scale.
   - **Prompt-to-Pixel Purity & Micro-Anchor Lock:**
     - **NEVER mention an accessory absent from the swapped keyframe** (e.g., `"round glasses"`, `"black fur hat"`, `"cream knit beanie"` — if Krea-2 didn't draw it, mentioning it causes H3 to pop the item onto the actor mid-clip or spawn a second twin wearing it!).
     - **Explicitly reinforce true facial micro-anchors** on every `CU`/`MCU` video prompt (e.g., exact side of a small mole beneath the lower lip corner, silver hairpin on right temple) so 8-step Turbo diffusion preserves them cleanly.
     - **2-Tier Automated Video QC:** Combine visual 4–8 frame contact sheets with `frame-to-frame MAD spike` measurement (`qc-sheet`). Re-roll any clip with temporal jump (`spike > 1.85×`), flash, dissolve, or spawned accessory using `B1` (`FP8_scaled`, `EasyCache` OFF).



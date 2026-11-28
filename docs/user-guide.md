# WormsPy 2 user guide

WormsPy controls the WormsPy tracking epifluorescence microscope. It shows the behaviour
(brightfield) and calcium (fluorescence) cameras live, keeps a crawling animal centred by
moving the stage, and records both cameras frame-synchronised with the stage position.

This guide covers setting up the rig, calibrating it, and running a session. The file format
is in [recording-format.md](recording-format.md), and the one-off hardware checks are in
[rework/rig-bringup.md](rework/rig-bringup.md).

> **Draft status.** WormsPy 2 has been developed against a simulated rig. Steps marked
> *(rig check)* describe behaviour that is designed and tested in simulation but not yet
> confirmed on the microscope. They may change after bring-up.

---

## 1. Before you start

### What you need
- The microscope, with both FLIR cameras connected by USB 3. A GPIO cable must run from the
  calcium camera's output line to the behaviour camera's trigger input; the calcium camera
  sets the pace for both.
- The Zaber XY and Z stages, connected and powered.
- A dual-stick gamepad.
- A **calibration slide** that both cameras can see. Fluorescent beads work best: under
  transmitted light they show dark in brightfield and bright in fluorescence.

### Installing (once per PC)
1. Install the Spinnaker SDK (4.x for Python 3.12) from Teledyne FLIR, and [uv](https://docs.astral.sh/uv/).
2. In the WormsPy folder, run:
   ```
   uv sync --extra zaber --extra gamepad --extra analysis
   uv pip install spinnaker_python-<version>.whl
   ```
   The wheel ships with the Spinnaker SDK and must match your Python version (`cp312`). Use
   `--no-sync` with `uv run` afterwards so `uv` does not uninstall `spinnaker_python` or the
   optional extras.
3. Copy `config/rig.example.toml` to `config/rig.toml` and edit it (next section).

### Configuring the rig: `config/rig.toml`
Every key is optional; the example file lists them all with their defaults. The ones you must
set:

| Setting | What to enter |
|---|---|
| `[cameras.clock] serial` | The calcium camera's serial number (SpinView shows it). |
| `[cameras.follower] serial` | The behaviour camera's serial number. |
| `[stage] xy_port`, `z_port` | The Zaber serial ports (Zaber Launcher shows them). |
| `[stage.safe_range_um] z` | **A Z range where the objective cannot touch the plate or holder.** WormsPy never moves outside it, and writes it into the Zaber controllers so the firmware enforces it too. |
| `[paths] data_root` | Where sessions are saved. |

The `[cameras]` exposure, gain and frame rate values become the **Default** camera preset
(section 5). If rig.toml has a mistake, such as an exposure longer than the frame period or an
unknown key, WormsPy refuses to start and names the offending key.

### Trying it without hardware
`uv run wormspy --sim` runs everything against a simulated rig with a synthetic worm. It has
a **Simulator** menu, which slides a calibration slide under the objective. It is the safe way
to learn the controls.

---

## 2. Starting WormsPy

1. Close **SpinView** and **Zaber Launcher**. Each holds the devices exclusively.
2. Run `uv run --no-sync wormspy` from the WormsPy folder (or `.venv\Scripts\wormspy` on Windows).

If a camera is missing, WormsPy stops with a message naming the serial number it expected and
the ones it found. If the stage is missing, WormsPy still starts, so you can image, but a red
alarm says so. The joystick, tracking and calibration need the stage. If an optional
`[overview]` camera serial is configured, a **Global view** button appears in the header to
open the WormTraffic plate-overview window (in `--sim`, a synthetic multi-worm plate is
simulated automatically).

---

## 3. The main window

```
┌ WormsPy v2  [LIVE] [● REC rec-002] [TRACKING]      X · Y · Z µm   fps   GB free ┐
│ ALARMS (only when there are any)                                                │
│ ┌──────── Brightfield ─────────┐ ┌──────── Fluorescence ────────┐               │
│ │        live feed             │ │        live feed             │               │
│ └──────────────────────────────┘ └──────────────────────────────┘               │
│  histogram + LUT                  histogram + LUT                               │
│ [SESSION] [RECORDING] [TRACKING] [CAMERAS] [FOCUS & CALIBRATION]                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Header
- **Mode chips.** `IDLE` or `LIVE`; `● REC rec-NNN` while recording, with elapsed time and a
  drop count if any frames were lost; and the tracking status.
- **Global view.** Opens the WormTraffic third window when an overview camera is configured
  (or in `--sim`): displays real-time whole-plate worm tracks and the current high-mag FOV box,
  and lets you click any track to move the stage directly to that worm. Use **Calibrate (4
  pts)** or **Import YAML…** to map overview pixels to Zaber XY coordinates.
- **Readouts.** The stage position (µm), each camera's measured frame rate, and the free disk
  space in the data folder.

### Live feeds
Each feed shows its camera's whole sensor at the camera's aspect ratio; feeds do not pan or
zoom. On each feed:
- **The green crosshair** marks the image centre, where tracking holds the animal.
- **The green dot** is where the tracker sees the animal on the camera it tracks with. **A
  green ring** is the same point mapped onto the other camera; it appears once calibration
  has aligned the two cameras (section 4).
- **Double-click** anywhere to move the stage so that point comes to the centre. This needs a
  calibration.
- **Mask** tints what the tracker currently detects as the target. Use it to check that the
  tracker is seeing the worm and not debris.
- **LUT** changes the colour map (display only). **Auto levels** sets the display range from
  the current frame.
- **"saturated x %"** appears in red when pixels are clipped at the camera's maximum. Lower
  the exposure or gain.

### Histograms
Each histogram shows the camera's full range: 0–255 for brightfield, 0–65535 for fluorescence.
It uses log counts, so a few bright pixels still show. Use it to judge exposure:
- the signal should sit well clear of the right edge (clipping);
- it should also sit well clear of the left edge (lost in the noise).

Drag the two handles to set the display range. This never changes what is recorded;
recordings are always raw. *(rig check: whether the calcium camera's 16-bit data really spans
0–65535.)*

---

## 4. Calibration

Calibration tells WormsPy how stage movement maps onto each camera's image: scale, rotation
and mirroring for each camera, plus how the two cameras' images line up with each other.
Tracking, double-click-to-centre and plate positions all depend on it. There are no
hand-entered field-of-view constants.

### When to calibrate
- The first time you set up the rig.
- After changing the objective, the tube lens, a camera's mounting, or a camera's cropping or
  binning.
- **Not** after changing exposure, gain or frame rate.

The result is saved to `config/calibration.json`, loaded at every start, and copied into each
session's `session.json`.

### How to calibrate
1. Start WormsPy and press **Start live**. Tracking must be off.
2. Put the calibration slide on the stage and bring the beads into focus.
3. Make sure **both** cameras show the beads. Turn on the transmitted light for brightfield
   and the excitation light for fluorescence; LEDs are switched by hand.
4. Check the histograms: beads clearly visible, nothing saturated.
5. Press **Calibrate stage** (FOCUS & CALIBRATION card). Don't touch the joystick. The stage
   makes six moves of 100 µm and returns to where it started. It takes a few seconds.
6. The card shows **Calibrated**.

### If something goes wrong
| Message | Cause and fix |
|---|---|
| *"the image barely moved. Is a textured calibration slide in focus…"* | The camera saw nothing that moves with the stage. Check focus and illumination, and that the slide is actually under the objective. |
| *"residual … px is too large"* | The images didn't shift consistently. The slide moved (clip it down), the focus drifted, or something in view is moving. |
| *"Cameras not registered: … share no features"* | Calibration **succeeded**: tracking and double-click work. But one camera couldn't find the other's features, so the ring overlay and plate positions from the second camera are unavailable. Recalibrate with a slide both cameras see (fluorescent beads under transmitted light). |
| *"the stage did not reach its target in time"* | Stage problem. Check the stage is connected, and that the slide isn't at the edge of the safe range. |

A failed calibration never overwrites a good one.

---

## 5. Camera settings and presets

The **CAMERAS** card sets the frame rate, and each camera's exposure (ms) and gain (dB). The
calcium camera sets the frame rate. The behaviour camera takes one frame per calcium frame,
with its own exposure; a short one reduces motion blur.

- **Picking a preset** from the list applies it straight away.
- **Editing a number** does nothing until you press **Apply**. The preset list then shows
  *(edited)*.
- **Save as…** stores the *applied* settings under a name. Using an existing name replaces
  that preset. **Delete** removes the selected preset.
- **Default** is always there and always equals the `[cameras]` values in rig.toml. To change
  Default, edit rig.toml.

Applying settings restarts the live view for about a second, so the card is locked while
recording, tracking or calibrating. Settings the cameras can't take are refused with the
reason in the status bar. For example, the exposure must be shorter than the frame period
minus 2 ms: under 98 ms at 10 fps.

Every session and recording notes which preset and settings were used.

---

## 6. Running a session

A **session** is one animal on one plate. It is a folder named `<date>_<animal-id>` holding
the metadata you enter, the calibration, and one or more **recordings** (`rec-001`,
`rec-002`, …).

### Step by step

**Set up**
1. Start WormsPy (section 2). The header should show `IDLE` and no red alarms.
2. Press **Start live**. Both feeds should update, and both frame rates in the header should
   match the preset.
3. Pick the camera preset for the experiment (CAMERAS card).

**Find and focus the animal**

4. Place the plate. Find the animal with the **left stick** (XY). The stick is proportional,
   with fine control near the centre.
5. Focus with the **right stick** (Z). When it's sharp, press **Set focus**, or **Y** on the
   gamepad, to remember that Z. **Return to focus**, or **A**, goes back to it later. Z never
   leaves the safe range, whatever you do.
6. Check the exposure on the histograms (section 3).

**Open the session**

7. Fill in **Animal**, **Operator**, **Condition** and **Notes**, then press **New session**.
   The session folder's name appears next to the button. Fields are saved when you press New
   session; later edits don't change an open session.

**Track**

8. In the TRACKING card, choose the **Target**:
   - **Brightfield silhouette:** the worm's body on the camera (default **Dark on bright**, or switch **Polarity** to **Bright on dark** for darkfield / whole-body fluorescence).
   - **Fluorescent marker:** the brightest spot on a fluorescence camera, e.g. a neuron or a
     co-injection marker.

   **Camera** follows the target; change it only to track on a different camera. Both
   targets set their detection threshold automatically on every frame, so there is nothing to
   adjust for a normal session (section 10 explains how, and what to change if needed).
9. Press **Start tracking**, or **X** on the gamepad. The dot should sit on the worm and the
   stage should keep it near the crosshair. Tick **Mask** to see exactly what the tracker
   detected: the whole body should be tinted, and nothing else.

**Record**

10. Optionally set a duration **Limit** (seconds; `∞` means manual stop) in the RECORDING card,
    then press **● Record**, or **B**. The header shows `● REC rec-001 · 00:00` (and the limit if
    set), and stops automatically when the preset duration is reached.
11. Type a label and press **Mark event** to note stimuli and interventions (e.g. *glycerol
    on*). The marker lands on the next frame and is saved with it.
12. Press **■ Stop recording**, or **B**. The files are finalised. Press Record again for
    `rec-002` in the same session.

**Finish**

13. Press **Stop tracking** (X), then **Stop live**. For the next animal, go back to step 4
    and press **New session** with the new animal's details.
14. Close the window. WormsPy stops tracking, closes any open recording and releases the
    hardware.

### While recording
- **Refocusing is allowed.** Frames where Z moved are flagged in the data (`z_moved`), because
  their intensities aren't directly comparable.
- **Camera settings are locked**, and a new session can't be started.
- **Dropped frames never stop a recording.** They are written as blank placeholders, flagged
  in the data, counted in the header, and raised as an alarm.
- **Stop live is disabled.** Stop the recording first.

### Tracking states
| Status | Meaning | What happens |
|---|---|---|
| **Tracking** | Target found. | The stage follows it. |
| **Target lost** | No plausible target for 3 frames: the worm left the view, or something implausible appeared. | The stage ramps to a stop. Tracking resumes on its own when the worm reappears near where it was last seen. Bring it back with the joystick if needed. |
| **Joystick override** | You are moving the left stick. | The joystick always wins; tracking resumes when you let go. |
| **At stage limit** | The stage reached the edge of the safe range. | That axis stops. Recording continues. Move the plate or animal. |

### Gamepad (default mapping)
| Control | Action |
|---|---|
| Left stick | Move XY (proportional; overrides tracking) |
| Right stick (vertical) | Move Z (focus) |
| **X** | Start / stop tracking |
| **B** | Start / stop recording |
| **Y** | Set focus |
| **A** | Return to focus |

Buttons can be remapped in rig.toml (`[gamepad.buttons]`). Stick speeds, dead zone and
direction are in `[gamepad.sticks]`. *(rig check: button and axis numbers on your
controller.)* If the gamepad drops out or goes to sleep, reconnect it or press **Reset gamepad**
in FOCUS & CALIBRATION without restarting WormsPy.

---

## 7. Alarms

Alarms appear in a red bar under the header and stay until you press **Acknowledge**, or until
their cause clears. Acknowledging only hides the message; it doesn't fix anything.

| Alarm | What it means | What to do |
|---|---|---|
| *N frame(s) dropped in this recording* | A camera missed frames, or the disk couldn't keep up (`writer backlog`). | Occasional drops are tolerated and flagged in the data. Repeated drops: check USB cables and ports, disk speed, and close other software. |
| *Frame N: the two cameras' frames were captured … ms apart* | The two cameras' frames are out of step. | Check the trigger cable, then Stop live and Start live again. Don't record until it's gone. |
| *Recording stopped: …* | The recording couldn't be written (disk full, drive removed). | Free space or fix the drive, then record again. The recording's files hold everything up to the error. |
| *Acquisition stopped: …* | A camera disconnected or failed. | Check the camera's USB cable, then Start live. |
| *Camera settings not applied: …* | A camera refused the new settings. | The old settings stay in force. Try other values. |
| *Calibration failed: …* | See section 4. | |
| *Cameras not registered: …* | See section 4. | |
| *No stage …* | The stage didn't connect at startup. | Check power, cables and ports in rig.toml, then restart WormsPy. |
| *Cannot track (… unavailable)* | Tracking couldn't start: no calibration for that camera, or an unknown channel. | Calibrate, or pick another camera. |
| *Gamepad disconnected* | The gamepad was unplugged. | Plug it back in. Joystick moves stop until then. |

---

## 8. Where the data goes

```
<data_root>/2026-09-28_N2-3/          one session
    session.json                      metadata, camera settings, calibration
    rec-001/
        gcamp.tif                     calcium: raw 16-bit, one page per frame (opens in Fiji)
        brightfield.mkv               behaviour: lossless video
        frames.csv                    per frame: time, stage X/Y/Z, drops, events
        tracking.csv                  per frame tracked: target, status
        recording.json                summary, written at Stop
```

Row *i* of `frames.csv` is page *i* of the TIFF and frame *i* of the video. To analyse in
Python:

```python
from wormspy.reader import open_recording      # uv sync --extra analysis
with open_recording("…/2026-09-28_N2-3/rec-001") as rec:
    calcium = rec["gcamp"].array()
    rec.frames[["x_um", "y_um"]]
    world = rec.plate_um_batch("brightfield", pts_px)   # vectorised pixels → plate µm
```

For offline behaviour/Tierpsy export and RIA pipeline integration:
- `uv run python -m wormspy.analysis.trajectory <rec-NNN>` (add `--hdf5` with `uv sync --extra tierpsy`)
- `uv run python -m wormspy.analysis.ria_bridge export <rec-NNN> --out <results_root> --run-id <id>`
- `uv run python -m wormspy.analysis.ria_bridge join <rec-NNN> --head-angles … --roi-intensity …`

Everything about the files, and how to read them without WormsPy, is in
[recording-format.md](recording-format.md).

### Reviewing a recording & selecting analysis pipelines

```
uv sync --extra analysis             # once: the reviewer reads recordings with pandas
uv run wormspy-review                                        # opens rig.toml's data_root in the browser
uv run wormspy-review <data_root>                            # browse all sessions in a folder
uv run wormspy-review <data_root>/2026-09-28_N2-3/rec-002    # open one recording directly
```

When opened on a `data_root` (or toggled via **Sessions**), the left **Session browser** lists
every session and recording with its **Animal**, **Operator**, **Condition**, duration, and
queued pipelines, with live text filtering:

- **Top row (Feeds):** brightfield and fluorescence side by side, with the same LUTs, level
  handles, histograms, and tracked-point overlays as the live view.
- **Bottom-left (World trajectory):** the worm's path on the plate in stage µm (upgrading
  automatically to reconstructed Tierpsy world coordinates once run), with clickable amber event
  markers.
- **Bottom-right (Calcium stats):** sampled fluorescence pixel-intensity distribution and
  summary metrics (`median`, `p99.9`, `SNR`, `sat %`, `z-moved %`), plus an **Over time** toggle
  showing `p99.9` and `median` synced to the playhead.
- **Send to Analysis Pipelines:** check the pipelines to queue for the open recording
  (`RIA-Segmentation export`, `World trajectory / Tierpsy`, `Classical neuron segmentation`), and
  use **Options…** next to any pipeline to configure its settings. Selections persist in
  `<data_root>/analysis_queue.json`, and **Run this recording** / **Run all queued** executes them
  in the background.
- **Scrub bar & Transport:** frame-synced playback (`¼×` to `8×`), dropped-frame flags, and
  event markers.

Playback follows the recorded capture times; frames the display cannot keep up with are
skipped rather than slowing playback down.

| Key | Action |
|---|---|
| Space | Play / pause |
| ← / → | One frame back / forward |
| Shift+← / Shift+→ | One second back / forward |
| Page Up / Page Down | Previous / next event |
| Home / End | First / last frame |

---

## 9. Troubleshooting

| Problem | Try |
|---|---|
| WormsPy won't start: *PySpin is not installed* | Install the Spinnaker SDK and its Python wheel (section 1), or use `--sim`. |
| WormsPy won't start: *Set cameras.clock.serial…* or *no camera with serial…* | Enter the serial numbers the message lists into rig.toml. Close SpinView. |
| Brightfield frozen, fluorescence running | The trigger isn't reaching the behaviour camera. Check the GPIO cable, and `clock_output_line` / `follower_trigger_line` in rig.toml. *(rig check)* |
| Tracking won't start | Calibrate first (section 4). The live view must be running. |
| Tracker follows debris | Tick **Mask** to see what it detects. Move the worm clear with the joystick. For persistent problems, see section 10. |
| Stage oscillates or lags while tracking | Adjust the servo gains (section 10). |
| Joystick moves the wrong way | Set `invert_y` / `invert_z` in `[gamepad.sticks]`. |
| Everything is dark / saturated | Adjust exposure and gain in the CAMERAS card. Press **Auto levels** for the display only. |

---

## 10. How tracking works, and tuning it

### The loop
Tracking runs beside acquisition and never slows it down. About 50 times a second it:

1. **Finds the animal** in the newest frame from the chosen camera (next section). The result
   is a pixel, or "nothing found".
2. **Turns that pixel into a position on the plate.** It uses the calibration, plus the stage
   position *at the moment that frame was exposed*: stage positions are sampled continuously
   and interpolated to each frame's capture time. So a moving stage or a late frame doesn't
   bias the result.
3. **Checks it is believable.** A new position is accepted only if the worm could have crawled
   there since the last accepted one: within `jump_margin_um` + `max_worm_speed_um_s` × the
   time since. Anything further is treated as debris, an egg or a second worm, and ignored.
   After `lost_after_misses` frames in a row without a believable position, the status becomes
   **Target lost**. The worm is picked up again automatically when it reappears near where it
   was last seen; the search radius grows the longer it is gone.
4. **Steers the stage** toward that plate position (below).

The target is an **absolute** plate position, not "move a bit left". A missed frame or a slow
stage therefore never accumulates into drift: the stage always heads for where the worm
actually is.

### Finding the animal
**Brightfield silhouette** (`[tracking.dark_object]`)
1. Works at half resolution for speed; the tracked point stays sub-pixel.
2. **Flattens the illumination.** It subtracts a heavily blurred copy of the frame, leaving a
   *contrast map*: how much darker each pixel is than its surroundings. Vignetting, a tilted
   lamp or a lawn edge no longer matter.
3. **Chooses the threshold automatically, on every frame,** with Otsu's method on the
   contrast map. Otsu picks the cut that best separates two populations (here background and
   body), so it follows the worm's own contrast: a pale L1 larva and a dark adult are both
   segmented whole, without re-tuning.
   - The contrast map is used instead of the raw image because the raw image breaks Otsu: the
     worm covers only ~3% of the frame, and uneven light spreads the background.
   - Otsu always finds *some* split, even in pure noise. So the threshold is never allowed
     below `k_sigma` × the frame's noise level, which is measured robustly from the frame
     itself. On an empty plate nothing clears it, and the tracker reports "nothing found"
     rather than chasing noise.
   - To use a fixed contrast instead, set `threshold` to a number of grey levels.
4. Removes specks, then keeps **the largest dark blob of at least `min_area_px`**. Its centre
   is the tracked point. The blob is what **Mask** shows.

**Fluorescent marker** (`[tracking.bright_marker]`)
1. Smooths the frame slightly (`spot_sigma_px`) to average out shot noise.
2. **Sets the threshold from the frame's own statistics:** background (median) +
   `k_sigma` × noise. It therefore follows exposure, gain and bleaching automatically. A frame
   with only noise yields nothing.
3. Picks the **brightest** spot of at least `min_area_px`, and tracks its intensity-weighted
   centre (sub-pixel).

### Moving the stage
The stage is driven with **velocity** commands, not a series of jumps:
- **Feed-forward:** the stage moves at the worm's own estimated velocity (`feed_forward`,
  smoothed by `velocity_smoothing`). A steadily crawling worm is followed without lagging
  behind.
- **Correction:** on top of that, a speed proportional to how far the worm is from the centre
  (`gain_per_s` µm/s per µm). Within `deadband_um` of the centre, no correction is applied, so
  the stage doesn't hunt.
- **Limits:** speed is capped at `max_speed_um_s`, and changes of speed at `max_accel_um_s2`.
  Starts, stops and a lost target are therefore smooth ramps. The stage never pushes further
  into the edge of the safe range (**At stage limit**).
- **The joystick always wins** (**Joystick override**). Tracking resumes from rest when you
  let go.

### What is recorded
Every frame the tracker evaluates is written to `tracking.csv`: the detected pixel, the
position the stage steered toward, whether it was accepted, and the status. See
[recording-format.md](recording-format.md).

### Tuning
All settings above are in `rig.toml`, under `[tracking.servo]`, `[tracking.dark_object]` and
`[tracking.bright_marker]`. Each is listed there with its default and a one-line explanation.
Restart WormsPy after editing. A mistyped name or an impossible value stops WormsPy at startup
with a message naming the key.

| Symptom | Setting |
|---|---|
| Debris or eggs picked up instead of the worm | Raise `dark_object.min_area_px` (tick **Mask** to see what is detected). |
| Worm's body detected in pieces, or only partly | Lower `dark_object.k_sigma`, or set a fixed `threshold` in grey levels. |
| Background noise or a shadow detected | Set a fixed `dark_object.threshold` above the noise, or raise `k_sigma`. |
| A large dark object (plate edge, bubble) wins | Set `dark_object.max_area_px`. |
| Stage lags behind a fast worm | Raise `servo.gain_per_s` (e.g. 2 → 3). Keep `feed_forward = 1`. |
| Stage overshoots or oscillates | Lower `servo.gain_per_s`, or raise `deadband_um`. |
| Stage jerks at starts and stops | Lower `servo.max_accel_um_s2`. |
| "Target lost" too often when the worm reverses or coils | Raise `jump_margin_um` or `lost_after_misses`. |
| Tracker jumps to a second worm | Lower `max_worm_speed_um_s` / `jump_margin_um`. |
| Marker lost when the neuron is dim | Lower `bright_marker.k_sigma` (e.g. 8 → 6). |

The defaults are a starting point from simulation *(rig check)*.

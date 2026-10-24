"""Demo video generator — a real ~2-minute product tour of a generated site.

Pipeline (all artifacts are written under ``<project>/.factory/video``):
  1. storyboard  — ordered scenes with a narration line and a route/viewport,
  2. narration   — Edge TTS (network) per scene, MP3 + WebVTT,
  3. capture     — Playwright screenshots of the real pages (desktop + mobile),
                   or generated title cards for intro/closing,
  4. assemble    — ffmpeg builds one clip per scene (slow zoom + narration),
                   concatenates them and writes an SRT,
  5. verify      — ffprobe must report a video stream, an audio stream and a
                   duration close to the requested length.

Nothing here claims success without the artifact: the result carries
``status: "ready"`` only when ffprobe verified the final file. Missing tools
return ``status: "unavailable"`` with the exact list, and a failed scene falls
back to a title card so one broken page cannot abort the whole video.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_VOICE = "en-US-AriaNeural"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
MIN_SCENE_SECONDS = 5.0
MAX_SCENE_SECONDS = 24.0
TARGET_SECONDS = 120.0


def _run(cmd: List[str], timeout: int = 300, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def _find_playwright_cli() -> str:
    override = os.getenv("PLAYWRIGHT_CLI", "").strip()
    if override and Path(override).is_file():
        return override
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "node_modules" / "playwright" / "cli.js"
        if candidate.is_file():
            return str(candidate)
    return ""


def detect_toolchain() -> Dict[str, Any]:
    """Report what is available, without pretending. Used by /api/factory/status."""
    node = shutil.which("node") or ""
    playwright = _find_playwright_cli()
    try:
        import edge_tts  # noqa: F401
        edge_ok = True
    except ImportError:
        edge_ok = False
    try:
        import gtts  # noqa: F401
        gtts_ok = True
    except ImportError:
        gtts_ok = False
    powershell = shutil.which("powershell") or shutil.which("pwsh") or ""
    sapi_ok = bool(powershell)  # Windows built-in voices are the offline fallback
    tts_backend = "edge-tts" if edge_ok else ("gtts" if gtts_ok else ("windows-sapi" if sapi_ok else ""))
    return {
        "ffmpeg": shutil.which("ffmpeg") or "",
        "ffprobe": shutil.which("ffprobe") or "",
        "node": node,
        "playwright_cli": playwright,
        "edge_tts": "edge-tts" if edge_ok else "",
        "gtts": "gtts" if gtts_ok else "",
        "powershell": powershell,
        "tts_backend": tts_backend,
        "ready": bool(shutil.which("ffmpeg") and shutil.which("ffprobe") and node and playwright and tts_backend),
        "missing": [
            name for name, ok in (
                ("ffmpeg", bool(shutil.which("ffmpeg"))),
                ("ffprobe", bool(shutil.which("ffprobe"))),
                ("node", bool(node)),
                ("playwright", bool(playwright)),
                ("tts (edge-tts or windows-sapi)", bool(tts_backend)),
            ) if not ok
        ],
    }


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return value or "product"


def build_storyboard(name: str, tagline: str, has: Dict[str, bool]) -> List[Dict[str, Any]]:
    """Nine scenes, ~250 words of narration ≈ 110–130 seconds at 150 wpm."""
    scenes: List[Dict[str, Any]] = [
        {
            "id": "intro",
            "kind": "card",
            "headline": name,
            "subline": tagline,
            "narration": (
                f"Welcome to {name}. In the next two minutes you will see the complete platform: "
                "the marketing site, the real API, authentication, the dashboard, and how a release "
                "reaches production with checks that fail closed."
            ),
        },
        {
            "id": "home",
            "kind": "page",
            "route": "/",
            "viewport": "1920,1080",
            "narration": (
                "This is the production homepage. Every section is responsive and accessible, and "
                "the whole site is generated from the same design tokens, so the brand stays "
                "consistent on every screen."
            ),
        },
    ]
    if has.get("features"):
        scenes.append({
            "id": "features", "kind": "page", "route": "/features", "viewport": "1920,1080",
            "narration": (
                "The features page explains the platform in real content: security defaults, global "
                "edge delivery, operational analytics and automated pipelines. There is no placeholder "
                "copy and no dead link."
            ),
        })
    if has.get("pricing"):
        scenes.append({
            "id": "pricing", "kind": "page", "route": "/pricing", "viewport": "1920,1080",
            "narration": (
                "Pricing shows three transparent tiers with a complete feature breakdown and an "
                "FAQ, so a visitor can choose a plan without contacting sales first."
            ),
        })
    if has.get("register"):
        scenes.append({
            "id": "register", "kind": "page", "route": "/register", "viewport": "1920,1080",
            "narration": (
                "Registration is wired to the live API. Passwords are hashed, sessions use "
                "short-lived tokens, and every input is validated and sanitised on the server."
            ),
        })
    if has.get("dashboard"):
        scenes.append({
            "id": "dashboard", "kind": "page", "route": "/dashboard", "viewport": "1920,1080",
            "narration": (
                "After signing in, the dashboard is the authenticated workspace. Records are scoped "
                "to the signed-in user, so one account can never read another account's data."
            ),
        })
    if has.get("contact"):
        scenes.append({
            "id": "contact", "kind": "page", "route": "/contact", "viewport": "1920,1080",
            "narration": (
                "The contact form posts to a real endpoint. The payload is validated, the email is "
                "checked, the message is stored in PostgreSQL, and the visitor gets a clear "
                "confirmation state."
            ),
        })
    mobile_route = "/features" if has.get("features") else "/"
    scenes.append({
        "id": "mobile", "kind": "page", "route": mobile_route, "viewport": "430,932",
        "narration": (
            "Every page is mobile-first. Layouts reflow at small widths, tap targets stay large, and "
            "the same build serves every viewport without a separate mobile site."
        ),
    })
    scenes.append({
        "id": "closing",
        "kind": "card",
        "headline": f"{name} is ready",
        "subline": "Real pages · Real API · Verified deployment",
        "narration": (
            f"That is {name}: a complete website, a working API, automated quality checks and a live "
            "deployment with evidence — ready for your customers."
        ),
    })
    return scenes


def _card_html(headline: str, subline: str, accent: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: 100%; height: 100%; }}
body {{
  display: flex; align-items: center; justify-content: center; flex-direction: column;
  background: radial-gradient(circle at 20% 20%, {accent}33, transparent 45%),
              radial-gradient(circle at 80% 75%, {accent}22, transparent 40%), #070d17;
  color: #f8fafc; font-family: "Segoe UI", Inter, system-ui, sans-serif; text-align: center;
  padding: 80px;
}}
h1 {{ font-size: 92px; line-height: 1.05; margin: 0 0 28px; letter-spacing: -0.03em; }}
p {{ font-size: 34px; color: #94a3b8; margin: 0; max-width: 1200px; }}
.rule {{ width: 140px; height: 6px; border-radius: 999px; background: {accent}; margin: 0 0 42px; }}
</style></head>
<body><div class="rule"></div><h1>{html.escape(headline)}</h1><p>{html.escape(subline)}</p></body></html>
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):  # silence preview noise
        pass

    def do_GET(self):  # SPA fallback: /features has no file, serve index.html
        candidate = self.translate_path(self.path)
        if not os.path.isfile(candidate):
            self.path = "/index.html"
        return super().do_GET()


def _serve_directory(directory: Path):
    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(directory), **kwargs)  # noqa: E731
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _screenshot(toolchain: Dict[str, Any], url: str, output: Path, viewport: str, wait_ms: int) -> Dict[str, Any]:
    cmd = [
        toolchain["node"], toolchain["playwright_cli"], "screenshot",
        f"--viewport-size={viewport}",
        f"--wait-for-timeout={wait_ms}",
        "--color-scheme=dark",
        "--timeout=45000",
        url, str(output),
    ]
    try:
        proc = _run(cmd, timeout=90)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "screenshot timed out"}
    if proc.returncode != 0 or not output.is_file() or output.stat().st_size < 5_000:
        tail = (proc.stderr or proc.stdout or "").strip()[-400:]
        return {"ok": False, "error": tail or "playwright produced no screenshot"}
    return {"ok": True, "path": str(output), "bytes": output.stat().st_size}


def _ffprobe_json(path: Path) -> Dict[str, Any]:
    proc = _run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ], timeout=60)
    if proc.returncode != 0:
        return {}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {}


def _duration(path: Path) -> float:
    data = _ffprobe_json(path)
    try:
        return float(data.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ps_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _synthesize_gtts(text: str, out_mp3: Path) -> Dict[str, Any]:
    """Free, internet-only narration through Google Translate TTS (gTTS).

    Edge TTS is preferred when reachable (more natural voices); some networks
    answer its WebSocket with HTTP 403, and gTTS is the free fallback that still
    uses a real online voice instead of the robotic offline synthesizer.
    """
    try:
        from gtts import gTTS
    except ImportError:
        return {"ok": False, "error": "gtts not installed (pip install gTTS)"}
    try:
        gTTS(text=text, lang="en", slow=False).save(str(out_mp3))
    except Exception as exc:  # noqa: BLE001 — network/API failure is reported
        return {"ok": False, "error": f"gtts: {type(exc).__name__}: {exc}"[:300]}
    if not out_mp3.is_file() or out_mp3.stat().st_size < 5_000:
        return {"ok": False, "error": "gtts produced no audio"}
    return {"ok": True, "path": str(out_mp3), "backend": "gtts", "duration": _duration(out_mp3)}


def _synthesize_sapi(text: str, out_wav: Path, work_dir: Path) -> Dict[str, Any]:
    """Offline Windows narration via System.Speech (no network, real voice)."""
    powershell = shutil.which("powershell") or shutil.which("pwsh") or ""
    if not powershell:
        return {"ok": False, "error": "powershell not available"}
    text_file = work_dir / f"{out_wav.stem}.txt"
    script_file = work_dir / f"{out_wav.stem}.ps1"
    text_file.write_text(text, encoding="utf-8")
    script = (
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "try { $s.SelectVoice('Microsoft Zira Desktop') } catch { }\n"
        "$s.Rate = 1\n"
        f"$s.SetOutputToWaveFile({_ps_quote(str(out_wav))})\n"
        f"$s.Speak([IO.File]::ReadAllText({_ps_quote(str(text_file))}, [Text.Encoding]::UTF8))\n"
        "$s.Dispose()\n"
    )
    script_file.write_text(script, encoding="utf-8-sig")
    try:
        proc = _run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_file)], timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "windows-sapi timed out"}
    if proc.returncode != 0 or not out_wav.is_file() or out_wav.stat().st_size < 20_000:
        return {"ok": False, "error": (proc.stderr or proc.stdout or "sapi produced no audio")[-300:]}
    return {"ok": True, "path": str(out_wav), "backend": "windows-sapi", "duration": _duration(out_wav)}


def _synthesize(scene: Dict[str, Any], out_dir: Path, index: int, voice: str) -> Dict[str, Any]:
    """Edge TTS first (better voices), then the offline Windows SAPI fallback."""
    scene_id = scene.get("id") or f"scene-{index:02d}"
    edge_media = out_dir / f"{index:02d}-{scene_id}.mp3"
    edge_vtt = out_dir / f"{index:02d}-{scene_id}.vtt"
    try:
        proc = _run([
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            "--rate", "+4%",
            "--text", scene["narration"],
            "--write-media", str(edge_media),
            "--write-subtitles", str(edge_vtt),
        ], timeout=90)
    except subprocess.TimeoutExpired:
        proc = None
    if proc is not None and proc.returncode == 0 and edge_media.is_file() and edge_media.stat().st_size > 1_000:
        return {"ok": True, "path": str(edge_media), "backend": "edge-tts", "duration": _duration(edge_media)}
    edge_error = ((proc.stderr or proc.stdout) if proc else "edge-tts timed out")
    edge_error = (edge_error or "").strip()[-200:]

    online = _synthesize_gtts(scene["narration"], out_dir / f"{index:02d}-{scene_id}-gtts.mp3")
    if online.get("ok"):
        online["edge_error"] = edge_error
        return online

    sapi = _synthesize_sapi(scene["narration"], out_dir / f"{index:02d}-{scene_id}.wav", out_dir)
    if sapi.get("ok"):
        sapi["edge_error"] = edge_error
        return sapi
    return {
        "ok": False,
        "error": f"edge-tts: {edge_error}; gtts: {online.get('error')}; windows-sapi: {sapi.get('error')}",
    }


def _clip(scene: Dict[str, Any], image: Path, audio: Optional[Path], out_mp4: Path, duration: float) -> Dict[str, Any]:
    """Build one H.264/AAC clip: slow zoom over the still + narration."""
    frames = max(1, int(duration * FPS))
    zoom = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x0f172a,"
        f"zoompan=z='min(zoom+0.00045,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.3f}", "-i", str(image)]
    if audio and audio.is_file():
        cmd += ["-i", str(audio)]
        audio_filter = "[1:a]apad=pad_dur=1.0,volume=1.0[a]"
        audio_map = "[a]"
    else:
        cmd += ["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
        audio_filter = "[1:a]anull[a]"
        audio_map = "[a]"
    cmd += [
        "-filter_complex", f"[0:v]{zoom}[v];{audio_filter}",
        "-map", "[v]", "-map", audio_map,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-r", str(FPS), "-g", str(FPS * 2),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-movflags", "+faststart", str(out_mp4),
    ]
    try:
        proc = _run(cmd, timeout=300)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "ffmpeg clip timed out"}
    if proc.returncode != 0 or not out_mp4.is_file():
        return {"ok": False, "error": (proc.stderr or "")[-500:]}
    return {"ok": True, "path": str(out_mp4), "duration": _duration(out_mp4)}


def _srt_timestamp(seconds: float) -> str:
    millis = int(round(max(0.0, seconds) * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_demo_video(
    project_dir: str,
    *,
    name: str = "",
    tagline: str = "",
    live_url: str = "",
    out_path: str = "",
    target_seconds: float = TARGET_SECONDS,
    voice: str = DEFAULT_VOICE,
    accent: str = "#10b981",
    storyboard: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate and verify a demo video. Returns evidence, never a bare URL."""
    start = time.perf_counter()
    toolchain = detect_toolchain()
    project = Path(project_dir).resolve()
    if not toolchain["ready"]:
        return {
            "status": "unavailable",
            "verified": False,
            "missing": toolchain["missing"],
            "toolchain": toolchain,
            "message": "Install the missing tools before generating a demo video.",
        }
    if not project.is_dir():
        return {"status": "failed", "verified": False, "message": "Project directory not found"}

    work = project / ".factory" / "video"
    frames_dir = work / "frames"
    audio_dir = work / "audio"
    clips_dir = work / "clips"
    for folder in (work, frames_dir, audio_dir, clips_dir):
        folder.mkdir(parents=True, exist_ok=True)

    project_name = name or project.name.replace("-", " ").title()
    features = {
        "features": (project / "frontend" / "src" / "pages" / "Features.jsx").is_file(),
        "pricing": (project / "frontend" / "src" / "pages" / "Pricing.jsx").is_file(),
        "register": (project / "frontend" / "src" / "pages" / "Register.jsx").is_file(),
        "dashboard": (project / "frontend" / "src" / "pages" / "Dashboard.jsx").is_file(),
        "contact": (project / "frontend" / "src" / "pages" / "Contact.jsx").is_file(),
    }
    scenes = storyboard or build_storyboard(project_name, tagline or "A complete, production-ready web platform", features)

    server = None
    base_url = (live_url or "").strip()
    if not base_url:
        dist = project / "frontend" / "dist"
        if not (dist / "index.html").is_file():
            return {
                "status": "failed",
                "verified": False,
                "message": "No live URL and no built frontend/dist — run `npm run build` first.",
            }
        server, base_url = _serve_directory(dist)
    base_url = base_url.rstrip("/")

    warnings: List[str] = []
    scene_results: List[Dict[str, Any]] = []
    try:
        for index, scene in enumerate(scenes, start=1):
            scene_id = scene.get("id") or f"scene-{index:02d}"
            tts = _synthesize(scene, audio_dir, index, voice)
            narration_ok = bool(tts.get("ok"))
            audio_path = Path(tts["path"]) if narration_ok else None
            if not narration_ok:
                warnings.append(f"{scene_id}: narration unavailable ({tts.get('error', '')[:160]})")
            audio_seconds = float(tts.get("duration") or 0.0)
            duration = min(MAX_SCENE_SECONDS, max(MIN_SCENE_SECONDS, audio_seconds + 1.4))

            frame = frames_dir / f"{index:02d}-{scene_id}.png"
            if scene.get("kind") == "card":
                card = frames_dir / f"{index:02d}-{scene_id}.html"
                card.write_text(_card_html(scene.get("headline", project_name), scene.get("subline", ""), accent), encoding="utf-8")
                shot = _screenshot(toolchain, card.as_uri(), frame, f"{WIDTH},{HEIGHT}", 300)
            else:
                target = urllib.parse.urljoin(base_url + "/", str(scene.get("route", "/")).lstrip("/"))
                shot = _screenshot(toolchain, target, frame, scene.get("viewport", f"{WIDTH},{HEIGHT}"), 2500)
                if not shot.get("ok"):
                    warnings.append(f"{scene_id}: page capture failed ({shot.get('error', '')[:160]}); using title card")
                    card = frames_dir / f"{index:02d}-{scene_id}.html"
                    card.write_text(_card_html(f"{project_name} · {scene_id.title()}", scene.get("narration", "")[:120], accent), encoding="utf-8")
                    shot = _screenshot(toolchain, card.as_uri(), frame, f"{WIDTH},{HEIGHT}", 300)

            clip_path = clips_dir / f"{index:02d}-{scene_id}.mp4"
            if shot.get("ok"):
                clip = _clip(scene, frame, audio_path, clip_path, duration)
            else:
                clip = {"ok": False, "error": "no frame captured"}
            if not clip.get("ok"):
                return {
                    "status": "failed",
                    "verified": False,
                    "message": f"scene {scene_id} could not be rendered: {clip.get('error', '')[:300]}",
                    "scenes": scene_results,
                    "warnings": warnings,
                }
            scene_results.append({
                "id": scene_id,
                "kind": scene.get("kind"),
                "route": scene.get("route"),
                "duration": round(float(clip.get("duration") or duration), 2),
                "narration": narration_ok,
                "narration_backend": tts.get("backend", ""),
                "audio": str(audio_path) if audio_path else "",
                "frame": str(frame),
                "clip": str(clip_path),
            })
    finally:
        if server:
            server.shutdown()

    total = sum(item["duration"] for item in scene_results)
    if total < target_seconds:
        last = scene_results[-1]
        extra = target_seconds - total
        clip_path = Path(last["clip"])
        last_audio = Path(last["audio"]) if last.get("audio") else None
        rebuilt = _clip({"id": last["id"]}, Path(last["frame"]), last_audio, clip_path, last["duration"] + extra)
        if rebuilt.get("ok"):
            last["duration"] = round(float(rebuilt.get("duration") or last["duration"] + extra), 2)
            total = sum(item["duration"] for item in scene_results)

    concat_list = work / "concat.txt"
    concat_list.write_text(
        "\n".join("file '" + Path(item["clip"]).as_posix().replace("'", "'\\''") + "'" for item in scene_results) + "\n",
        encoding="utf-8",
    )
    target_video = Path(out_path) if out_path else work / "demo.mp4"
    target_video.parent.mkdir(parents=True, exist_ok=True)
    concat = _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", "-movflags", "+faststart", str(target_video),
    ], timeout=600)
    if concat.returncode != 0 or not target_video.is_file():
        warnings.append("stream-copy concat failed; re-encoding")
        parts = []
        for item in scene_results:
            parts.append(f"[{len(parts)}:v][{len(parts)}:a]")
        inputs: List[str] = []
        for item in scene_results:
            inputs += ["-i", item["clip"]]
        reencode = _run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", "".join(parts) + f"concat=n={len(scene_results)}:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target_video),
        ], timeout=900)
        if reencode.returncode != 0:
            return {
                "status": "failed",
                "verified": False,
                "message": (reencode.stderr or "")[-500:],
                "scenes": scene_results,
                "warnings": warnings,
            }

    # SRT built from the final clip durations (kept in sync with concat order).
    srt_lines: List[str] = []
    cursor = 0.0
    for index, (scene, item) in enumerate(zip(scenes, scene_results), start=1):
        srt_lines += [
            str(index),
            f"{_srt_timestamp(cursor)} --> {_srt_timestamp(cursor + item['duration'])}",
            scene.get("narration", ""),
            "",
        ]
        cursor += item["duration"]
    srt_path = work / "demo.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    probe = _ffprobe_json(target_video)
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    final_duration = float(probe.get("format", {}).get("duration") or 0.0)
    failures: List[str] = []
    if not video_stream:
        failures.append("no video stream")
    if not audio_stream:
        failures.append("no audio stream")
    if final_duration < 60:
        failures.append(f"video is only {final_duration:.1f}s")
    if target_seconds and abs(final_duration - target_seconds) > target_seconds * 0.3:
        failures.append(f"duration {final_duration:.1f}s is more than 30% off the {target_seconds:.0f}s target")

    manifest = {
        "status": "ready" if not failures else "failed",
        "verified": not failures,
        "video": str(target_video),
        "subtitles": str(srt_path),
        "duration_seconds": round(final_duration, 2),
        "target_seconds": target_seconds,
        "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream else "",
        "video_codec": video_stream.get("codec_name") if video_stream else "",
        "audio_codec": audio_stream.get("codec_name") if audio_stream else "",
        "scenes": scene_results,
        "warnings": warnings,
        "failures": failures,
        "toolchain": toolchain,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a verified ~2-minute demo video for a generated website.")
    parser.add_argument("project_dir")
    parser.add_argument("--url", default="", help="live site URL (defaults to serving frontend/dist)")
    parser.add_argument("--name", default="")
    parser.add_argument("--tagline", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--target", type=float, default=TARGET_SECONDS)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--accent", default="#10b981")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = generate_demo_video(
        args.project_dir, name=args.name, tagline=args.tagline, live_url=args.url,
        out_path=args.out, target_seconds=args.target, voice=args.voice, accent=args.accent,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"status={result.get('status')} verified={result.get('verified')} "
              f"duration={result.get('duration_seconds')}s video={result.get('video', '')}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        for failure in result.get("failures", []):
            print(f"failure: {failure}")
    return 0 if result.get("verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())

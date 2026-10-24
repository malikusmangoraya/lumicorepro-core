"""Tests — demo_video: storyboard, SRT timing, and fail-closed verification."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent.demo_video as demo


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


PROBE_OK = {
    "format": {"duration": "120.0"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
        {"codec_type": "audio", "codec_name": "aac"},
    ],
}


def _project(root: Path) -> Path:
    dist = root / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>")
    return root


class StoryboardTests(unittest.TestCase):
    def test_storyboard_covers_marketing_auth_dashboard_mobile(self):
        scenes = demo.build_storyboard("Acme", "Cloud platform", {
            "features": True, "pricing": True, "register": True,
            "dashboard": True, "contact": True,
        })
        routes = {scene.get("route") for scene in scenes}
        self.assertTrue({"/", "/features", "/pricing", "/register", "/dashboard", "/contact"} <= routes)
        self.assertEqual(scenes[0]["kind"], "card")
        self.assertEqual(scenes[-1]["kind"], "card")
        self.assertTrue(any(scene.get("viewport") == "430,932" for scene in scenes))
        for scene in scenes:
            self.assertGreater(len(scene["narration"].split()), 15)

    def test_storyboard_skips_pages_that_do_not_exist(self):
        scenes = demo.build_storyboard("Acme", "Tagline", {})
        routes = [scene.get("route") for scene in scenes]
        self.assertIn("/", routes)
        self.assertNotIn("/features", routes)
        self.assertNotIn("/pricing", routes)

    def test_srt_timestamp_format(self):
        self.assertEqual(demo._srt_timestamp(0), "00:00:00,000")
        self.assertEqual(demo._srt_timestamp(61.5), "00:01:01,500")
        self.assertEqual(demo._srt_timestamp(3661.25), "01:01:01,250")


class ToolchainTests(unittest.TestCase):
    def test_toolchain_reports_missing_entries(self):
        toolchain = demo.detect_toolchain()
        self.assertIn("ready", toolchain)
        self.assertIn("missing", toolchain)
        self.assertIn("tts_backend", toolchain)


class NarrationFallbackTests(unittest.TestCase):
    def test_free_gtts_voice_is_used_when_edge_tts_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(demo, "_run", return_value=_Proc(1, stderr="403 Invalid response status")),                  patch.object(demo, "_synthesize_gtts", return_value={
                     "ok": True, "path": "g.mp3", "backend": "gtts", "duration": 9.0,
                 }) as gtts,                  patch.object(demo, "_synthesize_sapi") as sapi:
                result = demo._synthesize({"id": "s1", "narration": "hello"}, Path(tmp), 1, "voice")
        self.assertTrue(result["ok"])
        self.assertEqual(result["backend"], "gtts")
        gtts.assert_called_once()
        sapi.assert_not_called()

    def test_offline_sapi_is_the_last_resort(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(demo, "_run", return_value=_Proc(1, stderr="blocked")),                  patch.object(demo, "_synthesize_gtts", return_value={"ok": False, "error": "offline"}),                  patch.object(demo, "_synthesize_sapi", return_value={
                     "ok": True, "path": "s.wav", "backend": "windows-sapi", "duration": 8.0,
                 }):
                result = demo._synthesize({"id": "s2", "narration": "hello"}, Path(tmp), 2, "voice")
        self.assertEqual(result["backend"], "windows-sapi")

    def test_edge_tts_wins_when_it_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "01-s3.mp3"
            out.write_bytes(b"x" * 2048)
            def fake_run(cmd, **kwargs):
                return _Proc(0)
            with patch.object(demo, "_run", side_effect=fake_run),                  patch.object(demo, "_duration", return_value=7.0),                  patch.object(demo, "_synthesize_gtts") as gtts:
                result = demo._synthesize({"id": "s3", "narration": "hello"}, Path(tmp), 1, "voice")
        self.assertEqual(result["backend"], "edge-tts")
        gtts.assert_not_called()


class GenerateVideoTests(unittest.TestCase):
    def _patches(self, probe=PROBE_OK):
        def fake_run(cmd, **kwargs):
            target = Path(cmd[-1])
            if "ffmpeg" in str(cmd[0]):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"\x00" * 4096)
            return _Proc(0)

        def fake_shot(_toolchain, _url, output, _viewport, _wait):
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_bytes(b"png")
            return {"ok": True, "path": str(output), "bytes": 4096}

        def fake_tts(_scene, out_dir, index, _voice):
            path = Path(out_dir) / f"{index:02d}.wav"
            path.write_bytes(b"wav")
            return {"ok": True, "path": str(path), "duration": 55.0, "backend": "mock"}

        def fake_clip(_scene, _image, _audio, out_mp4, duration):
            Path(out_mp4).write_bytes(b"mp4")
            return {"ok": True, "path": str(out_mp4), "duration": duration}

        return [
            patch.object(demo, "detect_toolchain", return_value={
                "ready": True, "missing": [], "ffmpeg": "ffmpeg", "ffprobe": "ffprobe",
                "node": "node", "playwright_cli": "cli.js", "tts_backend": "mock",
            }),
            patch.object(demo, "_serve_directory", return_value=(None, "http://127.0.0.1:9")),
            patch.object(demo, "_synthesize", side_effect=fake_tts),
            patch.object(demo, "_screenshot", side_effect=fake_shot),
            patch.object(demo, "_clip", side_effect=fake_clip),
            patch.object(demo, "_run", side_effect=fake_run),
            patch.object(demo, "_ffprobe_json", return_value=probe),
        ]

    def test_ready_only_after_ffprobe_verifies_video_and_audio(self):
        storyboard = [
            {"id": "one", "kind": "page", "route": "/", "narration": "x" * 60},
            {"id": "two", "kind": "page", "route": "/", "narration": "y" * 60},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            patches = self._patches()
            for item in patches:
                item.start()
            try:
                result = demo.generate_demo_video(str(project), name="Acme", storyboard=storyboard, target_seconds=120)
            finally:
                for item in patches:
                    item.stop()

            self.assertEqual(result["status"], "ready")
            self.assertTrue(result["verified"])
            self.assertEqual(result["duration_seconds"], 120.0)
            self.assertTrue(Path(result["video"]).is_file())
            self.assertTrue((project / ".factory" / "video" / "manifest.json").is_file())
            self.assertTrue(Path(result["subtitles"]).is_file())

    def test_missing_audio_stream_fails_verification(self):
        probe = {"format": {"duration": "120.0"}, "streams": [{"codec_type": "video", "codec_name": "h264",
                                                                "width": 1920, "height": 1080}]}
        storyboard = [{"id": "only", "kind": "page", "route": "/", "narration": "z" * 60}]
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            patches = self._patches(probe=probe)
            for item in patches:
                item.start()
            try:
                result = demo.generate_demo_video(str(project), storyboard=storyboard, target_seconds=120)
            finally:
                for item in patches:
                    item.stop()
            self.assertEqual(result["status"], "failed")
            self.assertFalse(result["verified"])
            self.assertIn("no audio stream", result["failures"])

    def test_unavailable_toolchain_returns_missing_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(demo, "detect_toolchain", return_value={
                "ready": False, "missing": ["ffmpeg"], "tts_backend": "",
            }):
                result = demo.generate_demo_video(str(project))
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(result["missing"], ["ffmpeg"])

    def test_no_url_and_no_dist_fails_honestly(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "site"
            project.mkdir()
            with patch.object(demo, "detect_toolchain", return_value={
                "ready": True, "missing": [], "tts_backend": "mock",
            }):
                result = demo.generate_demo_video(str(project))
            self.assertEqual(result["status"], "failed")
            self.assertIn("built frontend/dist", result["message"])


if __name__ == "__main__":
    unittest.main()

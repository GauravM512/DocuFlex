from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path

from fastapi import HTTPException


class LibreOfficeWorkerManager:
    def __init__(self, lo_python: Path, worker_script: Path, timeout: int = 60) -> None:
        self._lo_python = lo_python
        self._worker_script = worker_script
        self._timeout = timeout
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        with self._lock:
            if self._is_running():
                return

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            self._process = subprocess.Popen(
                [
                    str(self._lo_python),
                    "-u",
                    str(self._worker_script),
                    "--serve",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
            )

            ready = self._read_stdout_line()
            if not ready:
                self._terminate_process()
                raise HTTPException(status_code=500, detail="LibreOffice worker did not start")

            try:
                payload = json.loads(ready)
            except json.JSONDecodeError:
                self._terminate_process()
                raise HTTPException(status_code=500, detail="LibreOffice worker returned invalid startup data")

            if payload.get("status") != "ready":
                self._terminate_process()
                message = payload.get("error") or "LibreOffice worker failed to start"
                raise HTTPException(status_code=500, detail=message)

    def shutdown(self) -> None:
        with self._lock:
            if not self._process:
                return

            if self._is_running() and self._process.stdin:
                try:
                    self._process.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
                    self._process.stdin.flush()
                except Exception:
                    pass

            self._terminate_process()

    def convert(self, input_path: Path, output_path: Path) -> Path:
        with self._lock:
            self.start()
            process = self._require_process()
            if not process.stdin:
                raise HTTPException(status_code=500, detail="LibreOffice worker stdin is unavailable")

            payload = {
                "action": "convert",
                "input_path": str(input_path),
                "output_path": str(output_path),
            }

            try:
                process.stdin.write(json.dumps(payload) + "\n")
                process.stdin.flush()
            except Exception as exc:
                self._restart_process()
                raise HTTPException(status_code=500, detail=f"Failed to send conversion job: {exc}")

            response = self._read_stdout_line()
            if not response:
                self._restart_process()
                raise HTTPException(status_code=500, detail="LibreOffice worker exited unexpectedly")

            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                self._restart_process()
                raise HTTPException(status_code=500, detail="LibreOffice worker returned invalid response")

            if not result.get("ok"):
                status_code = int(result.get("status_code", 400))
                detail = result.get("error") or "Conversion failed"
                raise HTTPException(status_code=status_code, detail=detail)

            if not output_path.exists():
                raise HTTPException(status_code=500, detail="Worker finished but no PDF created.")

            return output_path

    def _restart_process(self) -> None:
        self._terminate_process()
        self.start()

    def _is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _require_process(self) -> subprocess.Popen[str]:
        if not self._is_running():
            self.start()
        if not self._process:
            raise HTTPException(status_code=500, detail="LibreOffice worker is unavailable")
        return self._process

    def _read_stdout_line(self) -> str:
        process = self._process
        if not process or not process.stdout:
            return ""
        return process.stdout.readline().strip()

    def _terminate_process(self) -> None:
        process = self._process
        if not process:
            return

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass

        self._process = None
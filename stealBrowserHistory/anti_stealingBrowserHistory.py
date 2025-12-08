from __future__ import annotations

import os
import signal
import stat
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Set

try:
    import msvcrt  # type: ignore
except ImportError:
    msvcrt = None  # type: ignore

try:
    import fcntl  # type: ignore
except ImportError:
    fcntl = None  # type: ignore

# How often to rescan for Chrome profiles and refresh locks (seconds).
SCAN_INTERVAL = float(os.environ.get("ANTI_SCAN_INTERVAL", "2.0"))
# Pad the lock length so small/empty files are still covered.
LOCK_PADDING = 4096


def chrome_user_data_dir(username: str) -> str | None:
    """Return the platform Chrome user-data directory if it exists."""
    if os.name == "nt":
        path = os.path.join("C:\\", "Users", username, "AppData", "Local", "Google", "Chrome", "User Data")
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Google", "Chrome")
    else:
        # Linux/Unix default Chrome path
        path = os.path.join(os.path.expanduser("~"), ".config", "google-chrome")
    return path if os.path.isdir(path) else None


def list_profile_dirs(user_data_path: str) -> List[str]:
    """Collect Default and Profile* directories that hold History files."""
    profiles: List[str] = []
    default_path = os.path.join(user_data_path, "Default")
    if os.path.isdir(default_path):
        profiles.append("Default")

    for entry in os.listdir(user_data_path):
        full = os.path.join(user_data_path, entry)
        if not os.path.isdir(full):
            continue
        if entry.lower().startswith("profile"):
            profiles.append(entry)
    return profiles


def discover_history_files(user_data_path: str) -> Set[str]:
    """Return full paths to History files across all profiles."""
    paths: Set[str] = set()
    for profile in list_profile_dirs(user_data_path):
        history_path = os.path.join(user_data_path, profile, "History")
        if os.path.isfile(history_path):
            paths.add(history_path)
    return paths


@dataclass
class HistoryLock:
    path: str
    handle: object | None = None
    lock_len: int = 0
    last_mtime: float | None = None
    original_mode: int | None = None

    def acquire(self) -> bool:
        """Try to block access to the History file (platform-specific)."""
        if not os.path.isfile(self.path):
            return False
        if os.name == "nt" and msvcrt is not None:
            return self._acquire_windows()
        return self._acquire_posix()

    def _acquire_windows(self) -> bool:
        try:
            fh = open(self.path, "r+b")
        except OSError:
            return False

        size = max(os.path.getsize(self.path) + LOCK_PADDING, 1024)
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, size)
        except OSError:
            fh.close()
            return False

        self.handle = fh
        self.lock_len = size
        try:
            self.last_mtime = os.path.getmtime(self.path)
        except OSError:
            self.last_mtime = None
        return True

    def _acquire_posix(self) -> bool:
        # On POSIX we toggle permissions to 000 to prevent other opens, and keep a shared lock for good measure.
        try:
            st = os.stat(self.path)
            self.original_mode = stat.S_IMODE(st.st_mode)
        except OSError:
            self.original_mode = None
            return False

        try:
            os.chmod(self.path, 0)
        except OSError:
            return False

        if fcntl is not None:
            fh = None
            try:
                fh = open(self.path, "r+b")
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.handle = fh
            except OSError:
                try:
                    if fh is not None and not fh.closed:  # type: ignore[attr-defined]
                        fh.close()  # type: ignore[attr-defined]
                except Exception:
                    pass
        return True

    def is_active(self) -> bool:
        if not os.path.isfile(self.path):
            return False
        if os.name == "nt":
            if self.handle is None:
                return False
            if self.last_mtime is None:
                return True
            try:
                return os.path.getmtime(self.path) == self.last_mtime
            except OSError:
                return False
        # POSIX: check permissions are still zeroed.
        try:
            return stat.S_IMODE(os.stat(self.path).st_mode) == 0
        except OSError:
            return False

    def refresh(self) -> bool:
        """Ensure the protection is still in place; reacquire if needed."""
        if self.is_active():
            return True
        self.release()
        return self.acquire()

    def release(self) -> None:
        if os.name == "nt":
            if self.handle is not None and msvcrt is not None:
                try:
                    self.handle.seek(0)
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, self.lock_len or 1)
                except OSError:
                    pass
            try:
                if self.handle is not None:
                    self.handle.close()
            finally:
                self.handle = None
                self.lock_len = 0
                self.last_mtime = None
            return

        # POSIX: restore original permissions.
        if self.original_mode is not None:
            try:
                os.chmod(self.path, self.original_mode)
            except OSError:
                pass
        if self.handle is not None:
            try:
                if fcntl is not None:
                    fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                self.handle.close()
            except OSError:
                pass
        self.handle = None
        self.lock_len = 0
        self.last_mtime = None
        self.original_mode = None


def guard_history() -> None:
    try:
        username = os.getlogin()
    except OSError:
        print("Unable to determine current user; cannot locate AppData.")
        return

    user_data_path = chrome_user_data_dir(username)
    if not user_data_path:
        print("Chrome user data directory not found; nothing to lock.")
        return

    locks: Dict[str, HistoryLock] = {}
    stop = False

    def handle_stop(signum: int, frame) -> None:  # type: ignore[override]
        nonlocal stop
        stop = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handle_stop)
        except (ValueError, OSError):
            continue

    print("Anti-stealing guard active. Chrome history stays locked until this program exits.")

    try:
        while not stop:
            current_paths = discover_history_files(user_data_path)

            # Drop locks for histories that disappeared.
            for tracked in list(locks):
                if tracked not in current_paths:
                    locks[tracked].release()
                    del locks[tracked]

            # Acquire or refresh locks for existing histories.
            for path in current_paths:
                lock = locks.get(path)
                if lock is None:
                    lock = HistoryLock(path)
                    locks[path] = lock
                lock.refresh()

            time.sleep(SCAN_INTERVAL)
    finally:
        for lock in locks.values():
            lock.release()
        print("Anti-stealing guard stopped. Chrome history access restored.")


if __name__ == "__main__":
    guard_history()

# ui/workers/task.py
"""Run slow work off the GUI thread (D24). One helper for every tab (D28)."""
from __future__ import annotations

import threading
import traceback
from typing import Callable

from PySide6.QtCore import QObject, Signal

THREAD_NAME = "insightbridge-task"


class _Relay(QObject):
    """Lives on the GUI thread. Signals emitted from the worker thread are queued to slots on the GUI thread."""

    done = Signal(object)
    failed = Signal(str)


def run_in_thread(parent: QObject, fn: Callable, *args, on_done: Callable, on_error: Callable) -> threading.Thread:
    """Call fn(*args) on a worker thread. fn must not touch widgets or shared state; it returns a result instead.

    Pass methods of a widget as on_done/on_error so they run on the GUI thread.
    A plain Python thread, not a QThread: no Qt object ever lives on the worker thread, so garbage collection
    on the GUI thread cannot destroy one mid-run.
    """
    relay = _Relay(parent)  # parented: kept alive until the result is delivered
    relay.done.connect(on_done)
    relay.failed.connect(on_error)
    relay.done.connect(relay.deleteLater)
    relay.failed.connect(relay.deleteLater)

    def work():
        try:
            result = fn(*args)
        except Exception as e:
            traceback.print_exc()  # details go to the terminal only; dialogs show the message (D20)
            outcome = (relay.failed, str(e))
        else:
            outcome = (relay.done, result)
        try:
            outcome[0].emit(outcome[1])
        except RuntimeError:  # the window was closed while the job ran; nobody is left to tell
            pass

    # shortcut: daemon, so closing the window never hangs on a long load; an export cut off at exit can leave a
    # partial file. Make it non-daemon and wait on close if users report truncated exports.
    thread = threading.Thread(target=work, name=THREAD_NAME, daemon=True)
    thread.start()
    return thread

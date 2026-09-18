"""BringupPrompter: the Textual implementation of ``setup.base.Prompter``, and the only object in the
bring-up path that touches Textual. It carries no decisions (the "humble object"): every method
pushes a screen or updates a label. DeviceManager owns its lifecycle via open()/close()."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from wifit3.ui.screens.bringup_progress import BringupProgressModal
from wifit3.ui.screens.replug import ReplugModal
from wifit3.ui.screens.setup_error import SetupErrorDialog

if TYPE_CHECKING:
    from wifit3.models import DeviceID

logger = logging.getLogger(__name__)


class BringupPrompter:
    def __init__(self, app) -> None:
        self._app = app
        self._modal: BringupProgressModal | None = None

    async def open(self, title: str) -> None:
        """Show the unified progress modal for the whole bring-up; close() dismisses it."""
        self._modal = BringupProgressModal(title)
        await self._app.push_screen(self._modal)

    def close(self) -> None:
        if self._modal is not None:
            self._modal.dismiss()
            self._modal = None

    def status(self, message: str) -> None:
        if self._modal is not None:
            self._modal.set_status(message)

    def status_progress(self, fraction: float, message: str) -> None:
        """connect()'s progress_cb: (fraction 0..1, message)."""
        if self._modal is not None:
            self._modal.set_progress(fraction)
            self._modal.set_status(message)

    @contextmanager
    def suspend(self):
        """Drop the alternate screen so sudo's password prompt owns the real terminal. Falls back
        to a no-op where suspend is unsupported (headless test driver)."""
        try:
            cm = self._app.suspend()
            cm.__enter__()
        except Exception:
            logger.debug("bringup: TUI suspend unsupported; elevating inline", exc_info=True)
            yield
            return
        try:
            yield
        finally:
            # Clean args so a body error still resumes the driver; it keeps propagating after.
            cm.__exit__(None, None, None)

    def error(self, title: str, body: str) -> None:
        # Take down the progress modal first so the error dialog isn't buried under it.
        self.close()
        self._app.push_screen(SetupErrorDialog(title, body))

    async def ask(self, dialog):
        return await self._app.push_screen_wait(dialog)

    async def wait_replug(self, device_id) -> DeviceID | None:
        """The re-enumerated card after the unplug/replug (new bus/address), or None if skipped."""
        replugged = None

        async def _present(present: bool) -> bool:
            nonlocal replugged
            if not present:                               # phase 1: this card leaves the bus
                return await self._app.device_watch.wait_departure(device_id)
            replugged = await self._app.device_watch.wait_arrival(device_id)  # phase 2: fresh instance
            return replugged is not None

        outcome = await self._app.push_screen_wait(ReplugModal(device_id.description, _present))
        return replugged if outcome == "replugged" else None

    def begin_assistant(self, greeting: tuple[str, ...], messages: list[tuple[str, ...]],
                        *, intro_delay: float = 2.0) -> None:
        if self._modal is not None:
            self._app.run_worker(
                self._modal.show_assistant(greeting, messages, intro_delay=intro_delay),
                name="wiffy-show")

    async def end_assistant(self, ok: bool) -> None:
        if self._modal is not None:
            await self._modal.hide_assistant(ok)

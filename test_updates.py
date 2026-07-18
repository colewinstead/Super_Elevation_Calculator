import io
import json
import queue
import unittest
from unittest import mock

import super_app
import super_updates


class UpdateCheckerTests(unittest.TestCase):
    def release(self, version="1.4.0", assets=None, **overrides):
        payload = {
            "tag_name": f"v{version}",
            "draft": False,
            "prerelease": False,
            "html_url": f"https://github.com/{super_updates.REPOSITORY}/releases/tag/v{version}",
            "assets": assets or [],
        }
        payload.update(overrides)
        return payload

    def asset(self, name, version="1.4.0", url=None):
        return {
            "name": name,
            "browser_download_url": url
            or f"https://github.com/{super_updates.REPOSITORY}/releases/download/v{version}/{name}",
        }

    def test_equal_and_older_releases_are_silent(self):
        self.assertIsNone(super_updates.update_from_release(self.release("1.3.0"), "1.3.0"))
        self.assertIsNone(super_updates.update_from_release(self.release("1.2.9"), "1.3.0"))

    def test_draft_and_prerelease_are_silent(self):
        self.assertIsNone(super_updates.update_from_release(self.release(draft=True), "1.3.0"))
        self.assertIsNone(super_updates.update_from_release(self.release(prerelease=True), "1.3.0"))

    def test_windows_release_uses_direct_executable_download(self):
        name = "SuperElevation.exe"
        update = super_updates.update_from_release(
            self.release(assets=[self.asset(name)]),
            "1.3.0",
            platform_name="win32",
            machine="AMD64",
        )
        self.assertEqual(update.latest_version, "1.4.0")
        self.assertTrue(update.download_url.endswith(f"/v1.4.0/{name}"))

    def test_macos_release_selects_matching_processor(self):
        arm_name = "SuperelevationCalculator-macOS-Apple-Silicon.dmg"
        intel_name = "SuperelevationCalculator-macOS-Intel.dmg"
        release = self.release(assets=[self.asset(arm_name), self.asset(intel_name)])
        arm = super_updates.update_from_release(
            release, "1.3.0", platform_name="darwin", machine="arm64"
        )
        intel = super_updates.update_from_release(
            release, "1.3.0", platform_name="darwin", machine="x86_64"
        )
        self.assertTrue(arm.download_url.endswith(arm_name))
        self.assertTrue(intel.download_url.endswith(intel_name))

    def test_missing_or_untrusted_asset_falls_back_to_release_page(self):
        missing = super_updates.update_from_release(
            self.release(), "1.3.0", platform_name="win32", machine="AMD64"
        )
        untrusted = super_updates.update_from_release(
            self.release(assets=[self.asset("SuperElevation.exe", url="https://example.com/update.exe")]),
            "1.3.0",
            platform_name="win32",
            machine="AMD64",
        )
        expected = f"https://github.com/{super_updates.REPOSITORY}/releases/tag/v1.4.0"
        self.assertEqual(missing.download_url, expected)
        self.assertEqual(untrusted.download_url, expected)

    def test_malformed_versions_are_rejected(self):
        for value in ("1.4", "1.4.0-beta", "latest", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                super_updates.parse_version(value)

    def test_network_response_is_evaluated(self):
        name = "SuperElevation.exe"
        response = io.BytesIO(json.dumps(self.release(assets=[self.asset(name)])).encode("utf-8"))
        with mock.patch.object(super_updates, "urlopen", return_value=response) as mocked_urlopen:
            with mock.patch.object(super_updates.sys, "platform", "win32"):
                update = super_updates.check_for_update("1.3.0")
        self.assertEqual(update.latest_version, "1.4.0")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, super_updates.LATEST_RELEASE_API)
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], super_updates.REQUEST_TIMEOUT_SECONDS)
        self.assertIs(mocked_urlopen.call_args.kwargs["context"], super_updates.HTTPS_CONTEXT)

    def test_network_timeout_and_json_errors_are_silent_and_logged(self):
        logger = mock.Mock()
        failures = [OSError("offline"), TimeoutError("timed out")]
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with mock.patch.object(super_updates, "urlopen", side_effect=failure):
                    with mock.patch.object(super_updates.app_logging, "configure_logging", return_value=logger):
                        self.assertIsNone(super_updates.check_for_update("1.3.0"))
        with mock.patch.object(super_updates, "urlopen", return_value=io.BytesIO(b"{")):
            with mock.patch.object(super_updates.app_logging, "configure_logging", return_value=logger):
                self.assertIsNone(super_updates.check_for_update("1.3.0"))
        self.assertEqual(logger.info.call_count, 3)

    def test_launch_starts_one_daemon_worker_and_one_poll(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        app.after = mock.Mock()
        worker = mock.Mock()
        with mock.patch.object(super_app.threading, "Thread", return_value=worker) as thread_class:
            app._start_update_check()
        thread_class.assert_called_once_with(
            target=app._check_for_update_worker,
            name="superelevation-update-check",
            daemon=True,
        )
        worker.start.assert_called_once_with()
        app.after.assert_called_once_with(100, app._poll_update_check)

    def test_ui_poll_displays_only_a_newer_release(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        app._update_result_queue = queue.Queue()
        app._show_update_available = mock.Mock()
        update = super_updates.UpdateInfo("1.3.0", "1.4.0", "https://example.invalid/update")
        app._update_result_queue.put(update)
        app._poll_update_check()
        app._show_update_available.assert_called_once_with(update)

        app._show_update_available.reset_mock()
        app._update_result_queue.put(None)
        app._poll_update_check()
        app._show_update_available.assert_not_called()

    def test_download_button_opens_browser_and_closes_popup(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        update = super_updates.UpdateInfo("1.3.0", "1.4.0", "https://example.invalid/update")
        close_dialog = mock.Mock()
        with mock.patch.object(super_app.webbrowser, "open_new_tab", return_value=True) as open_tab:
            app._open_update_download(update, mock.sentinel.dialog, close_dialog)
        open_tab.assert_called_once_with(update.download_url)
        close_dialog.assert_called_once_with()

    def test_copy_download_link_uses_clipboard_and_resets_button_label(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        app.clipboard_clear = mock.Mock()
        app.clipboard_append = mock.Mock()
        app.update_idletasks = mock.Mock()
        app.after = mock.Mock()
        button = mock.Mock()
        button.winfo_exists.return_value = True
        update = super_updates.UpdateInfo("1.3.0", "1.4.0", "https://example.invalid/update")

        app._copy_update_download(update, mock.sentinel.dialog, button)

        app.clipboard_clear.assert_called_once_with()
        app.clipboard_append.assert_called_once_with(update.download_url)
        button.configure.assert_called_once_with(text="Copied")
        delay, reset = app.after.call_args.args
        self.assertEqual(delay, 2000)
        reset()
        button.configure.assert_called_with(text="Copy Download Link")

    def test_copy_download_link_failure_is_logged_and_explained(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        app.clipboard_clear = mock.Mock(side_effect=RuntimeError("clipboard unavailable"))
        button = mock.Mock()
        update = super_updates.UpdateInfo("1.3.0", "1.4.0", "https://example.invalid/update")
        with mock.patch.object(super_app.app_logging, "record_exception") as record_exception:
            with mock.patch.object(super_app.messagebox, "showerror") as showerror:
                app._copy_update_download(update, mock.sentinel.dialog, button)
        record_exception.assert_called_once()
        showerror.assert_called_once()
        self.assertIs(showerror.call_args.kwargs["parent"], mock.sentinel.dialog)

    def test_failed_browser_open_leaves_copy_button_popup_open(self):
        app = super_app.ModernSuperElevationUI.__new__(super_app.ModernSuperElevationUI)
        update = super_updates.UpdateInfo("1.3.0", "1.4.0", "https://example.invalid/update")
        close_dialog = mock.Mock()
        with mock.patch.object(super_app.webbrowser, "open_new_tab", return_value=False):
            with mock.patch.object(super_app.messagebox, "showerror") as showerror:
                app._open_update_download(update, mock.sentinel.dialog, close_dialog)
        close_dialog.assert_not_called()
        showerror.assert_called_once()
        self.assertIs(showerror.call_args.kwargs["parent"], mock.sentinel.dialog)


if __name__ == "__main__":
    unittest.main()

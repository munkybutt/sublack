from unittest import TestCase
from unittest.mock import patch

import time
import sublime

# from . import fixtures
# from fixtures import (
from fixtures import sublack_module
from fixtures import sublack_server_module
from fixtures import sublack_utils_module
from fixtures import blacked
from fixtures import unblacked
from fixtures import diff
from fixtures import folding1
from fixtures import folding1_expected
from fixtures import folding2
from fixtures import folding2_expected
from fixtures import TestCaseBlack
# )

# _typing = False
# if _typing:
#     import sublack_module
#     import sublack_module.server as sublack_server_module
#     import sublack_module.utils as sublack_utils_module
# del _typing


# import requests  # type: ignore

from pathlib import Path

TEST_BLACK_SETTINGS = {
    "black_command": "black",
    "black_on_save": True,
    "black_line_length": None,
    "black_fast": False,
    "black_debug_on": True,
    "black_default_encoding": "utf-8",
    "black_skip_string_normalization": False,
    "black_include": None,
    "black_py36": None,
    "black_exclude": None,
    "black_use_blackd": False,
    "black_blackd_host": "localhost",
    "black_blackd_port": "",
    "black_use_precommit": False,
}


@patch.object(sublack_module.utils, "is_python", return_value=True)
@patch.object(sublack_module.utils, "get_settings", return_value=TEST_BLACK_SETTINGS)
class TestBlack(TestCaseBlack):
    def test_black_file(self, s, c):
        self.setText(unblacked)
        self.view.run_command("black_file")
        self.assertEqual(blacked, self.all())

    def test_black_file_nothing_todo(self, s, c):
        # clear cache
        sublack_module.utils.clear_cache()

        self.setText(blacked)
        self.view.run_command("black_file")
        self.assertEqual(blacked, self.all())
        self.assertEqual(
            self.view.get_status(sublack_module.consts.STATUS_KEY),
            sublack_module.consts.ALREADY_FORMATTED_MESSAGE,
        )

    def test_black_file_nothing_todo_cached(self, s, c):
        # clear cache
        sublack_module.utils.clear_cache()

        self.setText(blacked)
        self.view.run_command("black_file")

        self.view.run_command("black_file")
        self.assertEqual(blacked, self.all())
        self.assertEqual(
            self.view.get_status(sublack_module.consts.STATUS_KEY),
            sublack_module.consts.ALREADY_FORMATTED_MESSAGE_CACHE,
        )

    def test_black_file_dirty_stay_dirty(self, s, c):
        self.setText(blacked)
        self.assertTrue(self.view.is_dirty())
        self.view.run_command("black_file")
        self.assertTrue(self.view.is_dirty())
        self.assertEqual(blacked, self.all())

    def test_black_diff(self, s, c):
        self.setText(unblacked)
        self.view.set_name("base")
        backup = self.view
        self.view.run_command("black_diff")

        window = sublime.active_window()
        view = window.active_view()
        assert view, "No active view found!"
        print(f"VIEW NAME: {view.name()}")
        region = sublime.Region(0, view.size())
        region = sublime.Region(view.lines(region)[0].begin(), view.size())
        region_content = view.substr(region).strip()
        r_lines = region_content.splitlines()
        lines = diff.splitlines()
        for index, (r, l) in enumerate(zip(r_lines, lines), 1):
            if r == l:
                continue

            raise AssertionError(f"'{r}' != '{l}' on line: {index}")

        self.assertEqual(region_content.strip(), diff.strip())
        self.assertEqual(
            view.settings().get("syntax"), "Packages/Diff/Diff.sublime-syntax"
        )
        self.view = backup
        view.set_scratch(True)
        view.close()

    def test_folding1(self, s, c):
        self.setText(folding1)
        self.view.fold(sublime.Region(25, 62))
        self.view.run_command("black_file")
        self.assertEqual(folding1_expected, self.all())
        self.assertEquals(
            self.view.unfold(sublime.Region(0, self.view.size())),
            [sublime.Region(25, 59)],
        )

    def test_folding2(self, s, c):
        self.setText(folding2)
        self.view.fold(sublime.Region(10, 57))
        self.view.run_command("black_file")
        self.assertEqual(folding2_expected, self.all())
        self.assertEquals(
            self.view.unfold(sublime.Region(0, self.view.size())),
            [sublime.Region(8, 55)],
        )


class TestBlackdServer(TestCase):
    def setUp(self):
        self.port = str(sublack_module.get_open_port())
        SETTINGS = {"sublack_module.black_blackd_port": self.port}

        self.view = sublime.active_window().new_file()
        self.settings = self.view.settings()
        # make sure we have a window to work with
        [self.settings.set(k, v) for k, v in SETTINGS.items()]
        self.settings.set("close_windows_when_empty", False)

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")
        sublime.run_command("blackd_stop")

    def test_start_and_stop_blackd(self, post=False, port=None):
        # because the blackd_start command runs asynchronously on a timeout
        # we need to break the execution loop to allow the async function
        # to be called. So this function is broken into two parts, pre and post.
        # Pre calls blackd_start, async itself, from a timeout, thus providing a
        # break in the execution. It also then calls itself again, but only running
        # the post functionality, which tests if blackd is running on the test port.
        # This provides a syncronous asyncronous way of running this test.
        # I am certain there is a much better method of doing this, so will have to come
        # back to it when I am less sleep deprived...
        if not post:
            port = port or sublack_utils_module.get_open_port()
            def _start_blackd():
                self.view.run_command("blackd_start", {"port": port})
                self.test_start_and_stop_blackd(post=True, port=port)

            sublime.set_timeout_async(_start_blackd, 0)
            return

        start_time = time.time()
        blackd_starting = sublack_server_module.is_blackd_starting()
        while blackd_starting:
            time.sleep(0.5)
            blackd_starting = sublack_server_module.is_blackd_starting()
            if time.time() - start_time > 20:
                raise AssertionError("Timed out waiting for blackd to start")

        self.assertTrue(
            sublack_utils_module.is_blackd_running_on_port(port),
            "ensure blackd is running for the test",
        )

        # self.assertEqual(
        #     self.view.get_status(sublack_module.STATUS_KEY),
        #     sublack_module.BLACKD_STARTED.format(self.port),
        #     "should tell it starts",
        # )

        # # already running aka port in use
        # with patch("sublime.message_dialog"):
        #     self.view.run_command("blackd_start")
        # self.assertEqual(
        #     self.view.get_status(sublack_module.STATUS_KEY),
        #     sublack_module.BLACKD_ALREADY_RUNNING.format(self.port),
        #     "sould tell it fails",
        # )

        sublime.run_command("blackd_stop")

    def test_stopblackd(self):
        return
        # set up
        # stop any existing blackd server first
        # else we lose track of the pid:
        test_port = sublack_utils_module.get_open_port()
        self.view.run_command("blackd_start", {"port": test_port})
        time.sleep(2)
        self.assertTrue(
            sublack_utils_module.is_blackd_running_on_port(test_port),
            "ensure blackd is running for the test",
        )

        # already running, normal way
        sublime.run_command("blackd_stop")
        # self.assertRaises(
        #     requests.ConnectionError,
        #     lambda: requests.post(
        #         "http://localhost:" + self.port, "server should be down"
        #     ),
        # )
        # self.assertEqual(
        #     self.view.get_status(sublack_module.STATUS_KEY),
        #     sublack_module.BLACKD_STOPPED,
        #     "should tell it stops",
        # )

        # # already stopped
        # sublime.run_command("blackd_stop")
        # self.assertEqual(
        #     self.view.get_status(sublack_module.STATUS_KEY),
        #     sublack_module.BLACKD_STOP_FAILED,
        #     "status tell stop failed",
        # )


class TestFormatAll(TestCaseBlack):
    def setUp(self):
        super().setUp()
        self.window.set_project_data({"folders": [{"path": str(self.folder)}]})

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "wrong"):
            self.wrong.unlink()

    def test_black_all_success(self):

        # make sure we have a window to work with
        # s = sublime.load_settings("Preferences.sublime-settings")
        # s.set("close_windows_when_empty", False)
        # self.maxDiff = None

        with patch("sublime.ok_cancel_dialog", return_value=True):
            self.window.run_command("black_format_all")
        self.assertEqual(
            self.window.active_view().get_status(sublack_module.STATUS_KEY),
            sublack_module.REFORMATTED_MESSAGE,
            "reformat should be ok",
        )

    def test_black_all_fail(self):

        self.wrong = self.folder / "wrong.py"
        with open(str(self.wrong), "w") as ww:
            ww.write("ab ac = 2")

        with patch("sublime.ok_cancel_dialog", return_value=True):
            self.window.run_command("black_format_all")
        self.assertEqual(
            self.window.active_view().get_status(sublack_module.STATUS_KEY),
            sublack_module.REFORMAT_ERRORS,
            "reformat should be error",
        )


PRECOMMIT_BLACK_SETTINGS = {
    "black_command": "black",
    "black_on_save": True,
    "black_line_length": None,
    "black_fast": False,
    "black_debug_on": True,
    "black_default_encoding": "utf-8",
    "black_skip_string_normalization": False,
    "black_include": None,
    "black_py36": None,
    "black_exclude": None,
    "black_use_blackd": False,
    "black_blackd_host": "localhost",
    "black_blackd_port": "",
    "black_use_precommit": True,
}

precommit_config_path = Path(Path(__file__).parent, ".pre-commit-config.yaml")


@patch.object(sublack_module.utils, "use_pre_commit", return_value=precommit_config_path)
@patch.object(sublack_module.utils, "is_python", return_value=True)
@patch.object(sublack_module.utils, "get_settings", return_value=PRECOMMIT_BLACK_SETTINGS)
class TestPrecommit(TestCaseBlack):
    def test_black_file(self, s, c, p):
        project = {"folders": [{"path": str(Path(Path(__file__).parents[1]))}]}
        self.window.set_project_data(project)
        # with tempfile.TemporaryDirectory() as T:
        self.setText(unblacked)
        self.view.run_command("black_file")
        self.assertEqual(blacked, self.all())


# @patch.object(sublack_module.commands, "is_python", return_value=True)
# @patch.object(sublack_module.blacker, "get_settings", return_value=TEST_BLACK_SETTINGS)
# class TestCommandsAsync(TestCaseBlackAsync):
#     def test_black_file_keeps_view_port_position(self, s, c):


#            ***** to enable if oneday it works with unittesting ******


#         content = (
#             'a="'
#             + "a" * int(self.view.viewport_extent()[0]) * 2
#             + " "
#             + "a" * int(self.view.viewport_extent()[0]) * 2
#             + '"'
#         )
#         import time

#         print(content)
#         # Packages/Python/Python.sublime-syntax
#         #'Packages/MagicPython/grammars/MagicPython.tmLanguage'
#         self.view.set_syntax_file(
#             "Packages/MagicPython/grammars/MagicPython.tmLanguage"
#         )
#         self.setText(content)

#         viewport = self.view.viewport_position()
#         print(self.view.viewport_extent())
#         print(viewport)
#         self.view.run_command("black_file")

#         yield 2000
#         print(self.view.viewport_position())
#         self.assertEqual(viewport, self.view.viewport_position())

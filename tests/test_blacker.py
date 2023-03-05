from __future__ import annotations

import copy
import os
import pathlib
import sublime
import tempfile

from fixtures import sublack_module
from fixtures import sublack_utils_module
from fixtures import TestCaseBlack
from fixtures import view
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch


TEST_CUSTOM_BLACK_SETTINGS = {
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


class TestBlackMethod(TestCaseBlack):
    def _get_view(self):
        window = sublime.active_window()
        view = window.active_view()
        assert view, "view is not defined"
        return view

    def _get_base_black_command(self, black_command: str | None = None):
        return copy.copy(
            sublack_utils_module.get_base_black_command(
                self._get_view(), black_command=black_command
            )
        )

    def _get_black_instance(self):
        return sublack_module.blacker.Black(view=self._get_view())

    # @patch.object(sublack_utils_module, "get_settings", return_value=TEST_CUSTOM_BLACK_SETTINGS)
    # def test_get_custom_command_line(self, s):
    #     view = self._get_view()
    #     black = sublack_module.blacker.Black(view)
    #     black_command = self.base_black_command
    #     command = sublack_utils_module.get_full_black_command(view)
    #     expected_command = black_command.extend(("-l", "90", "--fast"))
    #     self.assertEqual(command, expected_command)

    #     # test diff
    #     command = black.get_black_command(extra=["--diff"])
    #     expected_command = [python_exe_path, black_command, "--diff", "-l", "90", "--fast"]
    #     self.assertEqual(command, expected_command)

    #     # test skipstring
    #     black.settings = {"black_command": "black", "black_skip_string_normalization": True}
    #     command = black.get_black_command()
    #     expected_command = [python_exe_path, black_command, "--skip-string-normalization"]
    #     self.assertEqual(command, expected_command)

    #     # test py36
    #     black.settings = {"black_command": "black", "black_py36": True}
    #     command = black.get_black_command()
    #     expected_command = [python_exe_path, black_command, "--py36"]
    #     self.assertEqual(command, expected_command)

    #     # test tearget target-version
    #     black.settings = {"black_command": "black", "black_target_version": ["py36"]}
    #     command = black.get_black_command()
    #     expected_command = [python_exe_path, black_command, "--target-version", "py36"]
    #     self.assertEqual(command, expected_command)

    #     # test tearget target-version
    #     black.settings = {"black_command": "black", "black_target_version": ["py36", "py37"]}
    #     command = black.get_black_command()
    #     expected_command = [python_exe_path, black_command, "--target-version", "py36", "--target-version", "py37"]
    #     self.assertEqual(command, expected_command)

    #     # test pyi
    #     view = MagicMock()
    #     black.settings = {"black_command": "black"}
    #     black.view = view
    #     view.file_name.return_value = "blabla.pyi"
    #     command = black.get_black_command()
    #     expected_command = [python_exe_path, black_command, "--pyi"]
    #     self.assertEqual(command, expected_command)

    @patch.object(
        sublack_utils_module,
        "get_settings",
        return_value={
            "black_command": "black",
            "black_line_length": 90,
            "black_fast": True,
        },
    )
    def test_get_command_custom_90_fast(self, _):
        view = self._get_view()
        command = sublack_utils_module.get_full_black_command(view)
        expected_command = self._get_base_black_command(black_command="black")
        expected_command.extend(("-l", "90", "--fast"))
        self.assertEqual(command, expected_command)

    @patch.object(
        sublack_utils_module,
        "get_settings",
        return_value={
            "black_command": None,
            "black_line_length": 90,
            "black_fast": False,
        },
    )
    def test_get_command_custom_diff(self, _):
        view = self._get_view()
        command = sublack_utils_module.get_full_black_command(view, extra=["--diff"])
        expected_command = self._get_base_black_command()
        expected_command.extend(("--diff", "-l", "90"))
        self.assertEqual(command, expected_command)

    @patch.object(
        sublack_utils_module,
        "get_settings",
        return_value={
            "black_command": None,
            "black_line_length": None,
            "black_fast": False,
        },
    )
    def test_get_command_vendor(self, _):
        view = self._get_view()
        command = sublack_utils_module.get_full_black_command(view)
        expected_command = self._get_base_black_command()
        self.assertEqual(command, expected_command)

    def test_get_content_encoding(self):
        self.view.set_encoding("utf-8")
        black = sublack_module.blacker.Black(self.view)
        _, encoding = black.get_content()
        self.assertEqual(encoding, self.view.encoding())

    def test_get_content(self):
        self.view.set_encoding("utf-8")
        self.setText("hÃ©llo")
        black = sublack_module.blacker.Black(self.view)
        content, _ = black.get_content()
        self.assertEqual(content.decode("utf-8"), "hÃ©llo")

    @patch.object(
        sublack_utils_module,
        "get_settings",
        return_value={
            "black_command": None,
            "black_line_length": None,
            "black_fast": False,
            "black_use_blackd": False,
        },
    )
    def test_run_black(self, _):
        black = self._get_black_instance()
        view = self._get_view()
        command = sublack_utils_module.get_full_black_command(view)
        return_code, out, error = black.run_black(
            command, os.environ.copy(), None, "hello".encode()
        )
        self.assertEqual(return_code, 0)
        self.assertEqual(out, b"hello\n")
        self.assertIn(b"reformatted", error)

    def test_good_working_dir(self):
        gg = sublack_module.blacker.Black.get_good_working_dir

        # filename ok
        s = MagicMock()
        s.view.file_name.return_value = "/bla/bla.py"
        self.assertEqual("/bla", gg(s))

        # no filenmae, no window
        s.view.file_name.return_value = None
        s.variables.get.return_value = ""
        s.view.window.return_value = None
        self.assertEqual(None, gg(s))

        # not folders
        e = MagicMock()
        s.view.window.return_value = e
        e.folders.return_value = []
        self.assertEqual(None, gg(s))

        # folder dir
        e.folders.return_value = ["/bla", "ble"]
        self.assertEqual("/bla", gg(s))


class TestCache(TestCase):
    def setUp(self):
        # data
        self.view = view()
        self.ah = str(hash("a"))
        self.bh = str(hash("b"))
        self.cmd1 = ["cmd1"]
        self.cache = self.ah + "|||" + str(self.cmd1) + "\n" + self.bh + "|||" + str(self.cmd1)
        # view
        self.black = sublack_module.blacker.Black(self.view)

        # temp file
        temp = tempfile.NamedTemporaryFile(delete=True)
        temp.close()
        self.black.formatted_cache = pathlib.Path(temp.name)
        with self.black.formatted_cache.open(mode="w") as f:
            f.write(self.cache)

    def tearDown(self):
        self.black.formatted_cache.unlink()
        self.view.set_scratch(True)
        self.view.window().run_command("close_file")

    def test_is_cached(self):

        # test first line present
        self.assertTrue(self.black.is_cached("a", self.cmd1))

        # test second line present
        self.assertTrue(self.black.is_cached("b", self.cmd1))

        # test content ok cmd not ok
        self.assertFalse(self.black.is_cached("b", ["cmd2"]))

        # test contnent not cmd ok
        self.assertFalse(self.black.is_cached("c", self.cmd1))

    def test_add_to_cache(self):

        # test already in , not added
        self.assertFalse(self.black.add_to_cache("a", self.cmd1))

        # test added and contenu
        self.assertTrue(self.black.add_to_cache("c", self.cmd1))
        self.assertEqual(
            self.black.formatted_cache.open().read(),
            "{}|||['cmd1']\n{}|||['cmd1']\n{}|||['cmd1']".format(str(hash("c")), self.ah, self.bh),
        )

    def test_limit_cache_size(self):
        ligne = self.ah + "|||" + str(self.cmd1) + "\n"
        with self.black.formatted_cache.open("wt") as f:
            f.write(251 * ligne)

        self.black.add_to_cache("b", self.cmd1)

        new_line = "{}|||['cmd1']".format(self.bh)
        cached = self.black.formatted_cache.open().read().splitlines()
        self.assertEqual(len(cached), 251)
        self.assertEqual(cached[:2], [new_line] + [ligne.strip()])


class TestBlackdClass(TestCase):
    def test_format_header(self):
        self.maxDiff = None

        # dep
        cmd = (
            "black - -l 25 --fast --skip-string-normalization --target-version py37".split()
        )
        blackd = sublack_module.blacker.Blackd(cmd, b"", "utf-8", {})
        header = blackd.format_headers(cmd)
        header["X-Python-Variant"] = set(header["X-Python-Variant"].split(","))
        self.assertEqual(
            header,
            {
                "X-Line-Length": "25",
                "X-Skip-String-Normalization": "1",
                "X-Python-Variant": {"py3.7"},
                "X-Fast-Or-Safe": "fast",
            },
        )

        # standard
        cmd = "black - -l 25 --fast --skip-string-normalization".split()
        header = blackd.format_headers(cmd)
        self.assertEqual(
            header,
            {
                "X-Line-Length": "25",
                "X-Skip-String-Normalization": "1",
                # "X-Python-Variant": "py3.6",
                "X-Fast-Or-Safe": "fast",
            },
        )

        # target-version
        cmd = "black - -l 25 --fast --skip-string-normalization --target-version py36 --target-version py37".split()
        header = blackd.format_headers(cmd)
        header["X-Python-Variant"] = set(header["X-Python-Variant"].split(","))
        self.assertEqual(
            header,
            {
                "X-Line-Length": "25",
                "X-Skip-String-Normalization": "1",
                "X-Python-Variant": {"py3.6", "py3.7"},
                "X-Fast-Or-Safe": "fast",
            },
        )

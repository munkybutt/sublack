import sublack as _sb
import sublack.server as _sbs
import sublack.utils as _sbu
import sublime

from unittest import TestCase
from unittesting import DeferrableTestCase

sublack_module = _sb
sublack_server_module = _sbs
sublack_utils_module = _sbu


class TestCaseBlack(TestCase):
    def setUp(self): ...
    def tearDown(self): ...
    def all(self): ...
    def setText(self, string: str): ...


class TestCaseBlackAsync(DeferrableTestCase):
    def setUp(self): ...
    def tearDown(self): ...
    def all(self): ...
    def setText(self, string: str): ...


def view() -> sublime.View: ...


pre_commit_config: dict[str, str] = ...
blacked: str = ...
unblacked: str = ...
diff: str = ...
folding1: str = ...
folding1_expected: str = ...
folding2: str = ...
folding2_expected: str = ...

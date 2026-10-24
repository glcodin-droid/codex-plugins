"""Behavioral checks for title formatting and malformed historical titles."""
import importlib.util
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/codex-title-formatter/skills/format-chat-title/scripts/format_title.py"
spec = importlib.util.spec_from_file_location("format_title", SCRIPT)
formatter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formatter)


class FormatTitleTests(unittest.TestCase):
    def test_project_and_no_project(self):
        self.assertEqual(formatter.format_title("修复登录失败", "2026-10-29", "Codin"),
                         "10.29｜Codin｜修复登录失败")
        self.assertEqual(formatter.format_title("比较鼠标连接稳定性", "10.29"),
                         "10.29｜比较鼠标连接稳定性")

    def test_old_date_is_preserved_instead_of_today(self):
        self.assertEqual(formatter.format_title("0920｜比较工具价格", today=date(2026, 10, 29)),
                         "09.20｜比较工具价格")

    def test_explicit_date_overrides_old_date(self):
        self.assertEqual(formatter.format_title("09.20｜主题", "2026-10-29"), "10.29｜主题")

    def test_leading_zero_and_legacy_dates(self):
        for old in ("1.3", "1/3", "01-03", "0103", "2026-1-3"):
            with self.subTest(old=old):
                self.assertEqual(formatter.format_title(old + "|项目|主题"), "01.03｜项目｜主题")

    def test_missing_project_does_not_create_empty_segment(self):
        for project in (None, "", "无", "无项目", "None", "NULL", "N/A", "未指定"):
            with self.subTest(project=project):
                self.assertEqual(formatter.format_title("主题", "10.29", project), "10.29｜主题")

    def test_project_override_and_removal(self):
        self.assertEqual(formatter.format_title("10.29｜旧项目｜主题", project="新项目"),
                         "10.29｜新项目｜主题")
        self.assertEqual(formatter.format_title("10.29｜旧项目｜主题", project=""), "10.29｜主题")

    def test_repeated_date_prefixes_are_not_accumulated(self):
        self.assertEqual(formatter.format_title("1029 | 10.29｜项目｜主题"), "10.29｜项目｜主题")

    def test_idempotent(self):
        for title in ("10.29｜主题", "10.29｜Codin｜修复登录失败", "01.03｜比较工具价格"):
            with self.subTest(title=title):
                self.assertEqual(formatter.format_title(formatter.format_title(title)), title)

    def test_new_topic_does_not_invent_a_project_from_a_pipe(self):
        self.assertEqual(formatter.format_title("输入 | 输出", "10.29"), "10.29｜输入、输出")

    def test_field_whitespace_and_separators(self):
        self.assertEqual(formatter.format_title("  修复\n 登录  ", "10.29", "项目|客户端"),
                         "10.29｜项目、客户端｜修复 登录")

    def test_ambiguous_old_title_is_rejected(self):
        with self.assertRaises(ValueError):
            formatter.format_title("10.29｜项目｜主题｜其他")

    def test_invalid_dates_and_empty_topic_are_rejected(self):
        for value in ("13.01", "00.20", "04.31", "2026-02-29", "10299"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                formatter.format_title("主题", value)
        for value in ("", "  ", "10.29｜", "10.29｜项目｜"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                formatter.format_title(value, "10.29")

    def test_leap_day_is_valid_when_year_allows_it(self):
        self.assertEqual(formatter.format_title("主题", "2024-02-29"), "02.29｜主题")
        self.assertEqual(formatter.format_title("02.29｜主题"), "02.29｜主题")

    def test_current_date_fallback_is_explicitly_testable(self):
        self.assertEqual(formatter.format_title("主题", today=date(2026, 1, 3)), "01.03｜主题")

    def test_cli_output_and_error_exit_code(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--date", "2026-10-29",
                                 "--project", "Codin", "--topic", "修复登录失败"],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "10.29｜Codin｜修复登录失败\n")
        failed = subprocess.run([sys.executable, str(SCRIPT), "--date", "13.01", "--topic", "主题"],
                                capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(failed.stdout, "")


if __name__ == "__main__":
    unittest.main()

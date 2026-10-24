#!/usr/bin/env python3
"""Build a Codex title. This module never reads or changes chat storage."""

import argparse
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UNSET = object()
SEPARATOR = "｜"
DATE_PREFIX = re.compile(
    r"^\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}|\d{4})\s*[|｜]\s*"
)
EMPTY_PROJECTS = {"", "无", "无项目", "none", "null", "n/a", "-", "未指定"}


def parse_date(value):
    """Validate ISO dates or month/day forms, returning MM.DD.

    A month/day without a year may refer to a historical leap year, so validate
    it against 2000. An explicitly supplied year is always validated as given.
    """
    value = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", value):
        year, month, day = map(int, value.split("-"))
    elif re.fullmatch(r"\d{1,2}[./-]\d{1,2}", value):
        month, day = map(int, re.split(r"[./-]", value))
        year = 2000
    elif re.fullmatch(r"\d{4}", value):
        year, month, day = 2000, int(value[:2]), int(value[2:])
    else:
        raise ValueError("日期须使用 YYYY-MM-DD、MM.DD、MM/DD、MM-DD 或 MMDD")
    try:
        checked = date(year, month, day)
    except ValueError as exc:
        raise ValueError("无效日期：" + value) from exc
    return checked.strftime("%m.%d")


def clean_field(value):
    text = " ".join(str(value).split())
    return "、".join(
        part.strip() for part in re.split(r"[|｜]+", text) if part.strip()
    )


def format_title(topic, date_text=None, project=UNSET, today=None, timezone=None):
    """Compose a title; infer fields only from an existing date-prefixed title.

    project omitted: preserve a structured old title's project.
    project None or empty: explicitly remove any old project.
    date_text omitted: preserve an old prefix, otherwise use the local date.
    """
    text = str(topic).strip()
    old_date = None
    while True:
        match = DATE_PREFIX.match(text)
        if not match:
            break
        checked = parse_date(match.group(1))
        if old_date is None:
            old_date = checked
        text = text[match.end():]

    parts = [part.strip() for part in re.split(r"[|｜]", text)]
    old_project = None
    if old_date and len(parts) >= 3:
        raise ValueError("旧标题包含超过三个字段，请先明确项目和主题")
    if old_date and len(parts) == 2:
        old_project, text = parts

    selected_project = old_project if project is UNSET else project
    selected_project = "" if selected_project is None else clean_field(selected_project)
    if selected_project.casefold() in EMPTY_PROJECTS:
        selected_project = ""
    selected_topic = clean_field(text)
    if not selected_topic:
        raise ValueError("主题不能为空")

    if date_text is not None:
        selected_date = parse_date(date_text)
    elif old_date:
        selected_date = old_date
    else:
        if today is None:
            try:
                today = datetime.now(ZoneInfo(timezone) if timezone else None).date()
            except ZoneInfoNotFoundError as exc:
                raise ValueError("无法识别时区：" + str(timezone)) from exc
        selected_date = today.strftime("%m.%d")
    fields = [selected_date]
    if selected_project:
        fields.append(selected_project)
    fields.append(selected_topic)
    return SEPARATOR.join(fields)


def main():
    parser = argparse.ArgumentParser(description="生成 MM.DD｜项目｜主题 或 MM.DD｜主题")
    parser.add_argument("--topic", required=True, help="主题，或已有的日期前缀标题")
    parser.add_argument("--date", dest="date_text", help="明确的标题日期；不指定时保留已有日期")
    parser.add_argument("--project", default=UNSET, help="项目名；传空字符串可移除旧项目")
    parser.add_argument("--timezone", help="无日期依据时使用的 IANA 时区，如 Asia/Shanghai")
    args = parser.parse_args()
    try:
        result = format_title(**vars(args))
    except ValueError as exc:
        parser.error(str(exc))
    print(result)


if __name__ == "__main__":
    main()

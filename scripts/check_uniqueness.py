#!/usr/bin/env python3
"""Check that a report does not reuse substantive titles or prose from other reports."""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

IGNORED_PREFIXES = (
    '古籍原文', '本报告基于传统八字', '本报告把传统术语', '八字 + 紫微斗数综合解读'
)

def meaningful_lines(data):
    lines = []
    for section in data.get('sections') or []:
        title = re.sub(r'^\d+[A-Z]?｜', '', str(section.get('title') or '')).strip()
        if title:
            lines.append(('title', title))
        for field in ('content', 'basis', 'evidence'):
            for line in str(section.get(field) or '').splitlines():
                line = re.sub(r'\s+', '', line).strip()
                if len(line) < 22 or line.startswith(IGNORED_PREFIXES):
                    continue
                lines.append(('text', line))
        for action in section.get('actions') or []:
            line = re.sub(r'\s+', '', str(action)).strip()
            if len(line) >= 18:
                lines.append(('action', line))
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--against', nargs='*', default=[])
    args = ap.parse_args()
    current = json.loads(Path(args.input).read_text(encoding='utf-8'))
    current_lines = meaningful_lines(current)
    current_titles = {x for kind, x in current_lines if kind == 'title'}
    errors = []
    for other_path in args.against:
        other = json.loads(Path(other_path).read_text(encoding='utf-8'))
        other_lines = meaningful_lines(other)
        other_titles = {x for kind, x in other_lines if kind == 'title'}
        for title in sorted(current_titles & other_titles):
            errors.append(f'exact title reuse: {title}')
        other_text = {x for kind, x in other_lines if kind != 'title'}
        for kind, line in current_lines:
            if kind == 'title':
                continue
            if line in other_text:
                errors.append(f'exact prose reuse: {line[:80]}')
        current_blob = '\n'.join(x for kind, x in current_lines if kind == 'text')
        other_blob = '\n'.join(x for kind, x in other_lines if kind == 'text')
        ratio = difflib.SequenceMatcher(None, current_blob, other_blob).ratio()
        if ratio >= 0.62:
            errors.append(f'overall prose similarity {ratio:.2f} exceeds 0.62 against {other_path}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('uniqueness check passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

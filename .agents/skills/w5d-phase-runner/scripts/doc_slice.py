"""Bounded UTF-8 Markdown reads; no external dependencies or state writes."""
import argparse
import hashlib
import re
import sys
from pathlib import Path


def headings(lines):
    fence = None
    for number, line in enumerate(lines, 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        match = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*$", line)
        if fence is None and match:
            yield number, len(match.group(1)), line


def read_slice(root, file, start=1, count=80, section=None,
               heading_only=False, max_chars=12000):
    if start < 1 or count < 1 or not 256 <= max_chars <= 24000:
        raise ValueError("start/lines must be positive; max-chars must be 256..24000")
    base = Path(root).resolve()
    target = (base / file).resolve()
    if not target.is_relative_to(base):
        raise ValueError("file must stay inside project root")
    if target.suffix.lower() != ".md":
        raise ValueError("only Markdown documents are supported")
    raw = target.read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    index = list(headings(lines))
    if section:
        matches = [entry for entry in index if entry[2].strip().startswith(section)]
        if len(matches) != 1:
            raise ValueError(f"section matched {len(matches)} headings; use a unique prefix")
        first, level, _ = matches[0]
        stop = next((num for num, depth, _ in index if num > first and depth <= level),
                    len(lines) + 1)
        # --start is an absolute cursor, including when resuming a section.
        if start > 1 and not first <= start < stop:
            raise ValueError("start must fall inside the requested section")
        start = max(first, start)
        selected = [(num, lines[num - 1]) for num in range(start, stop)]
    elif heading_only:
        selected = [(num, title) for num, _, title in index if num >= start]
    else:
        selected = [(num, lines[num - 1])
                    for num in range(start, min(len(lines) + 1, start + count))]

    header = (f"FILE {target.relative_to(base).as_posix()} "
              f"SHA256 {hashlib.sha256(raw).hexdigest()}\n")
    footer_reserve = 200
    used = len(header)
    output = [header.rstrip("\n")]
    next_line = None
    for num, line in selected:
        rendered = f"{num}: {line}"
        if used + len(rendered) + 1 > max_chars - footer_reserve:
            next_line = num
            break
        output.append(rendered)
        used += len(rendered) + 1
    if next_line is not None:
        output.append(f"TRUNCATED next_line={next_line}; reduce slice or inspect this long line separately.")
    else:
        cursor = selected[-1][0] + 1 if selected else start
        output.append(f"COMPLETE_SLICE next_line={cursor}; total_lines={len(lines)}")
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--file", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--headings", action="store_true")
    mode.add_argument("--section", help="unique heading prefix, including # markers")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--lines", type=int, default=80)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()
    try:
        result = read_slice(args.root, args.file, args.start, args.lines,
                            args.section, args.headings, args.max_chars)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"doc_slice: {exc}\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(result)


if __name__ == "__main__":
    main()

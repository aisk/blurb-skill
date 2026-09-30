#!/usr/bin/env python3
"""Create a CPython ``Misc/NEWS.d/next`` entry without an interactive editor.

This does what ``blurb add`` does, minus the editor round trip: detect the
CPython checkout, validate the metadata and the body, wrap the body at 76
columns, then write

    Misc/NEWS.d/next/<section>/<date>.gh-issue-<issue>.<nonce>.rst

The date is read from the system clock at run time and the nonce is the
MD5 digest of the wrapped body.  Neither value may be supplied by hand.

Writing that file is the whole job; staging or committing it is left to
the caller.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import sys
import textwrap
import time

# Canonical section names, in the order blurb lists them.
SECTIONS = (
    'Security',
    'Core and Builtins',
    'Library',
    'Documentation',
    'Tests',
    'Build',
    'Windows',
    'macOS',
    'IDLE',
    'Tools/Demos',
    'C API',
)

# Section name -> directory name.
SANITIZED_SECTIONS = {
    'C API': 'C_API',
    'Core and Builtins': 'Core_and_Builtins',
    'Tools/Demos': 'Tools-Demos',
}

LOWEST_POSSIBLE_GH_ISSUE_NUMBER = 32426

NAUGHTY_PREFIXES = ('- ', 'Issue #', 'bpo-', 'gh-', 'gh-issue-')

README_RE = re.compile(r'This is \w+ version \d+\.\d+').match


class UserError(SystemExit):
    def __init__(self, msg: str) -> None:
        super().__init__(f'Error: {msg}')


# --------------------------------------------------------------------------
# repository detection
# --------------------------------------------------------------------------


def find_repo_root(start: str) -> str:
    """Walk up from *start* looking for the root of a CPython checkout.

    Uses the same signature as blurb: we can't ask git, because the tree
    may have been exported rather than cloned.
    """
    path = os.path.abspath(os.path.join(start, 'garglemox'))
    while True:
        next_path = os.path.dirname(path)
        if next_path == path:
            raise UserError(
                "You're not inside a CPython repo right now! "
                'Run this from a CPython checkout, or pass --repo-root.'
            )
        path = next_path
        if is_repo_root(path):
            return path


def is_repo_root(path: str) -> bool:
    def first_line_matches(filename: str, test) -> bool:
        full = os.path.join(path, filename)
        if not os.path.exists(full):
            return False
        with open(full, encoding='utf-8', errors='replace') as file:
            first_line = file.readline().rstrip('\n')
        return bool(test(first_line))

    if not (
        first_line_matches('README', README_RE)
        or first_line_matches('README.rst', README_RE)
    ):
        return False
    if not first_line_matches('LICENSE', 'A. HISTORY OF THE SOFTWARE'.__eq__):
        return False
    if not os.path.exists(os.path.join(path, 'Include', 'Python.h')):
        return False
    if not os.path.exists(os.path.join(path, 'Python', 'ceval.c')):
        return False
    return True


# --------------------------------------------------------------------------
# metadata validation
# --------------------------------------------------------------------------


def parse_issue(issue: str) -> int:
    """Accept 12345, gh-12345, #12345, or a GitHub issue URL."""
    issue = issue.strip()

    if issue.startswith(('GH-', 'gh-')):
        stripped = issue[3:]
    else:
        stripped = issue.removeprefix('#')
    if stripped.isdecimal():
        number = int(stripped)
    else:
        stripped = issue.removeprefix('https://')
        stripped = stripped.removeprefix('http://')
        stripped = stripped.removeprefix('github.com/python/cpython/issues/')
        stripped = stripped.split('#')[0].rstrip('/')
        if not stripped.isdecimal():
            raise UserError(f'Invalid GitHub issue number: {issue}')
        number = int(stripped)

    if number < LOWEST_POSSIBLE_GH_ISSUE_NUMBER:
        raise UserError(
            f'Invalid gh-issue number: {number} '
            f'(must be >= {LOWEST_POSSIBLE_GH_ISSUE_NUMBER})'
        )
    return number


def parse_section(section: str) -> str:
    """Match a section name case-insensitively, allowing underscores."""
    section = section.strip()
    if not section:
        raise UserError('Empty section name!')

    candidate = section.replace('_', ' ').lower()
    for section_name in SECTIONS:
        if candidate == section_name.replace('_', ' ').lower():
            return section_name

    section_list = '\n'.join(f'* {s}' for s in SECTIONS)
    raise UserError(f'Invalid section name: {section!r}\n\nValid names are:\n\n{section_list}')


def check_body(body: str) -> None:
    """Validate the wrapped body the way blurb does when it reads the file."""
    if not body.strip():
        raise UserError("Blurb 'body' text must not be empty!")
    # blurb treats leading '#' lines as comments and leading '..' lines as
    # metadata, and a line holding only '..' ends the entry.
    if body.startswith(('#', '..')):
        raise UserError(
            "Blurb 'body' can't start with '#' or '..'! "
            'blurb would read that line as a comment or as metadata.'
        )
    if '..' in body.split('\n'):
        raise UserError(
            "Blurb 'body' can't contain a line with only '..'! "
            'blurb would read it as the end of the entry.'
        )
    for naughty_prefix in NAUGHTY_PREFIXES:
        if re.match(naughty_prefix, body, re.I):
            raise UserError(
                f"Blurb 'body' can't start with {naughty_prefix!r}! "
                'The issue reference is added when the entry is rendered.'
            )


# --------------------------------------------------------------------------
# body formatting, date, nonce
# --------------------------------------------------------------------------


def textwrap_body(text: str) -> str:
    """Wrap prose paragraphs at 76 columns, leaving lists and code blocks alone."""
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    wrapped_paragraphs = []
    dont_reflow = False
    for paragraph in text.split('\n\n'):
        # Don't reflow bulleted or numbered lists, or literal blocks.
        dont_reflow = dont_reflow or paragraph.startswith(('* ', '1. ', '#. '))
        if dont_reflow:
            wrapped_paragraphs.append(paragraph)
        else:
            # Wrap twice: textwrap can collapse double spaces after a period
            # on the second pass, so one pass alone is not a fixed point.
            for _ in range(2):
                paragraph = '\n'.join(
                    textwrap.wrap(
                        paragraph.strip(),
                        width=76,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                ).rstrip()
            wrapped_paragraphs.append(paragraph)
        dont_reflow = paragraph.endswith('::')

    text = '\n\n'.join(wrapped_paragraphs).rstrip()
    return f'{text}\n'


def current_datetime() -> str:
    """Read the clock at run time, the same way blurb does."""
    return time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())


def generate_nonce(body: str) -> str:
    digest = hashlib.md5(body.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)[:6].decode('ascii')


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def read_body(args: argparse.Namespace) -> str:
    if args.body_file is not None:
        if args.body_file == '-':
            return sys.stdin.read()
        with open(args.body_file, encoding='utf-8') as file:
            return file.read()
    if args.body is not None:
        return args.body
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise UserError('No body given. Use --body, --body-file, or pipe it on stdin.')


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Create a Misc/NEWS.d/next entry in a CPython checkout.',
    )
    parser.add_argument(
        '-i', '--issue', required=True,
        help='GitHub issue number, gh-NNNNN, #NNNNN, or issue URL',
    )
    parser.add_argument(
        '-s', '--section', required=True,
        help='section name, case-insensitive (e.g. Library, "C API", c_api)',
    )
    parser.add_argument('-b', '--body', help='entry text, a single reST paragraph')
    parser.add_argument(
        '-f', '--body-file', help="read the entry text from a file ('-' for stdin)"
    )
    parser.add_argument(
        '--repo-root', help='CPython checkout to write into (default: search upwards)'
    )
    parser.add_argument(
        '-n', '--dry-run', action='store_true',
        help='print the path and the text, write nothing',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    issue = parse_issue(args.issue)
    section = parse_section(args.section)
    body = textwrap_body(read_body(args))
    check_body(body)

    if args.repo_root:
        root = os.path.abspath(args.repo_root)
        if not is_repo_root(root):
            raise UserError(f'{root} is not the root of a CPython checkout.')
    else:
        root = find_repo_root(os.getcwd())

    date = current_datetime()
    nonce = generate_nonce(body)
    directory = os.path.join(
        root, 'Misc', 'NEWS.d', 'next', SANITIZED_SECTIONS.get(section, section)
    )
    path = os.path.join(directory, f'{date}.gh-issue-{issue}.{nonce}.rst')

    if args.dry_run:
        print(path)
        print()
        print(body, end='')
        return 0

    if os.path.exists(path):
        raise UserError(f'{path} already exists!')

    os.makedirs(directory, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as file:
        file.write(body)
    print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main())

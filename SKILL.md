---
name: blurb
description: Create a CPython Misc/NEWS.d/next news entry (a "blurb") from the command line, without opening an editor. Use when the user asks to add a NEWS entry, a blurb, a changelog entry, or a Misc/NEWS.d file for a CPython change, or asks whether a change needs one. Handles CPython checkout detection, section and issue validation, body wrapping, and the timestamped filename.
license: MIT
compatibility: Requires Python 3.9+ and a CPython checkout to write into
---

# blurb

Write a `Misc/NEWS.d/next/<section>/<date>.gh-issue-<issue>.<nonce>.rst` file into a
CPython checkout. This is what `blurb add` produces, except `blurb add` always opens
`$GIT_EDITOR` / `$EDITOR`, which is unusable non-interactively.

Generating that file and putting it in the right place is the whole job. Staging or
committing it is not part of this skill; do that separately if the task calls for it.

Everything goes through `scripts/add_blurb.py`. Do not hand-write the file: the
timestamp and the nonce in the filename must be computed at run time, and the script
is the only thing that does that correctly.

## Usage

```bash
python3 <skill-dir>/scripts/add_blurb.py -i <issue> -s <section> -b "<body>"
```

`<skill-dir>` is the directory holding this file; the script lives next to it and is
referenced by absolute path, because the command must run from inside the CPython
checkout (or name it with `--repo-root`), not from the skill directory.

The script prints the path it wrote, and writes nothing else.

Options:

| Option | Meaning |
| --- | --- |
| `-i`, `--issue` | `109198`, `gh-109198`, `#109198`, or the full GitHub issue URL |
| `-s`, `--section` | section name, case-insensitive; `_` may stand in for a space |
| `-b`, `--body` | the entry text |
| `-f`, `--body-file` | read the text from a file (`-` means stdin) |
| `--repo-root` | target checkout, when running from outside it |
| `-n`, `--dry-run` | print the path and text, write nothing |

With neither `-b` nor `-f`, the body is read from stdin, which is the easiest way to
pass text containing quotes:

```bash
python3 <skill-dir>/scripts/add_blurb.py -i 109198 -s Library <<'BODY'
Fix a crash in :func:`os.stat` when the path contains a surrogate.
BODY
```

## Rules the script enforces

Read these before writing the body; a violation is a hard error, not a warning.

- **Must be inside a CPython checkout.** The script walks up from the current
  directory looking for a `README`/`README.rst` starting with `This is Python version
  X.Y`, a `LICENSE` starting with `A. HISTORY OF THE SOFTWARE`, plus `Include/Python.h`
  and `Python/ceval.c`. It does not ask git, because the tree may be an export. If it
  fails, you are in the wrong directory: find the checkout and pass `--repo-root`
  rather than working around the check.
- **Section** must be one of: Security, Core and Builtins, Library, Documentation,
  Tests, Build, Windows, macOS, IDLE, Tools/Demos, C API.
- **Issue number** must be at least 32426; anything lower is a Roundup (bpo) number,
  not a GitHub issue.
- **Body** must be non-empty and must not start with `- `, `Issue #`, `bpo-`, `gh-`, or
  `gh-issue-`. The `- gh-issue-N: ` prefix is added when NEWS is rendered, so writing it
  yourself would double it up.

## Writing the body

One paragraph of simple reST, in the past or present tense, describing the change from
the user's point of view. Sphinx roles such as :func:`os.stat` and :mod:`asyncio` are
expected. Avoid section headers, footnotes, tables, and anything needing hard line
breaks. The script wraps prose at 76 columns for you, so write it as one long line and
let it wrap; bulleted lists and literal blocks are left alone.

## Time and randomness

The filename carries a `YYYY-MM-DD-hh-mm-ss` timestamp and a 6-character nonce.

- The timestamp is read from the system clock when the script runs, in local time,
  matching blurb. Never supply a date you believe to be current; a remembered or
  inferred date will be wrong and will sort the entry into the wrong place.
- The nonce is the first 6 characters of the urlsafe base64 of the MD5 digest of the
  wrapped body. It exists to avoid filename collisions between contributors, so it is
  derived, never invented.

Both are computed inside the script. There is no option to override either, on purpose.

## Checking the result

`cat` on the printed path shows the wrapped text, and `git status --short Misc/NEWS.d`
shows the file as untracked. To preview how it will render in `Misc/NEWS`, run
`blurb merge /tmp/NEWS.preview` from the checkout if blurb is installed; do not let it
overwrite the real `Misc/NEWS`.

# blurb-skill

A [Claude Code](https://claude.com/claude-code) skill that adds a CPython
`Misc/NEWS.d/next` news entry from the command line, doing what `blurb add` does without
opening an editor. It detects the CPython checkout, validates the issue number and
section, wraps the body, and stages the file in git.

## Install

```bash
git clone https://github.com/aisk/blurb-skill ~/.claude/skills/blurb
```

Then ask Claude for a news entry inside a CPython checkout, or run `/blurb`.

See [SKILL.md](SKILL.md) for the options and the rules it enforces.

## License

MIT, see [LICENSE](LICENSE).

# blurb-skill

An [Agent Skill](https://agentskills.io/specification) that generates a CPython
`Misc/NEWS.d/next` news entry and writes it to the right place, doing what `blurb add`
does without opening an editor. It detects the CPython checkout, validates the issue
number and section, wraps the body, and computes the timestamp and nonce that go in the
filename.

Producing that one file is all it does; staging and committing are left to you.

## Install

The skill directory must be named `blurb`, so clone it into your agent's skills
directory under that name. For Claude Code:

```bash
git clone https://github.com/aisk/blurb-skill ~/.claude/skills/blurb
```

Other agents that implement the Agent Skills format read from their own directory;
point them at a clone named `blurb` the same way. The frontmatter uses only spec
fields, so nothing here is tied to a particular agent.

Then ask for a news entry from inside a CPython checkout.

## Use it directly

`scripts/add_blurb.py` is a self-contained CLI with no dependencies beyond Python 3.9,
so it also works without any agent:

```bash
cd ~/cpython
python3 ~/.claude/skills/blurb/scripts/add_blurb.py -i 109198 -s Library \
    -b "Fix a crash in :func:\`os.stat\` when the path contains a surrogate."
```

See [SKILL.md](SKILL.md) for every option and the rules it enforces.

## License

MIT, see [LICENSE](LICENSE).

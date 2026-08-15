# blurb-skill

An [agent skill](https://agentskills.io/specification) that lets an LLM generate a
CPython `Misc/NEWS.d/next` news entry and put it in the right place, without opening an
editor the way `blurb add` does.

## Install

```bash
npx skills add aisk/blurb-skill -g
```

That works for [75+ agents](https://github.com/vercel-labs/skills) and installs the
skill as `blurb`. Or clone it yourself, using `blurb` as the directory name:

```bash
git clone https://github.com/aisk/blurb-skill ~/.claude/skills/blurb
```

Then ask for a news entry from inside a CPython checkout.

See [SKILL.md](SKILL.md) for the options and the rules it enforces.

## License

MIT, see [LICENSE](LICENSE).

# blurb-skill

An [agent skill](https://agentskills.io/specification) that helps you write CPython
`Misc/NEWS.d/next` news entries. Describe the change and the agent drafts the entry,
picks the section, and puts the file in the right place. You can also leave the whole
entry to the agent.

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

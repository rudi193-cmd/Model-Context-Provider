# Security

This runtime's whole job is to decide what a model is given from a person's
own files, so a way around either of its lines is a security problem, and is
welcome.

## What counts

- a passage reaching a model, or leaving as a file, without a scope the
  person sealed;
- a page leaving short, changed, or with a name, number or address the
  withholding should have taken out;
- a stopped scope leaving by any door;
- a door deciding anything: serving, sealing, or letting a page out by
  itself;
- the person's key read, copied or printed;
- a seal or a decline the person didn't click: the seal page reached from
  another machine, another website, a frame, or a model's door, or made to
  seal something that wasn't waiting;
- the person's own door (the pipe, the `provider` command, the seal page or
  the seal prompt) run by a model's tool call, or the kernel's `seal` or
  `decline` run by one, in a shape the guard door names: a command line
  that runs it directly. A script a model writes to get round it is past
  what a guard of words can see; keeping the key where the account the
  assistant runs as can't read it is the guarantee for that;
- the guard door unwired by an assistant: from `~/.claude/settings.json`
  it can be, which `set_up.py` says; installed through Claude Code's managed
  settings (`set_up.py --write managed`) it should not be;
- what left not on the sent log, or the log changed without `check` saying
  so against a pin.

A wrong answer, a missed passage or a slow run is a bug, not a security
problem: open an issue.

## How to report one

In public, as an issue: the runtime runs only on the person's own machine and
has no server to attack. Say what you did, what happened and what you
expected, with the smallest made-up folder that shows it. **Leave out
anything from your own files.**

A way around Willow's own promises (the kernel, `approved-only`,
`sentence-check`, `privacy`) belongs to Willow: report it there.

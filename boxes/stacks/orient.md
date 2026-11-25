# orient: what a repository tells an agent before its first change

Run over one repository's box by `lay.py`, which fills in `{repo}` (the
repository's folder) before the stack add-on fills in `{box}`. Every step
only reads. Steps that walk a folder themselves are handed `{repo}`: they
refuse a box laid from pointed lists (Willow's `kernel.folder()`).

## which instruction files each coding agent loads, and what they name that is gone
# Want: know what this repo asks of an agent before touching it.
# Misreads: a path a build makes shows as missing until it is built.
- instruction-files -- --from {repo}
- agents-md-check -- --from {repo}

## what the code depends on that nothing pins
# Want: know which installs can drift under a test run.
# Misreads: a repo with no package.json, pyproject or Cargo.toml reads empty.
- unpinned -- --from {repo}

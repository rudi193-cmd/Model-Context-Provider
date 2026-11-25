# Boxes over the repositories this is built beside

A Willow box over each of the repositories worked on beside the Provider,
and the stacks that read them, so an agent working here can ask the code
where something is, what calls it and why it changed before it opens a
file. They are the maintainer's working boxes, not part of the runtime:
nothing in `runtime.py` or a door reads them.

    WILLOW=/path/to/Willow python boxes/lay.py --to WORK --across \
        --cbm /path/to/codebase-memory-mcp/build/c/codebase-memory-mcp

One command lays all of it again, which is what a cloud session needs: its
container is gone when the session ends, and only this folder is kept. The
repositories are found beside this checkout (`--repos DIR` for elsewhere);
[repos.json](repos.json) names them, the kinds of file kept and the folders
left out, and `path` where a repository is kept under another folder name
(the MCP specification, cloned read-only to
`modelcontextprotocol/modelcontextprotocol`).
It is public and not one of the session's repositories, so a new session
clones it first:

    git clone --depth 1000 https://github.com/modelcontextprotocol/modelcontextprotocol \
        ../modelcontextprotocol/modelcontextprotocol

## What each box is laid from

Pointed at, never copied (Willow's CONST-VI-9): `gather --point` writes the
list of the repository's files, and the box reads them where they are kept.
Beside the list, three mirrors that steps make, each a source of its own:

| source | made by | what it answers |
|---|---|---|
| `NAME` | gather `--point` | the code and docs, by file and line |
| `NAME-comments` | code-comments | comments and docstrings as passages |
| `NAME-history` | git-history `--messages` | commit messages, dated by the commit, without diffs (a diff's own dates would date the pile) |
| `NAME-graph` | codebase-memory-mcp, then codebase-memory | each function, its file and line, and what it calls; search a name to find what calls it |

The graph is made only with `--cbm`, a built codebase-memory-mcp
(`scripts/build.sh` in its checkout, about ten minutes); it writes its
graph under `WORK/graphdb/NAME` and nowhere in the repository. A shallow
clone has a short history: `git fetch --unshallow` first for the whole one.

The words list, [code-words.txt](code-words.txt), reads a question's words
as the code's (`function = def, fn, method …`, `gc = garbage, collector,
refcount …`).

## The stacks

| stack | over | asks |
|---|---|---|
| [orient](stacks/orient.md) | each box | the instruction files each agent loads, what they name that is gone, what nothing pins |
| [owes](stacks/owes.md) | each box | TODOs, risky lines, secrets in plain files, stale references: leads, not findings |
| [ask/NAME](stacks/ask/) | its indexes | standing questions about that repository, each source answering in turn |
| [across](stacks/across.md) | one box over all, and every index | where one repository leans on another, and the same thing solved in each |

Each step says what it is there for and what it misreads on this kind of
folder. The whole-folder steps are handed the repository (`{repo}`, filled
in by `lay.py`): they refuse a box laid from lists. The question steps use
fair-merge, which ranks each source on its own and takes turns, so
cpython's thousands of files can't crowd out a commit message.

## Indexes

Each source has an index under `WORK/indexes/NAME/SOURCE`, kept by Willow's
index-cache: a run hashes the source's files and rebuilds the index only
when one changed, so a run over unchanged repositories checks them in a
second. The question stacks ask through them (`{indexes}`, filled in by
`lay.py`), with the words list. The code's index is of the repository's
folder, a little wider than its list, since index-cache reads a folder and
not a list (`index-cache --from NAME=@LIST` is on Willow's branch, to
follow).

Each stack's page is `WORK/runs/NAME/STACK.md`. To ask one more question:

    I=WORK/indexes/NAME
    python $WILLOW/adapters/stdlib/fair-merge/fair_merge.py --index $I/NAME \
        --index $I/NAME-comments --index $I/NAME-history --index $I/NAME-graph \
        --words WORK/code-words.txt "your question"

That answers in about a second. The box itself still answers the kernel's
way (`kernel.py bite --box WORK/boxes/NAME`), reading every file: about
twelve seconds on willow-mcp and a minute and a half on cpython.

## What waits on the person

The boxes' keys are written by the kernel into `WORK/keys`, and nothing
here opens them. Nothing here seals or declines; reading these boxes needs
no seal, since nothing leaves the machine. A box laid again goes beside
the old one (`--again`), never over it, in case the old one holds a seal.
The key is the user's.

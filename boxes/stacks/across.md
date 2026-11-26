# across: one box over every repository, each answering in turn

Run by `lay.py --across` over the box laid from every repository's list
and mirrors at once. fair-merge ranks each source on its own, from its index, and takes
turns, so cpython's thousands of files can't crowd out the Provider's
eighty. `--top 28` gives every source (seven repositories, four sources
each) its turn on the page; at fair-merge's default of six, only the first
few would show. These are the questions that cross repositories: where one leans
on another, and where two solve the same thing.

## where one repository leans on another
- fair-merge -- {indexes} --top 28 "how does the provider call willow"
- fair-merge -- {indexes} --top 28 "how is the willow pin moved"
- fair-merge -- {indexes} --top 28 "how does pyperformance build cpython"
- fair-merge -- {indexes} --top 28 "how is the code graph read from sqlite"

## the same thing, solved in each
- fair-merge -- {indexes} --top 28 "what never leaves the machine"
- fair-merge -- {indexes} --top 28 "how is a secret kept out of a page"
- fair-merge -- {indexes} --top 28 "how is a hook allowed to block a tool"
- fair-merge -- {indexes} --top 28 "how are tests split to run in parallel"

## the words each uses for one thing
- first-mention -- --box {box} "seal"
- first-mention -- --box {box} "grant"

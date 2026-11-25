# ask: modelcontextprotocol, the official spec, its docs and its commits each answering in turn

Run by `lay.py` over the MCP specification's box. fair-merge ranks each
source of the box on its own (the spec and docs, its comments mirror, its
commit messages, its call graph when one was made) and merges them in turns.
These are the questions the Provider's MCP door answers to.

## how does a client and server negotiate capabilities at initialize
- fair-merge -- --box {box} "how does a client and server negotiate capabilities at initialize"

## what must a server do when a tool call fails
- fair-merge -- --box {box} "what must a server do when a tool call fails"

## how does sampling let a server ask the client for a completion
- fair-merge -- --box {box} "how does sampling let a server ask the client for a completion"

## how are resources listed and read
- fair-merge -- --box {box} "how are resources listed and read"

## what does elicitation ask of the user
- fair-merge -- --box {box} "what does elicitation ask of the user"

## how is authorization done over http
- fair-merge -- --box {box} "how is authorization done over http"

## what must a host show the user before a tool runs
- fair-merge -- --box {box} "what must a host show the user before a tool runs"

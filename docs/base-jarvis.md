# A base Jarvis

Everyone's base assistant: one setup a person who has never seen any of this
can walk into, running Willow's whole governance underneath, unchanged. Put
together on 2026-11-20 from four piles, asked through one stack (a record each
over Willow, this Provider, Die-Namic and Willow's Grove, a words list, and
`batch-ask`): what is already built or carded, layer by layer. Nothing on this
page is built yet as a whole; it is the assembly to build.

## The frame

From Willow's Grove (`docs/design/willow-grove-premise.md`, citing
`the-one-desk.md`, which is not in that tree): five layers, **Voice / Desk /
Tools / Memory / Trust**. *"Apps do not talk to each other. They talk to a
shared memory, and a human talks to all of them from one desk."*

The order, from the Grove's build order
(`governance/proposals/2026-09-02-build-order.md`), which opens on the
question this page answers: *was Jarvis smart because of the AI, or because of
the information it had access to?* The record's answer: the moat is context,
not IQ. Information first, connections second, the model last and smallest.

From Die-Namic (`open.md`), the rule for how it opens: **the governance stays
exactly as strict; only its words and its doors change.** The test for every
change: can someone who has never seen this sit down and use it without help?

## The layers, and what fills each

| Layer | Pieces | Built? |
|---|---|---|
| **Voice in** | Willow's `wake-gate` (a wake word of your own, Whisper on this machine; nothing before the wake word is transcribed, kept or sent), then `misheard` (a spoken question's misheard words corrected against your own words list, each change shown) | `wake-gate` built; `misheard` an idea |
| **Voice out** | Willow's `speak` (reads answers aloud, offline), saying what the Grove's `seat` says: a short plain sentence per thing (*"You need to ratify the work order. PR 712's still waiting, 126 tests pass."*) | `speak` an idea; `seat` built |
| **Desk** | Die-Namic's way in: no setup questions, straight to the thing; a words table (a proposal is "your call", a seal "yes, it's true", a session seal "that's our night"); the kernel one step in, there when wanted. This Provider's seal page, for review | built, for games |
| **Memory** | Willow's kernel and the person's record, made by `first-run` (the record, the key kept outside it, the `starter-words` list, a launcher, how to back it up) | built |
| **Tools** | the 43 Willow add-ons this Provider pins: `todo`, `coming-up`, `on-this-day`, `timeline`, `notes`, `people`, `minutes`, `mail`, `sms` and the rest | built |
| **Trust** | the seal and the person's key; `privacy`; this Provider's gate on what a model is given, its guard door, `session-seal` with the session's corrections folded in | built |
| **Assistant** | any client through this Provider's MCP door; a model on this machine through `local-model` | built |
| **Phone** | `telegram-bot`, `email-ask` or `home-assistant`; `qr` to carry an answer with no network | ideas |
| **Handing it on** | Willow's `stack-share`: a sealed stack written out to share, each choice with why | built |

## The rule it inherits

**Record choices, never people.** Die-Namic's homestead notes
(`the-table/docs/homestead-table-vision.md`) say why: an early draft logged
the kids' nightly presence to the ledger, and the properties that make a
ledger good for decisions (append-only, tamper-evident, attributed) *"become a
weapon the moment the subject is a person instead of a choice."* Die-Namic's
box already holds to it: nothing about the people at the table is written
down.

## What is left to build

- **The two ideas that close the voice loop:** `speak` and `misheard`.
- **One step.** Today it is four tools: `first-run` for the record and words,
  `ui/assemble.py` (or Willow's UI) for the stack, this Provider's
  `set_up.py --write all` for the assistant, `stack-share` to pass it on. A
  base Jarvis is those, run in order, opening in plain words.
- **The words.** Die-Namic's words table, for everyday life instead of a game
  table, with a column for what the model says: see "The broad fix" in
  [OPEN.md](OPEN.md) and its two usability lists.
- **A phone way in,** from the three ideas above.
- **The record's words list after it is made:** a kernel command, drafted
  (`words --box DIR --words FILE`), the owner's.

## Asked of the forge

Willow's `forge` was asked (`suggest`, which proposes nothing), with
forge-play 0.10.0, for *"a base assistant for everyone: ask out loud, answered
from my own files, read aloud back, kept private on my machine"*. The forge is
being worked on; what it gave, for that work:

- **One step, `backup`, by mistake:** *"what 'back' usually means here"*. A
  words-list entry fired on part of a phrase ("read aloud **back**").
- **An assistant fork** (`claude-code`, `mcp`, `mcp-lite`, `mcp-sampling`, and
  the ideas `claude` and `mcp-by-hash`) and **a private fork** (`privacy`,
  `transcript-redact`): reasonable.
- **Missed `wake-gate`,** whose card begins "Ask out loud", the sentence's
  own phrase: a phrase doesn't seem to count as one.
- **Missed `speak`** for "read aloud", and **`misheard`** and
  **`starter-words`**: nothing for words at all.
- **Couldn't name this Provider,** which is not a Willow add-on.

So the table above is hand built.

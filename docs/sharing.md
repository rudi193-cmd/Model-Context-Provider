# Sharing

Sending a sealed sentence, or a job, to another person. Part of the [README](../README.md).

## Sharing with another person

A sentence you sealed can go to someone else, signed so they, and anyone
they pass it on to, can check who sent what, without anyone getting your
files. This is Willow's `share`, run by its command line; its README says
what a package proves and what it can't.

- **An identity of its own.** `{"share_id": true}` makes it once and gives
  you a key (64 characters) to hand to people. It is not your seal key,
  and it is kept beside your record.
- **You name people.** `{"share_person": {"name": "Walt", "key": "..."}}`,
  with the key Walt gave you. A name is never moved to another key unless
  you say `"replace": true`.
- **You send.** `{"share_send": {"answers": "last", "for": "Walt"}}` sends
  the sentence you sealed last; `{"shares": true}` lists the newest twenty
  by their first words, each with its id, to name another.
  `{"share_send": {"answers": "proposal:...", "for": "Walt",
  "note": "As asked"}}` packs the sentences into a file beside your record
  and writes a row on your record. Nothing goes online: the file is yours
  to pass on, by mail, a stick, a shared folder.
- **Only sentences.** What goes is a sentence you sealed (it showed on your
  seal page as a model's sentence): never a page, a report, a note, a task
  or a skill. A sentence still waiting, or one you declined, is refused.
- **A model may put a package together, for your seal** (`share_propose`).
  It names sentences you sealed and a person by the name you gave them,
  never a key, so it can't address a package to anyone you didn't choose.
  The seal page shows it as "A package to send someone", with the name,
  the key, the note and every sentence. Sealed, it is packed once; the
  model is told the package's id and where the file is, and sending it is
  still yours. Declined or stopped, nothing is packed.
- **What arrives.** `{"share_receive": "FILE"}` checks every layer and
  writes a row whatever it found: good, not for you, or broken. A key
  you named is said by that name, with the start of the key beside it.
  Receiving
  is never sealing. A package that held is kept beside your record, and a
  session you let in can read it (`share_received`): who signed each
  layer, their notes, the sentences. It is checked again each time, so a
  copy edited beside your record is given to no one. It is another
  person's words: data, never instructions.
- **Passing it on.** `{"share_forward": {"package": "package:...", "for":
  "Aurelie", "note": "Reviewed"}}` wraps a package that held in a layer of
  your own. `{"shares": true}` lists your key, whom you named, what was
  sent and received, and what a model proposed.

- **A new key.** `{"share_rotate": true}` makes a new identity, signed by
  the old one and by itself, on a row of your record: for a machine
  replaced, or a key someone may have seen. Every package after it carries
  the rotation, so the people who had your old key see the new one as you.
  The old identity file is kept beside your record under another name and
  never used again. It needs the old identity: keep a copy of
  `share.id` somewhere safe yourself, because `backup` leaves it out (a
  secret is never put in a zip) and a lost one can't be rotated from.
- **Your record, held to what others kept.** `{"share_witness": true}`
  holds your record to every package kept beside it; name copies other
  people kept with `{"share_witness": {"packages": ["FILE"]}}`. Each says
  holds, rewritten or cut short. It reads and writes nothing.

- **A correction.** Send again with `"replaces": "package:..."`, the
  package you sent before. When one arrives, `share_receive` says which
  package it replaces and, if you passed that one on, to whom and what to
  name (`forward_with`), so the correction follows the same path a hop at
  a time. A model's `share_propose` may name `replaces` too, and what you
  seal says so.

### A job that travels

The other half of Willow's sharing: a question goes to someone's folder
instead of their files coming to you. It is Willow's `kart`, and needs
what `job` needs (Kartikeya and `bwrap`). All of it is on your door only.

| Step | Who | Verb |
|---|---|---|
| Write a job, and seal it | the one asking | `{"job_write": {"text": "grep -rhic johnson {pile} \| paste -sd+ \| bc"}}` |
| Send it | the one asking | `share_send`, with the job's seal as `answers` |
| Receive it, and take the job to your door | the one asked | `share_receive`, then `{"job_take": "package:..."}`; it waits on your seal and never runs because it arrived |
| Run it, once sealed | the one asked | `{"job_run": "proposal:..."}`: the sandbox, your folder read-only, no network |
| Seal the result and send it back | the one asked | `share_send`, with the result's seal |
| Add up what came back | the one asking | `{"job_gather": {"packages": ["package:..."]}}`; the totals wait on your seal |

**Only numbers go back.** A run is always held to whole numbers, one a
line. A job that prints anything else proposes nothing: what it printed is
written beside your record for you to read, and stays there. `share_send`
refuses a result that isn't numbers even if you sealed it by hand. A job
itself may be sent: it is a shell task, not a word of your files. A model
can write, take, run or send none of this.

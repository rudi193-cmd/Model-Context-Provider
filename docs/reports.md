# Reports, a timeline and a feed

Reports of your own files, and the two files made to hand on. Part of the [README](../README.md).

## A report of your files

Some things worth asking aren't a question: what did I write down to do,
what did I write on this day in earlier years. Willow has a report for
each, and a model can ask for one (the person's ruling of 2026-11-17):

| Report | What it lists |
|---|---|
| `todo` | every line marked to do (TODO, FIXME, "need to", "remember to", an open checkbox), oldest first |
| `coming-up` | every line holding a date in the next 14 days, soonest first, with the repeats of a birthday or a calendar's rule |
| `on-this-day` | what you wrote on this date in earlier years |
| `people` | everyone your files name, a line each: how often, in how many files, over what dates. Never every place they are mentioned. Its first line says it names people; a name on your list is withheld |
| `ref-check` | each link to another of your files, and each `file:line` place, that no longer holds: where it is written, and what it points at. A link that leads out of your folder is counted, never followed |
| `pii-audit` | where personal numbers sit (a card number, a National Insurance, Social Security, NHS or Medicare number), each by kind and place. Never the whole number. Your own door shows the last digits, as Willow does, so you can tell which card it is; a model is given the kind and the place and not a digit |
| `secrets-audit` | where a password, a key, a card number or an IBAN sits in plain text, by kind and place; each row says "value not shown", and it is not shown |
| `minutes` | each decision, and each action still open or closed, from your meeting notes: its place, its day, who owns it. It names those people, and its first line says so; a name on your list is withheld |

A model is told that there is a report, or that there is nothing to
report: no line, no file name, no count. A session you let in
([One yes for a session](session.md)) is given the report as it reads now, with names,
numbers and addresses withheld.

No report waits on a seal of its own (the owner's ruling, 2026-11-18). It
used to: but a report reads differently the day you add a line to do, so a
seal of one went stale almost at once, and the yes you give a session
already covers it. To stop a report leaving, end that session's yes. On
your own door, `{"report": "todo"}` gives you the report as it is: reading
needs no grant. A report isn't a page a model can `answer`.

**Leaving folders out.** A folder of commits, code or exports is full of
lines that look like things to do. List what to leave out of every report,
one a line, in `report-skip.txt` beside your record: a folder (`commits`),
a folder inside one (`code/vendor`), or one file's path. It only takes lines
out, on your door and a model's alike, and your own `report` says how many
it left out.

**Too long is too long to share.** A report over 20,000 characters is
never given to a model. It is
told to tell you so, without the size, and you still read the whole of it
on your own door.

Seen in Claude Code on 2026-11-17, over a real record: asked for `todo`, a
model was told only that it waits; the person sealed it on the seal page;
asked again, the model was given it. It ran to 571 lines, most of them
prose about todos in commits and code. That is where the skip list and the
limit come from, and Willow's `todo` now counts a mark only as it is
written to mark something (0.1.2).

## Two files to hand on

- **A timeline of one matter.** `{"timeline": "mould landlord"}` writes
  every line of your folder about it, oldest first, each with its file
  and line, to a file beside your record; `{"timeline": {"about": "...",
  "to": "FILE"}}` writes it where you say. It is Willow's `timeline`: made
  to hand to a lawyer, a doctor or a council, your lines as you wrote
  them, and it never guesses a date. A passage is in when it holds every
  one of your words; if none does, those holding half are used and it says
  so, and `"loose": true` asks for that from the start. A session you let in can make one for
  you (`timeline`): the file is written whole for you, and the session is
  given the same lines with names and numbers withheld. A long one comes
  to it in parts of whole lines, and it can ask for the days between two
  dates. What you leave out of every report (`report-skip.txt`) is left
  out of the session's part, and so is the note of where an undated line's
  date came from. Your file is the whole of it either way, and
  asking again makes no second copy while your files read the same.
- **A feed of what you sealed.** `{"feed": true}` writes the sentences you
  sealed as an RSS file for a feed reader, newest first (Willow's
  `rss-out`); `"since": "2026-11-01"` keeps the newer ones, `"to"` says
  where, and `"all": true` adds everything else you sealed (notes, tasks,
  the words of a skill). A session you let in can have it written for you
  (`feed`) and is told where it is and how many items it holds, and none
  of it.

Neither is sent or served anywhere: each is a file, never written over
one that is there, and where it goes next is yours.

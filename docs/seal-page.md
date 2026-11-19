# The seal page

The page where you read what waits and seal or decline it. Part of the [README](../README.md).

## The seal page

    python seal_page.py --box BOX

It prints a link and opens it in your browser. The page shows what waits on
your seal, each as what it is:

- **a session**: which rows of your record, and what was done in them;
- **a page to share**: the page as it would leave, withheld, by file and
  line (the runtime's `preview`);
- **a model's sentence**: its words, where it would be kept, and under it
  each check code ran on it ("What code checked before this reached you"),
  kept beside the box with the hash of the page it was held to. A sentence
  from before this was kept says its checks aren't on record, not that it
  passed;
- **a task to do**: its words, who proposed it and for which project, with
  **Seal: yes, do this**, which grants it nothing else.

Under each, "Exactly what you'd be sealing" unfolds the bytes your key
signs, and three buttons:

| Button | What it does |
|---|---|
| **Seal** | the kernel's own `seal`, proved with your key |
| **Decline** | the kernel's own `decline`, proved with your key, and final; it asks for a tick first |
| **Not now** | nothing on your record and no key: it still waits, and you aren't told about it again until you bring it back |

A second page, **What you've shared**, lists every page you were asked to
share, by file and line, and where each stands: waiting, sealed, changed in
your files since, or stopped. **Stop sharing this** is the runtime's `stop`:
the page is never given to a model again, by any door, and it needs no key.
Under them is what has left, to whom and when (the runtime's `shared`).

A third page, **How things stand**, is the runtime's `status`, and has
nothing to click: what waits on your seal, counted by what each thing is;
what your folder needs from you (approvals gone stale, dates coming up,
questions it never answered: Willow's `digest`, less the folders you leave
out of reports); what you've shared and kept, and each project's shelf; how
this is set (names withheld, folders left out, commands denied); and
whether the record is all right (Willow's `box-health`, the pinned Willow,
the sent log). A part that couldn't be looked at says so, and the rest
still shows. On your own door it is `{"status": true}`. No model's door
has it.

A fifth page, **What a model is offered**, lists the groups of tools a
model's client is shown, each with a button to turn it on or off. A switch
needs no key and is kept beside your record.

A fourth page, **What a model can never do**, is the runtime's `promises`,
and has nothing to click. It lists the verbs each kind of door has, read
from the code as it stands, not typed by hand; what no model's door can do
(no verb to seal or decline, the verbs only you have, an unknown door
treated as a model's); and the standing promises, each with the test that
holds it. A test fails if a test it names is gone, or if the verbs it lists
differ from the code. On your own door it is `{"promises": true}`. No
model's door has it.

**Close this page** stops it. To start it with a double-click:

    python seal_page.py launcher --box BOX --write

That saves a launcher for this machine: on Linux an entry named "Seal page"
in your applications menu, on macOS and Windows a file on your Desktop.
Without `--write` it prints all three and where each goes, and writes
nothing. It never writes over a file that differs. A page started that way
stops itself after half an hour with nobody asking (`--idle 30`). The
launcher holds no secret: each start makes its own. Only the Linux one has
been run; the macOS and Windows files are untried.

It is not a door, and it decides nothing. The decision is your click; the
seal is the kernel's, run by its command line as if you had typed it; the
kernel reads your key, and this project never does. No door imports the
page, and the runtime still has no verb to seal, so nothing a model's door
can ask for ends in a seal. Start it in a terminal of your own: the link
holds a secret made at each start, and it is printed nowhere else.

Who can reach it (the table Willow's `browse` is held to, the code written
here):

| Way in | What stops it |
|---|---|
| Another computer | It listens on 127.0.0.1 only. |
| Another website, in a browser you've opened it in | The secret is an HttpOnly, SameSite=Strict cookie, and every form carries it too; without both, 403. A form whose Origin isn't this page, or is missing or `null`, gets 403. |
| A website that renames itself as this machine | A Host that isn't `127.0.0.1:PORT` or `localhost:PORT` gets 403. |
| A website that frames it under a button | `frame-ancestors 'none'` and `X-Frame-Options: DENY`. |
| Words in a passage or a model's sentence | Every one is escaped, and the page allows no script at all. |
| A program already running as you | Nothing. It could run `kernel.py seal` itself; that includes an assistant you've given a shell or your browser. |

Checked in a real Chrome on 2026-11-17, over a made-up folder: the person's
Seal, Not now and Decline each did what they say; a page on another port
that framed it was refused by the CSP, and its form got 403 and left the
record as it was.

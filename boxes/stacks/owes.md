# owes: what the code still owes

Run over one repository's box by `lay.py` (it fills in `{repo}`). Each line
these print is a lead to read, not a finding: they match patterns, and a
test fixture, a doc quoting a bad example, or a security audit's own table
match too.

## what was left marked to do
# Want: the TODO, FIXME and "need to" lines, oldest first.
# Misreads: a string that holds the words "need to" counts.
- todo -- --box {box}

## code a reviewer should look at twice
# Want: lines matching known-dangerous patterns (shell, eval, SQL, TLS).
# Misreads: a test that checks for the pattern, or a doc naming it.
- risky-code -- --from {repo}

## what shouldn't be sitting in plain files
# Want: places a secret is written down, never showing the value.
# Misreads: test fixtures and made-up keys look the same as real ones.
- secrets-audit -- --from {repo}

## references that no longer hold
# Want: links between files, and quoted lines, that went stale.
# Misreads: a link a build makes, or a pattern that only looks like a path.
- ref-check -- --from {repo}

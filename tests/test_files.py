"""FILES.md names every file here and says what it is. This fails when the
tree in it and the folder disagree, as Willow's test_docs.py does for its
own: a file added, moved or removed is added, moved or removed there too."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
#: never listed: caches, the dev lock file, and anything hidden but these two
SKIPPED = {"__pycache__", "uv.lock"}
HIDDEN_BUT_LISTED = {".github", ".gitignore"}
ENTRY = re.compile(r"^((?:│   |    )*)[├└]── (\S+)(?:\s{2,}(.*))?$")


def listed(text: str) -> dict:
    """Each path the tree names → the words beside it. A folder ends in /."""
    block = text.split("```")[1].strip("\n").splitlines()
    out, above = {}, []
    for line in block[1:]:  # the first line is the repo's own name
        m = ENTRY.match(line)
        assert m, f"FILES.md has a line that isn't an entry of the tree: {line!r}"
        depth, name = len(m.group(1)) // 4, m.group(2)
        assert depth <= len(above), f"FILES.md: {name} sits under nothing"
        above = above[:depth]
        path = "".join(above) + name
        assert path not in out, f"FILES.md names {path} twice"
        out[path] = (m.group(3) or "").strip()
        if name.endswith("/"):
            above.append(name)
    return out


def on_disk(root: Path) -> set:
    """Every file and folder that should be listed, as the tree writes them."""
    out = set()

    def walk(folder: Path, prefix: str) -> bool:
        any_file = False
        for p in sorted(folder.iterdir()):
            hidden = p.name.startswith(".") and p.name not in HIDDEN_BUT_LISTED
            if p.name in SKIPPED or hidden or p.is_symlink():
                continue
            if p.is_dir():
                if walk(p, f"{prefix}{p.name}/"):  # an empty folder isn't in git
                    out.add(f"{prefix}{p.name}/")
                    any_file = True
            else:
                out.add(prefix + p.name)
                any_file = True
        return any_file

    walk(root, "")
    return out


def test_the_tree_and_the_folder_agree():
    said = listed((ROOT / "FILES.md").read_text())
    here = on_disk(ROOT)
    missing, gone = sorted(here - set(said)), sorted(set(said) - here)
    assert not missing, f"not in FILES.md: {missing}"
    assert not gone, f"in FILES.md, but not in the folder: {gone}"


def test_each_entry_says_what_it_is_in_a_few_words():
    for path, words in listed((ROOT / "FILES.md").read_text()).items():
        assert words, f"FILES.md says nothing about {path}"
        assert len(words) <= 110, f"FILES.md says too much about {path}"


def test_the_check_fires_on_a_file_added_removed_or_moved(tmp_path):
    """The check itself, held: a tree and a folder made here that disagree
    in each way must be caught, or a pass above means nothing."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.py").write_text("")
    (tmp_path / "two.md").write_text("")
    (tmp_path / ".hidden").write_text("")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_text("")
    (tmp_path / "empty").mkdir()
    tree = (
        "```\nrepo/\n"
        "├── a/          a folder\n"
        "│   └── one.py  a file\n"
        "└── two.md      another\n```\n"
    )
    assert set(listed(tree)) == on_disk(tmp_path) == {"a/", "a/one.py", "two.md"}
    (tmp_path / "three.md").write_text("")  # added
    assert on_disk(tmp_path) - set(listed(tree)) == {"three.md"}
    (tmp_path / "three.md").unlink()
    (tmp_path / "a" / "one.py").rename(tmp_path / "one.py")  # moved
    here = on_disk(tmp_path)
    assert here - set(listed(tree)) == {"one.py"}
    assert set(listed(tree)) - here == {"a/", "a/one.py"}

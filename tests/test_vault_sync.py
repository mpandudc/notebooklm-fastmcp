from types import SimpleNamespace

import pytest

from notebooklm_fastmcp.vault_sync import answer_text, format_obsidian_note, format_reference, write_to_vault


def test_answer_text_uses_answer_not_repr():
    result = SimpleNamespace(answer="## Heading\n\nBody line", conversation_id="c1", references=[])
    assert answer_text(result) == "## Heading\n\nBody line"
    assert answer_text(SimpleNamespace(text="from text")) == "from text"
    assert answer_text("plain string") == "plain string"


def test_format_reference_is_readable():
    ref = SimpleNamespace(source_id="d2fd18bc", citation_number=3, cited_text="AACSB SBMITB\nACCREDITED  text " * 30)
    line = format_reference(ref)
    assert line.startswith("[3] AACSB SBMITB ACCREDITED")
    assert "\n" not in line and len(line) < 260 and "ChatReference(" not in line
    assert line.endswith("(`d2fd18bc`)")


def test_note_does_not_link_notebook_alias():
    note = format_obsidian_note("T", "body", "ebla", "uuid-1", ["academic/mba"])
    assert 'notebook: "ebla"' in note and "[[ebla]]" not in note


def test_write_to_vault_blocks_sibling_prefix(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (tmp_path / "vault-evil").mkdir()
    with pytest.raises(ValueError):
        write_to_vault(str(vault), "../vault-evil/x.md", "x")
    p = write_to_vault(str(vault), "a/b.md", "hello\n")
    assert p.read_text(encoding="utf-8") == "hello\n"
    assert [f.name for f in p.parent.iterdir()] == ["b.md"]

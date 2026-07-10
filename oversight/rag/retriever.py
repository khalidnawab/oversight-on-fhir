import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

_CORPUS_DIR = Path(__file__).parent / "corpus"


@dataclass
class Passage:
    passage_id: str
    text: str
    source: str


def _chunk(md: str, source: str) -> list[Passage]:
    """Split a markdown doc into passages by '## ' heading sections."""
    passages: list[Passage] = []
    sections = re.split(r"\n(?=## )", md)
    for i, sec in enumerate(sections):
        text = sec.strip()
        if not text:
            continue
        first_line = text.splitlines()[0]
        if not first_line.startswith("## "):
            # top-of-file title block ("# ...") — skip as a standalone passage
            continue
        heading = first_line.lstrip("# ").strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", heading).strip("-") or f"sec{i}"
        passages.append(Passage(passage_id=f"{source}#{slug}", text=text, source=source))
    return passages


def _tokenize(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


class Retriever:
    """BM25 retrieval over the local antibiogram/formulary corpus. No external service (Section 4.8).
    Returns passages with citable ids so retrieved knowledge is evidence-linkable (Section 8)."""

    def __init__(self, corpus_dir: Path = _CORPUS_DIR):
        self.passages: list[Passage] = []
        for path in sorted(corpus_dir.glob("*.md")):
            self.passages.extend(_chunk(path.read_text(encoding="utf-8"), source=path.stem))
        self._bm25 = BM25Okapi([_tokenize(p.text) for p in self.passages])

    def retrieve(self, query: str, k: int = 3) -> list[Passage]:
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(scores, self.passages), key=lambda x: x[0], reverse=True)
        return [p for score, p in ranked[:k] if score > 0]

from oversight.rag.retriever import Retriever


def test_retrieves_relevant_passage():
    r = Retriever()
    hits = r.retrieve("MSSA narrow spectrum cefazolin", k=2)
    assert hits
    assert any("cefazolin" in h.text.lower() for h in hits)
    # Every hit must carry a citable id and source (evidence-linking, Section 8).
    assert all(h.passage_id and h.source for h in hits)


def test_passage_ids_are_stable_and_unique():
    r = Retriever()
    ids = [p.passage_id for p in r.passages]
    assert len(ids) == len(set(ids))


def test_k_limits_results():
    r = Retriever()
    assert len(r.retrieve("cephalosporin", k=1)) == 1

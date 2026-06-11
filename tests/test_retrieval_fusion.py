import uuid

from app.models.knowledge import KnowledgeChunk
from app.retrieval.search import SearchResult, reciprocal_rank_fusion


def create_mock_chunk() -> KnowledgeChunk:
    chunk = KnowledgeChunk(
        content="mock content",
    )
    chunk.id = uuid.uuid4()
    return chunk


def test_rrf_scoring_and_ranking() -> None:
    chunk_a = create_mock_chunk()
    chunk_b = create_mock_chunk()
    chunk_c = create_mock_chunk()

    # List 1: chunk A (rank 0), chunk B (rank 1)
    list_1 = [
        SearchResult(chunk=chunk_a, score=1.0, method="list_1"),
        SearchResult(chunk=chunk_b, score=0.8, method="list_1"),
    ]

    # List 2: chunk B (rank 0), chunk C (rank 1)
    list_2 = [
        SearchResult(chunk=chunk_b, score=0.9, method="list_2"),
        SearchResult(chunk=chunk_c, score=0.7, method="list_2"),
    ]

    # Fuse with k = 60
    # chunk_a: rank 0 in list 1. RRF score = 1 / (60 + 0 + 1) = 1/61
    # chunk_b: rank 1 in list 1, rank 0 in list 2.
    # RRF score = 1 / (60 + 1 + 1) + 1 / (60 + 0 + 1) = 1/62 + 1/61
    # chunk_c: rank 1 in list 2. RRF score = 1 / (60 + 1 + 1) = 1/62

    fused = reciprocal_rank_fusion([list_1, list_2], k=60)

    # chunk_b has rank 0 in list 2 and rank 1 in list 1, giving it the highest fused score.
    assert len(fused) == 3
    assert fused[0].chunk.id == chunk_b.id
    assert fused[1].chunk.id == chunk_a.id
    assert fused[2].chunk.id == chunk_c.id

    assert fused[0].score == (1.0 / 61.0) + (1.0 / 62.0)
    assert fused[1].score == 1.0 / 61.0
    assert fused[2].score == 1.0 / 62.0

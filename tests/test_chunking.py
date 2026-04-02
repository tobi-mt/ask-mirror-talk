from app.indexing.chunking import chunk_segments


def test_chunk_segments_keeps_original_span_when_under_limit():
    segments = [
        {"text": "First thought.", "start": 0.0, "end": 5.0},
        {"text": "Second thought.", "start": 5.0, "end": 10.0},
    ]

    chunks = chunk_segments(segments, max_chars=200, min_chars=40)

    assert chunks == [
        {
            "text": "First thought. Second thought.",
            "start": 0.0,
            "end": 10.0,
        }
    ]


def test_chunk_segments_splits_on_segment_boundaries_with_monotonic_timestamps():
    segments = [
        {"text": "A" * 30, "start": 0.0, "end": 10.0},
        {"text": "B" * 30, "start": 10.0, "end": 20.0},
        {"text": "C" * 30, "start": 20.0, "end": 30.0},
    ]

    chunks = chunk_segments(segments, max_chars=70, min_chars=40)

    assert len(chunks) == 2
    assert chunks[0]["start"] == 0.0
    assert chunks[0]["end"] == 20.0
    assert chunks[1]["start"] == 20.0
    assert chunks[1]["end"] == 30.0
    assert chunks[0]["end"] <= chunks[1]["start"]


def test_chunk_segments_splits_long_single_segment_without_collapsing_time():
    long_text = (
        "First sentence is reflective and long enough. "
        "Second sentence adds more detail and keeps going. "
        "Third sentence closes the idea with a clear ending."
    )
    segments = [{"text": long_text, "start": 100.0, "end": 160.0}]

    chunks = chunk_segments(segments, max_chars=80, min_chars=40)

    assert len(chunks) >= 2
    assert chunks[0]["start"] == 100.0
    assert chunks[-1]["end"] == 160.0

    previous_end = None
    for chunk in chunks:
        assert chunk["start"] <= chunk["end"]
        if previous_end is not None:
            assert previous_end <= chunk["start"]
        previous_end = chunk["end"]

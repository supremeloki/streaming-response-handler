import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from stream_handler import (
    ChunkType,
    StreamError,
    StreamHandler,
    StreamInterruptedError,
    chunk_text,
    done_chunk,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        self.now += 0.01
        return self.now


def test_chunk_text_splits_and_covers_all():
    pieces = [content for _, content in chunk_text("abcdefgh", size=3)]
    assert "".join(pieces) == "abcdefgh"
    assert len(pieces) == 3


def test_invalid_chunk_size_rejected():
    with pytest.raises(StreamError):
        list(chunk_text("x", size=0))


def test_consume_joins_text():
    handler = StreamHandler(clock=FakeClock())
    text, stats = handler.consume(
        [(ChunkType.TEXT, "Hello "), (ChunkType.TEXT, "world"), done_chunk()]
    )
    assert text == "Hello world"
    assert stats.chunk_count == 3
    assert stats.char_count == 11


def test_thinking_separated_from_text():
    handler = StreamHandler(clock=FakeClock())
    handler.consume([
        (ChunkType.THINKING, "let me think "),
        (ChunkType.TEXT, "answer"),
        (ChunkType.DONE, ""),
    ])
    acc = handler.accumulator
    assert acc.text == "answer"
    assert acc.thinking == "let me think "


def test_tool_calls_collected():
    handler = StreamHandler(clock=FakeClock())
    handler.consume([
        (ChunkType.TOOL_CALL, '{"name":'),
        (ChunkType.TOOL_CALL, '"calc"}'),
        (ChunkType.TEXT, "ok"),
        (ChunkType.DONE, ""),
    ])
    assert handler.accumulator.tool_calls == ('{"name":', '"calc"}')


def test_on_chunk_callback_fires_per_chunk():
    seen: list[ChunkType] = []
    handler = StreamHandler(on_chunk=lambda c: seen.append(c.chunk_type),
                            clock=FakeClock())
    handler.consume([(ChunkType.TEXT, "a"), (ChunkType.TEXT, "b"), done_chunk()])
    assert seen == [ChunkType.TEXT, ChunkType.TEXT, ChunkType.DONE]

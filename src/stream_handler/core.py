from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StreamError(Exception):
    pass


class StreamInterruptedError(StreamError):
    def __init__(self, chunks_before_interrupt: int) -> None:
        super().__init__(f"stream interrupted after {chunks_before_interrupt} chunks")
        self.chunks_received = chunks_before_interrupt


class ChunkType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    THINKING = "thinking"
    DONE = "done"


@dataclass(frozen=True)
class StreamChunk:
    index: int
    chunk_type: ChunkType
    content: str
    received_at: float

    @property
    def is_terminal(self) -> bool:
        return self.chunk_type is ChunkType.DONE


@dataclass(frozen=True)
class StreamStats:
    chunk_count: int
    char_count: int
    duration_seconds: float
    chunks_per_second: float
    first_token_latency: float | None

    @property
    def chars_per_second(self) -> float:
        if self.duration_seconds <= 0:
            return 0.0
        return round(self.char_count / self.duration_seconds, 2)


class StreamAccumulator:
    def __init__(self) -> None:
        self._text_parts: list[str] = []
        self._thinking_parts: list[str] = []
        self._tool_calls: list[str] = []
        self._count = 0

    def absorb(self, chunk: StreamChunk) -> None:
        self._count += 1
        if chunk.chunk_type is ChunkType.TEXT:
            self._text_parts.append(chunk.content)
        elif chunk.chunk_type is ChunkType.THINKING:
            self._thinking_parts.append(chunk.content)
        elif chunk.chunk_type is ChunkType.TOOL_CALL:
            self._tool_calls.append(chunk.content)

    @property
    def text(self) -> str:
        return "".join(self._text_parts)

    @property
    def thinking(self) -> str:
        return "".join(self._thinking_parts)

    @property
    def tool_calls(self) -> tuple[str, ...]:
        return tuple(self._tool_calls)

    @property
    def chunk_count(self) -> int:
        return self._count


class StreamHandler:
    def __init__(self,
                 on_chunk: Callable[[StreamChunk], None] | None = None,
                 interrupt_after: float | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._on_chunk = on_chunk
        self._interrupt_after = interrupt_after
        self._clock = clock
        self._accumulator = StreamAccumulator()

    def consume(self, raw_chunks: Iterable[tuple[ChunkType, str]]) -> tuple[str, StreamStats]:
        start = self._clock()
        first_token_latency: float | None = None
        index = 0
        try:
            for raw_type, raw_content in raw_chunks:
                now = self._clock()
                if first_token_latency is None and raw_content:
                    first_token_latency = round(now - start, 4)
                chunk = StreamChunk(
                    index=index,
                    chunk_type=raw_type,
                    content=raw_content,
                    received_at=now,
                )
                self._accumulator.absorb(chunk)
                if self._on_chunk is not None:
                    self._on_chunk(chunk)
                index += 1
                if (self._interrupt_after is not None
                        and now - start > self._interrupt_after):
                    raise StreamInterruptedError(index)
        except StopIteration:
            pass
        end = self._clock()
        stats = StreamStats(
            chunk_count=index,
            char_count=len(self._accumulator.text),
            duration_seconds=round(end - start, 4),
            chunks_per_second=round(index / max(end - start, 1e-9), 2),
            first_token_latency=first_token_latency,
        )
        return self._accumulator.text, stats

    @property
    def accumulator(self) -> StreamAccumulator:
        return self._accumulator


def chunk_text(text: str, size: int = 4) -> Iterator[tuple[ChunkType, str]]:
    if size < 1:
        raise StreamError("chunk size must be >= 1")
    for position in range(0, len(text), size):
        yield ChunkType.TEXT, text[position:position + size]


def done_chunk() -> tuple[ChunkType, str]:
    return ChunkType.DONE, ""

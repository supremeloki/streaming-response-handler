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

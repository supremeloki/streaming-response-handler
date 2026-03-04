# stream-handler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Streaming LLM response handling: typed chunk consumption, text/thinking/tool-call separation, per-chunk callbacks, first-token latency and throughput stats, and interrupt-on-timeout with partial results preserved.

## 🚀 Overview

Streaming responses arrive as a firehose of undifferentiated chunks — and UIs need more than concatenation. `stream-handler` types each chunk (TEXT / THINKING / TOOL_CALL / DONE), routes them into a `StreamAccumulator` that keeps reasoning traces separate from the answer, fires an optional callback per chunk for live rendering, and measures what actually matters: first-token latency, chunks/sec, chars/sec. A timeout mode raises `StreamInterruptedError` mid-stream while keeping everything absorbed so far.

## ✨ Features

- **Typed chunks:** text vs thinking vs tool-call never get mixed
- **Per-chunk callback:** wire straight into a live UI renderer
- **StreamStats:** first-token latency, duration, chunks/sec, chars/sec
- **Interrupt mode:** wall-clock timeout raises mid-stream; partial text survives in the accumulator
- **chunk_text helper:** split any string into sized fake-stream pieces (great for tests/demos)
- **Injectable clock:** deterministic latency/throughput numbers under test
- **Zero dependencies**

## 🚧 Structure

```
streaming-response-handler/
├── src/stream_handler/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/streaming-response-handler.git
cd streaming-response-handler
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from stream_handler import ChunkType, StreamHandler, chunk_text, done_chunk

handler = StreamHandler(on_chunk=lambda c: print(c.content, end="", flush=True))

raw = list(chunk_text("Streaming works.", size=6)) + [done_chunk()]
text, stats = handler.consume(raw)

print(f"\nfirst token after {stats.first_token_latency}s, "
      f"{stats.chars_per_second} chars/sec")
```

## 🔧 Error Handling

```text
StreamError               # invalid chunk size
StreamInterruptedError    # timeout exceeded mid-stream (.chunks_received tells how far it got)
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen chunks/stats
- Zero comments — names carry the meaning
- Latency, separation, interruption, and empty-stream edge cases covered against a fake clock

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!

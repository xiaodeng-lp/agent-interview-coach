from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from docx import Document
from pypdf import PdfReader


DEFAULT_SOURCE_DIR = Path(__file__).with_name("resume_materials")
DEFAULT_CACHE_PATH = Path(__file__).with_name("interview_corpus_cache.json")

SUPPORTED_SUFFIXES = {".md", ".txt", ".docx", ".pdf"}
SKIP_NAME_PREFIXES = ("~$", ".")
MAX_CHARS_PER_FILE = 120_000
CHUNK_SIZE = 2_000
CHUNK_OVERLAP = 250

NOISY_NAME_PATTERNS = (
    "backup",
    "before_",
    "before-",
    "before ",
    "副本",
    "证件照",
)


@dataclass
class CorpusChunk:
    source: str
    title: str
    suffix: str
    priority: int
    chunk_index: int
    text: str


@dataclass
class RetrievalTraceItem:
    chunk: CorpusChunk
    score: int
    matched_terms: list[str]
    reason: str
    selected: bool = False
    skip_reason: str = ""


def file_priority(path: Path) -> int:
    name = path.name.lower()
    if "ai动态模拟面试官协议" in name:
        return 100
    if "ai面试背景材料" in name:
        return 98
    if "开发岗-终极" in name:
        return 95
    if "support" in name or "客服" in name or "质检" in name or "knowledge" in name or "知识库" in name:
        return 90
    if "pptagent" in name or "ppt生成agent" in name:
        return 84
    if "q lora" in name or "qlora" in name or "finetune" in name:
        return 72
    if "llamaindex" in name or "rag" in name:
        return 70
    if path.suffix.lower() == ".pdf":
        return 55
    return 60


def should_keep_file(path: Path) -> bool:
    name = path.name.lower()
    if any(token in name for token in NOISY_NAME_PATTERNS):
        return False
    return True


def dedupe_files(paths: list[Path]) -> list[Path]:
    preferred_resume: Path | None = None
    resume_variants: list[Path] = []
    kept: list[Path] = []

    for path in paths:
        name = path.name
        if "开发岗-终极" in name:
            preferred_resume = path
            resume_variants.append(path)
            continue
        if "西安交通大学-邓楚君" in name and path.suffix.lower() in {".docx", ".pdf"}:
            resume_variants.append(path)
            continue
        kept.append(path)

    if preferred_resume is not None:
        kept.append(preferred_resume)
    else:
        kept.extend(sorted(resume_variants))
    return sorted(kept)


def iter_source_files(source_dir: Path) -> Iterable[Path]:
    candidates: list[Path] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith(SKIP_NAME_PREFIXES):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if not should_keep_file(path):
            continue
        candidates.append(path)
    yield from dedupe_files(candidates)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def read_docx(path: Path) -> str:
    document = Document(str(path))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:  # PDF extraction can fail on individual pages.
            page_text = f"[第 {index + 1} 页提取失败: {exc}]"
        if page_text.strip():
            pages.append(f"\n[PDF 第 {index + 1} 页]\n{page_text}")
    return "\n".join(pages)


def read_supported_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return read_text_file(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise ValueError(f"Unsupported file type: {path}")


def chunk_text(text: str) -> list[str]:
    text = normalize_text(text)[:MAX_CHARS_PER_FILE]
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return [chunk for chunk in chunks if chunk]


def build_corpus(source_dir: Path = DEFAULT_SOURCE_DIR) -> list[CorpusChunk]:
    corpus: list[CorpusChunk] = []
    for path in iter_source_files(source_dir):
        try:
            text = read_supported_file(path)
        except Exception as exc:
            text = f"[文件读取失败: {exc}]"
        for index, chunk in enumerate(chunk_text(text)):
            corpus.append(
                CorpusChunk(
                    source=str(path),
                    title=path.name,
                    suffix=path.suffix.lower(),
                    priority=file_priority(path),
                    chunk_index=index,
                    text=chunk,
                )
            )
    corpus.sort(key=lambda item: (-item.priority, item.title, item.chunk_index))
    return corpus


def atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def backup_corrupt_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.corrupt.{stamp}")
    path.replace(backup_path)
    return backup_path


def save_corpus_cache(
    corpus: list[CorpusChunk],
    cache_path: Path = DEFAULT_CACHE_PATH,
    source_dir: Path = DEFAULT_SOURCE_DIR,
) -> None:
    payload = {
        "source_dir": str(source_dir),
        "chunk_count": len(corpus),
        "files": sorted({chunk.source for chunk in corpus}),
        "chunks": [asdict(chunk) for chunk in corpus],
    }
    atomic_write_json(cache_path, payload)


def load_corpus_cache(
    cache_path: Path = DEFAULT_CACHE_PATH,
    expected_source_dir: Path | None = None,
) -> list[CorpusChunk]:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if expected_source_dir is not None and payload.get("source_dir") != str(expected_source_dir):
            raise ValueError(
                f"corpus cache source mismatch: {payload.get('source_dir')} != {expected_source_dir}"
            )
        chunks = payload["chunks"]
        if not isinstance(chunks, list):
            raise TypeError("corpus cache chunks must be a list")
        return [CorpusChunk(**item) for item in chunks]
    except json.JSONDecodeError as exc:
        backup_corrupt_file(cache_path)
        raise ValueError(f"corpus cache is not valid JSON: {cache_path}") from exc
    except (KeyError, TypeError) as exc:
        backup_corrupt_file(cache_path)
        raise ValueError(f"corpus cache schema is invalid: {cache_path}") from exc


def query_terms(user_message: str) -> set[str]:
    return set(re.findall(r"[\w\u4e00-\u9fff]{2,}", user_message.lower()))


def score_chunk(chunk: CorpusChunk, terms: set[str]) -> tuple[int, list[str], str]:
    text = (chunk.title + "\n" + chunk.text[:800]).lower()
    matched_terms = sorted(term for term in terms if term in text)
    score = chunk.priority + len(matched_terms) * 8
    reason = f"priority {chunk.priority} + {len(matched_terms)} term hits * 8"
    return score, matched_terms, reason


def trace_retrieval(
    corpus: list[CorpusChunk],
    user_message: str,
    max_chars: int = 6_000,
    max_chunks: int = 4,
    max_chunks_per_source: int = 2,
    trace_limit: int = 12,
) -> list[RetrievalTraceItem]:
    terms = query_terms(user_message)
    ranked: list[RetrievalTraceItem] = []
    for chunk in corpus:
        score, matched_terms, reason = score_chunk(chunk, terms)
        ranked.append(
            RetrievalTraceItem(
                chunk=chunk,
                score=score,
                matched_terms=matched_terms,
                reason=reason,
            )
        )
    ranked.sort(key=lambda item: (item.score, item.chunk.priority), reverse=True)

    used = 0
    source_counts: dict[str, int] = {}
    selected_count = 0
    trace_items: list[RetrievalTraceItem] = []
    for item in ranked:
        chunk = item.chunk
        if chunk.priority >= 100:
            item.skip_reason = "reserved protocol/reference file"
        else:
            per_source_limit = 1 if chunk.priority >= 98 else max_chunks_per_source
            if source_counts.get(chunk.source, 0) >= per_source_limit:
                item.skip_reason = f"per-source limit reached ({per_source_limit})"
            else:
                block = f"\n\n### {chunk.title} / chunk {chunk.chunk_index}\n{chunk.text}"
                if used + len(block) > max_chars:
                    item.skip_reason = "would exceed max_chars"
                elif selected_count >= max_chunks:
                    item.skip_reason = "max_chunks already selected"
                else:
                    item.selected = True
                    source_counts[chunk.source] = source_counts.get(chunk.source, 0) + 1
                    used += len(block)
                    selected_count += 1
        if item.selected or len(trace_items) < trace_limit:
            trace_items.append(item)
        if len(trace_items) >= trace_limit and selected_count >= max_chunks:
            break
    return trace_items


def select_retrieval_chunks(
    corpus: list[CorpusChunk],
    user_message: str,
    max_chars: int = 6_000,
    max_chunks: int = 4,
    max_chunks_per_source: int = 2,
) -> list[CorpusChunk]:
    return [
        item.chunk
        for item in trace_retrieval(
            corpus=corpus,
            user_message=user_message,
            max_chars=max_chars,
            max_chunks=max_chunks,
            max_chunks_per_source=max_chunks_per_source,
            trace_limit=max_chunks,
        )
        if item.selected
    ]


def select_context(
    corpus: list[CorpusChunk],
    user_message: str,
    max_chars: int = 6_000,
    max_chunks: int = 4,
    max_chunks_per_source: int = 2,
) -> str:
    selected = select_retrieval_chunks(
        corpus=corpus,
        user_message=user_message,
        max_chars=max_chars,
        max_chunks=max_chunks,
        max_chunks_per_source=max_chunks_per_source,
    )
    if not selected:
        return (
            "【本轮证据包】\n"
            "未检索到相关证据。资料里没有看到足够支持当前问题的候选人经历、项目职责、技术动作、指标或结果。"
        )
    evidence_blocks = [
        "【本轮证据包】",
    ]
    evidence_blocks.extend(
        (
            f"【证据 {index}】\n"
            f"来源文件：{chunk.title}\n"
            f"片段编号：{chunk.chunk_index}\n"
            f"证据等级：{chunk.priority}\n"
            f"正文：\n{chunk.text}"
        )
        for index, chunk in enumerate(selected, start=1)
    )
    return "\n\n".join(evidence_blocks).strip()


def preview_text(text: str, max_chars: int) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def format_retrieval_diagnostics(
    corpus: list[CorpusChunk],
    user_message: str,
    max_chars: int = 6_000,
    max_chunks: int = 4,
    max_chunks_per_source: int = 2,
    trace_limit: int = 12,
    evidence_preview_chars: int = 1_200,
) -> str:
    trace_items = trace_retrieval(
        corpus=corpus,
        user_message=user_message,
        max_chars=max_chars,
        max_chunks=max_chunks,
        max_chunks_per_source=max_chunks_per_source,
        trace_limit=trace_limit,
    )
    selected = [item for item in trace_items if item.selected]
    lines = [
        "Retrieval diagnostics",
        f"query: {user_message}",
        f"query_terms: {', '.join(sorted(query_terms(user_message))) or '(none)'}",
        f"corpus_chunks: {len(corpus)}",
        f"selected_chunks: {len(selected)}",
        "",
        "Ranked trace:",
    ]
    for rank, item in enumerate(trace_items, start=1):
        chunk = item.chunk
        state = "SELECTED" if item.selected else f"SKIPPED: {item.skip_reason or 'not reached'}"
        lines.extend(
            [
                f"{rank}. {state}",
                f"   title: {chunk.title}",
                f"   source: {chunk.source}",
                f"   chunk_index: {chunk.chunk_index}",
                f"   priority: {chunk.priority}",
                f"   score: {item.score}",
                f"   matched_terms: {', '.join(item.matched_terms) or '(none)'}",
                f"   reason: {item.reason}",
                f"   preview: {preview_text(chunk.text, 220)}",
            ]
        )

    evidence_pack = select_context(
        corpus=corpus,
        user_message=user_message,
        max_chars=max_chars,
        max_chunks=max_chunks,
        max_chunks_per_source=max_chunks_per_source,
    )
    lines.extend(
        [
            "",
            "Evidence pack preview:",
            preview_text(evidence_pack, evidence_preview_chars),
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build interview context corpus from resume materials.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--debug-query", help="Print retrieval diagnostics for one query.")
    parser.add_argument("--max-chars", type=int, default=6_000)
    parser.add_argument("--max-chunks", type=int, default=4)
    parser.add_argument("--max-chunks-per-source", type=int, default=2)
    parser.add_argument("--trace-limit", type=int, default=12)
    args = parser.parse_args()

    corpus = build_corpus(args.source_dir)
    save_corpus_cache(corpus, args.cache, args.source_dir)
    if args.debug_query:
        print(
            format_retrieval_diagnostics(
                corpus=corpus,
                user_message=args.debug_query,
                max_chars=args.max_chars,
                max_chunks=args.max_chunks,
                max_chunks_per_source=args.max_chunks_per_source,
                trace_limit=args.trace_limit,
            )
        )
        return
    files = sorted({chunk.source for chunk in corpus})
    print(f"Indexed {len(files)} files into {len(corpus)} chunks.")
    print(f"Cache: {args.cache}")
    for file in files:
        print(f"- {file}")


if __name__ == "__main__":
    main()

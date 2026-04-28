from __future__ import annotations

import re
from pathlib import Path

from wechat_clawbot.api.types import MessageItem, MessageItemType
from wechat_clawbot.media.download import download_media_from_item

from interview_corpus import (
    DEFAULT_CACHE_PATH,
    DEFAULT_SOURCE_DIR,
    build_corpus,
    load_corpus_cache,
    save_corpus_cache,
)
from paths import ENV_PATH, MATERIALS_INBOX


SUPPORTED_IMPORT_SUFFIXES = {".docx", ".pdf", ".md", ".txt"}


def log(message: str) -> None:
    print(f"[coach-bot] {message}", flush=True)


def ensure_corpus(source_dir: Path, refresh: bool = False):
    if refresh or not DEFAULT_CACHE_PATH.exists():
        log(f"正在读取简历资料目录: {source_dir}")
        corpus = build_corpus(source_dir)
        save_corpus_cache(corpus, DEFAULT_CACHE_PATH)
        log(f"资料库缓存完成: {len(corpus)} 个片段")
        return corpus
    corpus = load_corpus_cache(DEFAULT_CACHE_PATH)
    log(f"已载入资料库缓存: {len(corpus)} 个片段")
    return corpus


def update_env_value(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    next_lines: list[str] = []
    updated = False
    for line in lines:
        if line.startswith(f"{key}="):
            next_lines.append(f"{key}={value}")
            updated = True
        else:
            next_lines.append(line)
    if not updated:
        next_lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(next_lines) + "\n", encoding="utf-8")


def sanitize_filename(name: str) -> str:
    name = Path(name or "uploaded_file").name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name)
    return name[:120] or "uploaded_file"


async def save_uploaded_media(
    buffer: bytes,
    content_type: str | None,
    subdir: str,
    max_bytes: int,
    original_filename: str | None = None,
) -> dict[str, str]:
    if len(buffer) > max_bytes:
        raise ValueError("uploaded file is too large")
    MATERIALS_INBOX.mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(original_filename or "uploaded_file")
    path = MATERIALS_INBOX / filename
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while path.exists():
        path = MATERIALS_INBOX / f"{stem}_{counter}{suffix}"
        counter += 1
    path.write_bytes(buffer)
    return {"path": str(path)}


def find_supported_file_item(items: list[MessageItem] | None) -> MessageItem | None:
    if not items:
        return None
    for item in items:
        if item.type != MessageItemType.FILE or not item.file_item:
            continue
        suffix = Path(item.file_item.file_name or "").suffix.lower()
        if suffix in SUPPORTED_IMPORT_SUFFIXES:
            return item
    return None


async def import_wechat_file(items: list[MessageItem] | None, cdn_base_url: str) -> Path | None:
    item = find_supported_file_item(items)
    if not item:
        return None
    opts = await download_media_from_item(
        item=item,
        cdn_base_url=cdn_base_url,
        save_media=save_uploaded_media,
        log=log,
        err_log=log,
        label="resume-material",
    )
    if opts.decrypted_file_path:
        return Path(opts.decrypted_file_path)
    return None


def current_source_dir_from_env() -> Path:
    import os

    return Path(os.environ.get("RESUME_SOURCE_DIR", str(DEFAULT_SOURCE_DIR)))

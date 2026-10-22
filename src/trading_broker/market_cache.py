"""Immutable shared cache for market-data batches."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

from .market_data import MarketBatch, MarketDataProvider, MarketRequest
from .models import Bar


class MarketCacheCorruptError(RuntimeError):
    pass


def _request_dict(request: MarketRequest) -> dict[str, Any]:
    return {
        "symbols": list(request.symbols),
        "start": request.start.isoformat(),
        "end": request.end.isoformat(),
        "interval": request.interval,
        "prepost": request.prepost,
        "auto_adjust": request.auto_adjust,
        "actions": request.actions,
        "keepna": request.keepna,
    }


def _request_from_dict(value: dict[str, Any]) -> MarketRequest:
    return MarketRequest(
        symbols=tuple(value["symbols"]),
        start=datetime.fromisoformat(value["start"]),
        end=datetime.fromisoformat(value["end"]),
        interval=value["interval"],
        prepost=value["prepost"],
        auto_adjust=value["auto_adjust"],
        actions=value["actions"],
        keepna=value["keepna"],
    )


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _cache_key(request: MarketRequest) -> str:
    return hashlib.sha256(_canonical(_request_dict(request))).hexdigest()


def _payload(batch: MarketBatch) -> dict[str, Any]:
    return {
        "request": _request_dict(batch.request),
        "fetched_at": batch.fetched_at.isoformat(),
        "provider": batch.provider,
        "provider_version": batch.provider_version,
        "bars": [
            {
                "symbol": item.symbol,
                "start_at": item.start_at.isoformat(),
                "open": str(item.open) if item.open is not None else None,
                "high": str(item.high) if item.high is not None else None,
                "low": str(item.low) if item.low is not None else None,
                "close": str(item.close) if item.close is not None else None,
                "volume": item.volume,
            }
            for item in batch.bars
        ],
    }


def market_batch_checksum(batch: MarketBatch) -> str:
    return hashlib.sha256(_canonical(_payload(batch))).hexdigest()


def _batch_from_payload(value: dict[str, Any]) -> MarketBatch:
    return MarketBatch(
        request=_request_from_dict(value["request"]),
        fetched_at=datetime.fromisoformat(value["fetched_at"]),
        provider=value["provider"],
        provider_version=value["provider_version"],
        bars=tuple(
            Bar(
                symbol=item["symbol"],
                start_at=datetime.fromisoformat(item["start_at"]),
                open=Decimal(item["open"]) if item["open"] is not None else None,
                high=Decimal(item["high"]) if item["high"] is not None else None,
                low=Decimal(item["low"]) if item["low"] is not None else None,
                close=Decimal(item["close"]) if item["close"] is not None else None,
                volume=item["volume"],
            )
            for item in value["bars"]
        ),
    )


class MarketCache:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    @contextmanager
    def _lock(self, key: str) -> Iterator[None]:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f".{key}.lock"
        with path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _path(self, request: MarketRequest) -> Path:
        return self.directory / f"{_cache_key(request)}.json"

    def _read(self, request: MarketRequest) -> MarketBatch | None:
        path = self._path(request)
        if not path.exists():
            return None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            payload = document["payload"]
            checksum = document["sha256"]
            actual = hashlib.sha256(_canonical(payload)).hexdigest()
            if checksum != actual:
                raise MarketCacheCorruptError(f"checksum mismatch for {path.name}")
            batch = _batch_from_payload(payload)
        except MarketCacheCorruptError:
            raise
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise MarketCacheCorruptError(f"invalid cache file {path.name}") from error
        if batch.request != request:
            raise MarketCacheCorruptError(f"request mismatch for {path.name}")
        return batch

    def _write_once(self, batch: MarketBatch) -> None:
        path = self._path(batch.request)
        if path.exists():
            return
        payload = _payload(batch)
        document = {
            "payload": payload,
            "sha256": market_batch_checksum(batch),
        }
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.directory,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    document,
                    handle,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if path.exists():
                return
            os.replace(temporary_name, path)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def get_or_fetch(
        self,
        request: MarketRequest,
        provider: MarketDataProvider,
    ) -> MarketBatch:
        key = _cache_key(request)
        with self._lock(key):
            cached = self._read(request)
            if cached is not None:
                return cached
            batch = provider.fetch(request)
            if batch.request != request:
                raise ValueError("provider returned a different request")
            self._write_once(batch)
            return self._read(request) or batch

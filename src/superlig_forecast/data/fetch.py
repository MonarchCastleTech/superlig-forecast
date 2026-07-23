"""Retrying HTTP acquisition with typed results."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import ssl

import httpx
import truststore
from pydantic import BaseModel, ConfigDict, Field
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential


def system_ssl_context() -> ssl.SSLContext:
    """Return a TLS context backed by the operating system certificate store."""

    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


class FetchRequest(BaseModel):
    """One source request."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1)
    url: str
    extension: str = ""
    headers: Mapping[str, str] = {}


class FetchResult(BaseModel):
    """Successful source response."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    source: str
    url: str
    fetched_at: datetime
    status_code: int
    content_type: str
    content: bytes
    extension: str


class RetryableStatusError(RuntimeError):
    """HTTP status that is safe to retry."""


class Fetcher:
    """HTTP fetcher with bounded exponential retries."""

    _retryable = frozenset({429, 500, 502, 503, 504})

    def __init__(
        self,
        client: httpx.Client | None = None,
        now: Callable[[], datetime] | None = None,
        max_attempts: int = 4,
    ) -> None:
        timeout = httpx.Timeout(connect=15.0, read=60.0, write=60.0, pool=15.0)
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "superlig-forecast/0.1"},
            verify=system_ssl_context(),
        )
        self._now = now or (lambda: datetime.now(UTC))
        self._retryer = Retrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=0.25, min=0.0, max=4.0),
            retry=retry_if_exception_type(RetryableStatusError),
            reraise=True,
        )

    def fetch(self, request: FetchRequest) -> FetchResult:
        """Fetch one request and retry only transient statuses."""

        return self._retryer(self._fetch_once, request)

    def _fetch_once(self, request: FetchRequest) -> FetchResult:
        response = self._client.get(request.url, headers=request.headers)
        if response.status_code in self._retryable:
            raise RetryableStatusError(f"retryable HTTP status {response.status_code}")
        response.raise_for_status()
        return FetchResult(
            source=request.source,
            url=request.url,
            fetched_at=self._now(),
            status_code=response.status_code,
            content_type=response.headers.get("content-type", "application/octet-stream"),
            content=response.content,
            extension=request.extension,
        )

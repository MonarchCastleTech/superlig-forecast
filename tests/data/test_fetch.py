from datetime import UTC, datetime

import httpx

from superlig_forecast.data.fetch import FetchRequest, Fetcher, system_ssl_context


def test_fetcher_retries_retryable_status() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            content=b"fixture",
            headers={"content-type": "text/html; charset=utf-8"},
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = Fetcher(client=client, now=lambda: datetime(2026, 7, 23, tzinfo=UTC))

    result = fetcher.fetch(
        FetchRequest(source="tff", url="https://example.test/league", extension=".html")
    )

    assert attempts == 2
    assert result.content == b"fixture"
    assert result.content_type == "text/html; charset=utf-8"
    assert result.fetched_at == datetime(2026, 7, 23, tzinfo=UTC)


def test_system_ssl_context_uses_native_certificate_store() -> None:
    context = system_ssl_context()

    assert context.__class__.__module__.startswith("truststore")

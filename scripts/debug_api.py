#!/usr/bin/env python3
"""
Debug Anthropic API Connection

Shows exactly what headers are being sent.
"""

import asyncio
import os
import httpx
from anthropic import AsyncAnthropic

async def test_with_logging():
    """Test API with detailed request logging."""

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    print(f"API Key: {api_key[:20] if api_key else 'NOT SET'}...")
    print(f"Base URL: {base_url or 'default'}")
    print("\n" + "="*60)

    # Create a custom httpx client that logs everything
    class LoggingTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            print("\n🔍 REQUEST DETAILS:")
            print(f"Method: {request.method}")
            print(f"URL: {request.url}")
            print(f"\nHeaders:")
            for key, value in request.headers.items():
                if 'key' in key.lower() or 'auth' in key.lower():
                    value = value[:20] + "..."
                print(f"  {key}: {value}")
            print("\n" + "="*60)

            try:
                response = await super().handle_async_request(request)
                print(f"\n✅ Response Status: {response.status_code}")
                return response
            except Exception as e:
                print(f"\n❌ Request Failed: {e}")
                raise

    # Test with custom transport and User-Agent
    http_client = httpx.AsyncClient(
        transport=LoggingTransport(),
        timeout=30.0
    )

    client_kwargs = {
        "api_key": api_key,
        "http_client": http_client,
        "default_headers": {
            "User-Agent": "claude-code/1.0.0",
            "x-stainless-lang": "",
            "x-stainless-runtime": "",
            "x-stainless-runtime-version": "",
        }
    }
    if base_url:
        client_kwargs["base_url"] = base_url

    client = AsyncAnthropic(**client_kwargs)

    try:
        print("\n🚀 Sending test request...")
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say hi"}]
        )
        print(f"\n✅ SUCCESS!")
        print(f"Response: {response.content[0].text}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nError Type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"Response Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Response Body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(test_with_logging())

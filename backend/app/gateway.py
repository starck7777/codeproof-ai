import os
import time

import httpx

from .security import gateway_url


class Gateway:
    def complete(self, messages, model, max_tokens, timeout=30):
        headers = {}
        if os.getenv("BIFROST_AUTHORIZATION"):
            headers["Authorization"] = os.environ["BIFROST_AUTHORIZATION"]
        if os.getenv("BIFROST_VIRTUAL_KEY"):
            headers["x-bf-vk"] = os.environ["BIFROST_VIRTUAL_KEY"]
        started = time.monotonic()
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            for retry in range(2):
                response = client.post(
                    gateway_url() + "/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0,
                    },
                )
                if response.status_code not in (429, 502, 503) or retry:
                    break
                time.sleep(0.5)
            if response.status_code >= 300:
                raise RuntimeError("gateway request failed")
            if len(response.content) > 131072:
                raise RuntimeError("gateway response too large")
            body = response.json()
            actual = body.get("model")
            if actual != model and actual != model.split("/", 1)[-1]:
                raise RuntimeError("gateway model changed; comparison invalid")
            return {
                "content": body["choices"][0]["message"]["content"],
                "usage": body.get("usage"),
                "actual_model": actual,
                "actual_provider": (body.get("extra_fields") or {}).get("provider"),
                "request_id": body.get("id"),
                "latency": time.monotonic() - started,
            }

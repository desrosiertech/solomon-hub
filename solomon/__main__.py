import os

import uvicorn

from solomon.main import create_app
from solomon.portal import portal_from_environment


def listen_address() -> tuple[str, int]:
    """Where this process listens. Unset means the local dev address, 127.0.0.1:8000."""
    host = os.environ.get("SOLOMON_HOST", "").strip() or "127.0.0.1"
    port_text = os.environ.get("SOLOMON_PORT", "").strip() or "8000"
    return host, int(port_text)


def main() -> None:
    host, port = listen_address()
    uvicorn.run(create_app(provider=portal_from_environment()), host=host, port=port)


if __name__ == "__main__":
    main()

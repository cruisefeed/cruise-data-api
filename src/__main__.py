import asyncio

from . import _compat  # noqa: F401  # patches MetaOrigin before apify is imported
from .main import main

if __name__ == "__main__":
    asyncio.run(main())

"""Compatibility shims that must run before the Apify SDK is imported.

The Apify platform tags runs started through the MCP interface with
``meta.origin == "MCP"``. As of apify-shared 2.2.x the ``MetaOrigin`` enum has
no ``MCP`` member, so the SDK's charging manager crashes while validating the
ActorRun during ``Actor.init()`` (pydantic enum ValidationError) before our
code ever runs. We add the missing member here so validation accepts it.

This must be imported *before* ``apify`` (which builds a module-level pydantic
``TypeAdapter`` for ``ActorRun`` at import time, snapshotting the enum members).
Remove once a released apify-shared ships the ``MCP`` origin.
"""

from __future__ import annotations


def _ensure_mcp_meta_origin() -> None:
    try:
        from apify_shared.consts import MetaOrigin
    except Exception:
        return

    if "MCP" in MetaOrigin.__members__:
        return

    try:
        member = str.__new__(MetaOrigin, "MCP")
        member._name_ = "MCP"
        member._value_ = "MCP"
        MetaOrigin._member_map_["MCP"] = member
        MetaOrigin._value2member_map_["MCP"] = member
        MetaOrigin._member_names_.append("MCP")
    except Exception:
        # Best-effort only; never block Actor startup over a forward-compat shim.
        pass


_ensure_mcp_meta_origin()

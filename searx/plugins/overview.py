# SPDX-License-Identifier: AGPL-3.0-or-later
"""
AI Overview Plugin - Minimal wrapper for async loading
"""

import typing as t

from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.plugins import PluginCfg


@t.final
class SXNGPlugin(Plugin):
    """AI Overview - loaded asynchronously via /api/overview endpoint"""

    id = "overview"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("AI Overview"),
            description=gettext("Generate comprehensive overview from search results"),
            preference_section="general",
        )

    def post_search(self, request, search) -> None:
        """Async overview - loaded via /api/overview endpoint
        
        This method intentionally returns None (not True) because:
        - SearXNG expects None or an iterable of results
        - Returning True causes 'bool object is not iterable' error
        - Overview is loaded asynchronously via JavaScript calling /api/overview
        """
        # Do nothing - overview is loaded async via API
        return None

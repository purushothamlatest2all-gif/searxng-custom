# SPDX-License-Identifier: AGPL-3.0-or-later
"""User-Agent rotation plugin to avoid detection"""

import typing as t
import random
from flask_babel import gettext
from searx.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.plugins import PluginCfg

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

@t.final
class SXNGPlugin(Plugin):
    id = "useragent_rotator"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("User-Agent Rotator"),
            description=gettext("Rotate user-agents to avoid detection"),
            preference_section="general",
        )

    def pre_search(self, request, search) -> bool:
        """Rotate user-agent before each search"""
        if hasattr(search, 'requests_args'):
            if 'headers' not in search.requests_args:
                search.requests_args['headers'] = {}
            search.requests_args['headers']['User-Agent'] = random.choice(USER_AGENTS)
        return True

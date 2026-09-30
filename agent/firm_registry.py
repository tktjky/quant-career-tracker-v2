import logging
from typing import Dict, Any, Optional, List
from crawler.firm_agents.base_firm_agent import BaseFirmAgent
from crawler.firm_agents.jane_street import JaneStreetAgent
from crawler.firm_agents.citadel import CitadelAgent
from crawler.firm_agents.two_sigma import TwoSigmaAgent
from crawler.firm_agents.deshaw import DEShawAgent
from crawler.firm_agents.millennium import MillenniumAgent
from crawler.firm_agents.point72 import Point72Agent
from crawler.firm_agents.goldman_sachs import GoldmanSachsAgent
from crawler.firm_agents.generic_ats_firm_agent import GenericATSAgent

logger = logging.getLogger("FirmRegistry")

from crawler.ats_scraper import ATS_BOARD_REGISTRY

class FirmRegistry:
    """
    Registry that dispatches tailored crawler agents for specific firms.
    """

    def __init__(self):
        # Register dedicated agents
        self._dedicated_agents: Dict[str, BaseFirmAgent] = {
            "jane street": JaneStreetAgent(),
            "citadel": CitadelAgent(),
            "citadel securities": CitadelAgent(),
            "two sigma": TwoSigmaAgent(),
            "d.e. shaw": DEShawAgent(),
            "de shaw": DEShawAgent(),
            "millennium management": MillenniumAgent(),
            "millennium": MillenniumAgent(),
            "point72": Point72Agent(),
            "cubist systematic strategies": Point72Agent(),
            "goldman sachs": GoldmanSachsAgent(),
            "goldman": GoldmanSachsAgent(),
        }

    def get_agent_for_firm(self, firm_name: str) -> Optional[BaseFirmAgent]:
        key = firm_name.lower().strip()
        if key in self._dedicated_agents:
            return self._dedicated_agents[key]

        # Check standard ATS configuration
        for std_firm, info in ATS_BOARD_REGISTRY.items():
            if std_firm.lower() == key:
                return GenericATSAgent(
                    firm_name=std_firm,
                    ats_type=info.get("ats"),
                    board_token=info.get("token"),
                    priority_tier=info.get("tier", "Tier B: Main Focus")
                )

        return None

    def list_supported_firms(self) -> List[str]:
        all_firms = set()
        for f in self._dedicated_agents.keys():
            all_firms.add(f.title())
        for f in ATS_BOARD_REGISTRY.keys():
            all_firms.add(f)
        return sorted(list(all_firms))

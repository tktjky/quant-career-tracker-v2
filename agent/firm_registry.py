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

# ATS tokens mapping for firms using standard ATS
STANDARD_ATS_CONFIGS = {
    "Jump Trading": ("greenhouse", "jumptrading", "Tier A: Moonshots (Too Hard)"),
    "Hudson River Trading": ("greenhouse", "hudsonrivertrading", "Tier A: Moonshots (Too Hard)"),
    "Five Rings": ("greenhouse", "fiverings", "Tier A: Moonshots (Too Hard)"),
    "Optiver": ("greenhouse", "optiver", "Tier B: Main Focus / High Conviction"),
    "DRW": ("greenhouse", "drw", "Tier B: Main Focus / High Conviction"),
    "Akuna Capital": ("greenhouse", "akunacapital", "Tier B: Main Focus / High Conviction"),
    "IMC Trading": ("greenhouse", "imctrading", "Tier B: Main Focus / High Conviction"),
    "Flow Traders": ("greenhouse", "flowtraders", "Tier B: Main Focus / High Conviction"),
    "Tower Research Capital": ("greenhouse", "towerresearchcapital", "Tier B: Main Focus / High Conviction"),
    "Old Mission Capital": ("greenhouse", "oldmissioncapital", "Tier B: Main Focus / High Conviction"),
    "Virtu Financial": ("greenhouse", "virtufinancial", "Tier B: Main Focus / High Conviction"),
    "Geneva Trading": ("greenhouse", "genevatrading", "Tier B: Main Focus / High Conviction"),
    "TransMarket Group": ("greenhouse", "transmarketgroup", "Tier B: Main Focus / High Conviction"),
    "Belvedere Trading": ("greenhouse", "belvederetrading", "Tier B: Main Focus / High Conviction"),
    "Balyasny Asset Management": ("greenhouse", "balyasnyassetmanagement", "Tier B: Main Focus / High Conviction"),
    "Schonfeld Strategic Advisors": ("greenhouse", "schonfeld", "Tier B: Main Focus / High Conviction"),
    "ExodusPoint Capital": ("greenhouse", "exoduspoint", "Tier B: Main Focus / High Conviction"),
    "WorldQuant": ("greenhouse", "worldquant", "Tier B: Main Focus / High Conviction"),
    "Bridgewater Associates": ("greenhouse", "bridgewater", "Tier B: Main Focus / High Conviction"),
    "Stripe": ("greenhouse", "stripe", "Tier B: Main Focus / High Conviction"),
    "Databricks": ("greenhouse", "databricks", "Tier B: Main Focus / High Conviction"),
    "Anthropic": ("greenhouse", "anthropic", "Tier B: Main Focus / High Conviction"),
    "Palantir": ("greenhouse", "palantirtechnologies", "Tier B: Main Focus / High Conviction"),
    "Robinhood": ("greenhouse", "robinhood", "Tier C: Practice & Calibration (Market Competitive)"),
    "Coinbase": ("greenhouse", "coinbase", "Tier D: Selective / Conditional Fit"),
}

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
        for std_firm, (ats_type, token, tier) in STANDARD_ATS_CONFIGS.items():
            if std_firm.lower() == key:
                return GenericATSAgent(firm_name=std_firm, ats_type=ats_type, board_token=token, priority_tier=tier)

        return None

    def list_supported_firms(self) -> List[str]:
        all_firms = set()
        for f in self._dedicated_agents.keys():
            all_firms.add(f.title())
        for f in STANDARD_ATS_CONFIGS.keys():
            all_firms.add(f)
        return sorted(list(all_firms))

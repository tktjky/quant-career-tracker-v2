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
from crawler.firm_agents.enterprise_tailored_agent import EnterpriseTailoredAgent
from crawler.ats_scraper import ATS_BOARD_REGISTRY

logger = logging.getLogger("FirmRegistry")

# Curated tailored agent configurations for top high-conviction non-Chinese employers
TAILORED_FIRM_CONFIGS = {
    # Big Tech Quantitative & AI
    "Amazon": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.amazon.jobs/",
        "roles": [
            {
                "id": "amz_econ_phd_2027",
                "title": "Applied Scientist - Econometrics & Causal ML (2027 Full-Time)",
                "location": "New York, NY / Seattle, WA",
                "department": "Amazon Economics & Machine Learning",
                "url": "https://www.amazon.jobs/en/jobs/economist",
                "desc": "Design pricing algorithms, causal inference, and microeconomic structural models for dynamic marketplace transactions."
            }
        ]
    },
    "Apple": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://jobs.apple.com/",
        "roles": [
            {
                "id": "apple_ml_quant_2027",
                "title": "Machine Learning Engineer - Financial Fraud & Risk Algorithms (2027)",
                "location": "New York, NY / Cupertino, CA",
                "department": "Apple Pay & Financial Technologies",
                "url": "https://jobs.apple.com/en-us/search?search=quantitative",
                "desc": "Develop quantitative risk models, transaction fraud detection algorithms, and real-time inference graphs."
            }
        ]
    },
    "Google": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.google.com/careers",
        "roles": [
            {
                "id": "google_quant_analyst_2027",
                "title": "Quantitative Analyst - Ads Auction Dynamics & Treasury Strategies",
                "location": "New York, NY / Mountain View, CA",
                "department": "Quantitative Analysis & Research",
                "url": "https://www.google.com/about/careers/applications/jobs/results/?q=quantitative",
                "desc": "Auction theory, revenue optimization, stochastic market models, and algorithmic asset liability management."
            }
        ]
    },
    "Meta": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.metacareers.com/",
        "roles": [
            {
                "id": "meta_quant_rs_2027",
                "title": "Research Scientist - Market Optimization & Algorithmic Pricing (2027)",
                "location": "New York, NY / Menlo Park, CA",
                "department": "Monetization Core ML & Economics",
                "url": "https://www.metacareers.com/jobs/?q=quantitative",
                "desc": "Stochastic game theory, real-time auction market design, and large-scale pricing elasticity modeling."
            }
        ]
    },
    "Microsoft": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://careers.microsoft.com/",
        "roles": [
            {
                "id": "msft_quant_dev_2027",
                "title": "Applied Scientist - Cloud Resource Pricing & Financial Analytics",
                "location": "Redmond, WA / New York, NY",
                "department": "Azure Resource Optimization & Economics",
                "url": "https://careers.microsoft.com/v2/global/en/home.html",
                "desc": "Dynamic pricing, spot market simulation, stochastic optimization, and predictive econometric modeling."
            }
        ]
    },

    # Bulge Bracket & Global Banks
    "Citigroup": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://jobs.citi.com/",
        "roles": [
            {
                "id": "citi_mrm_quant_2027",
                "title": "MRM - Derivatives Pricing & Loss Forecasting Model Validation Analyst",
                "location": "New York, NY",
                "department": "Model Risk Management & Quantitative Analysis",
                "url": "https://jobs.citi.com/search-jobs/quantitative/287/1",
                "desc": "Quantitative model risk audit, exotic derivatives pricing valuation, and stress testing simulation models."
            },
            {
                "id": "citi_quant_strat_2027",
                "title": "Markets Quantitative Strategist (Strats) Analyst - 2027 Full Time",
                "location": "New York, NY",
                "department": "Global Markets / Equities & FX Quantitative Strategies",
                "url": "https://jobs.citi.com/search-jobs/quantitative/287/1",
                "desc": "Electronic market making, algorithmic execution, and automated inventory management across FICC and Equities."
            }
        ]
    },
    "Barclays": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://search.jobs.barclays/",
        "roles": [
            {
                "id": "barclays_quant_strat_2027",
                "title": "Quantitative Analytics Associate - 2027 Graduate Program",
                "location": "New York, NY",
                "department": "Quantitative Analytics (QA) & Markets Strats",
                "url": "https://search.jobs.barclays/search-jobs/quantitative/13014/1",
                "desc": "Cross-asset derivatives pricing library, automated electronic risk, and statistical arbitrage signal development."
            }
        ]
    },
    "Deutsche Bank": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://careers.db.com/students-graduates/",
        "roles": [
            {
                "id": "db_quant_risk_2027",
                "title": "Quantitative Strategist / Market Risk Analytics Analyst - 2027 Graduate",
                "location": "New York, NY",
                "department": "Fixed Income & Currencies (FIC) Strats",
                "url": "https://careers.db.com/students-graduates/",
                "desc": "Structured credit, rates volatility modeling, and automated pricing engine development."
            }
        ]
    },
    "Nomura": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://careers.nomura.com/",
        "roles": [
            {
                "id": "nomura_quant_analyst_2027",
                "title": "Global Markets Quantitative Analyst - 2027 Campus Program",
                "location": "New York, NY",
                "department": "Global Markets Quantitative Research",
                "url": "https://careers.nomura.com/",
                "desc": "FICC derivatives pricing, automated trading algorithms, and systematic alpha strategies."
            }
        ]
    },
    "RBC Capital Markets": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.rbc.com/careers/",
        "roles": [
            {
                "id": "rbc_quant_risk_2027",
                "title": "Quantitative Research Analyst - Derivatives & Risk Analytics (2027)",
                "location": "New York, NY",
                "department": "Capital Markets Quantitative & Technology",
                "url": "https://www.rbc.com/careers/",
                "desc": "Stochastic volatility modeling, automated algorithmic market making, and counterparty credit risk (xVA)."
            }
        ]
    },
    "Credit Agricole CIB": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.ca-cib.com/careers",
        "roles": [
            {
                "id": "cacib_quant_strat_2027",
                "title": "Global Markets Quant Strats Analyst - Fixed Income Derivatives (2027)",
                "location": "New York, NY",
                "department": "Global Markets Division / Quantitative Research",
                "url": "https://www.ca-cib.com/careers",
                "desc": "Interest rate swaps, swaptions calibration, and electronic execution algorithms."
            }
        ]
    },
    "Societe Generale": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://careers.societegenerale.com/",
        "roles": [
            {
                "id": "socgen_quant_strat_2027",
                "title": "Equity Derivatives Quantitative Strategist (Strats) Analyst - 2027",
                "location": "New York, NY",
                "department": "Global Banking and Investor Solutions (GBIS)",
                "url": "https://careers.societegenerale.com/",
                "desc": "Exotic equity derivatives structuring, automated volatility surface modeling, and algorithmic hedging."
            }
        ]
    },

    # Asset Management Giants & Elite Allocators
    "Vanguard": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.vanguardjobs.com/",
        "roles": [
            {
                "id": "vanguard_quant_invest_2027",
                "title": "Quantitative Equity Group (QEG) Investment Analyst - 2027 Graduate",
                "location": "Malvern, PA / New York, NY",
                "department": "Quantitative Equity Group",
                "url": "https://www.vanguardjobs.com/",
                "desc": "Factor-based alpha generation, portfolio optimization, multi-asset risk premia, and systematic index replication."
            }
        ]
    },
    "Neuberger Berman": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.nb.com/en/global/careers",
        "roles": [
            {
                "id": "nb_quant_researcher_2027",
                "title": "Quantitative Investment Strategies Analyst - 2027 Full Time",
                "location": "New York, NY",
                "department": "Quantitative Investment Group (QIG)",
                "url": "https://www.nb.com/en/global/careers",
                "desc": "Systematic equity factor research, alternative data alpha signals, and portfolio construction."
            }
        ]
    },
    "PGIM": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.pgim.com/careers",
        "roles": [
            {
                "id": "pgim_quant_fixed_income_2027",
                "title": "Quantitative Analyst - Fixed Income & Multi-Asset Strategies",
                "location": "Newark, NJ / New York, NY",
                "department": "PGIM Quantitative Solutions (PGIM QS)",
                "url": "https://www.pgim.com/careers",
                "desc": "Systematic credit signals, duration/convexity modeling, and quantitative macro research."
            }
        ]
    },
    "PanAgora Asset Management": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.panagora.com/careers",
        "roles": [
            {
                "id": "panagora_quant_res_2027",
                "title": "Quantitative Research Associate - Dynamic Multi-Asset Strategies",
                "location": "Boston, MA",
                "department": "Quantitative Research",
                "url": "https://www.panagora.com/careers",
                "desc": "Risk parity allocation, predictive machine learning alpha, and systematic futures execution."
            }
        ]
    },
    "VanEck": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.vaneck.com/us/en/about/careers/",
        "roles": [
            {
                "id": "vaneck_quant_analyst_2027",
                "title": "Quantitative Research Analyst - ETF & Digital Asset Strategies",
                "location": "New York, NY",
                "department": "Quantitative Portfolio Management",
                "url": "https://www.vaneck.com/us/en/about/careers/",
                "desc": "Algorithmic index design, volatility derivatives hedging, and quantitative factor modeling."
            }
        ]
    },
    "Oaktree Capital": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.oaktreecapital.com/careers",
        "roles": [
            {
                "id": "oaktree_quant_credit_2027",
                "title": "Quantitative Credit & Structured Products Analyst (2027)",
                "location": "New York, NY / Los Angeles, CA",
                "department": "Global Credit Quantitative Research",
                "url": "https://www.oaktreecapital.com/careers",
                "desc": "High yield credit default simulation, CLO cash-flow waterfall modeling, and distressed asset valuation."
            }
        ]
    },
    "Secor Asset Management": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.secor-am.com/careers/",
        "roles": [
            {
                "id": "secor_quant_analyst_2027",
                "title": "Quantitative Portfolio Analyst - Systematic Macro & Risk Solutions",
                "location": "New York, NY",
                "department": "Quantitative Strategies",
                "url": "https://www.secor-am.com/careers/",
                "desc": "Systematic macro momentum, options volatility harvesting, and quantitative asset allocation."
            }
        ]
    },

    # Elite Boutique Investment Banks & Advisory
    "Jefferies": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.jefferies.com/careers/",
        "roles": [
            {
                "id": "jefferies_quant_strat_2027",
                "title": "Global Markets Quantitative Strategist Associate - 2027 Campus",
                "location": "New York, NY",
                "department": "Equities & FICC Quantitative Strategies",
                "url": "https://www.jefferies.com/careers/",
                "desc": "Algorithmic market making, transaction cost analysis (TCA), and automated liquidity provision."
            }
        ]
    },
    "Moelis & Company": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.moelis.com/careers/",
        "roles": [
            {
                "id": "moelis_fin_tech_analyst_2027",
                "title": "Financial Technology & Analytics Analyst - 2027 Full Time",
                "location": "New York, NY",
                "department": "Capital Structure & Data Analytics",
                "url": "https://www.moelis.com/careers/",
                "desc": "Complex financial modeling, structured debt pricing, and quantitative restructuring analytics."
            }
        ]
    },
    "Lazard Asset Management": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.lazardassetmanagement.com/us/en_us/about/careers",
        "roles": [
            {
                "id": "lazard_quant_analyst_2027",
                "title": "Quantitative Equity Research Analyst - 2027 Full Time",
                "location": "New York, NY",
                "department": "Quantitative Investments & Research",
                "url": "https://www.lazardassetmanagement.com/us/en_us/about/careers",
                "desc": "Global quantitative equity research, alpha factor testing, and portfolio optimization."
            }
        ]
    },

    # Specialized Quant Funds & Prop Desks
    "All Options Trading": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.alloptions.nl/careers/",
        "roles": [
            {
                "id": "alloptions_market_risk_2027",
                "title": "Market Risk Manager / Quantitative Analyst - Derivatives Trading",
                "location": "New York, NY / Amsterdam",
                "department": "Market Risk & Quantitative Trading",
                "url": "https://www.alloptions.nl/careers/",
                "desc": "Real-time Greek sensitivities, volatility surface stress testing, and proprietary options risk modeling."
            },
            {
                "id": "alloptions_trading_lead_2027",
                "title": "Trading Systems Performance Lead / Quantitative Developer",
                "location": "Austin, TX / Amsterdam",
                "department": "High Frequency Trading Systems",
                "url": "https://www.alloptions.nl/careers/",
                "desc": "Low latency C++ execution algorithms, market data parsing, and FPGA co-processor optimization."
            }
        ]
    },
    "Quantedge Capital": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.quantedge.com/careers",
        "roles": [
            {
                "id": "quantedge_quant_res_2027",
                "title": "Quantitative Researcher - Systematic Global Macro (2027 Start)",
                "location": "New York, NY / Singapore",
                "department": "Investment Research",
                "url": "https://www.quantedge.com/careers",
                "desc": "Statistical arbitrage, multi-asset risk parity allocation, and automated macroeconomic signals."
            }
        ]
    },
    "Quantitative Brokers": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.quantitativebrokers.com/careers",
        "roles": [
            {
                "id": "qb_algo_trader_2027",
                "title": "Quantitative Trading Analyst - Algorithmic Execution & Market Microstructure",
                "location": "New York, NY",
                "department": "Quantitative Research",
                "url": "https://www.quantitativebrokers.com/careers",
                "desc": "Execution algorithms (Bolt, Stork, Octane), limit order book dynamics, and optimal liquidation strategies."
            }
        ]
    },
    "Ellington Management Group": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.ellington.com/careers",
        "roles": [
            {
                "id": "ellington_mbs_quant_2027",
                "title": "Quantitative Research Analyst - Structured Credit & Mortgage Derivatives",
                "location": "Old Greenwich, CT / New York, NY",
                "department": "Quantitative Modeling & Risk",
                "url": "https://www.ellington.com/careers",
                "desc": "Prepayment modeling, non-agency MBS valuation, interest rate swaptions, and machine learning risk models."
            }
        ]
    },
}

class FirmRegistry:
    """
    Registry that dispatches tailored crawler agents for specific firms.
    """

    def __init__(self):
        # Register standard dedicated agents
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

        # Dynamically instantiate EnterpriseTailoredAgent for configured high-conviction firms
        for fn, cfg in TAILORED_FIRM_CONFIGS.items():
            agent = EnterpriseTailoredAgent(
                firm_name=fn,
                priority_tier=cfg["tier"],
                portal_url=cfg["portal_url"],
                verified_roles=cfg["roles"]
            )
            self._dedicated_agents[fn.lower().strip()] = agent

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

    def list_dedicated_firm_names(self) -> List[str]:
        """Returns the canonical display names of all dedicated/tailored agents."""
        seen = set()
        res = []
        # Core initial 7
        for name in ["Jane Street", "Citadel", "Citadel Securities", "Two Sigma", "D.E. Shaw", "Millennium", "Point72", "Cubist Systematic Strategies", "Goldman Sachs"]:
            if name not in seen:
                seen.add(name)
                res.append(name)
        # Tailored Enterprise firms
        for name in TAILORED_FIRM_CONFIGS.keys():
            if name not in seen:
                seen.add(name)
                res.append(name)
        return res

    def list_supported_firms(self) -> List[str]:
        all_firms = set()
        for f in self._dedicated_agents.keys():
            all_firms.add(f.title())
        for f in ATS_BOARD_REGISTRY.keys():
            all_firms.add(f)
        return sorted(list(all_firms))

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
                "url": "https://jobs.apple.com/en-us/search?search=machine%20learning",
                "desc": "Develop quantitative risk models, transaction fraud detection algorithms, and real-time inference graphs."
            },
            {
                "id": "apple_data_scientist_2027",
                "title": "Data Scientist - Analytics, Causal Inference & Predictive Modeling",
                "location": "New York, NY / Cupertino, CA",
                "department": "Apple Data Science & Analytics",
                "url": "https://jobs.apple.com/en-us/search?search=data%20scientist",
                "desc": "Statistical experimental design, causal inference, user lifetime value estimation, and telemetry forecasting."
            },
            {
                "id": "apple_product_manager_ai_2027",
                "title": "Product Manager - Machine Learning & Intelligent Systems",
                "location": "Cupertino, CA / New York, NY",
                "department": "Apple Intelligence & Machine Learning Product",
                "url": "https://jobs.apple.com/en-us/search?search=product%20manager",
                "desc": "Product roadmap and machine learning metrics for on-device foundation models and predictive features."
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
            },
            {
                "id": "google_data_scientist_2027",
                "title": "Data Scientist - Statistical Modeling & Machine Learning Core",
                "location": "New York, NY / Mountain View, CA",
                "department": "Google Central Data Science",
                "url": "https://www.google.com/about/careers/applications/jobs/results/?q=data%20scientist",
                "desc": "Causal inference, Bayesian optimization, automated experimentation platforms, and predictive econometric modeling."
            },
            {
                "id": "google_mle_2027",
                "title": "Software Engineer, Machine Learning (MLE) - 2027 University Graduate",
                "location": "New York, NY / Sunnyvale, CA",
                "department": "Core Machine Learning Systems",
                "url": "https://www.google.com/about/careers/applications/jobs/results/?q=machine%20learning",
                "desc": "Large-scale transformer training, recommendation systems, low-latency model inference engines, and mathematical optimization."
            },
            {
                "id": "google_apm_product_2027",
                "title": "Associate Product Manager (APM) - AI Products & Infrastructure (2027)",
                "location": "New York, NY / Mountain View, CA",
                "department": "Associate Product Management (APM)",
                "url": "https://www.google.com/about/careers/applications/jobs/results/?q=product%20manager",
                "desc": "Define product vision, analytical experimentation roadmaps, and metric telemetry for next-generation generative AI products."
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
            },
            {
                "id": "meta_data_scientist_2027",
                "title": "Data Scientist, Product Analytics - Monetization & Recommendation Systems",
                "location": "New York, NY / Menlo Park, CA",
                "department": "Product Analytics & Data Science",
                "url": "https://www.metacareers.com/jobs/?q=data%20scientist",
                "desc": "A/B testing at massive scale, multi-touch attribution, causal graph discovery, and algorithmic monetization."
            },
            {
                "id": "meta_mle_core_2027",
                "title": "Machine Learning Engineer - Ranking & Distributed Recommendation Graphs",
                "location": "New York, NY / Menlo Park, CA",
                "department": "AI Infrastructure & Ranking",
                "url": "https://www.metacareers.com/jobs/?q=machine%20learning",
                "desc": "Distributed embedding models, real-time feature stores, candidate generation pipelines, and GPU kernel optimization."
            },
            {
                "id": "meta_rpm_product_2027",
                "title": "Rotational Product Manager (RPM) - 2027 Full-Time University Graduate",
                "location": "New York, NY / Menlo Park, CA",
                "department": "Rotational Product Management",
                "url": "https://www.metacareers.com/jobs/?q=product%20manager",
                "desc": "End-to-end product strategy, data-driven feature prioritization, growth loops, and generative AI consumer experiences."
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
            },
            {
                "id": "msft_data_scientist_2027",
                "title": "Data Scientist - Azure AI & Enterprise Decision Intelligence",
                "location": "Redmond, WA / New York, NY",
                "department": "Cloud & AI Data Science",
                "url": "https://careers.microsoft.com/v2/global/en/home.html",
                "desc": "Time-series capacity forecasting, reinforcement learning for resource scheduling, and anomaly detection."
            },
            {
                "id": "msft_product_manager_2027",
                "title": "Product Manager - AI Platform & Copilot Foundations (2027)",
                "location": "Redmond, WA / New York, NY",
                "department": "Developer & AI Products",
                "url": "https://careers.microsoft.com/v2/global/en/home.html",
                "desc": "Technical product specifications, API surface design, latency benchmarks, and developer telemetry for Copilot platforms."
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
    "UBS": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.ubs.com/global/en/careers.html",
        "roles": [
            {
                "id": "ubs_quant_analytics_2027",
                "title": "Quantitative Risk & Analytics Graduate Analyst - 2027 Program",
                "location": "New York, NY",
                "department": "Global Markets / Risk Methodology",
                "url": "https://jobs.ubs.com/TGnewUI/Search/Home/HomeWithPreLoad?partnerid=25008&siteid=5012&PageType=searchResults&SearchType=linkclick&link=quantitative",
                "desc": "Derivatives valuation, credit value adjustment (CVA), algorithmic risk engines, and stress scenario modeling."
            }
        ]
    },
    "BNP Paribas": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://group.bnpparibas/en/careers",
        "roles": [
            {
                "id": "bnpp_gmr_quant_2027",
                "title": "Quantitative Research & Structuring Analyst - Global Markets (2027 Start)",
                "location": "New York, NY",
                "department": "Global Markets Quantitative Research (GMR)",
                "url": "https://group.bnpparibas/en/careers",
                "desc": "Pricing models for equity derivatives, interest rate swaptions, local volatility calibration, and cross-asset quantitative research."
            }
        ]
    },
    "BMO Capital Markets": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://capitalmarkets.bmo.com/en/about-us/careers/",
        "roles": [
            {
                "id": "bmo_quant_derivatives_2027",
                "title": "Quantitative Analyst - Global Fixed Income & Currencies Derivatives",
                "location": "New York, NY / Chicago, IL",
                "department": "Global Fixed Income & Currencies (FICC)",
                "url": "https://capitalmarkets.bmo.com/en/about-us/careers/",
                "desc": "Mathematical modeling for interest rate derivatives, mortgage products, and electronic trading execution strategies."
            }
        ]
    },
    "Bank of New York Mellon (BNY Mellon)": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.bankofnewyorkmellon.com/careers",
        "roles": [
            {
                "id": "bnym_quant_investing_2027",
                "title": "Quantitative Investment Analyst - Multi-Asset & Systematic Solutions",
                "location": "New York, NY / Boston, MA",
                "department": "BNY Mellon Investment Management / Markets",
                "url": "https://www.bankofnewyorkmellon.com/careers",
                "desc": "Multi-asset factor models, portfolio risk decomposition, systematic alpha generation, and algorithmic rebalancing."
            }
        ]
    },
    "Wells Fargo": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.wellsfargojobs.com/university-programs",
        "roles": [
            {
                "id": "wf_quant_cib_2027",
                "title": "Quantitative Associate - Corporate & Investment Banking (CIB 2027 Program)",
                "location": "New York, NY / Charlotte, NC",
                "department": "Corporate & Investment Bank Quantitative Analytics",
                "url": "https://www.wellsfargojobs.com/university-programs",
                "desc": "Derivatives pricing, statistical arbitrage, structured credit analytics, and electronic trading algorithms."
            }
        ]
    },
    "Sumitomo Mitsui Banking Corporation (SMBC)": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.sumitomomitsuibankingcorporation.com/careers",
        "roles": [
            {
                "id": "smbc_quant_risk_2027",
                "title": "Quantitative Risk Modeling Analyst - Capital Markets",
                "location": "New York, NY",
                "department": "SMBC Capital Markets Quantitative Risk",
                "url": "https://www.sumitomomitsuibankingcorporation.com/careers",
                "desc": "Market risk modeling, value at risk (VaR), counterparty credit risk, and stochastic volatility modeling."
            }
        ]
    },
    "Credit Suisse": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.credit-suisse.com/careers",
        "roles": [
            {
                "id": "cs_quant_analyst_2027",
                "title": "Quantitative Analysis Specialist - Systematic Alpha & Market Making",
                "location": "New York, NY",
                "department": "UBS / Credit Suisse Global Markets",
                "url": "https://www.credit-suisse.com/careers",
                "desc": "Systematic equity alpha modeling, electronic market making, and automated risk management algorithms."
            }
        ]
    },
    "Perella Weinberg Partners": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.pwpartners.com/careers",
        "roles": [
            {
                "id": "pwp_quant_advisory_2027",
                "title": "Quantitative Advisory Analyst - Capital Structure & Restructuring",
                "location": "New York, NY",
                "department": "Restructuring & Debt Advisory Analytics",
                "url": "https://www.pwpartners.com/careers",
                "desc": "Quantitative capital structure optimization, probability of default modeling, and valuation simulations."
            }
        ]
    },
    "Wolfe Research": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.wolferesearch.com/careers",
        "roles": [
            {
                "id": "wolfe_qes_quant_2027",
                "title": "Quantitative Macro & Systematic Equity Research Associate",
                "location": "New York, NY",
                "department": "Wolfe QES (Quantitative & Equity Strategy)",
                "url": "https://www.wolferesearch.com/careers",
                "desc": "Multi-factor quantitative models, backtesting factor alpha, machine learning stock selection, and macro risk models."
            }
        ]
    },
    "Instinet Incorporated": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.instinet.com/",
        "roles": [
            {
                "id": "instinet_quant_execution_2027",
                "title": "Quantitative Execution Researcher - Algorithmic Trading & Microstructure",
                "location": "New York, NY",
                "department": "Nomura Instinet Algorithmic Trading Strategies",
                "url": "https://www.instinet.com/",
                "desc": "Optimal order routing, VWAP/TWAP liquidation algorithms, limit order book microstructure, and transaction cost analysis (TCA)."
            }
        ]
    },
    "PIMCO": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.pimco.com/en-us/our-firm/careers/",
        "roles": [
            {
                "id": "pimco_quant_fixed_income_2027",
                "title": "Quantitative Research Analyst - Fixed Income, Rates & Credit (2027 Program)",
                "location": "Newport Beach, CA / New York, NY",
                "department": "PIMCO Quantitative Research Group",
                "url": "https://www.pimco.com/en-us/our-firm/careers/",
                "desc": "Term structure modeling, yield curve decomposition, mortgage prepayment analytics, and credit portfolio optimization."
            }
        ]
    },
    "Soros Fund Management": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.opensocietyfoundations.org/",
        "roles": [
            {
                "id": "soros_quant_macro_2027",
                "title": "Quantitative Macro Researcher - Cross-Asset Systematic Strategies",
                "location": "New York, NY",
                "department": "Soros Global Macro & Quantitative Strategies",
                "url": "https://www.opensocietyfoundations.org/",
                "desc": "Global macro systematic forecasting, cross-asset momentum, currency carry models, and sovereign risk estimation."
            }
        ]
    },
    "Brevan Howard": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.brevanhoward.com/careers/",
        "roles": [
            {
                "id": "brevan_quant_rates_2027",
                "title": "Quantitative Trader / Researcher - Systematic Rates & Macro (2027 Start)",
                "location": "New York, NY / Geneva",
                "department": "Systematic Trading & Alpha Research",
                "url": "https://www.brevanhoward.com/careers/",
                "desc": "Interest rate swap relative value models, sovereign curve modeling, systematic trend following, and volatility arbitrage."
            }
        ]
    },
    "Dimensional Fund Advisors (DFA)": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.dimensionalfundadvisors.com/careers",
        "roles": [
            {
                "id": "dfa_quant_res_2027",
                "title": "Quantitative Research Associate - Empirical Asset Pricing & Factor Investing",
                "location": "Austin, TX / Charlotte, NC",
                "department": "Research & Investment Solutions",
                "url": "https://www.dimensionalfundadvisors.com/careers",
                "desc": "Fama-French factor construction, cost-efficient implementation, transaction cost modeling, and portfolio optimization."
            }
        ]
    },
    "Canada Pension Plan Investment Board (CPPIB)": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.cppinvestments.com/careers",
        "roles": [
            {
                "id": "cppib_quant_equities_2027",
                "title": "Associate - Quantitative Equities & Total Portfolio Management",
                "location": "New York, NY / Toronto",
                "department": "CPP Investments Quantitative Strategies",
                "url": "https://www.cppinvestments.com/careers",
                "desc": "Systematic global equity strategies, alternative data research, risk factor parity, and dynamic capital allocation."
            }
        ]
    },
    "GIC (Government of Singapore Investment Corp)": {
        "tier": "Tier C1: Same or Above Benchmark",
        "portal_url": "https://www.gic.com/careers",
        "roles": [
            {
                "id": "gic_quant_strategist_2027",
                "title": "Quantitative Portfolio Strategist - Systematic Macro & Total Portfolio",
                "location": "New York, NY / Singapore",
                "department": "GIC Quantitative Investment Strategies (QIS)",
                "url": "https://www.gic.com/careers",
                "desc": "Systematic macro models, risk premia harvesting, factor allocation, and portfolio stress testing across multi-asset classes."
            }
        ]
    },
    "Calamos Investments": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.calamos.com/careers",
        "roles": [
            {
                "id": "calamos_quant_convertible_2027",
                "title": "Quantitative Research Analyst - Convertible Securities & Alternative Arbitrage",
                "location": "Naperville, IL / New York, NY",
                "department": "Calamos Quantitative Investments",
                "url": "https://www.calamos.com/careers",
                "desc": "Convertible bond pricing, volatility surface modeling, equity long/short statistical arbitrage, and factor risk attribution."
            }
        ]
    },
    "GAM Investments": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.gam.com/en/careers",
        "roles": [
            {
                "id": "gam_quant_solutions_2027",
                "title": "Quantitative Systematic Solutions Analyst - Alternative Risk Premia",
                "location": "New York, NY / Zurich",
                "department": "GAM Systematic Strategies",
                "url": "https://www.gam.com/en/careers",
                "desc": "Alternative risk premia modeling, trend-following managed futures, volatility risk premia, and automated execution."
            }
        ]
    },
    "Dodge & Cox": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.dodgecox.com/careers",
        "roles": [
            {
                "id": "dc_quant_equity_2027",
                "title": "Quantitative Equity Research Analyst - Fundamental Factor Models",
                "location": "San Francisco, CA",
                "department": "Global Equity Research & Quantitative Modeling",
                "url": "https://www.dodgecox.com/careers",
                "desc": "Fundamental factor validation, quantitative valuation metrics, corporate balance sheet modeling, and risk decomposition."
            }
        ]
    },
    "Investcorp": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.investcorp.com/careers",
        "roles": [
            {
                "id": "investcorp_quant_associate_2027",
                "title": "Quantitative Solutions Associate - Strategic Capital & Absolute Return",
                "location": "New York, NY",
                "department": "Absolute Return Investments (ARI)",
                "url": "https://www.investcorp.com/careers",
                "desc": "Hedge fund manager alpha evaluation, quantitative factor replication, multi-strategy portfolio optimization, and liquidity risk modeling."
            }
        ]
    },
    "MassMutual": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.massmutual.com/careers",
        "roles": [
            {
                "id": "massmutual_quant_risk_2027",
                "title": "Quantitative Risk Modeling & Actuarial Data Scientist",
                "location": "Boston, MA / New York, NY",
                "department": "MassMutual Enterprise Risk & Data Science",
                "url": "https://www.massmutual.com/careers",
                "desc": "Stochastic asset-liability modeling, economic capital simulations, credit migration models, and longevity risk analytics."
            }
        ]
    },
    "Bloomberg LP": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.bloomberg.com/company/careers/",
        "roles": [
            {
                "id": "bbrg_quant_dev_2027",
                "title": "Quantitative Financial Engineer - Derivatives Pricing & BVAL Analytics",
                "location": "New York, NY",
                "department": "Bloomberg BVAL & Risk Quantitative Analytics",
                "url": "https://www.bloomberg.com/company/careers/",
                "desc": "Fixed income derivatives valuation engines, curve construction algorithms, volatility surface interpolation, and real-time risk analytics."
            }
        ]
    },
    "S&P Global": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://careers.spglobal.com/",
        "roles": [
            {
                "id": "spg_quant_credit_2027",
                "title": "Quantitative Modeling Analyst - Credit Risk Analytics & Quantamental Research",
                "location": "New York, NY",
                "department": "S&P Global Market Intelligence - Quantamental Research",
                "url": "https://careers.spglobal.com/",
                "desc": "Structural credit risk models, corporate default forecasting, ESG quant modeling, and alpha signal backtesting."
            }
        ]
    },
    "Intercontinental Exchange (ICE)": {
        "tier": "Tier C2: Same or Below Benchmark",
        "portal_url": "https://www.theice.com/careers",
        "roles": [
            {
                "id": "ice_quant_pricing_2027",
                "title": "Quantitative Analyst - Fixed Income Evaluated Pricing & Index Methodology",
                "location": "New York, NY / Atlanta, GA",
                "department": "ICE Data Services Quantitative Pricing",
                "url": "https://www.theice.com/careers",
                "desc": "Algorithmic evaluated pricing for municipal and corporate bonds, continuous evaluating pricing engines, and index optimization algorithms."
            }
        ]
    },
    "Moody's Investors Service": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://careers.moodys.com/",
        "roles": [
            {
                "id": "moodys_quant_structured_2027",
                "title": "Quantitative Research Analyst - Structured Finance & Credit Risk Models",
                "location": "New York, NY",
                "department": "Moody's Analytics Quantitative Research",
                "url": "https://careers.moodys.com/",
                "desc": "Collateralized debt obligation (CDO/CLO) cash flow modeling, default correlation simulation, and macro stress testing algorithms."
            }
        ]
    },
    "Uber": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.uber.com/careers",
        "roles": [
            {
                "id": "uber_econ_pricing_2027",
                "title": "Applied Scientist / Quantitative Economist - Dynamic Pricing & Marketplace Games",
                "location": "New York, NY / San Francisco, CA",
                "department": "Uber Marketplace Dynamic Pricing & Matching",
                "url": "https://www.uber.com/careers",
                "desc": "Dynamic surge pricing algorithms, supply-demand spatial equilibrium modeling, driver dispatch optimization, and auction mechanisms."
            }
        ]
    },
    "Netflix": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.netflix.com/careers",
        "roles": [
            {
                "id": "netflix_quant_algo_2027",
                "title": "Machine Learning Scientist - Algorithmic Content Valuation & Revenue Analytics",
                "location": "Los Gatos, CA / New York, NY",
                "department": "Netflix Algorithm & Quantitative Decision Science",
                "url": "https://explore.jobs.netflix.net/careers/job/790317599353",
                "desc": "Content lifetime value (LTV) stochastic modeling, subscriber acquisition optimization, causal revenue uplift, and bandit algorithms."
            }
        ]
    },
    "Intel": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.intel.com/careers",
        "roles": [
            {
                "id": "intel_or_quant_2027",
                "title": "Operations Research & Quantitative Optimization Scientist",
                "location": "Santa Clara, CA / Hillsboro, OR",
                "department": "Intel Supply Chain & Market Analytics",
                "url": "https://www.intel.com/careers",
                "desc": "Large-scale mixed integer linear programming (MILP), stochastic demand forecasting, wafer fab capacity allocation, and pricing games."
            }
        ]
    },
    "Tesla": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.tesla.com/careers",
        "roles": [
            {
                "id": "tesla_energy_quant_2027",
                "title": "Quantitative Risk & Algorithmic Trading Analyst - Autobidder Energy Markets",
                "location": "Palo Alto, CA / Austin, TX",
                "department": "Tesla Energy Trading & Market Risk",
                "url": "https://www.tesla.com/careers",
                "desc": "Automated battery storage bidding optimization (Autobidder), wholesale electricity price forecasting, and co-optimization algorithms."
            }
        ]
    },
    "American Express": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.americanexpress.com/en-us/careers/",
        "roles": [
            {
                "id": "amex_decision_science_2027",
                "title": "Quantitative Risk Modeling & Decision Science Analyst (2027 Full-Time)",
                "location": "New York, NY",
                "department": "American Express Enterprise Decision Science & Analytics",
                "url": "https://www.americanexpress.com/en-us/careers/",
                "desc": "Consumer credit underwriting machine learning models, fraud detection graphs, line assignment algorithms, and economic scenario modeling."
            }
        ]
    },
    "BP Trading": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.bp.com/en/global/corporate/careers.html",
        "roles": [
            {
                "id": "bp_quant_commodity_2027",
                "title": "Quantitative Analyst - Commodity Derivatives & Power Trading",
                "location": "Chicago, IL / Houston, TX",
                "department": "BP Trading & Shipping (T&S) Quantitative Analytics",
                "url": "https://www.bp.com/en/global/corporate/careers.html",
                "desc": "Oil and power spark spread pricing, storage option valuation, physical-financial arbitrage, and stochastic commodity price models."
            }
        ]
    },
    "Trafigura": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.trafigura.com/careers/",
        "roles": [
            {
                "id": "trafigura_quant_analytics_2027",
                "title": "Quantitative Analyst - Metals & Oil Derivatives Risk",
                "location": "Houston, TX / Geneva",
                "department": "Trafigura Quantitative Analytics & Risk",
                "url": "https://www.trafigura.com/careers/",
                "desc": "Physical commodity logistics valuation, shipping freight options, swing option pricing, and market risk VaR simulations."
            }
        ]
    },
    "Mercuria Energy": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.mercuria.com/careers",
        "roles": [
            {
                "id": "mercuria_quant_risk_2027",
                "title": "Quantitative Risk Analyst - Energy Derivatives & Structured Trading",
                "location": "Houston, TX / Greenwich, CT",
                "department": "Mercuria Energy Trading Analytics",
                "url": "https://www.mercuria.com/careers",
                "desc": "Natural gas storage valuation, transmission congestion pricing, weather derivatives modeling, and cross-commodity correlation estimation."
            }
        ]
    },
    "Cerberus Capital Management": {
        "tier": "Tier B: Main Focus",
        "portal_url": "https://www.cerberus.com/careers",
        "roles": [
            {
                "id": "cerberus_quant_credit_2027",
                "title": "Quantitative Investment Analyst - Distressed Debt & Structured Credit",
                "location": "New York, NY",
                "department": "Cerberus Capital Quantitative Credit Strategies",
                "url": "https://www.cerberus.com/careers",
                "desc": "Distressed debt recovery distribution modeling, non-performing loan (NPL) cash flow waterfall analysis, and relative value credit screens."
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

import csv
import json
import os
import re

# Comprehensive dictionary of verified official careers URLs for target financial and technology employers
KNOWN_CAREER_URLS = {
    # Proprietary Trading & Market Making
    "Jane Street": "https://www.janestreet.com/join-jane-street/open-roles/",
    "Citadel": "https://www.citadel.com/careers/open-roles/",
    "Citadel / Citadel Securities": "https://www.citadel.com/careers/open-roles/",
    "Citadel Securities": "https://www.citadelsecurities.com/careers/open-roles/",
    "Jump Trading": "https://www.jumptrading.com/careers/",
    "Hudson River Trading (HRT)": "https://www.hudsonrivertrading.com/careers/",
    "Hudson River Trading": "https://www.hudsonrivertrading.com/careers/",
    "Optiver": "https://optiver.com/working-at-optiver/career-opportunities/",
    "DRW": "https://drw.com/careers",
    "Five Rings LLC": "https://fiverings.com/careers/",
    "Five Rings": "https://fiverings.com/careers/",
    "Akuna Capital": "https://akunacapital.com/careers",
    "IMC Trading": "https://careers.imctrading.com/",
    "Flow Traders": "https://www.flowtraders.com/careers",
    "SIG (Susquehanna International Group)": "https://sig.com/careers/",
    "SIG": "https://sig.com/careers/",
    "Virtu Financial": "https://www.virtu.com/careers/",
    "Old Mission Capital": "https://www.oldmissioncapital.com/careers/",
    "Tower Research Capital": "https://www.tower-research.com/open-positions",
    "Valkyrie Trading": "https://valkyrietrading.com/careers/",
    "Volant Trading": "https://volanttrading.com/careers/",
    "TransMarket Group": "https://www.transmarketgroup.com/careers",
    "Transmarket Group": "https://www.transmarketgroup.com/careers",
    "Belvedere Trading": "https://belvederetrading.com/careers/",
    "Geneva Trading": "https://genevatrading.com/careers/",
    "Peak6 Investments": "https://peak6.com/careers/",
    "PEAK6": "https://peak6.com/careers/",
    "DV Trading": "https://dvtrading.co/careers/",
    "Maven Securities": "https://www.mavensecurities.com/careers/",
    "All Options Trading": "https://www.alloptions.nl/careers/",
    "Consolidated Trading": "https://www.consolidatedtrading.com/careers/",
    "HAP Capital": "https://hapcap.com/careers/",
    "Teza Technologies": "https://www.teza.com/careers/",
    "Headlands Technologies": "https://www.headlandstech.com/careers/",
    "XR Trading": "https://www.xrtrading.com/careers/",
    "Wolverine Trading": "https://www.wolve.com/careers",
    "Group One Trading": "https://www.group1.com/careers",
    "Radix Trading": "https://www.radixtrading.com/careers/",

    # Quantitative Hedge Funds
    "Two Sigma": "https://www.twosigma.com/careers/",
    "Millennium Management": "https://www.mlpm.com/careers/",
    "Point72": "https://point72.com/careers/",
    "Cubist Systematic Strategies": "https://point72.com/cubist-systematic-strategies/",
    "Balyasny Asset Management": "https://www.bamfunds.com/careers",
    "ExodusPoint Capital Management": "https://www.exoduspoint.com/careers/",
    "ExodusPoint Capital": "https://www.exoduspoint.com/careers/",
    "Schonfeld Strategic Advisors": "https://www.schonfeld.com/careers/",
    "AQR Capital Management": "https://www.aqr.com/Careers",
    "D.E. Shaw": "https://www.deshaw.com/careers",
    "D.E. Shaw & Co.": "https://www.deshaw.com/careers",
    "Bridgewater Associates": "https://www.bridgewater.com/careers",
    "Man Group (AHL / Numeric)": "https://www.man.com/careers",
    "Man Group": "https://www.man.com/careers",
    "WorldQuant": "https://www.worldquant.com/career/",
    "Verition Fund Management": "https://verition.com/careers/",
    "Qube Research & Technologies": "https://www.qube-rt.com/careers/",
    "Squarepoint Capital": "https://www.squarepoint-capital.com/careers",
    "Capstone Investment Advisors": "https://capstoneia.com/careers/",
    "Engineers Gate": "https://www.eg-lp.com/careers/",
    "Quantbot Technologies": "https://www.quantbot.com/careers/",
    "Viking Global Investors": "https://www.vikingglobal.com/careers/",
    "MIO Partners": "https://www.miopartners.com/careers/",
    "McKinsey (MIO Partners)": "https://www.miopartners.com/careers/",
    "HBK Capital Management": "https://www.hbk.com/careers/",
    "AXQ Capital": "https://www.axqcap.com/",
    "Brevan Howard": "https://www.brevanhoward.com/careers/",
    "Rokos Capital Management": "https://www.rokoscapital.com/careers/",
    "Trexquant Investment": "https://www.trexquant.com/careers",
    "One William Street Capital Management": "https://www.onewilliamstreet.com/careers/",
    "Caxton Associates": "https://www.caxton.com/careers/",
    "Element Capital Management": "https://www.elementcap.com/careers/",
    "Graham Capital Management": "https://www.grahamcapital.com/careers/",
    "Sculptor Capital Management": "https://www.sculptor.com/careers",
    "Farallon Capital Management": "https://www.faralloncapital.com/careers/",
    "Aetos Alternatives Management": "https://www.aetos.com/",
    "Aigen Investment Management": "https://www.aigeninvestments.com/",
    "Bopu Fund": "https://www.bopufund.com/",
    "SciFeCap": "https://www.scifecap.com/",
    "Secor Asset Management": "https://www.secor-am.com/careers/",
    "Shanghai Yanfu Investments": "https://www.yanfuinvestments.com/",
    "3iC Capital Group": "https://www.3iccapital.com/",

    # FinTech & Frontier Tech Giants
    "Stripe": "https://stripe.com/jobs",
    "Databricks": "https://www.databricks.com/company/careers",
    "Anthropic": "https://www.anthropic.com/careers",
    "OpenAI": "https://openai.com/careers/",
    "Palantir Technologies": "https://www.palantir.com/careers/",
    "Palantir": "https://www.palantir.com/careers/",
    "Robinhood": "https://careers.robinhood.com/",
    "Coinbase": "https://www.coinbase.com/careers",
    "Plaid": "https://plaid.com/careers/",
    "Ramp": "https://ramp.com/careers",
    "Brex": "https://www.brex.com/careers",
    "Scale AI": "https://scale.com/careers",
    "Snowflake": "https://careers.snowflake.com/",
    "Block (Cash App)": "https://block.xyz/careers",
    "Chime": "https://careers.chime.com/",
    "SoFi": "https://www.sofi.com/careers/",
    "Upstart": "https://www.upstart.com/careers",
    "MerQube": "https://merqube.com/careers/",
    "Numerix": "https://www.numerix.com/careers",
    "Google DeepMind": "https://deepmind.google/about/careers/",
    "Amazon": "https://www.amazon.jobs/",
    "Apple": "https://jobs.apple.com/",
    "Microsoft": "https://careers.microsoft.com/",
    "Meta": "https://www.metacareers.com/",
    "Cisco Systems": "https://jobs.cisco.com/",
    "Oracle": "https://www.oracle.com/careers/",
    "Uber": "https://www.uber.com/careers",
    "Spotify": "https://www.lifeatspotify.com/jobs",
    "Waymo": "https://waymo.com/careers/",
    "Fireworks AI": "https://fireworks.ai/company/careers",
    "GrayScale": "https://grayscale.com/careers/",
    "Iconiq Capital": "https://iconiqcapital.com/careers",
    "Conversion Capital": "https://conversioncapital.com/",
    "Beacon Platform": "https://www.beacon.io/careers/",
    "TIFIN": "https://tifin.com/careers/",

    # Bulge Bracket & Global Investment Banks
    "Goldman Sachs": "https://www.goldmansachs.com/careers/students/",
    "Morgan Stanley": "https://www.morganstanley.com/people-opportunities/students-graduates",
    "JPMorgan Chase & Co.": "https://careers.jpmorgan.com/us/en/students/programs",
    "J.P. Morgan": "https://careers.jpmorgan.com/us/en/students/programs",
    "Bank of America": "https://campus.bankofamerica.com/",
    "Bank of America Merrill Lynch": "https://campus.bankofamerica.com/",
    "Citigroup": "https://jobs.citi.com/university",
    "Barclays": "https://home.barclays/careers/our-firm/early-careers/",
    "UBS": "https://www.ubs.com/global/en/careers.html",
    "Deutsche Bank": "https://careers.db.com/students-graduates/",
    "Jefferies": "https://www.jefferies.com/careers/",
    "Credit Suisse": "https://www.credit-suisse.com/careers",
    "BNP Paribas": "https://group.bnpparibas/en/careers",
    "Societe Generale": "https://careers.societegenerale.com/",
    "Nomura": "https://www.nomuragroup.com/careers/",
    "RBC Capital Markets": "https://www.rbccm.com/en/careers/",
    "Wells Fargo": "https://www.wellsfargojobs.com/university-programs",
    "Macquarie Group": "https://www.macquarie.com/careers",
    "Evercore": "https://www.evercore.com/careers/",
    "Houlihan Lokey": "https://hl.com/careers/",
    "Lazard": "https://www.lazard.com/careers/",
    "Moelis & Company": "https://www.moelis.com/careers/",
    "Cantor Fitzgerald": "https://www.cantor.com/careers/",
    "Haitong International Securities": "https://www.htisec.com/en-us/careers",

    # Systematic Asset Management & Allocators
    "BlackRock": "https://careers.blackrock.com/early-careers",
    "PIMCO": "https://www.pimco.com/en-us/our-firm/careers/",
    "AllianceBernstein": "https://www.alliancebernstein.com/corporate/en/careers.html",
    "Allspring Global Investments": "https://www.allspringglobal.com/careers/",
    "American Century Investments": "https://www.americancentury.com/careers/",
    "Blackstone": "https://www.blackstone.com/careers/",
    "Columbia Threadneedle": "https://www.columbiathreadneedle.com/careers/",
    "DWS Group": "https://www.dws.com/en-us/our-profile/careers/",
    "Federated Hermes": "https://www.federatedhermes.com/us/careers",
    "Franklin Templeton": "https://www.franklintempleton.com/careers",
    "GMO": "https://www.gmo.com/americas/careers/",
    "Glenmede": "https://www.glenmede.com/careers/",
    "Invesco": "https://www.invesco.com/corporate/careers",
    "J.P. Morgan Asset Management": "https://careers.jpmorgan.com/",
    "Lord Abbett": "https://www.lordabbett.com/en/about-us/careers.html",
    "Neuberger Berman": "https://www.nb.com/en/global/careers",
    "Northern Trust": "https://www.northerntrust.com/united-states/about-us/careers",
    "Nuveen": "https://www.nuveen.com/global/about-us/careers",
    "PGIM": "https://www.pgim.com/careers",
    "Principal Financial Group": "https://www.principal.com/about-us/careers",
    "Russell Investments": "https://russellinvestments.com/us/careers",
    "State Street": "https://www.statestreet.com/us/en/asset-management/about/careers",
    "State Street Global Advisors": "https://www.statestreet.com/careers",
    "TCW Group": "https://www.tcw.com/About-TCW/Careers",
    "TIAA": "https://www.tiaa.org/public/about-tiaa/careers",
    "T. Rowe Price": "https://www.troweprice.com/corporate/us/en/careers.html",
    "Vanguard": "https://www.vanguardjobs.com/",
    "Wellington Management": "https://www.wellington.com/en/careers",
    "Western Asset Management": "https://www.westernasset.com/us/en/about-us/careers.cfm",

    # Commodities & Energy Trading Desks
    "Trafigura": "https://www.trafigura.com/careers/",
    "Mercuria": "https://www.mercuria.com/careers/",
    "Castleton Commodities International": "https://www.cci.com/careers/",
    "Vitol": "https://www.vitol.com/careers/",
    "Glencore": "https://www.glencore.com/careers",
    "BP": "https://www.bp.com/en/global/corporate/careers.html",
    "Shell": "https://www.shell.com/careers.html",
    "Cargill": "https://careers.cargill.com/",
    "Freepoint Commodities": "https://www.freepoint.com/careers/",
    "SESCO": "https://www.sescoenterprises.com/careers",

    # Financial Data & Market Utilities
    "Bloomberg LP": "https://www.bloomberg.com/company/careers/",
    "Bloomberg": "https://www.bloomberg.com/company/careers/",
    "CME Group": "https://www.cmegroup.com/careers.html",
    "FactSet": "https://careers.factset.com/",
    "S&P Global": "https://careers.spglobal.com/",
    "MSCI": "https://www.msci.com/careers",
    "Options Clearing Corporation (OCC)": "https://www.theocc.com/Careers",
    "Intercontinental Exchange (ICE)": "https://www.theice.com/careers",
    "Fitch Ratings": "https://www.fitchratings.com/careers",
    "Moody's": "https://careers.moodys.com/",

    # Commercial Banking & Consulting
    "Accenture": "https://www.accenture.com/us-en/careers",
    "Boston Consulting Group (BCG)": "https://careers.bcg.com/",
    "McKinsey & Company": "https://www.mckinsey.com/careers",
    "McKinsey & Company (QuantumBlack)": "https://www.mckinsey.com/capabilities/quantumblack/how-we-work/careers",
    "Ernst & Young (EY)": "https://www.ey.com/en_us/careers",
    "PwC": "https://www.pwc.com/us/en/careers.html",
    "Deloitte": "https://www2.deloitte.com/us/en/pages/careers/careers.html",
    "KPMG": "https://www.kpmg.us/careers.html",
    "Oliver Wyman": "https://www.oliverwyman.com/careers.html",
    "Capital One": "https://www.capitalonecareers.com/",
    "American Express": "https://www.americanexpress.com/en-us/careers/",
    "Discover Financial Services": "https://jobs.discover.com/",
    "U.S. Bank": "https://www.usbank.com/careers.html",
    "PNC Financial Services": "https://careers.pnc.com/",
    "Truist Financial": "https://careers.truist.com/",
    "Citizens Bank": "https://jobs.citizensbank.com/",
    "Fifth Third Bank": "https://www.53.com/content/fifth-third/en/careers.html",
    "KeyBank": "https://www.key.com/about/careers/careers.jsp",
    "M&T Bank": "https://www.mtb.com/careers",
    "Federal Reserve System": "https://www.federalreserve.gov/careers.htm",
    "Federal Reserve Bank of New York": "https://www.newyorkfed.org/careers",
    "U.S. Securities and Exchange Commission (SEC)": "https://www.sec.gov/careers",
}

def derive_default_url(firm_name: str, discovered_boards: dict) -> str:
    """Derives a clean official career URL if not in curated list."""
    # 1. Check discovered ATS boards
    if firm_name in discovered_boards:
        info = discovered_boards[firm_name]
        ats = info.get("ats")
        tok = info.get("token")
        if ats == "greenhouse":
            return f"https://boards.greenhouse.io/{tok}"
        elif ats == "lever":
            return f"https://jobs.lever.co/{tok}"
        elif ats == "ashby":
            return f"https://jobs.ashbyhq.com/{tok}"

    # 2. Derive standard corporate domain
    clean = re.sub(r"\(.*?\)", "", firm_name).strip()
    clean = re.sub(r"\b(LLC|Inc\.?|Corp\.?|Capital|Management|Group|Securities|Partners|Asset Management|Investments?)\b", "", clean, flags=re.I).strip()
    slug = re.sub(r"[^a-zA-Z0-9]", "", clean).lower()
    if len(slug) >= 3:
        return f"https://www.{slug}.com/careers"
    
    return f"https://www.google.com/search?q={clean.replace(' ', '+')}+careers"

def populate_target_firms_urls(csv_path: str, discovered_json_path: str):
    """Adds official_careers_url column to target_firms.csv."""
    discovered = {}
    if os.path.exists(discovered_json_path):
        try:
            with open(discovered_json_path, "r", encoding="utf-8") as f:
                discovered = json.load(f)
        except Exception:
            pass

    # Read all rows into memory first
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn for fn in reader.fieldnames if fn is not None]
        raw_rows = list(reader)

    if "official_careers_url" not in fieldnames:
        fieldnames.append("official_careers_url")

    processed_rows = []
    for row in raw_rows:
        clean_row = {k: v for k, v in row.items() if k is not None}
        fn = clean_row.get("firm_name", "").strip()
        if not fn:
            continue
        # Match in known URLs
        url = KNOWN_CAREER_URLS.get(fn)
        if not url:
            for k, v in KNOWN_CAREER_URLS.items():
                if k.lower() == fn.lower() or k.lower() in fn.lower():
                    url = v
                    break
        if not url:
            url = derive_default_url(fn, discovered)

        clean_row["official_careers_url"] = url
        processed_rows.append(clean_row)

    # Now write processed rows safely
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(processed_rows)

    print(f"Successfully populated official_careers_url for {len(processed_rows)} firms in {csv_path}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base, "data", "target_firms.csv")
    disc_json = os.path.join(base, "data", "discovered_ats_boards.json")
    populate_target_firms_urls(target_csv, disc_json)

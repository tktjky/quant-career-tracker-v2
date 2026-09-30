import os
import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from agent.crawl_agent import CrawlAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("V2Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
DATA_DIR = os.path.join(BASE_DIR, "data")
OPENINGS_FILE = os.path.join(DATA_DIR, "live_openings.json")

class V2DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/openings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if os.path.exists(OPENINGS_FILE):
                with open(OPENINGS_FILE, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                empty_payload = json.dumps({"openings": [], "stats": {}, "last_updated": None})
                self.wfile.write(empty_payload.encode("utf-8"))
            return

        elif self.path == "/data.js":
            # Provide data.js dynamically from live_openings.json
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.end_headers()
            data_str = "{}"
            if os.path.exists(OPENINGS_FILE):
                with open(OPENINGS_FILE, "r", encoding="utf-8") as f:
                    data_str = f.read()
            self.wfile.write(f"window.LIVE_OPENINGS_DATA = {data_str};".encode("utf-8"))
            return

        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            status_payload = {
                "server": "Quant Career Intelligence v2 Server",
                "status": "online",
                "data_file_exists": os.path.exists(OPENINGS_FILE)
            }
            self.wfile.write(json.dumps(status_payload).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == "/api/crawl":
            firm = query_params.get("firm", [None])[0]
            logger.info(f"Received POST /api/crawl request (Firm: {firm or 'ALL'}). Triggering CrawlAgent...")
            try:
                agent = CrawlAgent()
                if firm:
                    result = agent.crawl_single_firm(firm)
                else:
                    result = agent.run_crawl()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                logger.error(f"Error executing crawl: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port: int = 8081):
    server_address = ("", port)
    httpd = HTTPServer(server_address, V2DashboardHandler)
    print("\n" + "=" * 70)
    print(f"  Quant Career Intelligence v2 Web Dashboard (Live Openings)")
    print(f"  Dashboard URL: http://localhost:{port}")
    print(f"  Crawl API:     http://localhost:{port}/api/crawl")
    print(f"  Target Cohort: Quantitative Finance (Class of 2027)")
    print("  Press Ctrl+C to terminate server.")
    print("=" * 70 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server gracefully...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()

#!/usr/bin/env python3
"""保定学院校园导览 - API 代理服务器"""
import http.server
import json
import urllib.request
import urllib.parse
import os
import sys

BAIDU_TOKEN = os.environ.get("BAIDU_MAP_AUTH_TOKEN", "")
BASE_URL = "https://api.map.baidu.com/agent_plan/v1"
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baoding_college_map_v4.html")

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API 代理
        if self.path.startswith("/api/"):
            self._proxy_api("GET")
            return
        # 静态文件
        if self.path == "/" or self.path == "":
            self.path = "/baoding_college_map_v4.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy_api("POST")
            return
        self.send_error(404)

    def _proxy_api(self, method):
        # 解析目标 API
        # /api/place → /agent_plan/v1/place
        target = self.path.replace("/api/", "/agent_plan/v1/")
        url = f"https://api.map.baidu.com{target}"

        # 读取请求体
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b""

        # 处理 GET 参数
        if method == "GET" and "?" in self.path:
            _, qs = self.path.split("?", 1)
            url += "?" + qs
            body = None

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {BAIDU_TOKEN}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def main():
    if not BAIDU_TOKEN:
        print("错误: 请先设置环境变量 BAIDU_MAP_AUTH_TOKEN")
        sys.exit(1)

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print(f"保定学院校园导览服务已启动")
    print(f"访问地址: http://localhost:{port}")
    print(f"Token 已加载: {BAIDU_TOKEN[:20]}...")

    server = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.shutdown()

if __name__ == "__main__":
    main()

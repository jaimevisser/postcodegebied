import http.server
import socketserver
import webbrowser


def start_web_server(port):
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"Web server started on port {port}. Press Ctrl+C to stop.")
        webbrowser.open(f"http://localhost:{port}/map.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        print("Web server stopped.")
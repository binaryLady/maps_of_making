"""Minimal SPARQL 1.1 Protocol server backed by pyoxigraph.

Stands in for the ghcr.io/oxigraph/oxigraph container in environments that
cannot pull container images. Implements exactly the surface the app uses:

  GET  /health           — liveness (load_ontology.sh probes this)
  POST /query            — Content-Type: application/sparql-query → JSON results
  POST /update           — Content-Type: application/sparql-update
  PUT  /store?graph=<g>  — Graph Store Protocol replace-graph with Turtle

Persists to the same location the container bind-mounts: data/oxigraph/.
Run: venv/bin/python local_run/oxigraph_server.py [--port 7878] [--location data/oxigraph]
"""
import argparse
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import pyoxigraph as ox

store = None
write_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body=b"", ctype="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, b"ok")
        elif path == "/query":
            qs = parse_qs(urlparse(self.path).query)
            q = (qs.get("query") or [None])[0]
            if not q:
                self._send(400, b"missing query")
            else:
                self._run_query(q)
        else:
            self._send(404, b"not found")

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body().decode("utf-8")
        try:
            if path == "/query":
                self._run_query(body)
            elif path == "/update":
                with write_lock:
                    store.update(body)
                    store.flush()
                self._send(204)
            else:
                self._send(404, b"not found")
        except Exception as e:  # surface SPARQL errors like oxigraph does: 400 + message
            self._send(400, str(e).encode())

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path != "/store":
            self._send(404, b"not found")
            return
        graph = (parse_qs(parsed.query).get("graph") or [None])[0]
        body = self._body()
        ctype = (self.headers.get("Content-Type") or "text/turtle").split(";")[0].strip()
        fmt = ox.RdfFormat.from_media_type(ctype) or ox.RdfFormat.TURTLE
        target = ox.NamedNode(graph) if graph else ox.DefaultGraph()
        try:
            with write_lock:
                existed = graph is not None and store.contains_named_graph(target)
                if existed:
                    store.clear_graph(target)
                store.load(body, format=fmt, to_graph=target)
                store.flush()
            self._send(204 if existed else 201)
        except Exception as e:
            self._send(400, str(e).encode())

    def _run_query(self, q):
        results = store.query(q)
        body = results.serialize(format=ox.QueryResultsFormat.JSON)
        self._send(200, body, "application/sparql-results+json")

    def log_message(self, fmt, *args):  # keep stdout terse; errors still raise
        pass


def main():
    global store
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7878)
    ap.add_argument("--location", default="data/oxigraph")
    args = ap.parse_args()
    store = ox.Store(args.location)
    print(f"oxigraph (pyoxigraph {ox.__version__}) serving {args.location} on :{args.port}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

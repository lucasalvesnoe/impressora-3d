"""HTTPS local: serve index.html e grava cada POST /frame em cam2.jpg (camera do 2o iPhone)."""
import http.server, ssl, os, threading
D = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=D, **k)
    def log_message(s, *a): pass
    def do_POST(s):
        try:
            n = int(s.headers.get('Content-Length', 0))
            if n > 0:
                b = s.rfile.read(n)
                tmp = os.path.join(D, f'cam2_{threading.get_ident()}.tmp')
                with open(tmp, 'wb') as f:
                    f.write(b)
                from urllib.parse import parse_qs, urlparse
                nome = parse_qs(urlparse(s.path).query).get('nome', ['cam2'])[0]
                nome = nome if nome.isalnum() else 'cam2'      # ?nome=frente grava frente.jpg (outro iPhone)
                os.replace(tmp, os.path.join(D, nome + '.jpg'))
            s.send_response(204)
            s.end_headers()
        except Exception as e:
            try:
                s.send_response(500)
                s.end_headers()
            except Exception:
                pass
srv = http.server.ThreadingHTTPServer(('0.0.0.0', 8443), H)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(os.path.join(D, 'cert.pem'), os.path.join(D, 'key.pem'))
srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
srv.serve_forever()


from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import mimetypes, os

class Handler(SimpleHTTPRequestHandler):
    def guess_type(self, path):
        if path.endswith(".pbf"):
            return "application/x-protobuf"
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        ctype = self.guess_type(path)
        self.send_header("Content-Type", ctype)
        # ใส่ Content-Encoding: gzip เฉพาะไฟล์ที่เป็น gzip จริง ๆ
        head = f.read(2); f.seek(0)
        if path.endswith(".pbf") and head == b"\x1f\x8b":
            self.send_header("Content-Encoding", "gzip")
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs.st_size))
        self.end_headers()
        return f

if __name__ == "__main__":
    os.chdir("/mnt/c/Users/wongs/OneDrive/Desktop/DemoIndoor")
    ThreadingHTTPServer(("", 8000), Handler).serve_forever()

"""Task-local review server with byte ranges for real video seeking."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re


class ReviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            return super().send_head()
        stream = path.open('rb')
        size = path.stat().st_size
        value = self.headers.get('Range')
        start, end = 0, size - 1
        if value:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
            try:
                if not match or not any(match.groups()):
                    raise ValueError('invalid range')
                first, last = match.groups()
                if first:
                    start = int(first)
                    end = min(int(last), size - 1) if last else size - 1
                else:
                    suffix = int(last)
                    if suffix <= 0:
                        raise ValueError('invalid suffix')
                    start = max(0, size - suffix)
                if start > end or start >= size:
                    raise ValueError('unsatisfiable range')
            except ValueError:
                stream.close()
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return None
            self.byte_range = start, end
        self.send_response(206 if value else 200)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Last-Modified', self.date_time_string(path.stat().st_mtime))
        if value:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        start, end = self.byte_range
        source.seek(start)
        remaining = end - start + 1
        while remaining:
            data = source.read(min(remaining, 1024 * 1024))
            if not data:
                break
            outputfile.write(data)
            remaining -= len(data)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[3]
    handler = partial(ReviewHandler, directory=str(root))
    ThreadingHTTPServer(('127.0.0.1', 8876), handler).serve_forever()

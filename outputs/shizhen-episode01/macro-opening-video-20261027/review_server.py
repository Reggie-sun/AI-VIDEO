"""Reuse the existing byte-range review handler for this task's local playback."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
import importlib.util
root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('shizhen_existing_review',root/'outputs/shizhen-episode01/opening-world-title-20261026/review_server.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8883),partial(m.ReviewHandler,directory=str(root))).serve_forever()

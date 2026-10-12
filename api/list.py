"""GET /api/list?folder=<Google Drive folder link or id>

The videos in a Google Drive folder shared with anyone who has the link,
subfolders included, as JSON for the page:

    {"folder": "<id>", "name": "<folder name>",
     "videos": [{"id": "<file id>", "name": "<full file name>", "path": ["<subfolder>", ...]}]}

A web page cannot read a Drive folder without a Google API key, but the
folder's public embeddable view can be read from here without one. Each video
keeps the chain of folder names it sits in; the page sorts the list itself.
Stdlib only.
"""
import html.parser
import json
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

VIEW = "https://drive.google.com/embeddedfolderview?id={}"
VIDEO_NAME = re.compile(r"\.(mp4|m4v|mov|webm|mkv|avi|wmv|flv|mpe?g|3gp|ts|mts|m2ts)$", re.I)
MAX_FOLDERS = 100  # one request each; a bigger tree would outlast the function


def folder_id(text):
    """The folder id from a link in any of the shapes Drive hands out, or a bare id."""
    text = text.strip()
    match = (re.search(r"/folders/([\w-]{10,})", text) or re.search(r"[?&]id=([\w-]{10,})", text)
             or re.fullmatch(r"([\w-]{10,})", text))
    return match.group(1) if match else ""


class FolderView(html.parser.HTMLParser):
    """The entries of one folder view, each with its id, link, icon and full
    title, and the folder's own name from <title>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.name = ""
        self.entries = []
        self._entry = None
        self._depth = 0        # <div>s open inside the current entry
        self._title_at = 0     # depth of the entry's title <div>, 0 outside it
        self._in_name = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_name = True
        elif tag == "div":
            classes = (attrs.get("class") or "").split()
            ident = attrs.get("id") or ""
            if self._entry is None:
                if "flip-entry" in classes and ident.startswith("entry-"):
                    self._entry = {"id": ident[len("entry-"):], "href": "", "icon": "", "title": ""}
                    self.entries.append(self._entry)
                    self._depth = 1
                return
            self._depth += 1
            if "flip-entry-title" in classes:
                self._title_at = self._depth
        elif self._entry is not None:
            if tag == "a" and not self._entry["href"]:
                self._entry["href"] = attrs.get("href") or ""
            elif tag == "img" and not self._entry["icon"]:
                self._entry["icon"] = attrs.get("src") or ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_name = False
        elif tag == "div" and self._entry is not None:
            if self._depth == self._title_at:
                self._title_at = 0
            self._depth -= 1
            if self._depth == 0:
                self._entry = None

    def handle_data(self, data):
        if self._in_name:
            self.name += data
        elif self._entry is not None and self._title_at:
            self._entry["title"] += data


def read(folder):
    request = urllib.request.Request(VIEW.format(folder), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        view = FolderView()
        view.feed(response.read().decode("utf-8", "replace"))
    return view


def target(entry):
    """The id the entry's link opens. For a shortcut that is the file or folder
    it points to, not the shortcut itself."""
    match = re.search(r"/(?:folders|file/d)/([\w-]+)", entry["href"])
    return match.group(1) if match else entry["id"]


def collect(folder, path, videos, seen):
    """Adds the folder's videos to videos and returns the folder's name."""
    seen.add(folder)  # a shortcut can point back up the tree
    view = read(folder)
    for entry in view.entries:
        title = entry["title"].strip()
        if "/folders/" in entry["href"] or "vnd.google-apps.folder" in entry["icon"]:
            if target(entry) not in seen and len(seen) < MAX_FOLDERS:
                collect(target(entry), path + [title], videos, seen)
        elif "/type/video/" in entry["icon"] or VIDEO_NAME.search(title):
            videos.append({"id": target(entry), "name": title, "path": path})
    return re.sub(r"\s+[-–]\s+(Google Drive|Dysk Google)$", "", view.name.strip())


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        folder = folder_id(parse_qs(urlparse(self.path).query).get("folder", [""])[0])
        if not folder:
            return self.reply(400, {"error": "not a folder link"})
        videos = []
        try:
            name = collect(folder, [], videos, set())
        except urllib.error.HTTPError as error:
            return self.reply(404 if error.code == 404 else 502, {"error": f"Drive answered {error.code}"})
        except (urllib.error.URLError, TimeoutError):
            return self.reply(502, {"error": "Drive did not answer"})
        # A list is cached for a few minutes, so new videos show up soon after
        # they are added. An empty one is not: it usually means the folder is
        # not shared yet, and that gets fixed and retried at once.
        self.reply(200, {"folder": folder, "name": name, "videos": videos}, cache=bool(videos))

    def reply(self, status, body, cache=False):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, s-maxage=300, stale-while-revalidate=86400" if cache else "no-store")
        self.end_headers()
        self.wfile.write(data)

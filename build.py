from argparse import ArgumentParser
from pathlib import Path, PurePosixPath
import subprocess
from urllib.parse import urlparse, urlunparse
from html5lib import parse, serialize

wix_root_url = "https://katarinaquartet.wixsite.com/"

crawl_dir = Path("crawl")
out_dir = Path("docs")

html_files = [
]

def pick_file_path(name):
	base = PurePosixPath(name)
	if base.suffix == ".html":
		return base
	else:
		return base.joinpath("index.html")

html_files = [(PurePosixPath("/website").joinpath(item), pick_file_path(item)) for item in [
	"",
	"about",
	"calendar",
	"contact",
	"media",
	"photo-2",
	"photo1"
]]

def do_crawl():
	for (url_path, file_path) in html_files:
		url_components = list(urlparse(wix_root_url))
		url_components[2] = str(url_path)
		full_url = urlunparse(url_components)
		file_path = crawl_dir.joinpath(file_path)
		file_path.parent.mkdir(parents=True, exist_ok=True)
		subprocess.run(["wget", "-O", file_path, "--", full_url], check=True)

def do_build():
	for (url_path, file_path) in html_files:
		file_path = Path(file_path)
		out_path = out_dir.joinpath(file_path)
		out_path.parent.mkdir(parents=True, exist_ok=True)
		with crawl_dir.joinpath(file_path).open("r") as in_file, out_path.open("w") as out_file:
			html = parse(in_file, treebuilder="dom")
			xfrm_traverse(url_path, html)
			out_file.write(serialize(html, tree="dom"))

def xfrm_traverse(url_path, dom_node):
	if dom_node.nodeType == 1:
		if dom_node.nodeName == "a":
			href_components = list(urlparse(dom_node.getAttribute("href")))
			href_path = PurePosixPath(href_components[2])
			if href_components[1] == "katarinaquartet.wixsite.com" and href_path.is_relative_to("/website"):
				href_components[:3] = ("", "", str(super_relativize(href_path, url_path)))
				dom_node.setAttribute("href", urlunparse(href_components))
		elif dom_node.nodeName == "link" and dom_node.getAttribute("href") == "https://www.wix.com/favicon.ico":
			dom_node.parentNode.removeChild(dom_node)
		elif dom_node.getAttribute("id") == "WIX_ADS":
			dom_node.parentNode.removeChild(dom_node)
	for child in dom_node.childNodes:
		xfrm_traverse(url_path, child)

# Make an absolute path relative to another absolute path, using ".." segments when necessary
def super_relativize(path, base):
	trail = PurePosixPath("")
	for _ in range(10000):
		if path.is_relative_to(base):
			return trail.joinpath(path.relative_to(base))
		assert base != base.parent
		base = base.parent
		trail = trail.joinpath("..")
	raise RuntimeError("path has too many segments")

def main():
	parser = ArgumentParser()
	parser.add_argument("--crawl", action="store_true")
	parser.add_argument("--build", action="store_true")
	args = parser.parse_args()
	no_action_given = not any([args.crawl, args.build])
	if args.crawl or no_action_given:
		do_crawl()
	if args.build or no_action_given:
		do_build()

if __name__ == "__main__":
	main()

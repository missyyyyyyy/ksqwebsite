from argparse import ArgumentParser
from pathlib import Path, PurePosixPath
import subprocess
from urllib.parse import urlparse, urlunparse
from html5lib import parse, serialize

wix_root_url = "https://katarinaquartet.wixsite.com/"

crawl_dir = Path("crawl")
out_dir = Path("docs")

html_files = [(PurePosixPath(v0), Path(v1)) for (v0, v1) in (
	("/website", "index.html"),
	("/website/about", "about"),
	("/website/calendar", "calendar"),
	("/website/contact", "contact"),
	("/website/media", "media"),
	("/website/photo-2", "photo-2"),
	("/website/photo1", "photo1")
)]

def do_crawl():
	crawl_dir.mkdir(exist_ok=True)
	for (url_path, file_path) in html_files:
		url_components = list(urlparse(wix_root_url))
		url_components[2] = str(url_path)
		full_url = urlunparse(url_components)
		subprocess.run(["wget", "-O", crawl_dir.joinpath(file_path), "--", full_url], check=True)

def do_build():
	out_dir.mkdir(exist_ok=True)
	for (url_path, file_path) in html_files:
		file_path = Path(file_path)
		with crawl_dir.joinpath(file_path).open("r") as in_file, out_dir.joinpath(file_path).open("w") as out_file:
			html = parse(in_file, treebuilder="dom")
			xfrm_traverse(html)
			out_file.write(serialize(html, tree="dom"))

def xfrm_traverse(dom_node):
	if dom_node.nodeType == 3:
		if dom_node.nodeName == "a":
			href_components = list(urlparse(href_attr.getAttributeNode("href")))
			href_path = PurePosixPath(href_components[2])
			if href_components[1] == "katarinaquartet.wixsite.com" and href_components[2].is_relative_to("/website"):
				href_components[3:] = ("", "", str(href_components[2].relative_to("/website")))
				href_attr.nodeValue = urlunparse(href_components)
		elif dom_node.nodeName == "link" and dom_node.getAttribute("href") == "https://www.wix.com/favicon.ico":
			dom_node.parentNode.removeChild(dom_node)
		elif dom_node.getAttribute("id") == "WIX_ADS":
			dom_node.parentNode.removeChild(dom_node)
		for child in dom_node.childNodes:
			xfrm_traverse(child)

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

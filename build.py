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

yt_embeds = {
	"comp-lufug0sf": "VtzwB9atbb8",
	"comp-lufukhkz": "EYs9HHpQd1o",
	"comp-lufujfzk": "Ce6ikVuxyBU",
	"comp-lufuoh59": "sYBkxy6Dh_w"
}

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
		if dom_node.tagName == "a":
			href_components = list(urlparse(dom_node.getAttribute("href")))
			href_path = PurePosixPath(href_components[2])
			if href_components[1] == "katarinaquartet.wixsite.com" and href_path.is_relative_to("/website"):
				href_components[:3] = ("", "", str(super_relativize(href_path, url_path)))
				dom_node.setAttribute("href", urlunparse(href_components))
		elif dom_node.tagName == "link" and dom_node.getAttribute("href") == "https://www.wix.com/favicon.ico":
			dom_node.parentNode.removeChild(dom_node)
		elif dom_node.getAttribute("id") == "WIX_ADS":
			dom_node.parentNode.removeChild(dom_node)
		elif dom_node.tagName == "img" and dom_node.getAttribute("src") == "https://static.wixstatic.com/media/377e36_949307df43a148dba4346538db3089d2~mv2.jpg/v1/fill/w_147,h_98,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_auto/377e36_949307df43a148dba4346538db3089d2~mv2.jpg":
			dom_node.setAttribute("src", "IMG_2944_crop.jpeg")
#		elif dom_node.getAttribute("data-src"):
#			dom_node.setAttribute("data-src", "IMG_2944_crop.jpeg")
		elif dom_node.getAttribute("class") == "cM88eO":
			dom_node.parentNode.removeChild(dom_node)
		elif 'lsvsgd2b' in dom_node.getAttribute("id"):
			dom_node.setAttribute("id", "")
			if dom_node.getAttribute("data-src"):
				dom_node.removeAttribute("data-src")
			if dom_node.getAttribute("class"):
				dom_node.removeAttribute("class")
		elif dom_node.tagName == "div" and dom_node.getAttribute("id") in yt_embeds:
			yt_vid = yt_embeds[dom_node.getAttribute("id")]
			yt_iframe = dom_node.ownerDocument.createElement("iframe")
			yt_iframe.setAttribute("allowfullscreen", "")
			yt_iframe.setAttribute("src", "https://www.youtube.com/embed/{}?autoplay=0&mute=0&controls=1&loop=0".format(yt_vid))
			yt_iframe.setAttribute("width", "100%")
			yt_iframe.setAttribute("height", "100%")
			yt_iframe.setAttribute("frameborder", "0")
			dom_node.appendChild(yt_iframe)
			#dom_node.setAttribute("id", "")
	for child in dom_node.childNodes:
		xfrm_traverse(url_path, child)
	if dom_node.nodeType == 1 and dom_node.tagName == "head":
		style_node = dom_node.ownerDocument.createElement("style")
		style_node.appendChild(dom_node.ownerDocument.createTextNode(
			":root { --wix-ads-height: 0 !important } .zbdMFh { display: block }"
		))
		dom_node.appendChild(style_node)

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

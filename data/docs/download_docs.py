import requests
from bs4 import BeautifulSoup
import os
import time

PAGES = [
    "https://docs.python.org/3/tutorial/index.html",
    "https://docs.python.org/3/library/functions.html",
    "https://docs.python.org/3/library/stdtypes.html",
    "https://docs.python.org/3/library/exceptions.html",
    "https://docs.python.org/3/library/os.html",
    "https://docs.python.org/3/library/os.path.html",
    "https://docs.python.org/3/library/sys.html",
    "https://docs.python.org/3/library/json.html",
    "https://docs.python.org/3/library/re.html",
    "https://docs.python.org/3/library/collections.html",
    "https://docs.python.org/3/library/itertools.html",
    "https://docs.python.org/3/library/functools.html",
    "https://docs.python.org/3/library/pathlib.html",
    "https://docs.python.org/3/library/datetime.html",
    "https://docs.python.org/3/library/typing.html",
    "https://docs.python.org/3/library/dataclasses.html",
    "https://docs.python.org/3/library/contextlib.html",
    "https://docs.python.org/3/library/logging.html",
    "https://docs.python.org/3/library/unittest.html",
    "https://docs.python.org/3/library/asyncio.html",
    "https://docs.python.org/3/reference/expressions.html",
    "https://docs.python.org/3/reference/compound_stmts.html",
    "https://docs.python.org/3/glossary.html",
]

def scrape_page(url: str) -> str:
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # remove navigation, headers, footers, TOC
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    
    # remove table of contents
    for tag in soup.find_all("div", {"class": "toctree-wrapper"}):
        tag.decompose()
    
    # get main content
    main = soup.find("div", {"role": "main"}) or soup.find("body")
    
    # process each paragraph/block element properly
    result = []
    
    for element in main.find_all(["p", "h1", "h2", "h3", "h4", "li", "dt", "dd", "pre"]):
        # get all text in this element joined properly
        text = " ".join(element.get_text().split())
        if text.strip():
            result.append(text.strip())
    
    return "\n\n".join(result)

def download_all():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    total = len(PAGES)
    
    for i, url in enumerate(PAGES, 1):
        page_name = url.split("/")[-1].replace(".html", "")
        output_path = os.path.join(output_dir, f"{page_name}.txt")
        
        if os.path.exists(output_path):
            print(f"[{i}/{total}] skipping {page_name} (already exists)")
            continue
        
        try:
            print(f"[{i}/{total}] downloading {page_name}...", end=" ")
            text = scrape_page(url)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"SOURCE: {url}\n\n")
                f.write(text)
            
            print(f"done ({len(text)} chars)")
            time.sleep(0.5)  # be polite to python.org
            
        except Exception as e:
            print(f"failed: {e}")

if __name__ == "__main__":
    download_all()
    print("\nall docs downloaded!")
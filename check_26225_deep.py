import urllib.request
import urllib.error
import re

# Check the readme and index files
urls = [
    "https://www.gutenberg.org/files/26225/26225-readme.txt",
    "https://www.gutenberg.org/files/26225/26225-index.html",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read(2000)
        print(f"=== {url} ===")
        print(f"HTTP {resp.status}, {len(data)} bytes read")
        print(data[:500].decode('utf-8', errors='replace'))
        print()
    except urllib.error.HTTPError as e:
        print(f"=== {url} === HTTP {e.code}")
    except Exception as e:
        print(f"=== {url} === Error: {e}")

# Check the full page for any text download link
req = urllib.request.Request("https://www.gutenberg.org/ebooks/26225", 
                             headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode('utf-8', errors='replace')

# Look for all download links more carefully
print("=== All links containing '26225' ===")
all_links = re.findall(r'href=["\']([^"\']*26225[^"\']*)["\']', html, re.IGNORECASE)
for link in all_links:
    print(f"  {link}")

# Look for the text download section specifically
print("\n=== Looking for 'Plain Text' or 'Text' download ===")
for match in re.finditer(r'.{0,200}(?:Plain\s*Text|text/plain|\.txt)[^<]{0,200}', html, re.IGNORECASE):
    print(f"  ...{match.group().strip()}...")

# Check if there's a "Download" section
print("\n=== Download section ===")
for match in re.finditer(r'<[^>]*download[^>]*>', html, re.IGNORECASE):
    print(f"  {match.group()}")

# Check for the actual text content - maybe it's embedded
print("\n=== Looking for book content ===")
# Check if the page itself contains the text
if 'useful' in html.lower() or 'phrase' in html.lower():
    # Find where the actual content might start
    for match in re.finditer(r'<body[^>]*>.*?</body>', html, re.IGNORECASE | re.DOTALL):
        body = match.group()
        # Check if body has substantial text
        text_only = re.sub(r'<[^>]+>', ' ', body)
        words = text_only.split()
        print(f"  Body has {len(words)} words")
        if len(words) > 100:
            print(f"  First 300 chars: {text_only[:300]}")
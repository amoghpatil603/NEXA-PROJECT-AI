<<<<<<< HEAD
import urllib.request
import urllib.error
import json

urls = [
    "https://www.gutenberg.org/ebooks/26225.txt.utf-8",
    "https://www.gutenberg.org/files/26225/26225.txt",
    "https://www.gutenberg.org/files/26225/26225-0.txt",
    "https://www.gutenberg.org/cache/epub/26225/pg26225.txt",
    "https://www.gutenberg.org/ebooks/26225.html.images",
    "https://www.gutenberg.org/files/26225/26225-h/26225-h.htm",
    "https://www.gutenberg.org/ebooks/26225",
    "https://www.gutenberg.org/cache/epub/26225/pg26225-images.html",
]

print("=== Testing 26225 endpoints ===")
for url in urls:
    try:
        req = urllib.request.Request(url, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"  {url}")
        print(f"    HTTP {resp.status} {resp.reason} ({resp.length if resp.length else '?'} bytes)")
        # If we get a 200, try to read a bit to verify it's text
        if resp.status == 200:
            try:
                full_req = urllib.request.Request(url)
                full_resp = urllib.request.urlopen(full_req, timeout=10)
                data = full_resp.read(500)
                print(f"    First 500 bytes: {data[:200]}...")
            except Exception as e2:
                print(f"    Read error: {e2}")
    except urllib.error.HTTPError as e:
        print(f"  {url}")
        print(f"    HTTP {e.code} {e.reason}")
    except Exception as e:
        print(f"  {url}")
        print(f"    Error: {e}")

# Also try the official page to see if it exists at all
print("\n=== Testing 26225 official page (GET) ===")
try:
    req = urllib.request.Request("https://www.gutenberg.org/ebooks/26225")
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read(2000).decode('utf-8', errors='replace')
    # Look for title
    import re
    title_match = re.search(r'<title>(.*?)</title>', data, re.IGNORECASE)
    if title_match:
        print(f"  Title: {title_match.group(1)}")
    else:
        print(f"  Response snippet: {data[:500]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code} {e.reason}")
except Exception as e:
=======
import urllib.request
import urllib.error
import json

urls = [
    "https://www.gutenberg.org/ebooks/26225.txt.utf-8",
    "https://www.gutenberg.org/files/26225/26225.txt",
    "https://www.gutenberg.org/files/26225/26225-0.txt",
    "https://www.gutenberg.org/cache/epub/26225/pg26225.txt",
    "https://www.gutenberg.org/ebooks/26225.html.images",
    "https://www.gutenberg.org/files/26225/26225-h/26225-h.htm",
    "https://www.gutenberg.org/ebooks/26225",
    "https://www.gutenberg.org/cache/epub/26225/pg26225-images.html",
]

print("=== Testing 26225 endpoints ===")
for url in urls:
    try:
        req = urllib.request.Request(url, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"  {url}")
        print(f"    HTTP {resp.status} {resp.reason} ({resp.length if resp.length else '?'} bytes)")
        # If we get a 200, try to read a bit to verify it's text
        if resp.status == 200:
            try:
                full_req = urllib.request.Request(url)
                full_resp = urllib.request.urlopen(full_req, timeout=10)
                data = full_resp.read(500)
                print(f"    First 500 bytes: {data[:200]}...")
            except Exception as e2:
                print(f"    Read error: {e2}")
    except urllib.error.HTTPError as e:
        print(f"  {url}")
        print(f"    HTTP {e.code} {e.reason}")
    except Exception as e:
        print(f"  {url}")
        print(f"    Error: {e}")

# Also try the official page to see if it exists at all
print("\n=== Testing 26225 official page (GET) ===")
try:
    req = urllib.request.Request("https://www.gutenberg.org/ebooks/26225")
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read(2000).decode('utf-8', errors='replace')
    # Look for title
    import re
    title_match = re.search(r'<title>(.*?)</title>', data, re.IGNORECASE)
    if title_match:
        print(f"  Title: {title_match.group(1)}")
    else:
        print(f"  Response snippet: {data[:500]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code} {e.reason}")
except Exception as e:
>>>>>>> origin/main
    print(f"  Error: {e}")
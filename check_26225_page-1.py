<<<<<<< HEAD
import urllib.request
import urllib.error
import re

# Get the full page to check available formats
try:
    req = urllib.request.Request("https://www.gutenberg.org/ebooks/26225", 
                                 headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    
    # Look for title
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    if title_match:
        print(f"Title: {title_match.group(1)}")
    
    # Look for author
    author_match = re.search(r'Author[^<]*<[^>]*>([^<]+)', html, re.IGNORECASE)
    if author_match:
        print(f"Author: {author_match.group(1).strip()}")
    
    # Look for download links
    print("\n=== Download links found ===")
    # Find all hrefs that look like download links
    links = re.findall(r'href=["\']([^"\']*\.(?:txt|zip|html?|epub|kindle|pdf))["\']', html, re.IGNORECASE)
    for link in links:
        if '26225' in link:
            print(f"  {link}")
    
    # Look for "No download" or similar messages
    if 'no longer' in html.lower() or 'removed' in html.lower():
        print("\nWARNING: Page may indicate the book was removed")
    
    # Check for text format specifically
    if 'text/plain' in html.lower() or 'txt' in html.lower():
        print("\nText format references found in page")
    
    # Check for "not available" messages
    not_avail = re.findall(r'[Nn]ot\s+available[^.]*\.', html)
    if not_avail:
        print(f"\nNot available messages: {not_avail[:3]}")
    
    # Print a snippet around "download" or "format"
    for match in re.finditer(r'.{0,100}(?:download|format|text|plain).{0,100}', html, re.IGNORECASE):
        print(f"  ...{match.group().strip()}...")
        break
    
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.reason}")
except Exception as e:
=======
import urllib.request
import urllib.error
import re

# Get the full page to check available formats
try:
    req = urllib.request.Request("https://www.gutenberg.org/ebooks/26225", 
                                 headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    
    # Look for title
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    if title_match:
        print(f"Title: {title_match.group(1)}")
    
    # Look for author
    author_match = re.search(r'Author[^<]*<[^>]*>([^<]+)', html, re.IGNORECASE)
    if author_match:
        print(f"Author: {author_match.group(1).strip()}")
    
    # Look for download links
    print("\n=== Download links found ===")
    # Find all hrefs that look like download links
    links = re.findall(r'href=["\']([^"\']*\.(?:txt|zip|html?|epub|kindle|pdf))["\']', html, re.IGNORECASE)
    for link in links:
        if '26225' in link:
            print(f"  {link}")
    
    # Look for "No download" or similar messages
    if 'no longer' in html.lower() or 'removed' in html.lower():
        print("\nWARNING: Page may indicate the book was removed")
    
    # Check for text format specifically
    if 'text/plain' in html.lower() or 'txt' in html.lower():
        print("\nText format references found in page")
    
    # Check for "not available" messages
    not_avail = re.findall(r'[Nn]ot\s+available[^.]*\.', html)
    if not_avail:
        print(f"\nNot available messages: {not_avail[:3]}")
    
    # Print a snippet around "download" or "format"
    for match in re.finditer(r'.{0,100}(?:download|format|text|plain).{0,100}', html, re.IGNORECASE):
        print(f"  ...{match.group().strip()}...")
        break
    
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.reason}")
except Exception as e:
>>>>>>> origin/main
    print(f"Error: {e}")
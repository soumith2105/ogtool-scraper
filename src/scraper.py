# Import necessary libraries for parsing, markdown conversion, HTTP requests, and browser automation
from readability import Document
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from src.book_parser import extract_chapters
from src.knowledgebase_payload import KnowledgebaseItem, KnowledgebasePayload
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp

from playwright.async_api import async_playwright
import fitz  # PyMuPDF for PDF extraction
import re


# -------------------------------------------------
# Extract all internal links from a JavaScript-heavy page using Playwright.
# -------------------------------------------------
async def extract_links_js_heavy_page(url):
    internal_links = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(3000)  # Wait for hydration of dynamic content

        # Find all anchor tags with href
        anchors = await page.query_selector_all("a[href]")
        for anchor in anchors:
            href = await anchor.get_attribute("href")
            if not href or href.startswith("#"):  # Skip empty and hash links
                continue
            full_url = urljoin(url, href)
            # Only add internal links (same domain)
            if urlparse(full_url).netloc == urlparse(url).netloc:
                internal_links.add(full_url)

        await browser.close()
    return sorted(internal_links)


# -------------------------------------------------
# Extract links from clickable card-like elements (used for quill.co-like sites)
# -------------------------------------------------
async def extract_click_links_from_quill(url):
    visited_links = set()
    clicked_indices = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        base_origin = urlparse(url).netloc

        # Loop to click all clickable cards that haven't been clicked yet
        while True:
            clickable_elements = await page.query_selector_all(
                'div.bg-white.p-\\[30px\\].hover\\:bg-slate-50[style*="cursor:pointer"]'
            )
            if len(clicked_indices) >= len(clickable_elements):
                break

            for i, element in enumerate(clickable_elements):
                if i in clicked_indices:
                    continue

                try:
                    current_url = page.url
                    await element.click(timeout=2000)
                    await page.wait_for_url("**", timeout=3000)

                    new_url = page.url
                    # Only add unique internal navigation
                    if (
                        new_url != current_url
                        and urlparse(new_url).netloc == base_origin
                    ):
                        visited_links.add(new_url)

                    clicked_indices.add(i)

                    # Go back to the original page and try the next card
                    await page.goto(current_url, wait_until="networkidle")
                    await page.wait_for_timeout(1000)
                    break

                except Exception as e:
                    clicked_indices.add(i)  # Skip this element if error occurs
                    continue

        await browser.close()

    return sorted(visited_links)


# -------------------------------------------------
# Simple async GET request to fetch the HTML content of a page
# -------------------------------------------------
async def fetch(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


# -------------------------------------------------
# Extract all internal links from a static HTML page using BeautifulSoup
# -------------------------------------------------
async def extract_links(session, base_url):
    html = await fetch(session, base_url)
    if not html:
        return set()

    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)
        # Only add links from the same domain
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)

    return links


# -------------------------------------------------
# High-level async orchestrator: gather all links from multiple sources (blog, guide, PDF, etc.)
# -------------------------------------------------
async def extract_blog_and_guide_links_async(start_urls):
    all_links = set()
    async with aiohttp.ClientSession() as session:
        drive_links = []  # Collect Google Drive PDF links separately
        tasks = []
        for url in start_urls:
            # Use the appropriate extractor depending on the domain
            if "substack.com" in urlparse(url).netloc:
                tasks.append(extract_links_js_heavy_page(url))
            elif urlparse(url).netloc in ("quill.co"):
                tasks.append(extract_click_links_from_quill(url))
            elif "drive.google.com" in urlparse(url).netloc:
                drive_links.append(url)  # Handle PDFs separately
            else:
                tasks.append(extract_links(session, url))
        # Gather results from all extraction tasks
        results = await asyncio.gather(*tasks)

        for link_set in results:
            all_links.update(link_set)

        all_links.update(drive_links)  # Add Drive links to the final set

    print("Found", len(all_links), "links. Extracting books, blogs and guides...")

    return sorted(all_links)


# -------------------------------------------------
# Synchronous entry point: returns a structured KnowledgebasePayload after extracting and scraping links
# -------------------------------------------------
def extract_blog_and_guides(team_id, urls) -> KnowledgebasePayload:
    result = asyncio.run(extract_blog_and_guide_links_async(urls))
    return asyncio.run(scrape_all_blogs_async(team_id, result))


# -------------------------------------------------
# Scrape a single blog page and convert its main content to Markdown
# -------------------------------------------------
async def scrape_blog_to_markdown(session, url, semaphore):
    async with semaphore:  # Limit concurrency for resource control
        try:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    print(f"❌ Failed to fetch {url}")
                    return None
                html_content = await response.text()

                # Use readability to extract the main article content
                doc = Document(html_content)
                title = doc.title()
                main_html = doc.summary(html_partial=True)

                # Convert headers to paragraphs for better markdown formatting
                soup = BeautifulSoup(main_html, "lxml")
                for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                    tag.name = "p"

                markdown_content = md(str(soup))

                return KnowledgebaseItem(
                    title=title.strip(),
                    content=markdown_content.strip(),
                    content_type="blog",
                    source_url=url,
                )
        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            return None


# -------------------------------------------------
# Orchestrate scraping all found blogs/links and return them as a KnowledgebasePayload
# -------------------------------------------------
async def scrape_all_blogs_async(team_id, urls, concurrency=8):
    semaphore = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            if "drive.google.com" in urlparse(url).netloc:
                tasks.append(extract_text_from_drive_pdf(session, url))
            else:
                tasks.append(scrape_blog_to_markdown(session, url, semaphore))
        results = await asyncio.gather(*tasks)

    # Flatten results: each item can be a KnowledgebaseItem or a list of KnowledgebaseItem
    flat_items = []
    for item in results:
        if item is None:
            continue
        if isinstance(item, list):
            flat_items.extend([i for i in item if i is not None])
        else:
            flat_items.append(item)
    return KnowledgebasePayload(
        team_id=team_id,
        items=flat_items,
    )


# -------------------------------------------------
# Download a PDF from Google Drive and extract its text (one item per document)
# -------------------------------------------------
async def extract_text_from_drive_pdf(session, drive_url: str) -> KnowledgebaseItem:
    async with session.get(drive_url, timeout=20) as response:
        if response.status != 200:
            raise Exception(f"Failed to download PDF: {response.status}")
        pdf_bytes = await response.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    doc.close()

    kb_items = extract_chapters(text, drive_url)
    return kb_items

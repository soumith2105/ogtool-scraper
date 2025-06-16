# Knowledgebase Blog and Guide Extractor


This repository provides a high-performance, asynchronous toolkit for extracting, crawling, and scraping **blogs, guides, and PDFs** from a diverse set of web sources—including static websites, JavaScript-heavy blogs (like Substack), card-based sites (like Quill), and Google Drive PDFs. The content is normalized into clean **Markdown** or plain text and wrapped in a consistent schema for downstream use in knowledge bases, documentation, or LLM ingestion.

## Features

- **Smart Link Extraction**  
  Handles both static HTML and dynamic, JavaScript-rendered pages using Playwright.

- **PDF Text Extraction**  
  Downloads and parses PDFs from Google Drive.

- **Markdown Conversion**  
  Converts blog and guide content to clean Markdown using [readability](https://github.com/buriy/python-readability), [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/), and [markdownify](https://github.com/matthewwithanm/python-markdownify).

- **Asynchronous Architecture**  
  Fast and scalable—designed for bulk operations using Python asyncio.

- **Consistent Data Model**  
  All content is returned as `KnowledgebaseItem` objects, packaged in a `KnowledgebasePayload`.

## Technologies

- Python 3.8+
- [aiohttp](https://docs.aiohttp.org/)
- [playwright](https://playwright.dev/python/)
- [readability-lxml](https://github.com/buriy/python-readability)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [markdownify](https://github.com/matthewwithanm/python-markdownify)
- [PyMuPDF (fitz)](https://github.com/pymupdf/PyMuPDF)

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-username/your-repo.git
   cd your-repo

2. **Creating Virtual Environment and Activating it**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    playwright install chromium
    ```
4. **Run the code**
    ```sh
    python main.py
    ```

## **Usage**

### **Core API**

The main entrypoint is:

```python
from your_module import extract_blog_and_guide_links

urls = [
    "https://yourblog.com",
    "https://some.substack.com",
    "https://quill.co/some/guide",
    "https://drive.google.com/file/d/XXX/view",
    # ...more URLs
]

knowledgebase_payload = extract_blog_and_guides(urls)
for item in knowledgebase_payload.items:
    print(item.title)
    print(item.content[:200])  # Preview content
```

### **Returned Schema**

* KnowledgebasePayload
  * **team_id**: hardcoded team identifier
  * **items**: list of **KnowledgebaseItem**
    * **title**: Page or document title
    * **content**: Markdown or plain text
    * content_type**: **"blog"** or **"book"**
    * **source_url**: Original URL

### **What Sites Are Supported?**

* **Static HTML pages**
* **JavaScript-heavy blogs** (e.g., Substack)
* **Card/click-based navigation** (e.g., Quill)
* **Google Drive PDFs**
* *Extensible* : Add more strategies for custom domains as needed

## **Tips**

* For large batches, adjust the **concurrency** parameter in **scrape_all_blogs_async** for best performance.
* If you encounter scraping issues (e.g., sites blocking headless browsers), consider Playwright’s stealth plugins or proxy rotation.
* Extend the code by adding new extraction strategies for unique site layouts.

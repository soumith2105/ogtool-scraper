from src.scraper import extract_blog_and_guides
import json
import os
from dataclasses import asdict


if __name__ == "__main__":
    team_id = "aline123"

    urls = (
        "https://interviewing.io/blog",
        "https://interviewing.io/topics#companies",
        "https://interviewing.io/learn#interview-guides",
        "https://nilmamano.com/blog/category/dsa",
        "https://shreycation.substack.com",
        "https://quill.co/blog",
        "https://drive.google.com/uc?export=download&id=1aLUbg2Hif1zG2TcN_ldVQZbygcvtW9Hr",
    )
    print("Starting extraction of KnowledgeBase Items.")
    print("Crawling the defined URLs...")
    markdown = extract_blog_and_guides(team_id, urls)
    knowledgebasepayload = asdict(markdown)

    # Ensure the output directory exists
    os.makedirs("knowledgebase", exist_ok=True)

    # Write the payload to a JSON file
    with open(f"knowledgebase/{team_id}.json", "w", encoding="utf-8") as f:
        json.dump(knowledgebasepayload, f, ensure_ascii=False, indent=2)

    # Write the first 20 knowledgebase items to individual markdown files
    os.makedirs("knowledgebase/markdown", exist_ok=True)
    items = knowledgebasepayload.get("items", [])[:20]

    # Preparing markdown files of the first 20 items
    for idx, item in enumerate(items):
        title = item.get("title", f"Item {idx+1}")
        link = item.get("link", "")
        content = item.get("content", "")
        # Sanitize filename
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[
            :50
        ]
        filename = f"knowledgebase/markdown/{idx+1:02d}_{safe_title}.md"
        with open(filename, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {title}\n\n")
            if link:
                md_file.write(f"[Source Link]({link})\n\n")
            md_file.write(content)

    print("Extraction of KnowledgeBase Items complete")
    print(f"KnowledgeBase items saved to knowledgebase/{team_id}.json")

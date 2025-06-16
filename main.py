from src.scraper import extract_blog_and_guides
import json
import os
from dataclasses import asdict


if __name__ == "__main__":
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
    markdown = extract_blog_and_guides(urls)
    knowledgebasepayload = asdict(markdown)

    # Ensure the output directory exists
    os.makedirs("knowledgebase", exist_ok=True)

    # Write the payload to a JSON file
    with open("knowledgebase/aline123.json", "w", encoding="utf-8") as f:
        json.dump(knowledgebasepayload, f, ensure_ascii=False, indent=2)

    print("Extraction of KnowledgeBase Items complete")
    print(f"KnowledgeBase items saved to knowledgebase/aline123.json")

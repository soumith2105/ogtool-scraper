from typing import List
import re

from src.knowledgebase_payload import KnowledgebaseItem


def clean_text(text: str) -> str:
    # Remove lines like: CHAPTER 2 ▸ WHAT'S BROKEN ABOUT CODING INTERVIEWS
    text = re.sub(
        r"^C\s*H\s*A\s*P\s*T\s*E\s*R\s+\d+\s*▸[^\n]*\n?",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Remove lines with only dots (e.g., ". . . . . .")
    text = re.sub(r"^(?:\.\s*){3,}\n?", "", text, flags=re.MULTILINE)
    # Remove lines like: 26\nBEYOND CRACKING THE CODING INTERVIEW ▸ UGLY TRUTHS & HIDDEN REALITIES
    text = re.sub(
        r"^\d+\s*\nBEYOND CRACKING THE CODING INTERVIEW\s*▸[^\n]*\n?",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    # Remove lines like: just a page number
    text = re.sub(r"^\d+\n?", "", text, flags=re.MULTILINE)
    return text


def normalize_title(title: str) -> str:
    # Remove all double/triple spaces to single space
    title = re.sub(r"\s{2,}", " ", title)
    # Remove spaces between all caps (if matches spaced style)
    if re.fullmatch(r"([A-Z0-9'’]+\s+){2,}[A-Z0-9'’]+", title):
        title = "".join(title.split())
        # Add spaces between capitalized words
        title = re.sub(r"(?<!^)(?=[A-Z])", " ", title)
    # Title-case, but keep ALL-UPPER acronyms
    title = re.sub(
        r"\b([A-Z]{2,})\b",  # don't lowercase acronyms
        lambda m: m.group(1),
        title.title(),
    )
    return title.strip()


def extract_chapters(text: str, drive_url: str) -> List[KnowledgebaseItem]:
    text = clean_text(text)  # Remove unwanted headers/footers

    chapter_pattern = re.compile(
        r"(?:(?:C\s*H\s*A\s*P\s*T\s*E\s*R\s+\d+\s*I*\s*){1,20})", re.IGNORECASE
    )

    chapters = []
    positions = [m.start() for m in chapter_pattern.finditer(text)]
    positions.append(len(text))  # End of text

    # Book intro before first chapter
    if positions and positions[0] != 0:
        intro = text[: positions[0]].strip()
        if intro:
            chapters.append(("BookIntroMetaData", intro))

    for i in range(len(positions) - 1):
        chap_start = positions[i]
        chap_end = positions[i + 1]
        chapter_text = text[chap_start:chap_end].strip()

        # Extract chapter number for display
        chap_num_match = re.search(
            r"C\s*H\s*A\s*P\s*T\s*E\s*R\s+(\d+)", chapter_text, re.IGNORECASE
        )
        chap_num = chap_num_match.group(1) if chap_num_match else f"{i+1}"

        # Remove all 'C H A P T E R N' and 'I' at the start, even if glued together
        chapter_text = re.sub(
            r"^(?:(?:C\s*H\s*A\s*P\s*T\s*E\s*R\s+\d+\s*I*\s*)+)",
            "",
            chapter_text,
            flags=re.IGNORECASE,
        ).strip()

        # Find the next non-empty line: that's the title
        lines = [line.strip() for line in chapter_text.splitlines() if line.strip()]
        chap_title = "Unknown Title"
        content_lines = []
        for idx, line in enumerate(lines):
            # Remove lingering chapter keywords if they appear
            if "CHAPTER" in line.upper():
                continue
            chap_title = normalize_title(line)
            content_lines = lines[idx + 1 :]
            break

        # Fallback: if not found, use first line, normalized
        if chap_title == "Unknown Title" and lines:
            chap_title = normalize_title(lines[0])
            content_lines = lines[1:]

        # Format bullets and wrap lines
        formatted = []
        paragraph = ""
        for ln in content_lines:
            ln = ln.replace("•", "-")  # Markdown bullet
            if (
                re.match(r"^\d+$", ln)
                or re.match(r"^[A-Z ]+\s*▸.*$", ln)
                or re.match(r"^BEYOND CRACKING.*$", ln)
            ):
                continue
            if paragraph:
                if not re.search(r'[.!?]"?$', paragraph):
                    paragraph += " " + ln
                else:
                    formatted.append(paragraph)
                    paragraph = ln
            else:
                paragraph = ln
        if paragraph:
            formatted.append(paragraph)

        chapter_content = "\n\n".join(formatted).strip()
        chapters.append((f"Chapter {chap_num}: {chap_title}", chapter_content))

    kb_items = []
    for title, content in chapters:
        if not content:
            continue
        kb_items.append(
            KnowledgebaseItem(
                title=title, content=content, content_type="book", source_url=drive_url
            )
        )
    return kb_items

from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class KnowledgebaseItem:
    title: str
    content: str
    content_type: str  # blog|podcast_transcript|call_transcript|linkedin_post|reddit_comment|book|other
    source_url: Optional[str] = None
    author: Optional[str] = ""
    user_id: Optional[str] = ""

@dataclass
class KnowledgebasePayload:
    team_id: str
    items: List[KnowledgebaseItem] = field(default_factory=list)
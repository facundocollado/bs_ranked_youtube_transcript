from typing_extensions import TypedDict, NotRequired, List

class BrawlerMention(TypedDict):
    name: str
    context_in_transcript: str
    relevant_tips_or_strategies: str

class TranscriptAnalysisResult(TypedDict):
    summary: str
    key_topics: List[str]
    brawlers_mentioned: List[BrawlerMention]
    meta_notes: str
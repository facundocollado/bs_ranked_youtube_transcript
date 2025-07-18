import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    m = re.search(r"v=([^&]+)", url)
    return m.group(1) if m else url

def get_transcript(video_id: str):
    segments = YouTubeTranscriptApi.get_transcript(video_id)
    text = "\n".join([seg["text"] for seg in segments])
    return text, segments

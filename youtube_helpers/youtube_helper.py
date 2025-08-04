import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscriptSnippet
from llm_helpers.brawlers_data import BRAWLERS_LIST

class YouTubeHelper:
    def __init__(self, url: str):
        self.url = url
        self.video_id = self.extract_video_id(url)
        self._response = requests.get(url)
        self._soup = BeautifulSoup(self._response.text, features="html.parser")
        self._title = None
        self._publish_date = None

    @staticmethod
    def extract_video_id(url: str) -> str:
        match = re.search(r"v=([^&]+)", url)
        return match.group(1) if match else url

    def get_title(self) -> str:
        if self._title is not None:
            return self._title
        link = self._soup.find_all(name="title")[0]
        title = str(link).replace("<title>", "").replace("</title>", "")
        cleaned = re.sub(r'[^a-zA-Z0-9]', '_', title)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        self._title = cleaned
        return self._title

    def get_publish_date(self) -> str:
        if self._publish_date is not None:
            return self._publish_date
        meta_date = self._soup.find("meta", itemprop="datePublished")
        if meta_date and meta_date.get("content"):
            date_str = meta_date["content"]
            date_only = date_str.split("T")[0]
            self._publish_date = date_only
            return date_only
        return ""

    def get_transcript(self) -> tuple[str, list[FetchedTranscriptSnippet]]:
        transcript = YouTubeTranscriptApi().fetch(self.video_id)
        text = " ".join(snippet.text for snippet in transcript.snippets)
        return text, transcript.snippets

    def extract_all(self) -> dict:
        """Devuelve un diccionario con título, fecha y transcript."""
        title = self.get_title()
        publish_date = self.get_publish_date()
        transcript_text, transcript_snippets = self.get_transcript()
        return {
            "title": title,
            "publish_date": publish_date,
            "transcript_text": transcript_text,
            "transcript_snippets": transcript_snippets,
        }
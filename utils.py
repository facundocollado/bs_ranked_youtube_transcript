from llm_helpers.brawlers_data import BRAWLERS_LIST
import jsonlines


# filtrar brawlers_mentioned por BRAWLERS_LIST
def filter_brawlers(json_output):
    filtered = [
        b for b in json_output["brawlers_mentioned"]
        if b["name"] in BRAWLERS_LIST
    ]
    json_output["brawlers_mentioned"] = filtered
    return json_output

# Process the video dictionary to create chunks for RAG storage
def process_video_dict(d: dict, file_id: str, publish_date: str):
    """ Divide estructura original en chunks individuales y globales """
    chunks = []

    # 1. Embedding global: summary, key_topics y meta_notes
    global_text = (
        "Summary: " + d.get("summary", "") + "\n" +
        "Topics: " + ", ".join(d.get("key_topics", [])) + "\n" +
        "Meta: " + d.get("meta_notes", "")
    )
    chunks.append({
        "id": f"{file_id}_global",
        "text": global_text,
        "restricts": [
            {"namespace": "chunk_type", "allow": ["global"]},
            {"namespace": "publish_date", "allow": [publish_date]}
        ]
    })

    # 2. Embeddings para cada brawler
    for b in d.get("brawlers_mentioned", []):
        b_id = b.get("name", "unknown").lower()
        text = (
            f"Brawler: {b.get('name')}. \n "
            f"Context: {b.get('context_in_transcript')}. \n "
            f"Tips: {b.get('relevant_tips_or_strategies')}"
        )
        chunks.append({
            "id": f"{file_id}_{b_id}",
            "text": text,
            "restricts": [
                {"namespace": "chunk_type", "allow": ["brawler"]},
                {"namespace": "brawler", "allow": [b.get("name")]},
                {"namespace": "publish_date", "allow": [publish_date]}
            ]
        })
    return chunks

    

def save_chunks_to_jsonl(chunks: list, file_name: str = ""):
    """ Save the processed chunks to a JSONL file. """
    with jsonlines.open(file_name, mode="w") as writer:
        for c in chunks:
            writer.write({
                "id": c["id"],
                "text": c["text"],
                "restricts": c["restricts"]
            })
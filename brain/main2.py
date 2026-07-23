import os
import re
import json
from typing import List, Dict
from transformers import pipeline


TIME_PATTERN = re.compile(r'^\[(\d{2}:\d{2})\]\s*(.*)')


def parse_journal_file(file_path: str) -> List[str]:
    """
    Parse a single journal file.
    Format:
        [08:30] First line of entry
        more lines...

        [10:15] Another entry
        ...
    Returns a list of entry texts (without the [hh:mm]).
    """
    entries: List[str] = []

    with open(file_path, "r", encoding="utf-8") as f:
        current_lines: List[str] = []

        for line in f:
            m = TIME_PATTERN.match(line)
            if m:
                # New entry starts
                if current_lines:
                    entry_text = " ".join(current_lines).strip()
                    if entry_text:
                        entries.append(entry_text)
                    current_lines = []

                rest = m.group(2).strip()
                if rest:
                    current_lines.append(rest)
            else:
                # Continuation of current entry (if any)
                if current_lines:
                    stripped = line.strip()
                    if stripped:
                        current_lines.append(stripped)

        # flush last entry
        if current_lines:
            entry_text = " ".join(current_lines).strip()
            if entry_text:
                entries.append(entry_text)

    return entries


def concatenate_entries(entries: List[str]) -> str:
    # Separate entries by blank line – helps summarizer see boundaries
    return "\n\n".join(entries)


def build_summarizer():
    """
    Portuguese summarization pipeline.
    If this is too slow, swap model to a smaller one (e.g. bert2bert).
    """
    summarizer = pipeline(
        "summarization",
        model="cnmoro/ptt5_small_portuguese_summarizer",
        device_map="auto"
    )
    return summarizer


def summarize_large_text(
    text: str,
    summarizer,
    chunk_size: int = 3000,
    max_length: int = 120,
    min_length: int = 40,
) -> str:
    """
    Summarize long text by splitting into character chunks and
    summarizing twice (partial summaries -> final summary).
    """
    text = text.strip()
    if not text:
        return "Texto vazio."

    # Split into chunks by characters (simple, but works for journals)
    chunks: List[str] = []
    while text:
        chunk = text[:chunk_size]
        text = text[chunk_size:]
        chunks.append(chunk)

    partial_summaries: List[str] = []
    for chunk in chunks:
        out = summarizer(
            chunk,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        partial_summaries.append(out[0]["summary_text"].strip())

    # Only one chunk -> done
    if len(partial_summaries) == 1:
        return partial_summaries[0]

    # Multiple chunks -> summarize the summaries
    combined = " ".join(partial_summaries)
    final = summarizer(
        combined,
        max_length=max_length,
        min_length=min_length,
        do_sample=False
    )
    return final[0]["summary_text"].strip()


def summarize_folder_per_day(folder_path: str) -> Dict[str, str]:
    """
    For each .txt in folder:
        - parse entries
        - concatenate
        - summarize
    Returns dict {day_id: summary}
    where day_id is filename without extension.
    """
    summarizer = build_summarizer()
    results: Dict[str, str] = {}

    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(folder_path, filename)
        day_id, _ = os.path.splitext(filename)

        entries = parse_journal_file(file_path)
        if not entries:
            results[day_id] = "Nenhuma entrada encontrada neste dia."
            continue

        full_text = concatenate_entries(entries)
        day_summary = summarize_large_text(full_text, summarizer)
        results[day_id] = day_summary

    return results


def save_summaries_to_json(summaries: Dict[str, str], output_path: str) -> None:
    """
    Save {day_id: summary} to a JSON file for later LLM consumption.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    folder = "/Users/reimor/notes/journal"
    output_json = "journal_summaries_per_day.json"

    per_day_summaries = summarize_folder_per_day(folder)
    save_summaries_to_json(per_day_summaries, output_json)

    print(f"Saved {len(per_day_summaries)} daily summaries to {output_json}")


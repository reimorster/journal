import os
import re
from transformers import pipeline

# -------- STEP 1: EXTRACT LINES IN [NOTES] --------
def parse_journal_folder(folder_path: str, summarizer):
    notes = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    #match = re.search(r"\[(.*?)\]", line)
                    #if match:
                    #    notes.append(match.group(1).strip())

                    notes.append(line)

            notes = concatenate_notes(notes)

            summarize_large_text(notes, summarizer)

            notes = []
    
    return notes

# -------- STEP 2: CONCATENATE --------
def concatenate_notes(notes):
    print(notes)
    return "\n".join(notes)

# -------- STEP 3: CHUNK + SUMMARIZE --------
def summarize_large_text(text, summarizer, chunk_size=3000):
    """
    Splits long text into manageable parts for summarization.
    chunk_size is character-based, conservative to avoid token overflow.
    """
    chunks = []
    while text:
        chunk = text[:chunk_size]
        text = text[chunk_size:]
        chunks.append(chunk)

    partial_summaries = []
    for chunk in chunks:
        out = summarizer(
            chunk,
            max_length=50,
            min_length=20,
            do_sample=False
        )
        partial_summaries.append(out[0]["summary_text"])

    # If multiple chunks -> summarize the summaries (recursive compression)
    if len(partial_summaries) > 1:
        combined = " ".join(partial_summaries)
        final = summarizer(
            combined,
            max_length=120,
            min_length=40,
            do_sample=False
        )
        return final[0]["summary_text"]

    return partial_summaries[0]

# -------- STEP 4: MAIN --------
def run(folder_path):
    # Portuguese summarizer
    summarizer = pipeline(
        "summarization",
        model="pierreguillou/t5-base-qa-squad-v1.1-portuguese",
        device_map="auto"
    )
    
    notes = parse_journal_folder(folder_path, summarizer)

    if not notes:
        return "Nenhuma anotação encontrada."

    #text = concatenate_notes(notes)


    #return summarize_large_text(text, summarizer)

# -------- USAGE --------
if __name__ == "__main__":
    folder = "/Users/reimor/notes/journal"
    summary = run(folder)
    
    print("\n=============== RESUMO ===============\n")
    print(summary)


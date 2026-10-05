# Long Document Summarizer via Chunking 

An educational project demonstrating how to summarize a long PDF containing text, a table, and an image, by splitting it into smaller pieces (chunks), summarizing each piece separately, and then merging those summaries into one final summary covering the whole document.

## Goal

Understand a core problem when working with long documents: language models have a maximum amount of text they can read in a single request (the context window). When a document exceeds that limit, it must be split into pieces — but the splitting itself can introduce new problems, which is exactly what this project documents through hands-on experimentation.

## What was built

1. **Text extraction** from a multi-page PDF using the PyMuPDF library
2. **Image extraction** from inside the file, sent to the Gemini model to get a text description, which is then merged back into the full text at its original position
3. **Fixed-size chunking** of the text into pieces, with no regard for where sentences end
4. **Per-chunk summarization** using the model
5. **Merging the summaries into one final summary** (progressive summarization), by sending all the small summaries back to the model to be rewritten as a single coherent piece of text

## Testing methodology

Before building anything, predictions were written down for what chunking might break:
- Related information being disconnected at the cut point
- Images being lost entirely when only extracting text
- Tables losing their structure when flattened into plain text

A test PDF was built containing connected, extended prose ( 8,800 characters), a small table (4 rows), and an image (a bar chart with five known numeric values), specifically to test these predictions directly.

## Actual results

### The table (within full context)
Extracted correctly and readable within the full text, since it is small and simple.

### The image
Did not appear at all when extracting text alone, confirming the core prediction. This was solved by sending the image to Gemini and getting an accurate text description back. All five values (12, 15, 9, 18, 21) matched the chart's real values almost every run, with full accuracy.

### Chunk size comparison: 800 characters vs. 2000 characters
The script was run on the same document with two different chunk sizes:

| | 800 characters | 2000 characters |
|---|---|---|
| Number of chunks | 11 | 5 |
| Number of cut points | 10 | 4 |
| Share of cut points landing mid-word | 30% | **75% (3 of 4)** |

**Key finding:** increasing the chunk size reduced the total number of cut points (since the number of chunks itself dropped), but it did not make each individual cut point any "smarter" or more respectful of word boundaries. Of the 4 cut points at size 2000, 3 landed exactly mid-word ("team" → "t / eam", "Metric" → "Me / tric", "brittle" → "br / ittle"). The root problem (random cutting by a fixed character count) did not change — only the chance of it showing up dropped.

### Progressive summarization
After summarizing the five chunks individually, the summaries were merged and sent back to the model to produce one final summary. The result was two coherent paragraphs covering every angle of the document (technical, operational, and financial) in a unified style — not just the five summaries pasted next to each other.

### Break-it test: summarizing the table in isolation, with no surrounding text

**Prediction written before the experiment:**
> The model will most likely understand the table's general structure (thanks to clear column names) and state the numbers accurately, but may "invent" an incorrect context (such as assuming it's an employee performance report), given the absence of any information about the table's real subject.

**Code used for this test:**

```python

table_only = """Release
Month
Metric Improved
Change
Routing
March
Routing Accuracy
+12%
Templates
July
Avg. Response Time
-18%
Escalation
November
Escalation Precision
+9%"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"Summarize this text in 1-2 sentences:\n\n{table_only}",
)

print("\n--- Summary of TABLE ONLY (no surrounding context) ---")
print(response.text)
```

**Code explanation:** `table_only` is a text variable holding just the table's content, copied exactly as PyMuPDF extracted it from the PDF (rows and columns, no introductory paragraph or surrounding context). This isolated text is sent to the model using the same summarization prompt pattern used throughout the rest of the project, with no change to how the call itself is made — the goal is purely to isolate the table from its context and observe the effect of that missing context on summary quality.

**Actual result:**
```
Three feature releases throughout the year successfully enhanced key performance
metrics, highlighted by a 12% increase in routing accuracy in March, an 18%
reduction in average response time in July, and a 9% boost in escalation
precision in November.
```

**Analysis:** the prediction was partially correct the model did understand the general structure and stated the numbers with full accuracy (12%, 18%, 9%). But contrary to the prediction, **the model did not invent any incorrect context** (it did not assume "employee performance" or any other story) instead, it chose a generic, safe description ("Three feature releases", "key performance metrics") that avoids any assumption that could be wrong. This reveals a different behavior pattern from the hallucination observed earlier in this project: rather than inventing incorrect details, the model here leaned toward a summary that is "empty of interpretive meaning" but numerically accurate a safer failure mode, but a less useful one in practice.

## What was learned

- Fixed-size chunking (by character count) is the simplest possible approach, but it is fragile and disrespects sentence or paragraph structure, regardless of the chunk size chosen
- A larger chunk size reduces *how often* the problem occurs, not the *likelihood* of it occurring at any single cut point
- Extracting images from a PDF and describing them via a language model is an effective solution to the problem of losing visual information
- The "merge the summaries" step is necessary, not optional — without it, you get a set of disconnected sentences, not a genuinely coherent summary
- When sufficient context is missing (as in the isolated table test), the model does not necessarily invent incorrect details; sometimes it prefers a generic, safe summary that sacrifices interpretive usefulness in order to preserve accuracy

## Current limitations

- Chunking does not respect sentence or paragraph boundaries, and could be improved by chunking on sentence breaks instead of raw character counts
- Tested on a medium-length document (~9,000 characters, 3 pages); not yet tested on genuinely long documents (tens or hundreds of pages)
- Larger or more complex tables were not tested; the table used here is small (4 rows), and the same results may not hold for larger tables

## How to run

```bash
pip install pymupdf google-genai
export GEMINI_API_KEY="your-key-here"
python3 Summarize.py
```


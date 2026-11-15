# PDF Q&A Agent — Project 2 of 5

**Beginner Agentic AI Projects** (from @aman_views, Instagram post
`De8R_m-FDtg`, 25 Oct 2026) — Project 2: *Learn Basic RAG*.

A small Python agent that answers questions **only from a document you
give it**. If the answer is not in the document, it says so — it never
guesses.

## What it does

- Upload a PDF, `.txt` or `.md` file
- Break the text into small chunks
- Find the most relevant chunks for your question
- Answer only from those chunks, and show the chunks it used

## The RAG workflow

```
PDF / .txt / .md
    → EXTRACT TEXT
    → CHUNK  (~500 chars, 100 chars overlap)
    → SEARCH (TF-IDF retrieval)
    → ANSWER (grounded in the cited chunks only)
```

## Tech

- **Python 3.10+** (tested on Python 3.12), standard library only for
  the agent itself — `re`, `math`, `collections`
- **TF-IDF retrieval** — a local retrieval method that ranks chunks by
  word overlap. It is *not* an embedding model and needs no API key.
- **pypdf** — only for reading `.pdf` files (see `requirements.txt`).
  `.txt` and `.md` work without it.
- **Optional embeddings hook** — `search_chunks()` accepts an optional
  `embed_fn`. No embedding model is bundled; the hook is there if you
  add one later.

## The grounded-answers rule

Every answer comes with its source chunks and a relevance score.
Stopwords are ignored when ranking, and at least half of the
question's topic words must appear in the best chunk — so a question
that only shares a name with the document (e.g. "What is Alex
Carter's salary?") is not "answered" with a chunk that never
mentions salary. If no chunk passes those checks, the answer is:

> I don't know — that information is not in the document.

## How to run

```bash
cd 02-pdf-qa-agent
pip install -r requirements.txt   # pypdf, for .pdf files only
```

One question:

```bash
python main.py sample_resume.txt "Which skills are mentioned in this resume?"
```

Interactive mode (ask as many questions as you like):

```bash
python main.py sample_resume.txt
```

Try it with your own file:

```bash
python main.py my-notes.pdf "What does this document say about ...?"
```

## Example questions (sample resume)

The included `sample_resume.txt` is a **short fictional resume**
(SAMPLE data — no real person). Try:

| Question | Expected result |
|---|---|
| Which skills are mentioned in this resume? | Python, SQL, Excel, Power BI, Tableau, … (from the SKILLS chunk) |
| What experience does Alex Carter have? | Data analyst, 3 years; Junior Data Analyst at Northwind Retail (from the EXPERIENCE chunk) |
| What is the capital of France? | "I don't know — that information is not in the document." |
| What is Alex Carter's salary? | "I don't know — that information is not in the document." |

## Files

| File | What it is |
|---|---|
| `agent.py` | `extract_text()`, `chunk_text()`, TF-IDF `search_chunks()`, `pdf_agent()` |
| `main.py` | CLI — one question, or interactive mode |
| `sample_resume.txt` | Fictional sample resume for the demo |
| `requirements.txt` | `pypdf` only |
| `test_agent.py` | Unit tests (chunking, retrieval ranking, not-in-document) |

## Run the tests

```bash
python -m unittest test_agent -v
```

## Key takeaway

Retrieve relevant text first; then answer from it. The agent does
not guess — it calls a tool (retrieval) and shows its evidence.

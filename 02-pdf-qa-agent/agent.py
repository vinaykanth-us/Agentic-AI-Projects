"""
PDF Q&A Agent — Project 2 of 5: Beginner Agentic AI Projects
(@aman_views, Instagram post De8R_m-FDtg, 25 Oct 2026)

Workflow:  PDF -> EXTRACT TEXT -> CHUNK -> SEARCH -> ANSWER

The agent answers ONLY from the supplied document. If the answer is
not in the document it says so — it never guesses / hallucinates.

Retrieval: TF-IDF (term frequency / inverse document frequency)
implemented with the Python standard library only (re, math,
collections). TF-IDF is a *local* retrieval method — it ranks chunks
by word overlap, not by meaning. That is honest and needs no API key.

Optional embeddings hook: search_chunks() accepts an optional
``embed_fn``. If one is supplied it is used instead of TF-IDF.
No embedding model is bundled and none is required.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter

# Relevance floor: a chunk must score above this to count as evidence.
# TF-IDF cosine scores here are 0.0 (no shared words) to 1.0.
MIN_SCORE = 0.05

# At least half of the question's topic words must appear in the best
# chunk. This stops a question sharing only a name with the document
# ("What is Alex Carter's salary?") from being "answered" with a
# chunk that never mentions salary.
MIN_TOPIC_COVERAGE = 0.5

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Common words carry no meaning for retrieval, so they are ignored
# when ranking chunks. Without this, "What is the capital of France?"
# would match a chunk just because both contain "the" / "is".
STOPWORDS = frozenset("""
a an the and or but if then else when at by for with about against
between into through during before after above below to from up down
in out on off over under again further once here there all any both
each few more most other some such no nor not only own same so than
too very can will just should now is am are was were be been being
have has had having do does did doing would could shall may might
what which who whom this that these those there here how why where
when i you he she it we they me him her us them my your his its our
their of as at by in of on to
""".split())


# ---------------------------------------------------------------- extract

def extract_text(doc_path: str) -> str:
    """Return the plain text of a .txt, .md or .pdf document.

    Raises FileNotFoundError for a missing file and a clear
    ImportError / ValueError when .pdf support is unavailable.
    """
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Document not found: {doc_path}")

    ext = os.path.splitext(doc_path)[1].lower()
    if ext in (".txt", ".md"):
        with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError(
                "pypdf is not installed, so .pdf files cannot be read. "
                "Install it with: pip install -r requirements.txt"
            ) from exc
        reader = PdfReader(doc_path)
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages)
    raise ValueError(
        f"Unsupported file type: {ext!r}. Use .txt, .md or .pdf."
    )


# ---------------------------------------------------------------- chunking

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks.

    Default: ~500 characters with 100 characters of overlap, so a
    fact that falls on a boundary is still found whole in one chunk.
    The end of a chunk is moved back to the previous space so words
    are not cut in half (except for very long unbroken strings).
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Prefer a word boundary inside the window.
            space = text.rfind(" ", start, end)
            if space > start + 100:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


# ---------------------------------------------------------------- TF-IDF

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _content_tokens(text: str) -> list[str]:
    """Meaningful tokens: lowercased, stopwords removed."""
    return [t for t in _tokenize(text) if t not in STOPWORDS]


def _topic_tokens(question: str) -> list[str]:
    """Content words of the question, excluding capitalised entity
    words (e.g. "Alex Carter" in "What is Alex Carter's salary?").

    Entity words help *rank* chunks, but the topic words are what
    the question is actually asking about — at least half of them
    must appear in the best chunk, or the fact is not in the doc.
    The first word of the question is never treated as an entity
    ("Which" in "Which skills ...?").
    """
    words = re.findall(r"[A-Za-z0-9]+", question)
    topics = []
    for i, word in enumerate(words):
        token = word.lower()
        if token in STOPWORDS:
            continue
        if i > 0 and word[0].isupper():
            continue  # entity word, e.g. a person's name
        topics.append(token)
    return topics


def _tfidf_vectors(chunks: list[str]):
    """Return (vectors, idf) for the chunks.

    vector: {token: tf * idf}, tf = count / chunk length.
    idf = log((N + 1) / (df + 1)) + 1  (smoothed, always positive).
    """
    tokenised = [_content_tokens(c) for c in chunks]
    n = len(chunks)
    df: Counter = Counter()
    for tokens in tokenised:
        for token in set(tokens):
            df[token] += 1
    idf = {t: math.log((n + 1) / (d + 1)) + 1 for t, d in df.items()}

    vectors = []
    for tokens in tokenised:
        counts = Counter(tokens)
        total = len(tokens) or 1
        vectors.append(
            {t: (c / total) * idf[t] for t, c in counts.items()}
        )
    return vectors, idf


def _cosine(a: dict, b: dict) -> float:
    dot = sum(a[t] * b[t] for t in a.keys() & b.keys())
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_chunks(query: str, chunks: list[str], top_k: int = 3,
                  embed_fn=None) -> list[dict]:
    """Rank chunks by relevance to the query, most relevant first.

    Returns a list of {"chunk": str, "score": float} with score > 0,
    at most top_k entries.

    Default retrieval is TF-IDF (standard library only, no API key).
    OPTIONAL hook: pass embed_fn(query, chunks) -> list[float] to use
    an embedding model instead. It is not required and not bundled.
    """
    if not chunks or not query.strip():
        return []
    if embed_fn is not None:
        scores = embed_fn(query, chunks)
        ranked = sorted(
            ({"chunk": c, "score": float(s)}
             for c, s in zip(chunks, scores)),
            key=lambda r: r["score"], reverse=True,
        )
        return [r for r in ranked if r["score"] > 0][:top_k]

    vectors, idf = _tfidf_vectors(chunks)
    q_tokens = _content_tokens(query)
    q_counts = Counter(q_tokens)
    total = len(q_tokens) or 1
    # Unknown query words get the highest idf (they are rare by default).
    default_idf = math.log((len(chunks) + 1) / 1) + 1
    q_vec = {t: (c / total) * idf.get(t, default_idf)
             for t, c in q_counts.items()}

    ranked = sorted(
        ({"chunk": c, "score": _cosine(q_vec, v)}
         for c, v in zip(chunks, vectors)),
        key=lambda r: r["score"], reverse=True,
    )
    return [r for r in ranked if r["score"] > 0][:top_k]


# ---------------------------------------------------------------- agent

def pdf_agent(question: str, doc_path: str, top_k: int = 3) -> dict:
    """Answer a question using ONLY the document at doc_path.

    Returns {"answer": str, "chunks": [...], "source": doc_path}.
    "chunks" are the cited source chunks (with scores) the answer
    came from. When nothing relevant is found, the answer says the
    information is not in the document.
    """
    text = extract_text(doc_path)
    if not text.strip():
        return {
            "answer": "I don't know — the document appears to be empty.",
            "chunks": [],
            "source": doc_path,
        }
    chunks = chunk_text(text)
    results = search_chunks(question, chunks, top_k=top_k)
    relevant = [r for r in results if r["score"] >= MIN_SCORE]

    # Topic gate: the best chunk must actually contain what the
    # question asks about — not just a shared name or stopword.
    if relevant:
        topics = _topic_tokens(question)
        if topics:
            best_tokens = set(_content_tokens(relevant[0]["chunk"]))
            covered = sum(1 for t in topics if t in best_tokens)
            if covered / len(topics) < MIN_TOPIC_COVERAGE:
                relevant = []

    if not relevant:
        return {
            "answer": (
                "I don't know — that information is not in the document."
            ),
            "chunks": [],
            "source": doc_path,
        }

    # Answer with the sentences that actually mention the question's
    # topic words, instead of dumping whole 500-char chunks. The full
    # chunks are still returned in "chunks" so the answer can be checked.
    topics = set(_topic_tokens(question))
    sentences: list[str] = []
    for item in relevant:
        for sentence in re.split(r"(?<=[.!?])\s+", item["chunk"]):
            sentence = sentence.strip()
            if not sentence:
                continue
            if not topics or topics & set(_content_tokens(sentence)):
                if sentence not in sentences:
                    sentences.append(sentence)
    evidence = "\n".join(sentences) if sentences else "\n---\n".join(
        r["chunk"] for r in relevant
    )
    return {
        "answer": (
            "Based on the document:\n\n" + evidence
        ),
        "chunks": relevant,
        "source": doc_path,
    }

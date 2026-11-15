#!/usr/bin/env python3
"""PDF Q&A Agent — CLI.

Usage:
    python main.py sample_resume.txt "Which skills are mentioned in this resume?"
    python main.py sample_resume.txt            # interactive mode
    python main.py                              # asks for a document, then interactive

The agent answers ONLY from the document and prints the source
chunks it used, so every answer can be checked.
"""
import sys

from agent import pdf_agent


def ask(doc_path: str, question: str) -> None:
    try:
        result = pdf_agent(question, doc_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return
    except (ImportError, ValueError) as exc:
        print(f"Error: {exc}")
        return

    print(f"\nQuestion: {question}")
    print(f"Source: {result['source']}")
    print("\nAnswer:")
    print(result["answer"])
    if result["chunks"]:
        print("\nSource chunks used:")
        for i, item in enumerate(result["chunks"], 1):
            print(f"  [{i}] (score {item['score']:.3f}) {item['chunk']}")
    else:
        print("\nSource chunks used: none — no relevant text found.")


def main(argv: list[str]) -> int:
    if len(argv) >= 3:
        ask(argv[1], " ".join(argv[2:]))
        return 0

    if len(argv) == 2:
        doc_path = argv[1]
    else:
        doc_path = input("Document (.txt, .md or .pdf): ").strip()
        if not doc_path:
            print("No document given.")
            return 1

    print(f"Loaded: {doc_path}")
    print("Ask questions about the document. Type 'quit' to exit.")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not question:
            continue
        ask(doc_path, question)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

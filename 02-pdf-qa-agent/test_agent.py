"""Tests for the PDF Q&A Agent — run:  python -m unittest test_agent -v"""
import os
import unittest

from agent import chunk_text, pdf_agent, search_chunks

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "sample_resume.txt")


class TestChunking(unittest.TestCase):
    def test_chunking_produces_overlapping_chunks(self):
        text = " ".join(f"word{i}" for i in range(300))  # ~2000 chars
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 500)
        # Overlap: a long stretch at the start of chunk 2 must also
        # appear in chunk 1 (the 100-char overlap, allowing for the
        # word-boundary trim and stripped whitespace).
        self.assertIn(chunks[1][:60], chunks[0])

    def test_short_text_is_one_chunk(self):
        self.assertEqual(chunk_text("Hello world"), ["Hello world"])

    def test_empty_text_is_no_chunks(self):
        self.assertEqual(chunk_text("   "), [])


class TestRetrieval(unittest.TestCase):
    def test_retrieval_ranks_relevant_chunk_first(self):
        chunks = [
            "The cat sat on the mat all afternoon.",
            "Python, SQL and Power BI are the skills listed here.",
            "The train leaves the station at nine in the morning.",
        ]
        results = search_chunks("Which skills are mentioned?", chunks)
        self.assertTrue(results)
        self.assertIn("Python", results[0]["chunk"])
        self.assertGreater(results[0]["score"], 0)

    def test_retrieval_returns_nothing_for_unrelated_query(self):
        chunks = ["Python, SQL and Power BI are the skills listed here."]
        results = search_chunks("What is the capital of France?", chunks)
        self.assertEqual(results, [])


class TestAgent(unittest.TestCase):
    def test_agent_answers_from_sample_resume(self):
        result = pdf_agent(
            "Which skills are mentioned in this resume?", SAMPLE
        )
        self.assertIn("Python", result["answer"])
        self.assertIn("SQL", result["answer"])
        self.assertTrue(result["chunks"])

    def test_agent_says_not_in_document_for_unrelated_question(self):
        result = pdf_agent("What is the capital of France?", SAMPLE)
        self.assertIn("not in the document", result["answer"])
        self.assertEqual(result["chunks"], [])

    def test_agent_says_not_in_document_for_missing_fact(self):
        result = pdf_agent("What is Alex Carter's salary?", SAMPLE)
        self.assertIn("not in the document", result["answer"])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            pdf_agent("Hello?", os.path.join(HERE, "does-not-exist.txt"))


if __name__ == "__main__":
    unittest.main()

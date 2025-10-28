"""PDF retrieval tool for LangChain agents."""

from typing import Optional

from langchain.tools import BaseTool
from pydantic import Field

from src.rag.service import RAGService


class PDFRetrievalTool(BaseTool):
    """Tool for searching academic papers in vector store.

    This tool wraps the existing DocumentRetriever from Task 2.1
    and formats results for consumption by the ReAct agent.
    """

    name: str = "pdf_retrieval"
    description: str = """Search academic papers on generative AI and text-to-SQL.
Use this tool when the query asks about:
- Experimental results from papers (accuracies, benchmarks)
- Specific papers or authors in the corpus
- Model comparisons or state-of-the-art approaches
- Methodologies or techniques from academic research
- Text-to-SQL approaches, Spider dataset, prompt templates

Input: A search query string
Output: Relevant document chunks with sources and page numbers"""

    rag_service: RAGService
    session_id: str
    min_similarity_score: float = 0.5  # Configurable minimum similarity threshold

    def _run(self, query: str) -> str:
        """Execute PDF retrieval and format for agent.

        Retrieves relevant document chunks from the vector store.
        Only returns documents with similarity score > min_similarity_score.
        """
        # Use retriever to get relevant documents
        documents = self.rag_service.retriever.retrieve(query, top_k=5)

        # Filter by minimum similarity score
        filtered_docs = [doc for doc in documents if doc['score'] > self.min_similarity_score]

        # Format for LLM consumption
        if not filtered_docs:
            return f"No relevant documents found in the academic papers (all similarity scores ≤ {self.min_similarity_score})."

        formatted = []
        for i, doc in enumerate(filtered_docs, 1):
            formatted.append(
                f"[Document {i}] (Source: {doc['source']}, Page: {doc['page']}, Score: {doc['score']:.2f})\n"
                f"{doc['text']}\n"
            )

        return "\n".join(formatted)

    async def _arun(self, query: str) -> str:
        """Async version (not used yet)."""
        return self._run(query)

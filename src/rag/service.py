"""RAG service orchestrating retrieval and generation."""

import uuid
from typing import Any

from src.rag.retriever.document_retriever import DocumentRetriever
from src.rag.utils import format_documents
from tools.llm.client.base import BaseLLM
from tools.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """Lightweight RAG service for document retrieval and generation.

    Provides document retrieval with optional LLM generation.
    Agents handle conversation state through LangGraph checkpointer.

    Example:
        >>> # Just retrieval (used by PDFRetrievalTool)
        >>> rag = RAGService(retriever=retriever)
        >>> docs = rag.retriever.retrieve("query", top_k=5)
        >>>
        >>> # With generation (for simple Q&A)
        >>> rag = RAGService(retriever=retriever, llm_client=llm)
        >>> response = rag.answer_question("What is RAG?")
    """

    def __init__(
        self,
        document_retriever: DocumentRetriever,
        llm_client: BaseLLM = None,
    ):
        """Initialize RAG service.

        Args:
            document_retriever: Document retriever for semantic search
            llm_client: LLM client for answer generation (optional)
        """
        self.retriever = document_retriever
        self.llm_client = llm_client
        logger.info("RAGService initialized")

    def answer_question(
        self,
        question: str,
        session_id: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Answer a question using RAG pipeline (stateless).

        Simple pipeline for document retrieval + LLM generation.
        No session memory - agents handle conversation state via LangGraph.

        Pipeline:
        1. Retrieve relevant documents from vector store
        2. Build prompt with context + question
        3. Generate answer using LLM dotprompt
        4. Return answer with sources

        Args:
            question: User question
            session_id: Session identifier (optional, for logging/tracing only)
            top_k: Number of documents to retrieve (1-20)

        Returns:
            Dictionary with:
                - answer: Generated answer
                - sources: List of source documents
                - session_id: Session identifier (for compatibility)
                - message_count: Always 2 (user question + assistant answer)

        Raises:
            ValueError: If question is empty or parameters invalid
            Exception: If retrieval or generation fails

        Example:
            >>> response = rag.answer_question("What is RAG?", top_k=5)
            >>> print(response["answer"])
        """
        # Validate input
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if top_k < 1 or top_k > 20:
            raise ValueError("top_k must be between 1 and 20")

        # Generate session_id if not provided (for logging/tracing only)
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated session_id: {session_id}")

        try:
            # Step 1: Retrieve relevant documents
            logger.debug(f"Retrieving top-{top_k} documents for question")
            documents = self.retriever.retrieve(
                query=question,
                top_k=top_k
            )
            logger.info(f"Retrieved {len(documents)} documents")

            if not documents:
                logger.warning("No documents retrieved from vector store")

            # Step 2: Build prompt variables
            context = format_documents(documents)

            prompt_variables = {
                "question": question,
                "context": context,
                "history": "",  # No history - agents handle this
            }

            logger.debug(f"Prompt variables prepared (context: {len(context)} chars)")

            # Step 3: Generate answer using LLM dotprompt
            if not self.llm_client:
                raise ValueError("LLM client not configured - cannot generate answers")

            logger.debug("Generating answer with LLM using dotprompt")
            answer = self.llm_client.generate(
                prompt_variables=prompt_variables
            )
            logger.info(f"Generated answer ({len(answer)} chars)")

            # Step 4: Return response
            response = {
                "answer": answer,
                "sources": documents,
                "session_id": session_id,
                "message_count": 2,  # Question + Answer
            }

            logger.info(f"RAG pipeline completed successfully (session: {session_id})")
            return response

        except ValueError as e:
            logger.error(f"Validation error in RAG pipeline: {e}")
            raise

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}", exc_info=True)
            raise Exception(f"Failed to generate answer: {e}") from e

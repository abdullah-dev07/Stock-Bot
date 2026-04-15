import os
import asyncio

from ...config import DATA_DIR
from ...services import rag_service, stock_service


class RagHandler:

    @staticmethod
    async def initiate(company_name: str, context: dict) -> dict:
        """Load or fetch the 10-K filing and build the vector store.

        Returns a result dict with 'message' and 'company_name'.
        Raises RuntimeError if the document cannot be obtained.
        """
        # Currently hardcoded — to be made dynamic later
        ticker = "AMZN"
        actual_name = "Amazon"

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        file_name = f"{actual_name.replace(' ', '_')}_10k.txt"
        file_path = os.path.join(DATA_DIR, file_name)

        document_text = None
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        else:
            document_text = await asyncio.to_thread(
                stock_service.get_10k_filing_text, ticker
            )
            if document_text:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(document_text)

        if not document_text:
            raise RuntimeError(
                f"Sorry, I was unable to retrieve the 10-K report for {actual_name}."
            )

        await rag_service.create_vector_store_from_text(document_text, actual_name)
        return {
            "message": f"The latest 10-K report for {actual_name} is ready. What would you like to know?",
            "company_name": actual_name,
        }

    @staticmethod
    def query(company_name: str, question: str):
        """Returns an async generator that streams the RAG answer."""
        return rag_service.query_rag_pipeline(company_name, question)

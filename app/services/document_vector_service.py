"""
Document Vectorization Service
Indexes city reports (PDFs and Markdown) into ChromaDB for semantic search
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from app.config.defaults import defaults


class DocumentVectorService:
    def __init__(self, persist_directory: str = "data/chroma_db_city_reports"):
        """
        Initialize the document vectorization service

        Args:
            persist_directory: Directory to store ChromaDB data
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize sentence transformer model from config
        model_name = defaults.get_default("vector_search", "embedding_model")
        self.model = SentenceTransformer(model_name)

        # Get or create collection using config
        collection_name = defaults.get_default("data", "vector_db_collection", "city_insights")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "City and region intelligence reports"}
        )

        print(f"✓ DocumentVectorService initialized with {self.collection.count()} documents")

    def load_markdown_file(self, file_path: str) -> str:
        """Load text content from a Markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_pdf_file(self, file_path: str) -> str:
        """Load text content from a PDF file"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    def extract_city_region_from_path(self, file_path: str) -> tuple:
        """
        Extract city and region from file path

        Examples:
        - docs/city-reports/Pune/Pune.md -> (Pune, None)
        - docs/city-reports/Pune/regions/Chakan,_Pune.pdf -> (Pune, Chakan)
        """
        parts = Path(file_path).parts

        # Find the city-reports index
        try:
            city_reports_idx = parts.index('city-reports')
        except ValueError:
            return (None, None)

        # City is the next directory
        if len(parts) > city_reports_idx + 1:
            city = parts[city_reports_idx + 1]
        else:
            return (None, None)

        # Check if there's a regions subdirectory
        if len(parts) > city_reports_idx + 2 and parts[city_reports_idx + 2] == 'regions':
            # Extract region from filename (e.g., "Chakan,_Pune.pdf" -> "Chakan")
            filename = Path(file_path).stem
            region = filename.split(',')[0].replace('_', ' ')
            return (city, region)

        return (city, None)

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to split
            chunk_size: Maximum words per chunk (from config if not provided)
            overlap: Number of words to overlap between chunks (from config if not provided)
        """
        # Use config defaults if not provided
        if chunk_size is None:
            chunk_size = defaults.get_default("vector_search", "chunk_size", 500)
        if overlap is None:
            overlap = defaults.get_default("vector_search", "chunk_overlap", 50)

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def extract_salient_features(self, text: str, city: str, region: Optional[str] = None) -> List[str]:
        """
        Extract salient features from text using pattern matching

        Looks for:
        - Executive insights
        - Key metrics (population, density, prices)
        - Infrastructure mentions (metro, roads)
        - Economic indicators (IT hub, industrial zone)
        - Cultural/geographic features
        """
        salient_features = []

        # Patterns to match salient information
        patterns = [
            r'^\*\*.*?\*\*.*?(?=\n\n|\n\*\*|$)',  # Markdown bold headings with content
            r'- \*\*.*?\*\*.*?(?=\n|$)',  # List items with bold
            r'(IT hub|industrial|metro|infrastructure|population|density|price|₹\d+)',  # Key terms
        ]

        # Extract executive insights section if present
        executive_match = re.search(r'## 1\. Executive Insights.*?(?=##|\Z)', text, re.DOTALL)
        if executive_match:
            executive_text = executive_match.group(0)
            # Split into bullet points
            for line in executive_text.split('\n'):
                if line.startswith('- **') or line.startswith('* **'):
                    salient_features.append(line.strip())

        # Extract regional micro-market insights
        if region:
            region_pattern = rf'### {region}.*?(?=###|\Z)'
            region_match = re.search(region_pattern, text, re.DOTALL | re.IGNORECASE)
            if region_match:
                region_text = region_match.group(0)
                for line in region_text.split('\n'):
                    if line.startswith('- **') or line.startswith('* **'):
                        salient_features.append(line.strip())

        return salient_features

    def index_document(self, file_path: str):
        """
        Index a single document (PDF or Markdown) into ChromaDB

        Args:
            file_path: Path to the document file
        """
        # Extract city and region from path
        city, region = self.extract_city_region_from_path(file_path)

        if not city:
            print(f"⚠ Could not extract city from {file_path}")
            return

        # Load document content
        if file_path.endswith('.pdf'):
            content = self.load_pdf_file(file_path)
            doc_type = 'pdf'
        elif file_path.endswith('.md'):
            content = self.load_markdown_file(file_path)
            doc_type = 'markdown'
        else:
            print(f"⚠ Unsupported file type: {file_path}")
            return

        # Extract salient features
        salient_features = self.extract_salient_features(content, city, region)

        # Chunk the document
        chunks = self.chunk_text(content)

        # Create document IDs
        doc_ids = [f"{city}_{region or 'city'}_{doc_type}_{i}" for i in range(len(chunks))]

        # Create metadata for each chunk
        metadatas = [{
            'city': city,
            'region': region or 'city',
            'source_file': file_path,
            'doc_type': doc_type,
            'chunk_index': i
        } for i in range(len(chunks))]

        # Add documents to collection
        self.collection.add(
            documents=chunks,
            ids=doc_ids,
            metadatas=metadatas
        )

        print(f"✓ Indexed {len(chunks)} chunks from {city}/{region or 'city'} ({doc_type})")

    def index_all_documents(self, base_path: str = "docs/city-reports"):
        """
        Index all documents in the city-reports directory

        Args:
            base_path: Base path to the city-reports directory
        """
        indexed_count = 0

        # Find all PDF and Markdown files
        for file_path in Path(base_path).rglob('*.pdf'):
            self.index_document(str(file_path))
            indexed_count += 1

        for file_path in Path(base_path).rglob('*.md'):
            self.index_document(str(file_path))
            indexed_count += 1

        print(f"✓ Indexed {indexed_count} documents. Total chunks: {self.collection.count()}")

    def query_city_insights(self, city: str, region: Optional[str] = None, n_results: int = None) -> Dict:
        """
        Query city/region insights using semantic search

        Args:
            city: City name (e.g., "Pune")
            region: Optional region name (e.g., "Chakan")
            n_results: Number of results to return (from config if not provided)

        Returns:
            Dict with salient features and relevant text chunks
        """
        # Use config default if not provided
        if n_results is None:
            n_results = defaults.get_default("vector_search", "top_k_results", 5)

        # Build query
        if region:
            query = f"What are the key features, economy, infrastructure, and characteristics of {region}, {city}?"
            where_filter = {
                "$and": [
                    {"city": {"$eq": city}},
                    {"region": {"$eq": region}}
                ]
            }
        else:
            query = f"What are the key features, economy, infrastructure, and characteristics of {city}?"
            where_filter = {"city": {"$eq": city}}

        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        if not results['documents'] or not results['documents'][0]:
            return {
                'city': city,
                'region': region,
                'salient_features': [],
                'error': 'No data found for this location'
            }

        # Extract salient features from top results
        salient_features = []
        for doc in results['documents'][0]:
            # Extract key sentences (those starting with -, *, or containing key terms)
            for line in doc.split('\n'):
                line = line.strip()
                if (line.startswith('- **') or line.startswith('* **') or
                    'IT hub' in line or 'industrial' in line or 'metro' in line or
                    'infrastructure' in line or '₹' in line):
                    if line not in salient_features and len(line) > 20:
                        salient_features.append(line)

        return {
            'city': city,
            'region': region or city,
            'salient_features': salient_features[:10],  # Top 10 features
            'full_context': results['documents'][0][:3]  # Top 3 chunks
        }


# Singleton instance
_document_vector_service: Optional[DocumentVectorService] = None


def get_document_vector_service() -> DocumentVectorService:
    """Get or create the singleton DocumentVectorService instance"""
    global _document_vector_service
    if _document_vector_service is None:
        _document_vector_service = DocumentVectorService()
    return _document_vector_service

"""
Vector Database Service - City Insights RAG System

Implements semantic search over city market reports using ChromaDB and
sentence-transformers for intelligent insights enrichment.
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import hashlib


class VectorDBService:
    """
    Manages vector embeddings and semantic search for city market reports
    """

    def __init__(self, persist_directory: str = "data/chroma_db"):
        """
        Initialize ChromaDB client and embedding model

        Args:
            persist_directory: Path to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Load embedding model (384-dimensional, fast, good for semantic search)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="city_insights",
            metadata={"description": "City market reports and insights"}
        )

        print(f"✓ VectorDB initialized with {self.collection.count()} documents")

    def _chunk_markdown_by_sections(self, markdown_content: str, city: str) -> List[Dict[str, Any]]:
        """
        Intelligently chunk markdown by sections, preserving context

        Args:
            markdown_content: Raw markdown content
            city: City name

        Returns:
            List of chunk dictionaries with text, metadata
        """
        chunks = []

        # Split by headers (##, ###, etc.)
        sections = re.split(r'\n##+ ', markdown_content)

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # Extract section title and content
            lines = section.split('\n', 1)
            section_title = lines[0].strip() if lines else f"Section {i}"
            section_content = lines[1] if len(lines) > 1 else ""

            # Skip very short sections
            if len(section_content.strip()) < 50:
                continue

            # Extract micro-markets mentioned in content
            micro_markets = self._extract_micro_markets(section_content)

            # Create chunk metadata
            metadata = {
                "city": city,
                "section": section_title,
                "micro_markets": ",".join(micro_markets) if micro_markets else "",
                "chunk_index": i,
                "chunk_type": self._classify_section_type(section_title)
            }

            # For tables, extract locality data separately
            if '|' in section_content and 'Locality' in section_content:
                table_chunks = self._parse_table_as_chunks(section_content, city, section_title)
                chunks.extend(table_chunks)
            else:
                # Full section chunk
                chunk_text = f"{section_title}\n\n{section_content}"
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata
                })

        return chunks

    def _extract_micro_markets(self, text: str) -> List[str]:
        """Extract mentioned micro-market/locality names"""
        # Common Mumbai micro-markets
        micro_markets = [
            "Malabar Hill", "Altamount Road", "Cuffe Parade", "Worli", "Bandra", "Juhu",
            "Powai", "Santacruz", "Andheri", "Goregaon", "Kandivali", "Chembur", "Kurla",
            "Borivali", "Mira Road", "Panvel", "Virar", "Thane", "Navi Mumbai",
            # Pune markets
            "Koregaon Park", "Kalyani Nagar", "Hinjewadi", "Viman Nagar", "Kharadi",
            "Hadapsar", "Pune Camp", "Deccan", "Pimpri", "Chinchwad", "Wakad", "Baner"
        ]

        found = []
        for market in micro_markets:
            if market.lower() in text.lower():
                found.append(market)

        return list(set(found))

    def _classify_section_type(self, section_title: str) -> str:
        """Classify section type for better retrieval"""
        title_lower = section_title.lower()

        if any(word in title_lower for word in ['executive', 'overview', 'summary']):
            return "executive_summary"
        elif any(word in title_lower for word in ['table', 'indicator', 'comparative']):
            return "data_table"
        elif any(word in title_lower for word in ['region', 'suburb', 'corridor', 'micro-market']):
            return "regional_analysis"
        elif any(word in title_lower for word in ['infrastructure', 'amenities', 'schools', 'hospitals', 'malls']):
            return "social_infrastructure"
        elif any(word in title_lower for word in ['outlook', 'investment', 'forecast', 'projection']):
            return "future_outlook"
        else:
            return "general"

    def _parse_table_as_chunks(self, table_content: str, city: str, section_title: str) -> List[Dict[str, Any]]:
        """Parse markdown table into individual locality chunks"""
        chunks = []
        lines = table_content.split('\n')

        headers = []
        for line in lines:
            if '|' not in line:
                continue

            cols = [c.strip() for c in line.split('|')[1:-1]]  # Remove empty first/last

            if not headers:
                headers = cols
                continue

            if '---' in line or not cols[0]:  # Skip separator or empty rows
                continue

            # Create a locality-specific chunk
            locality = cols[0]
            locality_data = dict(zip(headers, cols))

            # Format as readable text
            locality_text = f"**{locality}** ({city})\n\n"
            for key, value in locality_data.items():
                if key != 'Locality':
                    locality_text += f"- {key}: {value}\n"

            chunks.append({
                "text": locality_text,
                "metadata": {
                    "city": city,
                    "section": section_title,
                    "micro_markets": locality,
                    "chunk_type": "locality_data",
                    "locality": locality
                }
            })

        return chunks

    def ingest_city_report(self, report_path: str, city: str) -> int:
        """
        Ingest a single city report into vector database

        Args:
            report_path: Path to markdown report
            city: City name

        Returns:
            Number of chunks indexed
        """
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Chunk the document
        chunks = self._chunk_markdown_by_sections(content, city)

        if not chunks:
            print(f"⚠ No chunks extracted from {city} report")
            return 0

        # Generate IDs, embeddings, and metadata
        ids = []
        texts = []
        metadatas = []

        for chunk in chunks:
            # Create unique ID based on content hash
            chunk_id = hashlib.md5(chunk["text"].encode()).hexdigest()
            ids.append(chunk_id)
            texts.append(chunk["text"])
            metadatas.append(chunk["metadata"])

        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"✓ Indexed {len(chunks)} chunks from {city} report")
        return len(chunks)

    def ingest_all_reports(self, reports_dir: str = "docs/city-reports") -> Dict[str, int]:
        """
        Ingest all city reports from directory

        Args:
            reports_dir: Directory containing markdown reports

        Returns:
            Dictionary mapping city -> chunk count
        """
        reports_path = Path(reports_dir)
        stats = {}

        for report_file in reports_path.glob("*.md"):
            city = report_file.stem  # Filename without extension
            chunk_count = self.ingest_city_report(str(report_file), city)
            stats[city] = chunk_count

        return stats

    def semantic_search(
        self,
        query: str,
        city: Optional[str] = None,
        section_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over city insights

        Args:
            query: Natural language query
            city: Optional filter by city
            section_type: Optional filter by section type
            n_results: Number of results to return

        Returns:
            List of matching chunks with metadata and scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Build where clause for filtering
        # ChromaDB requires explicit $and operator for multiple conditions
        where_clause = None
        conditions = []
        if city:
            conditions.append({"city": city})
        if section_type:
            conditions.append({"chunk_type": section_type})

        if len(conditions) > 1:
            where_clause = {"$and": conditions}
        elif len(conditions) == 1:
            where_clause = conditions[0]

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted_results = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "rank": i + 1
                })

        return formatted_results

    def get_city_overview(self, city: str) -> Optional[str]:
        """Get executive summary for a city"""
        results = self.semantic_search(
            query=f"{city} market overview executive summary",
            city=city,
            section_type="executive_summary",
            n_results=1
        )

        if results:
            return results[0]['text']
        return None

    def get_locality_insights(self, locality: str, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get insights for a specific locality/micro-market"""
        results = self.semantic_search(
            query=f"{locality} price trends amenities infrastructure",
            city=city,
            n_results=3
        )

        # Filter results that actually mention the locality
        filtered = [r for r in results if locality.lower() in r['text'].lower()]
        return filtered if filtered else results[:1]

    def enrich_project_insights(self, city: str, location: str, price_psf: float) -> Dict[str, Any]:
        """
        Enrich project data with contextual market insights

        Args:
            city: City name
            location: Locality/micro-market
            price_psf: Price per square foot

        Returns:
            Dictionary with market context, comparables, trends
        """
        # Search for location-specific insights
        location_results = self.get_locality_insights(location, city)

        # Search for price context
        price_query = f"{city} {location} price trends {price_psf} per square foot market comparison"
        price_results = self.semantic_search(price_query, city=city, n_results=2)

        # Search for infrastructure/amenities
        infra_query = f"{location} {city} malls schools hospitals infrastructure amenities"
        infra_results = self.semantic_search(infra_query, city=city, section_type="social_infrastructure", n_results=2)

        return {
            "location_insights": location_results[0] if location_results else None,
            "price_context": price_results[0] if price_results else None,
            "infrastructure": infra_results[0] if infra_results else None,
            "market_overview": self.get_city_overview(city)
        }

    def reset_database(self):
        """Reset/clear the entire database (use with caution!)"""
        self.client.reset()
        self.collection = self.client.get_or_create_collection(name="city_insights")
        print("✓ Database reset complete")


# Singleton instance
_vector_db_instance: Optional[VectorDBService] = None

def get_vector_db() -> VectorDBService:
    """Get or create VectorDB singleton instance"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDBService()
    return _vector_db_instance

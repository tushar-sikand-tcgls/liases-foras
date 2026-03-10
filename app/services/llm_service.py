"""
LLM Service: Intelligent Question Answering using Gemini

Two modes:
1. Knowledge Graph Mode: Uses our data as golden truth (no hallucinations)
2. General Query Mode: Uses LLM's knowledge with enrichment and confidence scoring
"""

import os
import json
import re
import numpy as np
import requests
from typing import Dict, Any, Optional, List, Tuple
import google.generativeai as genai
from spellchecker import SpellChecker
from app.services.data_service import data_service


class LLMService:
    """
    LLM service for intelligent question answering

    Two Query Modes:
    1. Knowledge Graph (Golden Truth): Answers based ONLY on our data
    2. General Query: Answers general real estate questions with enrichment
    """

    # Static metric descriptions mapping (cached in RAM)
    # Maps metric keys to human-readable descriptions for tooltip lookup
    METRIC_DESCRIPTIONS = {
        # L0 - Raw Dimensions
        'totalSupplyUnits': 'Units',
        'annualSalesUnits': 'Units',
        'projectSizeAcres': 'Area',
        'projectSizeUnits': 'Units',
        'unitSaleableSizeSqft': 'Unit Saleable Size',
        'launchDate': 'Time',
        'possessionDate': 'Time',
        'annualSalesValueCr': 'Cash',
        # L1 - Derived Metrics
        'currentPricePSF': 'Price per Sqft',
        'launchPricePSF': 'Price per Sqft',
        'salesVelocityPctPerMonth': 'Sales Velocity',
        'soldPct': 'Percentage Sold',
        'unsoldPct': 'Percentage Unsold',
        # L2 - Financial Metrics
        'npvCr': 'Net Present Value',
        'irrPct': 'Internal Rate of Return',
        'paybackPeriodYears': 'Payback Period',
        'profitabilityIndex': 'Profitability Index',
        'roiPct': 'Return on Investment',
        'totalRevenueCr': 'Cash',
        'totalCostCr': 'Cash',
        'absorptionRatePctPerYear': 'Absorption Rate',
        'projectDurationYears': 'Time'
    }

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Using Gemini 2.0 Flash for fast, intelligent responses
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Load project names from knowledge graph for smart routing
        self.kg_projects = self._load_kg_project_names()

        # Initialize spell checker
        self.spell_checker = SpellChecker()

        # Load term definitions for tooltips
        self.term_definitions = self._load_term_definitions()

        # Add real estate domain words and common words to improve corrections
        real_estate_words = [
            # Real estate metrics & acronyms
            'psf', 'bhk', 'sqft', 'rera', 'npv', 'irr', 'roi', 'asp',
            'crore', 'lakh', 'cr', 'lacs', 'saleable', 'possession',
            'absorption', 'velocity', 'units', 'unit',

            # Locations
            'chakan', 'pune', 'mumbai', 'navi', 'andheri',
            'baner', 'hinjewadi', 'kharghar',

            # Common amenities & places
            'hospitals', 'hospital', 'restaurants', 'restaurant',
            'hotels', 'hotel', 'atms', 'clinics', 'clinic',
            'salons', 'salon', 'malls', 'mall', 'gym', 'gyms',
            'clubhouse', 'playground', 'parking'
        ]
        self.spell_checker.word_frequency.load_words(real_estate_words)

        # Load all project names from knowledge graph to avoid correcting them
        try:
            projects = data_service.get_all_projects()
            project_words = []
            for project in projects:
                project_name = data_service.get_value(project.get('projectName', ''))
                if project_name:
                    # Add full name and individual words
                    name_normalized = ' '.join(project_name.split())
                    project_words.append(name_normalized.lower())
                    # Add individual words from project name
                    for word in name_normalized.lower().split():
                        if len(word) > 2:  # Skip very short words
                            project_words.append(word)

            if project_words:
                self.spell_checker.word_frequency.load_words(project_words)
                print(f"[DEBUG] Loaded {len(project_words)} project name words to spell checker")
        except Exception as e:
            print(f"[WARNING] Could not load project names for spell checker: {e}")

        # Vectorized query classification: Example queries for each mode
        self.kg_query_examples = [
            # Units & Counts
            "How many units does this project have?",
            "What is the total supply of units?",
            "How many 2BHK units are there?",
            "Show me the unit count",

            # Pricing & Financials
            "What is the price per square foot?",
            "What is the current PSF?",
            "What is the launch price?",
            "What is the sales velocity?",
            "What is the absorption rate?",
            "What is the total revenue?",
            "Calculate the NPV",
            "What is the IRR?",
            "Show me the ROI",
            "What is the payback period?",
            "What is the profitability index?",

            # Project Info
            "What is the location of this project?",
            "Who is the developer?",
            "What is the launch date?",
            "When is possession date?",
            "Is it RERA registered?",
            "What is the project size in acres?",
            "What is the average unit size?",

            # Sales & Performance
            "How many units are sold?",
            "What percentage is sold?",
            "What is the unsold percentage?",
            "What is the annual sales value?"
        ]

        self.llm_query_examples = [
            # Amenities
            "Does this project have a swimming pool?",
            "Is there a gym available?",
            "Does it have yoga facilities?",
            "Is there a clubhouse?",
            "Does it have parking?",
            "Is there a library?",
            "Does it have a playground?",
            "Is there a basketball court?",
            "Does it have home automation?",
            "Is there 24/7 security?",

            # Proximity & Location
            "How far is the nearest hospital?",
            "Is there a school nearby?",
            "Where is the nearest metro station?",
            "Are there ATMs near the project?",
            "Is there a shopping mall nearby?",
            "How far is the nearest restaurant?",
            "Are there hotels near this location?",
            "Is there a petrol pump nearby?",
            "Where is the nearest market?",
            "Are there clinics near this project?",

            # Investment Advice
            "Should I invest in this project?",
            "Is this a good investment?",
            "What is the rental value?",
            "Can I get this on rent?",
            "Is this project worth buying?",
            "Give me investment recommendations"
        ]

        # Comprehensive query examples (for semantic similarity detection)
        self.comprehensive_query_examples = [
            "Show me all numbers for this project",
            "Give me all the metrics",
            "Tell me everything about this project",
            "Show me all the data",
            "Give me complete information",
            "Tell me all numbers and metrics",
            "Show me full data",
            "What are all the numbers",
            "Give me all project metrics",
            "Tell me numbers and metrics",
            "Show me comprehensive data",
            "Give me everything",
            "Tell me all the details with numbers",
            "Show me all metrics and numbers",
            "Give me all financial numbers"
        ]

        # Generate embeddings for example queries (cached)
        self._initialize_query_embeddings()

    def _load_kg_project_names(self) -> List[str]:
        """Load project names from knowledge graph for smart routing"""
        try:
            projects = data_service.get_all_projects()
            names = []
            for p in projects:
                if p.get('projectName'):
                    name = data_service.get_value(p.get('projectName', ''))
                    # Normalize: remove newlines and extra spaces
                    name_normalized = ' '.join(name.split()).lower()
                    names.append(name_normalized)
            return names
        except:
            return []

    def _load_term_definitions(self) -> Dict[str, Any]:
        """Load term definitions from static JSON file for tooltips"""
        try:
            definitions_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'term_definitions.json'
            )
            with open(definitions_path, 'r') as f:
                definitions = json.load(f)
            print(f"[DEBUG] Loaded {len(definitions)} term definitions for tooltips")
            return definitions
        except Exception as e:
            print(f"[WARNING] Could not load term definitions: {e}")
            return {}

    def _initialize_query_embeddings(self):
        """Generate and cache embeddings for example queries"""
        try:
            print("[DEBUG] Generating embeddings for query classification...")
            self.kg_embeddings = self._get_embeddings_batch(self.kg_query_examples)
            self.llm_embeddings = self._get_embeddings_batch(self.llm_query_examples)
            self.comprehensive_embeddings = self._get_embeddings_batch(self.comprehensive_query_examples)
            print(f"[DEBUG] ✓ Generated {len(self.kg_embeddings)} KG embeddings, {len(self.llm_embeddings)} LLM embeddings, and {len(self.comprehensive_embeddings)} comprehensive query embeddings")
        except Exception as e:
            print(f"[WARNING] Failed to generate embeddings, falling back to keyword-based routing: {e}")
            # Fallback: set empty embeddings, will use keyword-based routing
            self.kg_embeddings = []
            self.llm_embeddings = []
            self.comprehensive_embeddings = []

    def _get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts using Gemini"""
        embeddings = []
        for text in texts:
            try:
                # Use Gemini's embedding model
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_query"
                )
                embeddings.append(np.array(result['embedding']))
            except Exception as e:
                print(f"[WARNING] Failed to generate embedding for '{text[:50]}...': {e}")
                # Continue without this embedding
                continue
        return embeddings

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text"""
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return np.array(result['embedding'])
        except:
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _correct_spelling(self, question: str) -> str:
        """
        Correct common misspellings while preserving acronyms

        Examples:
        - "What is the hosptal nearby?" → "What is the hospital nearby?"
        - "Show me the IRR and NPV" → "Show me the IRR and NPV" (unchanged)
        - "How many untis?" → "How many units?"
        """
        # Domain-specific corrections (manual mappings for common misspellings)
        domain_corrections = {
            'untis': 'units',
            'unts': 'units',
            'restrant': 'restaurant',
            'restrants': 'restaurants',
            'hosptal': 'hospital',
            'hosptals': 'hospitals',
            'resturant': 'restaurant',
            'resturants': 'restaurants',
            'loaction': 'location',
            'loactions': 'locations',
            'appartment': 'apartment',
            'appartments': 'apartments',
        }

        words = question.split()
        corrected_words = []

        for word in words:
            # Remove punctuation for checking, but remember it
            clean_word = word.strip('.,?!;:')
            punctuation = word[len(clean_word):] if len(word) > len(clean_word) else ''

            # Skip if:
            # 1. All uppercase (likely acronym: IRR, NPV, PSF, RERA)
            # 2. Contains numbers (137562, 2BHK, 3BHK)
            # 3. Too short (<= 2 chars)
            if (clean_word.isupper() or
                any(char.isdigit() for char in clean_word) or
                len(clean_word) <= 2):
                corrected_words.append(word)
                continue

            clean_word_lower = clean_word.lower()

            # Check domain-specific corrections first
            if clean_word_lower in domain_corrections:
                corrected = domain_corrections[clean_word_lower]
                # Preserve original capitalization
                if clean_word[0].isupper():
                    corrected = corrected.capitalize()
                print(f"[SPELL] Corrected '{clean_word}' → '{corrected}' (domain)")
                corrected_words.append(corrected + punctuation)
                continue

            # Then check general spelling
            corrected = self.spell_checker.correction(clean_word_lower)

            # If correction is different, apply it
            if corrected and corrected != clean_word_lower:
                # Preserve original capitalization
                if clean_word[0].isupper():
                    corrected = corrected.capitalize()
                print(f"[SPELL] Corrected '{clean_word}' → '{corrected}'")
                corrected_words.append(corrected + punctuation)
            else:
                corrected_words.append(word)

        corrected_question = ' '.join(corrected_words)
        return corrected_question

    def _is_knowledge_graph_query_vectorized(self, question: str) -> bool:
        """
        Vectorized query classification using semantic similarity

        Compares question embedding with KG and LLM example embeddings
        Returns True if question is closer to KG examples
        """
        # Get embedding for the question
        question_embedding = self._get_embedding(question)
        if question_embedding is None:
            # Fallback to keyword-based routing
            return self._is_knowledge_graph_query_keyword_based(question)

        # Calculate average similarity with KG examples
        kg_similarities = []
        for kg_emb in self.kg_embeddings:
            similarity = self._cosine_similarity(question_embedding, kg_emb)
            kg_similarities.append(similarity)

        # Calculate average similarity with LLM examples
        llm_similarities = []
        for llm_emb in self.llm_embeddings:
            similarity = self._cosine_similarity(question_embedding, llm_emb)
            llm_similarities.append(similarity)

        # Get average scores
        avg_kg_similarity = np.mean(kg_similarities) if kg_similarities else 0.0
        avg_llm_similarity = np.mean(llm_similarities) if llm_similarities else 0.0

        print(f"[DEBUG] Vectorized routing: KG similarity={avg_kg_similarity:.3f}, LLM similarity={avg_llm_similarity:.3f}")

        # Route based on which set has higher average similarity
        # Use a slight bias towards KG (0.05) to prefer KG when similarities are close
        return avg_kg_similarity > (avg_llm_similarity + 0.05)

    def _is_knowledge_graph_query(self, question: str) -> bool:
        """
        Smart routing: Uses vectorized classification if embeddings available,
        falls back to keyword-based routing otherwise
        """
        # Check if we have embeddings
        if hasattr(self, 'kg_embeddings') and len(self.kg_embeddings) > 0:
            return self._is_knowledge_graph_query_vectorized(question)
        else:
            # Fallback to keyword-based
            return self._is_knowledge_graph_query_keyword_based(question)

    def _is_knowledge_graph_query_keyword_based(self, question: str) -> bool:
        """
        Determine if question should use knowledge graph (vs LLM)

        KG queries: Questions about data IN our knowledge graph
        - units, price, sales velocity, revenue, NPV, IRR, location, developer, dates, etc.

        LLM queries: Questions about things NOT in KG
        - amenities (swimming pool, gym, parking, etc.)
        - rent prices, market trends
        - distances from specific places
        - general real estate advice
        """
        question_lower = question.lower()

        # Keywords that indicate KG data fields (these ARE in our graph)
        kg_keywords = [
            'units', 'unit', 'price', 'psf', 'cost', 'revenue', 'sales',
            'velocity', 'sold', 'unsold', 'absorption', 'npv', 'irr', 'roi',
            'location', 'developer', 'launch', 'possession', 'rera',
            'area', 'size', 'sqft', 'acres', 'payback', 'profitability',
            # Comprehensive overview patterns (trigger Section 1 + 2 + 3 response)
            'tell me about', 'overview', 'summary', 'complete info',
            'full details', 'everything about', 'all about'
        ]

        # Keywords that indicate LLM queries (these are NOT in our graph)
        llm_keywords = [
            # Amenities (general)
            'amenities', 'amenity', 'facilities', 'features',

            # Sports & Recreation
            'swimming pool', 'pool', 'gym', 'fitness', 'yoga', 'meditation',
            'tennis', 'badminton', 'court', 'table-tennis', 'squash',
            'pickleball', 'turf', 'basketball', 'golf', 'sports',

            # Common Areas
            'clubhouse', 'club', 'community', 'hall', 'theatre', 'movie',
            'mini-theatre', 'library', 'park', 'playground', 'garden',
            'lawn', 'fountain', 'balcony', 'balconies',

            # Technology & Services
            'home automation', 'security camera', 'wifi', 'printer',
            'solar', 'smart home', 'cctv',

            # Luxury Amenities
            'jacuzzi', 'spa', 'sauna', 'creche', 'daycare',

            # Parking & Security
            'parking', 'security', 'gated', 'surveillance',

            # Location & Proximity
            'rent', 'rental', 'lease', 'distance from', 'how far', 'nearby',
            'schools near', 'hospitals near', 'malls near', 'metro near',
            'atm near', 'atms near', 'hotel near', 'hotels near',
            'petrol pump near', 'gas station near', 'restaurant near',
            'restaurants near', 'market near', 'markets near',
            'clinic near', 'clinics near', 'salon near', 'salons near',
            'pharmacy near', 'bank near', 'supermarket near', 'temple near',
            'mosque near', 'church near', 'bus stop near', 'railway station near',

            # Investment Advice
            'should i buy', 'is it good', 'investment advice', 'recommend'
        ]

        # Check if question contains LLM keywords → use LLM
        for keyword in llm_keywords:
            if keyword in question_lower:
                return False  # Use LLM, not KG

        # Check if question contains KG keywords → use KG
        for keyword in kg_keywords:
            if keyword in question_lower:
                # Check if we can identify ANY project (full name or partial match)
                if self._can_extract_project(question_lower):
                    return True  # Use KG

        # If project name mentioned but no specific KG keyword → still use KG
        # (might be asking "what is location of Sara City?" etc.)
        if self._can_extract_project(question_lower):
            return True

        return False  # Default to LLM for general questions

    def _can_extract_project(self, question_lower: str) -> bool:
        """Check if we can extract a project from the question"""
        # Check for full project name match
        for project_name in self.kg_projects:
            if project_name in question_lower:
                return True

        # Check for partial matches on distinctive words
        # (e.g., "Kalpavruksh" should match "Kalpavruksh Heights")
        projects = data_service.get_all_projects()
        for project in projects:
            project_name = data_service.get_value(project.get('projectName', ''))
            if not project_name:
                continue
            # Normalize project name
            project_name_normalized = ' '.join(project_name.split()).lower()
            name_words = project_name_normalized.split()

            # Check if any word from project name is in question
            # (for multi-word names, this acts as partial matching)
            for word in name_words:
                if len(word) > 4 and word in question_lower:
                    return True

        return False

    def _extract_project_from_question(self, question: str) -> Optional[Dict]:
        """
        Extract project from question by finding mentioned project name

        Strategy (NO hardcodings):
        1. Check for exact full name match first
        2. For multi-word names, check if distinctive words appear in question
        3. A word is "distinctive" if it's >3 chars and appears in only 1-2 project names
        """
        question_lower = question.lower()

        # Get all projects from knowledge graph
        projects = data_service.get_all_projects()
        print(f"[DEBUG] Extracting project from question: {question}")

        # Build word frequency map across all projects (to find distinctive words)
        word_to_projects = {}
        for project in projects:
            project_name = data_service.get_value(project.get('projectName', ''))
            if not project_name:
                continue
            # Normalize: remove newlines and extra spaces
            project_name_normalized = ' '.join(project_name.split())
            name_words = project_name_normalized.lower().split()
            for word in name_words:
                if len(word) > 3:  # Only consider words >3 chars
                    if word not in word_to_projects:
                        word_to_projects[word] = []
                    word_to_projects[word].append(project)

        # Now check each project
        for project in projects:
            project_name = data_service.get_value(project.get('projectName', ''))
            if not project_name:
                continue

            # Normalize: remove newlines and extra spaces (some project names have \n)
            project_name_normalized = ' '.join(project_name.split())
            project_name_lower = project_name_normalized.lower().strip()

            # Strategy 1: Exact full name match
            if project_name_lower in question_lower:
                print(f"[DEBUG] EXACT MATCH: {project_name_lower}")
                return project

            # Strategy 2: Distinctive word match (for multi-word names)
            name_words = project_name_lower.split()
            if len(name_words) > 1:
                # Find distinctive words (words that appear in ONLY 1 project)
                # This ensures we only match on truly unique words
                distinctive_words = [w for w in name_words if len(w) > 3 and len(word_to_projects.get(w, [])) == 1]

                for word in distinctive_words:
                    if word in question_lower:
                        print(f"[DEBUG] DISTINCTIVE WORD MATCH: '{word}' → {project_name_lower}")
                        return project

        print("[DEBUG] No project found in question")
        return None

    # ================================================================
    # TABLE FORMATTING FOR NUMERICAL DATA
    # ================================================================

    def _classify_metric_layer(self, key: str) -> Tuple[str, str, str]:
        """
        Classify a metric into its layer (L0, L1, L2, L3)

        Returns:
            Tuple of (layer, color, description)
        """
        key_lower = key.lower()

        # Layer 0: Raw Dimensions (U, L², T, C)
        # Check for keywords that indicate L0 metrics
        if any(kw in key_lower for kw in ['totalsupplyunits', 'annualsalesunits']) or key_lower == 'units':
            return ('L0', '#E3F2FD', 'Units (U)')
        elif any(kw in key_lower for kw in ['projectsizeacres', 'acres']):
            return ('L0', '#E3F2FD', 'Area (L²)')
        elif any(kw in key_lower for kw in ['projectdurationyears', 'duration']) and 'payback' not in key_lower:
            return ('L0', '#E3F2FD', 'Time (T)')
        elif any(kw in key_lower for kw in ['totalrevenue', 'totalcost', 'annualsalesvalue']):
            return ('L0', '#E3F2FD', 'Cash (C)')

        # Layer 1: Derived Metrics (Simple Ratios: C/L², C/U, U/T, L²/U, etc.)
        # IMPORTANT: unitSaleableSizeSqft is L1 with dimension L²/U
        elif any(kw in key_lower for kw in ['unitsaleablesizesqft', 'saleablesize', 'unitsize']):
            return ('L1', '#E8F5E9', 'Unit Saleable Size (L²/U)')
        elif any(kw in key_lower for kw in ['launchpricepsf', 'currentpricepsf', 'priceperpsf', 'psf']) and 'price' in key_lower:
            return ('L1', '#E8F5E9', 'Price per Sqft (C/L²)')
        elif any(kw in key_lower for kw in ['monthlysalesvelocity', 'velocity', 'salesvelocity']):
            return ('L1', '#E8F5E9', 'Sales Velocity (U/T)')
        elif 'sold' in key_lower and 'pct' in key_lower:
            return ('L1', '#E8F5E9', 'Percentage Sold (U/U)')
        elif 'unsold' in key_lower and 'pct' in key_lower:
            return ('L1', '#E8F5E9', 'Percentage Unsold (U/U)')
        elif any(kw in key_lower for kw in ['absorptionrate', 'absorption']) and 'rate' in key_lower:
            return ('L1', '#E8F5E9', 'Absorption Rate (%/T)')

        # Layer 2: Financial Metrics (Complex: NPV, IRR, etc.)
        elif 'npv' in key_lower:
            return ('L2', '#FFF3E0', 'Net Present Value')
        elif 'irr' in key_lower:
            return ('L2', '#FFF3E0', 'Internal Rate of Return')
        elif 'payback' in key_lower or (key_lower == 'period' or key_lower.endswith('period')):
            return ('L2', '#FFF3E0', 'Payback Period')
        elif 'profitability' in key_lower or (key_lower == 'index' or key_lower.endswith('index')):
            return ('L2', '#FFF3E0', 'Profitability Index')
        elif 'roi' in key_lower:
            return ('L2', '#FFF3E0', 'Return on Investment')

        # Layer 3: Optimization & Scenarios
        elif any(kw in key_lower for kw in ['optimalproductmix', 'productmix', 'optimal']):
            return ('L3', '#F3E5F5', 'Product Mix Optimization')
        elif any(kw in key_lower for kw in ['scenarioanalysis', 'scenario']):
            return ('L3', '#F3E5F5', 'Scenario Analysis')

        else:
            # Default: try to infer from common patterns
            if 'revenue' in key_lower or 'cost' in key_lower or 'value' in key_lower:
                return ('L0', '#E3F2FD', 'Cash (C)')
            elif 'size' in key_lower or 'sqft' in key_lower or 'area' in key_lower:
                return ('L1', '#E8F5E9', 'Area Metric (L²)')
            elif 'rate' in key_lower or 'pct' in key_lower or '%' in key_lower:
                return ('L1', '#E8F5E9', 'Percentage Metric')
            elif 'years' in key_lower:
                return ('L0', '#E3F2FD', 'Time (T)')
            else:
                return ('L0', '#E3F2FD', 'Raw Dimension')

    def _parse_numerical_response(self, text: str) -> Optional[List[Dict[str, str]]]:
        """
        Parse numerical key-value pairs from response text

        Returns:
            List of dicts with {key, value, unit, layer, color, description}
            or None if no numerical data found
        """
        # Pattern: key: value unit (non-greedy, stops at newline or end of line)
        # Format examples:
        # - totalSupplyUnits: 1109 count
        # - currentPricePSF: 3996 INR/sqft
        # - irrPct: 19.71 %
        pattern = r'(\w+):\s*([0-9.,\-]+)\s*([^\n\r:]+?)(?:\s*\n|\s*$)'
        matches = re.findall(pattern, text, re.MULTILINE)

        if len(matches) < 3:  # Require at least 3 metrics to format as table
            return None

        parsed_data = []
        seen_keys = set()  # Avoid duplicate keys

        for key, value, unit in matches:
            # Skip if we've already seen this key
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Clean unit (remove trailing whitespace and newlines)
            unit_clean = unit.strip()

            # Skip if unit is empty or looks like another key
            if not unit_clean or ':' in unit_clean:
                continue

            layer, color, description = self._classify_metric_layer(key)
            parsed_data.append({
                'key': key,
                'value': value,
                'unit': unit_clean,
                'layer': layer,
                'color': color,
                'description': description
            })

        # Return None if we don't have enough valid metrics
        if len(parsed_data) < 3:
            return None

        return parsed_data

    def _camel_case_to_human_readable(self, text: str) -> str:
        """
        Convert camelCase to human-readable Title Case

        Examples:
            totalSupplyUnits → Total Supply Units
            currentPricePSF → Current Price PSF
            irrPct → IRR %
            npvCr → NPV Crore
        """
        # Handle special abbreviations first
        replacements = {
            'Pct': '%',
            'Cr': 'Crore',
            'Psf': 'PSF',
            'Irr': 'IRR',
            'Npv': 'NPV',
            'Roi': 'ROI',
            'Rera': 'RERA'
        }

        # Split camelCase into words
        # Insert space before uppercase letters
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Apply special replacements
        for old, new in replacements.items():
            spaced = spaced.replace(old, new)

        # Capitalize first letter
        if spaced:
            spaced = spaced[0].upper() + spaced[1:]

        return spaced

    def _add_tooltip_to_text(self, text: str, lookup_key: str = None) -> str:
        """
        Wrap text with tooltip if definition exists

        Args:
            text: The display text (e.g., "Internal Rate of Return" or "IRR")
            lookup_key: Optional key to look up in term_definitions (if different from text)

        Returns HTML with hover tooltip that displays term definition with info icon
        """
        # Use lookup_key if provided, otherwise use text itself
        search_term = lookup_key if lookup_key else text

        # Check if we have a definition for this term
        if search_term in self.term_definitions:
            term_def = self.term_definitions[search_term]

            # Create tooltip HTML with CORRECTED hover behavior
            # Key fix: onmouseenter/onmouseleave on OUTER span, not inner tooltip
            tooltip_html = f"""<span class="tooltip-wrapper" style="position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #999;" onmouseenter="this.querySelector('.tooltip-box').style.visibility='visible'; this.querySelector('.tooltip-box').style.opacity='1';" onmouseleave="this.querySelector('.tooltip-box').style.visibility='hidden'; this.querySelector('.tooltip-box').style.opacity='0';">
{text}
<span class="tooltip-box" style="visibility: hidden; opacity: 0; width: 280px; max-width: 85vw; background-color: #fff; color: #333;
             text-align: left; border-radius: 8px; padding: 12px; position: absolute;
             z-index: 10000; bottom: 130%; left: 50%; transform: translateX(-50%);
             transition: opacity 0.3s, visibility 0.3s;
             box-shadow: 0 6px 16px rgba(0,0,0,0.2);
             border: 1px solid #ddd;
             font-style: normal;
             font-size: 12px;
             line-height: 1.5;
             white-space: normal;
             word-wrap: break-word;">
<div style="display: flex; align-items: center; margin-bottom: 8px;">
  <span style="font-size: 18px; margin-right: 8px;">ℹ️</span>
  <strong style="color: #1976d2; font-size: 14px;">{search_term}</strong>
</div>
<div style="margin-bottom: 10px; color: #555;">{term_def.get('definition', '')}</div>
<div style="background: #f0f7ff; padding: 8px; border-left: 3px solid #4CAF50; border-radius: 4px; margin-bottom: 8px;">
  <strong style="color: #2e7d32; font-size: 12px;">💡 Example:</strong>
  <div style="color: #555; font-size: 12px; margin-top: 4px;">{term_def.get('example', '')}</div>
</div>
<div style="display: flex; justify-content: space-around; font-size: 11px; padding-top: 8px; border-top: 1px solid #eee;">
  <span style="color: #4CAF50;">✓ Good: {term_def.get('good_threshold', 'N/A')}</span>
  <span style="color: #EF5350;">✗ Bad: {term_def.get('bad_threshold', 'N/A')}</span>
</div>
</span>
</span>"""
            return tooltip_html
        else:
            # No definition found, return plain text
            return text

    def _format_as_table(self, data: List[Dict[str, str]], project_name: str = "") -> str:
        """
        Format numerical data as an HTML table with layer-based color coding

        Args:
            data: List of metric dicts with key, value, unit, layer, color, description
            project_name: Name of the project (for title)

        Returns:
            HTML markdown string
        """
        # Group by layer
        layers = {'L0': [], 'L1': [], 'L2': [], 'L3': []}
        for item in data:
            layer = item['layer']
            if layer in layers:
                layers[layer].append(item)

        # Build HTML table
        html = f"""
<div style="margin: 20px 0;">
    <h4 style="color: #333; margin-bottom: 10px;">📊 All Metrics{f' - {project_name}' if project_name else ''}</h4>
    <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
        <thead>
            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <th style="padding: 12px; text-align: left; font-weight: 600;">Layer</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Metric</th>
                <th style="padding: 12px; text-align: right; font-weight: 600;">Value</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Unit</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Description</th>
            </tr>
        </thead>
        <tbody>
"""

        # Layer labels
        layer_labels = {
            'L0': 'Layer 0 - Raw Dimensions',
            'L1': 'Layer 1 - Derived Metrics',
            'L2': 'Layer 2 - Financial Metrics',
            'L3': 'Layer 3 - Optimization'
        }

        # Add rows grouped by layer
        for layer in ['L0', 'L1', 'L2', 'L3']:
            if not layers[layer]:
                continue

            for idx, item in enumerate(layers[layer]):
                # Format metric name (camelCase to Title Case)
                metric_name = self._camel_case_to_human_readable(item['key'])

                # Get proper description for tooltip lookup (from static class constant)
                proper_description = self.METRIC_DESCRIPTIONS.get(item['key'], item.get('description', ''))

                # Add tooltips to BOTH metric name AND description
                metric_name_with_tooltip = self._add_tooltip_to_text(metric_name, proper_description)
                description_with_tooltip = self._add_tooltip_to_text(proper_description)

                # Only show layer label on first row of each layer
                layer_cell = f"<strong>{layer_labels[layer]}</strong>" if idx == 0 else ""

                html += f"""
            <tr style="background-color: {item['color']}; border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px; font-size: 12px; color: #666; vertical-align: top;">{layer_cell}</td>
                <td style="padding: 10px; font-weight: 500;">{metric_name_with_tooltip}</td>
                <td style="padding: 10px; text-align: right; font-family: 'Courier New', monospace; font-weight: 600; color: #333;">{item['value']}</td>
                <td style="padding: 10px; color: #666; font-size: 13px;">{item['unit']}</td>
                <td style="padding: 10px; color: #666; font-size: 12px; font-style: italic;">{description_with_tooltip}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</div>

<div style="margin-top: 15px; padding: 12px; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px;">
    <strong style="color: #667eea;">🔍 Layer Guide:</strong>
    <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 13px; color: #666;">
        <li><strong>L0 (Blue):</strong> Raw Dimensions - Atomic units (U, L², T, C)</li>
        <li><strong>L1 (Green):</strong> Derived Metrics - Simple ratios (PSF = C/L², Velocity = U/T, Unit Size = L²/U)</li>
        <li><strong>L2 (Orange):</strong> Financial Metrics - Complex calculations (NPV, IRR, ROI)</li>
        <li><strong>L3 (Purple):</strong> Optimization - Strategic scenarios and product mix</li>
    </ul>
</div>
"""

        return html

    def answer_question(
        self,
        question: str,
        project_id: Optional[str] = None,
        force_general: bool = False,
        location_context: Optional[Dict[str, str]] = None,
        admin_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Smart routing: Knowledge graph mode OR general query mode

        Args:
            question: User's question
            project_id: Specific project ID (if None, auto-detects)
            force_general: Force general query mode (ignore knowledge graph)
            location_context: Location context for general queries
            admin_mode: If True, returns rich HTML tables; if False, returns GPT-like markdown

        Returns:
            {
                "answer": "...",
                "status": "success|error",
                "mode": "knowledge_graph|general",
                "source_layer": "..." (for KG mode)
            }
        """
        try:
            # Step 1: Correct spelling (preserves acronyms like IRR, NPV, PSF)
            corrected_question = self._correct_spelling(question)

            # If question was corrected, use the corrected version
            if corrected_question != question:
                print(f"[SPELL] Original: {question}")
                print(f"[SPELL] Corrected: {corrected_question}")
                question = corrected_question

            # Step 1.5: Check for comprehensive overview patterns BEFORE routing
            # This ensures "Tell me about PROJECT" always triggers comprehensive overview
            # regardless of vectorized/keyword-based routing
            question_lower = question.lower()
            is_comprehensive = any(pattern in question_lower for pattern in [
                'tell me about', 'overview of', 'summary of', 'complete info',
                'full details', 'everything about', 'all about'
            ])

            if is_comprehensive and not force_general:
                print(f"[ROUTING] Comprehensive overview pattern detected: {question}")
                # Route directly to knowledge graph with comprehensive mode
                return self._answer_from_knowledge_graph(question, project_id, admin_mode)

            # Step 1.75: Check for aggregation queries (sum, average, top N, etc.)
            aggregation_result = self._detect_aggregation_query(question, location_context)
            if aggregation_result:
                print(f"[ROUTING] Aggregation query detected: {aggregation_result['type']}")
                return self._handle_aggregation_query(
                    question=question,
                    aggregation_info=aggregation_result,
                    location_context=location_context,
                    admin_mode=admin_mode
                )

            # Step 2: Smart routing: Check if this is a knowledge graph query
            if not force_general and self._is_knowledge_graph_query(question):
                # Use knowledge graph mode (golden truth)
                return self._answer_from_knowledge_graph(question, project_id, admin_mode)
            else:
                # Use general query mode (with enrichment and location context)
                return self._answer_general_query(question, location_context)

        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "status": "error",
                "question": question
            }

    def _answer_from_knowledge_graph(
        self,
        question: str,
        project_id: Optional[str] = None,
        admin_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Answer using knowledge graph (golden truth - no hallucinations)

        Args:
            question: User's question
            project_id: Specific project ID (if None, auto-detects)
            admin_mode: If True, returns rich HTML tables; if False, returns GPT-like markdown
        """
        try:
            # Get project data
            if project_id:
                project = data_service.get_project(project_id)
            else:
                # Try to extract project from question
                project = self._extract_project_from_question(question)

                if not project:
                    # Default to first project if no project mentioned
                    projects = data_service.get_all_projects()
                    if not projects:
                        return {
                            "answer": "No project data available",
                            "status": "error",
                            "mode": "knowledge_graph"
                        }
                    project = projects[0]

            if not project:
                return {
                    "answer": f"Project {project_id} not found",
                    "status": "error",
                    "mode": "knowledge_graph"
                }

            # Check if this is a comprehensive "Tell me about X" query
            question_lower = question.lower()
            is_comprehensive = any(pattern in question_lower for pattern in [
                'tell me about', 'overview of', 'summary of', 'complete info',
                'full details', 'everything about'
            ])

            if is_comprehensive:
                return self._generate_comprehensive_overview(project, question, admin_mode)

            # Prepare knowledge graph context
            context = self._prepare_context(project)

            # Create prompt for Gemini (with admin_mode flag for formatting)
            prompt = self._create_kg_prompt(question, context, admin_mode)

            # Call Gemini
            response = self.model.generate_content(prompt)

            # Extract answer
            answer_text = response.text.strip()

            # Format based on admin_mode
            if admin_mode:
                # ADMIN mode: Check if answer contains numerical data - if so, format as table
                parsed_data = self._parse_numerical_response(answer_text)
                if parsed_data:
                    project_name = data_service.get_value(project.get('projectName', ''))
                    formatted_answer = self._format_as_table(parsed_data, project_name)
                else:
                    formatted_answer = answer_text
            else:
                # Regular mode: Return conversational markdown (answer_text is already conversational from prompt)
                formatted_answer = answer_text

            # Determine source layer from answer
            source_layer = self._determine_layer(answer_text, project)

            return {
                "answer": formatted_answer,
                "status": "success",
                "mode": "knowledge_graph",
                "source_layer": source_layer,
                "question": question,
                "project": {
                    "projectId": str(data_service.get_value(project.get('projectId'))),
                    "projectName": data_service.get_value(project.get('projectName'))
                }
            }

        except Exception as e:
            return {
                "answer": f"Error processing knowledge graph query: {str(e)}",
                "status": "error",
                "mode": "knowledge_graph",
                "question": question
            }

    def _answer_general_query(self, question: str, location_context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Answer general real estate query with enrichment and confidence scoring

        Anti-hallucination mechanism:
        1. Fetch web search results for grounding (Google Custom Search API)
        2. Ask LLM twice with grounded data
        3. Return only common elements

        Args:
            question: User's question
            location_context: Optional location context (region, city, state) from UI
        """
        try:
            # Step 1: Enrich the question with context
            enriched_question = self._enrich_question(question)

            # Step 2: Fetch web search results for grounding (with location context)
            search_results = self._fetch_web_search_results(enriched_question, location_context)

            # Step 3: Create prompt with search results for grounding
            prompt = self._create_general_prompt(enriched_question, search_results)

            # Step 4: Call Gemini TWICE to reduce hallucinations (with same grounded data)
            response1 = self.model.generate_content(prompt)
            response2 = self.model.generate_content(prompt)

            # Step 5: Extract answers
            answer1 = response1.text.strip()
            answer2 = response2.text.strip()

            # Step 6: Find common elements (anti-hallucination filter)
            common_answer = self._find_common_elements(answer1, answer2)

            return {
                "answer": common_answer,
                "status": "success",
                "mode": "general",
                "enriched_question": enriched_question,
                "original_question": question,
                "double_check": True,  # Indicates this answer was verified twice
                "web_grounded": search_results is not None  # Indicates web search was used
            }

        except Exception as e:
            return {
                "answer": f"Error processing general query: {str(e)}",
                "status": "error",
                "mode": "general",
                "question": question
            }

    def _find_common_elements(self, answer1: str, answer2: str) -> str:
        """
        Find common facts between two LLM responses to reduce hallucinations

        Compares bullet points and returns only those that appear in both answers
        (using fuzzy matching to account for slight wording variations)
        """
        def extract_bullets(text: str) -> List[str]:
            """Extract bullet points from answer text"""
            bullets = []
            for line in text.split('\n'):
                line = line.strip()
                # Remove bullet symbols and clean
                for bullet_char in ['•', '-', '*', '▸']:
                    if line.startswith(bullet_char):
                        line = line[1:].strip()
                        break
                if line and len(line) > 10:  # Skip very short lines
                    bullets.append(line.lower())
            return bullets

        def word_overlap(bullet1: str, bullet2: str) -> float:
            """Calculate word overlap between two bullet points"""
            words1 = set(bullet1.split())
            words2 = set(bullet2.split())
            if not words1 or not words2:
                return 0.0
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

        # Extract bullets from both answers
        bullets1 = extract_bullets(answer1)
        bullets2 = extract_bullets(answer2)

        # Find common bullets (with fuzzy matching)
        common_bullets = []
        similarity_threshold = 0.6  # 60% word overlap

        for b1 in bullets1:
            for b2 in bullets2:
                similarity = word_overlap(b1, b2)
                if similarity >= similarity_threshold:
                    # Use the first answer's wording (could also merge them)
                    common_bullets.append(b1)
                    break  # Found a match, move to next bullet

        # Format output
        if not common_bullets:
            return "Information not available with high confidence (answers varied between verification attempts)"

        # Return as bulleted list
        formatted = "\n".join([f"• {bullet.capitalize()}" for bullet in common_bullets])
        return formatted

    def _fetch_web_search_results(self, question: str, location_context: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Fetch relevant web search results using Google Custom Search API

        Used to ground LLM answers for amenities, market insights, and general queries
        Returns formatted search results or None if API key not configured

        Args:
            question: User's question
            location_context: Optional location context (region, city, state) to scope search
        """
        google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        google_search_cx = os.getenv("GOOGLE_SEARCH_CX")

        if not google_search_api_key or not google_search_cx:
            print("[WEB_SEARCH] Google Custom Search API not configured, skipping web search")
            return None

        try:
            # Build search query with location context
            search_query = question

            # Append location context to ensure results are scoped to the selected region
            if location_context:
                region = location_context.get("region")
                city = location_context.get("city")

                if region and city:
                    search_query = f"{question} in {region}, {city}"
                    print(f"[WEB_SEARCH] Added location context: {region}, {city}")
                elif city:
                    search_query = f"{question} in {city}"
                    print(f"[WEB_SEARCH] Added location context: {city}")

            # Use Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": google_search_api_key,
                "cx": google_search_cx,
                "q": search_query,  # Use modified search query with location
                "num": 5  # Top 5 results for context
            }

            print(f"[WEB_SEARCH] Fetching search results for: {search_query}")
            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                if not items:
                    print("[WEB_SEARCH] No search results found")
                    return None

                # Format search results as grounding data
                search_context = "**Web Search Results (for reference):**\n\n"
                for idx, item in enumerate(items[:5], 1):
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")

                    search_context += f"{idx}. **{title}**\n"
                    search_context += f"   {snippet}\n"
                    search_context += f"   Source: {link}\n\n"

                print(f"[WEB_SEARCH] Found {len(items)} search results")
                return search_context
            else:
                print(f"[WEB_SEARCH] API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"[WEB_SEARCH] Error fetching search results: {str(e)}")
            return None

    def _enrich_question(self, question: str) -> str:
        """
        Enrich question with context (location, project type, etc.)

        Example:
        "What amenities does raheja solitaire have?"
        →
        "What amenities does the Raheja Solitaire residential apartment building
         in Goregaon West, Mumbai, have?"
        """
        # For now, let Gemini do intelligent enrichment
        # In production, you could use a database of known projects

        enrichment_prompt = f"""Enrich this real estate question with obvious contextual details:

**Original Question:** {question}

**Instructions:**
1. Add project type (e.g., "residential apartment building", "township", "villa complex")
2. Add likely location/region if you know it (e.g., "in Goregaon West, Mumbai")
3. Make it more specific and complete
4. Keep it concise - just add essential context

**Enriched Question:**"""

        try:
            response = self.model.generate_content(enrichment_prompt)
            enriched = response.text.strip()

            # Clean up any markdown or extra formatting
            enriched = enriched.replace("**", "").replace("*", "")

            return enriched
        except:
            # If enrichment fails, return original
            return question

    def _create_general_prompt(self, enriched_question: str, search_results: Optional[str] = None) -> str:
        """
        Create prompt for general queries with strict anti-hallucination rules

        Args:
            enriched_question: Question with added context
            search_results: Optional web search results for grounding
        """

        # Base prompt with anti-hallucination rules
        prompt = f"""You are a real estate expert. Answer this question based ONLY on factual knowledge.

**Question:**
{enriched_question}
"""

        # Add web search results for grounding if available
        if search_results:
            prompt += f"""
{search_results}

**IMPORTANT:** Use the web search results above as reference to provide accurate, grounded answers. Do NOT make up facts not supported by the search results.
"""

        # Add strict anti-hallucination rules
        prompt += """
**STRICT ANTI-HALLUCINATION RULES:**
1. **90% Confidence Cutoff:** Only state facts you are 90%+ certain about
2. **No Guessing:** If unsure, write "Information not available with high confidence"
3. **Succinct:** Brief, to-the-point facts only - no fluff or explanations
4. **Bullet Format:** Use • symbol, one fact per line, no nesting
5. **Factual Only:** Do NOT make assumptions or extrapolate
6. **Web Grounded:** If web search results are provided, prioritize information from those sources

**Answer (high-confidence facts only):**
"""
        return prompt

    def _prepare_context(self, project: Dict) -> Dict:
        """
        Prepare knowledge graph context for LLM

        Structures data into:
        - Metadata (project info)
        - L1 Attributes (raw data with dimensions)
        - L2 Metrics (calculated financials)
        """
        context = {
            "project_metadata": {},
            "l1_attributes": {},
            "l2_metrics": {}
        }

        # Extract metadata (non-nested fields)
        metadata_fields = ['projectId', 'projectName', 'developerName', 'location',
                          'launchDate', 'possessionDate', 'reraRegistered']

        for field in metadata_fields:
            if field in project:
                value = data_service.get_value(project[field]) if isinstance(project[field], dict) else project[field]
                context["project_metadata"][field] = value

        # Extract L1 attributes (numeric data with dimensions)
        for attr_name, attr_data in project.items():
            if not isinstance(attr_data, dict):
                continue

            if attr_name in metadata_fields or attr_name in ['l2_metrics', 'l3_insights', 'layer', 'nodeType', 'priorityWeight', 'extractionTimestamp']:
                continue

            value = data_service.get_value(attr_data)
            unit = data_service.get_unit(attr_data)
            dimension = data_service.get_dimension(attr_data)

            context["l1_attributes"][attr_name] = {
                "value": value,
                "unit": unit,
                "dimension": dimension
            }

        # Extract L2 metrics (calculated financials)
        l2_metrics = project.get('l2_metrics', {})
        for metric_name, metric_data in l2_metrics.items():
            if isinstance(metric_data, dict):
                value = data_service.get_value(metric_data)
                unit = data_service.get_unit(metric_data)

                context["l2_metrics"][metric_name] = {
                    "value": value,
                    "unit": unit,
                    "calculation": metric_data.get('calculation', '')
                }

        return context

    def _create_kg_prompt(self, question: str, context: Dict, admin_mode: bool = False) -> str:
        """
        Create prompt for knowledge graph queries

        Args:
            question: User's question
            context: Knowledge graph context (metadata, L1, L2 data)
            admin_mode: If True, formats for table output; if False, conversational markdown
        """

        # Use semantic similarity to detect comprehensive queries
        is_comprehensive_query = False

        try:
            # Generate embedding for user question
            question_embedding = self._get_embedding(question)

            if question_embedding is not None and len(self.comprehensive_embeddings) > 0:
                # Calculate similarity with comprehensive query examples
                similarities = [
                    self._cosine_similarity(question_embedding, comp_emb)
                    for comp_emb in self.comprehensive_embeddings
                ]
                max_similarity = max(similarities) if similarities else 0.0

                # Threshold for comprehensive query detection
                COMPREHENSIVE_THRESHOLD = 0.65

                if max_similarity >= COMPREHENSIVE_THRESHOLD:
                    is_comprehensive_query = True
                    print(f"[DEBUG] Comprehensive query detected (similarity={max_similarity:.3f})")
            else:
                # Fallback to keyword-based detection if embeddings not available
                question_lower = question.lower()
                is_comprehensive_query = any(phrase in question_lower for phrase in [
                    'all numbers', 'all metrics', 'all the numbers', 'all the metrics',
                    'everything about', 'complete data', 'full data', 'numbers and metrics'
                ])
        except Exception as e:
            print(f"[WARNING] Semantic detection failed, using keyword fallback: {e}")
            # Fallback to keyword-based detection
            question_lower = question.lower()
            is_comprehensive_query = any(phrase in question_lower for phrase in [
                'all numbers', 'all metrics', 'all the numbers', 'all the metrics',
                'everything about', 'complete data', 'full data', 'numbers and metrics'
            ])

        # Format instructions based on admin_mode
        if admin_mode:
            # ADMIN mode: Table-optimized format
            if is_comprehensive_query:
                format_instruction = """
**OUTPUT FORMAT (MANDATORY):**
You MUST output in this exact format (plain text, NO HTML):

metricName1: value1 unit1
metricName2: value2 unit2
metricName3: value3 unit3

Example:
totalSupplyUnits: 150 count
projectSizeAcres: 48 acres
launchPricePSF: 4352 INR/sqft
irrPct: -23.27 %

DO NOT use HTML tables, DO NOT use markdown, DO NOT use any formatting.
Just plain text with "metricName: value unit" on each line.
"""
            else:
                format_instruction = ""

            prompt = f"""You are a real estate analytics assistant with access to a knowledge graph.

**CRITICAL INSTRUCTIONS:**
1. Answer ONLY based on the data provided below
2. If the data doesn't contain the answer, respond with "Information not available in the knowledge graph"
3. Do NOT make up or estimate any values
4. Be concise and direct in your answers
5. For numeric values, preserve the exact format (integers without decimals, percentages as %, currency with units)
{format_instruction}

**KNOWLEDGE GRAPH DATA (GOLDEN TRUTH):**

**Project Metadata:**
{json.dumps(context['project_metadata'], indent=2)}

**L1 Attributes (Raw Data with Dimensions):**
{json.dumps(context['l1_attributes'], indent=2)}

**L2 Metrics (Calculated Financial Metrics):**
{json.dumps(context['l2_metrics'], indent=2)}

**USER QUESTION:**
{question}

**YOUR ANSWER (based ONLY on the data above):**
"""
        else:
            # CONVERSATIONAL mode: GPT-like markdown format with inline citations
            project_name = context.get('project_metadata', {}).get('projectName', 'Unknown Project')

            prompt = f"""You are a conversational AI assistant helping users understand real estate project data.

**INSTRUCTIONS:**
1. Answer the user's question in a natural, conversational tone (like ChatGPT, Gemini, or Perplexity)
2. Use markdown formatting for readability:
   - Use **bold** for important terms and numbers
   - Use bullet points for lists
   - Use paragraphs for explanations
3. Provide context and transitions (e.g., "Based on the data...", "Let me explain...")
4. When presenting numbers, explain what they mean
5. Be conversational but professional
6. **CITATION FORMAT (MANDATORY):**
   - Include inline citations immediately after each data point, like Perplexity
   - Format: `[Knowledge Graph - {project_name}]` or `[Knowledge Graph Layer N - {project_name}]`
   - Example: "The IRR is **32.33%** [Knowledge Graph Layer 2 - {project_name}], which indicates excellent returns"
   - Example: "The project has **150 units** [Knowledge Graph - {project_name}]"
   - Place citations inline, naturally within the flow of text
   - For Layer 1 (L1) data: Use `[Knowledge Graph Layer 1 - {project_name}]`
   - For Layer 2 (L2) financial metrics: Use `[Knowledge Graph Layer 2 - {project_name}]`
   - For general metadata: Use `[Knowledge Graph - {project_name}]`

**IMPORTANT:**
- Base your answer ONLY on the data provided below
- If data is not available, say so clearly
- Do NOT hallucinate or make up information
- Format your entire response in clean markdown
- ALWAYS include inline citations for EVERY data point you mention

**KNOWLEDGE GRAPH DATA (GOLDEN TRUTH):**

**Project Metadata:**
{json.dumps(context['project_metadata'], indent=2)}

**L1 Attributes (Raw Data with Dimensions):**
{json.dumps(context['l1_attributes'], indent=2)}

**L2 Metrics (Calculated Financial Metrics):**
{json.dumps(context['l2_metrics'], indent=2)}

**USER QUESTION:**
{question}

**YOUR CONVERSATIONAL ANSWER (with inline citations):**
"""

        return prompt

    def _create_conversational_prompt(self, question: str, context: str, project_name: str) -> str:
        """
        Create GPT-like conversational prompt for natural language responses

        The prompt instructs the LLM to respond conversationally with:
        - Natural explanations and transitions
        - Markdown formatting (bold, bullets, paragraphs)
        - Conversational flow like ChatGPT/Gemini/Perplexity
        - Inline Perplexity-style citations
        """
        prompt = f"""You are a conversational AI assistant helping users understand real estate project data.

**USER QUESTION:** {question}

**PROJECT DATA (Knowledge Graph - Golden Truth):**
{context}

**INSTRUCTIONS:**
1. Answer the user's question in a natural, conversational tone (like ChatGPT, Gemini, or Perplexity)
2. Use markdown formatting for readability:
   - Use **bold** for important terms and numbers
   - Use bullet points for lists
   - Use paragraphs for explanations
   - Use `inline code` for technical terms if needed
3. Provide context and transitions (e.g., "Let me walk you through...", "Based on the data...", "Here's what stands out...")
4. When presenting numbers, explain what they mean (e.g., "The IRR is **18.19%**, which indicates a strong return on investment")
5. Be conversational but professional - avoid overly formal language
6. **CITATION FORMAT (MANDATORY):**
   - Include inline citations immediately after each data point, like Perplexity
   - Format: `[Knowledge Graph - {project_name}]` or `[Knowledge Graph Layer N - {project_name}]`
   - Example: "The IRR is **32.33%** [Knowledge Graph Layer 2 - Sara City], which indicates excellent returns"
   - Example: "The project has **150 units** [Knowledge Graph - Sara City] with a total saleable area of **120,000 sqft** [Knowledge Graph - Sara City]"
   - Place citations inline, naturally within the flow of text
   - For Layer 1 (L1) data: Use `[Knowledge Graph Layer 1 - {project_name}]`
   - For Layer 2 (L2) financial metrics: Use `[Knowledge Graph Layer 2 - {project_name}]`
   - For general metadata: Use `[Knowledge Graph - {project_name}]`
7. If asked for comprehensive information, organize it logically with clear sections

**IMPORTANT:**
- Base your answer ONLY on the data provided above
- If data is not available, say so clearly
- Do NOT hallucinate or make up information
- Format your entire response in clean markdown
- ALWAYS include inline citations for EVERY data point you mention

**YOUR CONVERSATIONAL ANSWER (with inline citations):**"""
        return prompt

    def _create_fallback_conversational_response(self, project: Dict, project_name: str) -> str:
        """
        Create fallback markdown response if LLM fails

        Returns basic project information in conversational markdown format
        """
        # Extract key metrics
        l1_attrs = project.get('l1_attributes', {})
        l2_metrics = project.get('l2_metrics', {})

        # Build conversational response
        response = f"I found comprehensive information about **{project_name}**.\n\n"

        # Basic info
        response += "### Project Overview\n\n"
        response += f"- **Developer:** {data_service.get_value(project.get('developerName', 'N/A'))}\n"
        response += f"- **Location:** {data_service.get_value(project.get('microMarket', 'N/A'))}, {data_service.get_value(project.get('city', 'N/A'))}\n"
        response += f"- **Launch Date:** {data_service.get_value(project.get('launchDate', 'N/A'))}\n"
        response += f"- **Possession Date:** {data_service.get_value(project.get('possessionDate', 'N/A'))}\n\n"

        # Key metrics
        if l1_attrs or l2_metrics:
            response += "### Key Metrics\n\n"

            if l1_attrs:
                response += "**Dimensional Attributes:**\n"
                for key, value_dict in list(l1_attrs.items())[:5]:  # Show first 5
                    if isinstance(value_dict, dict) and 'value' in value_dict:
                        metric_name = self._camel_case_to_human_readable(key)
                        response += f"- **{metric_name}:** {value_dict['value']} {value_dict.get('unit', '')}\n"
                response += "\n"

            if l2_metrics:
                response += "**Financial Metrics:**\n"
                for key, value in list(l2_metrics.items())[:5]:  # Show first 5
                    metric_name = self._camel_case_to_human_readable(key)
                    response += f"- **{metric_name}:** {value}\n"
                response += "\n"

        response += "*Source: Liases Foras*\n"
        response += "\n*Note: For detailed tables and visualizations, use the ADMIN: prefix before your question.*"

        return response

    def _generate_conversational_overview(self, project: Dict, question: str) -> Dict[str, Any]:
        """
        Generate GPT-like conversational overview with markdown formatting

        Returns natural, conversational response formatted in markdown instead of HTML tables
        """
        project_name = data_service.get_value(project.get('projectName', ''))

        # Prepare comprehensive context for LLM
        context = self._prepare_context(project)

        # Create conversational prompt
        prompt = self._create_conversational_prompt(question, context, project_name)

        try:
            # Call Gemini with conversational prompt
            response = self.model.generate_content(prompt)
            conversational_answer = response.text.strip()

            return {
                "answer": conversational_answer,
                "status": "success",
                "mode": "conversational_overview",
                "project": {
                    "projectId": str(data_service.get_value(project.get('projectId'))),
                    "projectName": project_name
                }
            }
        except Exception as e:
            # Fallback to basic markdown if LLM fails
            fallback_response = self._create_fallback_conversational_response(project, project_name)
            return {
                "answer": fallback_response,
                "status": "success",
                "mode": "conversational_overview_fallback",
                "project": {
                    "projectId": str(data_service.get_value(project.get('projectId'))),
                    "projectName": project_name
                },
                "error": str(e)
            }

    def _generate_comprehensive_overview(self, project: Dict, question: str, admin_mode: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive 4-section project overview:
        1. Metadata labels
        2. Metrics table (L0, L1, L2)
        3. Rule-based insights
        4. Recommendation suggestions

        Args:
            project: Project data dictionary
            question: User's question
            admin_mode: If True, returns rich HTML tables; if False, returns GPT-like markdown
        """
        project_name = data_service.get_value(project.get('projectName', ''))

        # If NOT admin mode, convert to markdown format (Phase 3 implementation)
        if not admin_mode:
            return self._generate_conversational_overview(project, question)

        # SECTION 1: Metadata
        metadata_html = self._generate_metadata_section(project)

        # SECTION 2: Metrics Table
        metrics_table = self._generate_metrics_table(project)

        # SECTION 3: Rule-based Insights
        insights = self._generate_rule_based_insights(project)

        # SECTION 4: Actionable Recommendations (clickable suggestions)
        recommendations = self._generate_recommendation_suggestions(project, insights)

        # Combine all sections
        comprehensive_html = f"""
{metadata_html}

<div style="margin: 30px 0;">
    <hr style="border: 0; height: 1px; background: linear-gradient(to right, transparent, #667eea, transparent);">
</div>

{metrics_table}

<div style="margin: 30px 0;">
    <hr style="border: 0; height: 1px; background: linear-gradient(to right, transparent, #667eea, transparent);">
</div>

{insights}

<div style="margin: 30px 0;">
    <hr style="border: 0; height: 1px; background: linear-gradient(to right, transparent, #667eea, transparent);">
</div>

{recommendations}
"""

        return {
            "answer": comprehensive_html,
            "status": "success",
            "mode": "comprehensive_overview",
            "project": {
                "projectId": str(data_service.get_value(project.get('projectId'))),
                "projectName": project_name
            },
            "has_recommendations": len(recommendations) > 0
        }

    def _generate_metadata_section(self, project: Dict) -> str:
        """Generate Section 1: Project metadata labels"""
        metadata = {
            "Project Name": data_service.get_value(project.get('projectName', 'N/A')),
            "Developer": data_service.get_value(project.get('developerName', 'N/A')),
            "Location": f"{data_service.get_value(project.get('microMarket', 'N/A'))}, {data_service.get_value(project.get('city', 'N/A'))}",
            "Launch Date": data_service.get_value(project.get('launchDate', 'N/A')),
            "Possession Date": data_service.get_value(project.get('possessionDate', 'N/A')),
            "RERA Number": data_service.get_value(project.get('reraNumber', 'N/A')),
            "Project Type": data_service.get_value(project.get('projectType', 'N/A')),
        }

        html = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
    <h2 style="margin: 0 0 15px 0; font-size: 24px;">📋 Project Overview</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
"""

        for label, value in metadata.items():
            html += f"""
        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; backdrop-filter: blur(10px);">
            <div style="font-size: 11px; opacity: 0.9; margin-bottom: 5px;">{label}</div>
            <div style="font-size: 16px; font-weight: 600;">{value}</div>
        </div>
"""

        html += """
    </div>
</div>
"""
        return html

    def _generate_metrics_table(self, project: Dict) -> str:
        """Generate Section 2: L0, L1, L2 metrics table"""
        # Collect all metrics from project
        all_metrics = []

        # L0 attributes
        l1_attrs = project.get('l1_attributes', {})
        for key, value_dict in l1_attrs.items():
            if isinstance(value_dict, dict) and 'value' in value_dict:
                layer, color, desc = self._classify_metric_layer(key)
                all_metrics.append({
                    'key': key,
                    'value': str(value_dict['value']),
                    'unit': value_dict.get('unit', ''),
                    'layer': layer,
                    'color': color,
                    'description': desc
                })

        # L2 metrics
        l2_metrics = project.get('l2_metrics', {})
        for key, value_dict in l2_metrics.items():
            if isinstance(value_dict, dict) and 'value' in value_dict:
                layer, color, desc = self._classify_metric_layer(key)
                all_metrics.append({
                    'key': key,
                    'value': str(value_dict['value']),
                    'unit': value_dict.get('unit', ''),
                    'layer': layer,
                    'color': color,
                    'description': desc
                })

        # Generate table
        project_name = data_service.get_value(project.get('projectName', ''))
        return self._format_as_table(all_metrics, project_name)

    def _generate_rule_based_insights(self, project: Dict) -> str:
        """Generate Section 3: Rule-based insights from metrics"""
        insights = []

        # Get key metrics
        l2_metrics = project.get('l2_metrics', {})
        l1_attrs = project.get('l1_attributes', {})

        # Rule 1: Negative IRR
        irr = data_service.get_value(l2_metrics.get('irrPct', {}).get('value', 0))
        if isinstance(irr, (int, float)) and irr < 0:
            insights.append({
                'type': 'warning',
                'metric': 'IRR',
                'value': f'{irr}%',
                'message': f'Negative IRR ({irr}%) indicates the project is not generating adequate returns on investment.',
                'severity': 'high'
            })

        # Rule 2: Negative NPV
        npv = data_service.get_value(l2_metrics.get('npvCr', {}).get('value', 0))
        if isinstance(npv, (int, float)) and npv < 0:
            insights.append({
                'type': 'warning',
                'metric': 'NPV',
                'value': f'₹{npv} Cr',
                'message': f'Negative NPV (₹{npv} Cr) suggests the project is destroying value.',
                'severity': 'high'
            })

        # Rule 3: Low absorption rate
        absorption = data_service.get_value(l1_attrs.get('absorptionRatePctPerYear', {}).get('value', 0))
        if isinstance(absorption, (int, float)) and absorption < 10:
            insights.append({
                'type': 'info',
                'metric': 'Absorption Rate',
                'value': f'{absorption}%/year',
                'message': f'Low absorption rate ({absorption}%/year) may indicate market demand issues or pricing concerns.',
                'severity': 'medium'
            })

        # Rule 4: High unsold inventory
        unsold_pct = data_service.get_value(l1_attrs.get('unsoldPct', {}).get('value', 0))
        if isinstance(unsold_pct, (int, float)) and unsold_pct > 50:
            insights.append({
                'type': 'warning',
                'metric': 'Unsold Inventory',
                'value': f'{unsold_pct}%',
                'message': f'High unsold inventory ({unsold_pct}%) requires attention to improve sales velocity.',
                'severity': 'medium'
            })

        # Rule 5: Long payback period
        payback = data_service.get_value(l2_metrics.get('paybackPeriodYears', {}).get('value', 0))
        if isinstance(payback, (int, float)) and payback > 10:
            insights.append({
                'type': 'info',
                'metric': 'Payback Period',
                'value': f'{payback} years',
                'message': f'Extended payback period ({payback} years) indicates capital will be tied up for a long time.',
                'severity': 'low'
            })

        # Generate HTML
        if not insights:
            return """
<div style="background: #e8f5e9; padding: 20px; border-radius: 12px; border-left: 4px solid #4caf50;">
    <h3 style="margin: 0 0 10px 0; color: #2e7d32;">✅ Insights</h3>
    <p style="margin: 0; color: #1b5e20;">All metrics are performing within expected ranges.</p>
</div>
"""

        html = """
<div style="background: #fff3e0; padding: 20px; border-radius: 12px; border-left: 4px solid #ff9800;">
    <h3 style="margin: 0 0 15px 0; color: #e65100;">📊 Key Insights</h3>
    <ul style="margin: 0; padding-left: 20px;">
"""

        for insight in insights:
            icon = '⚠️' if insight['severity'] == 'high' else '⚡' if insight['severity'] == 'medium' else 'ℹ️'
            html += f"""
        <li style="margin-bottom: 10px; color: #333;">
            <strong>{icon} {insight['metric']}:</strong> {insight['message']}
            <span style="color: #666; font-size: 13px;">(Current: {insight['value']})</span>
        </li>
"""

        html += """
    </ul>
</div>
"""
        return html

    def _generate_recommendation_suggestions(self, project: Dict, insights: str) -> str:
        """Generate Section 4: Actionable recommendation buttons"""
        # Generate suggestions based on poor-performing metrics
        suggestions = []

        l2_metrics = project.get('l2_metrics', {})
        l1_attrs = project.get('l1_attributes', {})

        # Check for issues
        irr = data_service.get_value(l2_metrics.get('irrPct', {}).get('value', 0))
        if isinstance(irr, (int, float)) and irr < 0:
            suggestions.append({
                'question': f'How can I improve the negative IRR of {irr}%?',
                'context': 'irr_improvement'
            })

        npv = data_service.get_value(l2_metrics.get('npvCr', {}).get('value', 0))
        if isinstance(npv, (int, float)) and npv < 0:
            suggestions.append({
                'question': f'What strategies can turn around the negative NPV?',
                'context': 'npv_improvement'
            })

        unsold = data_service.get_value(l1_attrs.get('unsoldPct', {}).get('value', 0))
        if isinstance(unsold, (int, float)) and unsold > 50:
            suggestions.append({
                'question': f'How to reduce the {unsold}% unsold inventory?',
                'context': 'inventory_reduction'
            })

        absorption = data_service.get_value(l1_attrs.get('absorptionRatePctPerYear', {}).get('value', 0))
        if isinstance(absorption, (int, float)) and absorption < 10:
            suggestions.append({
                'question': f'How to improve absorption rate from {absorption}%/year?',
                'context': 'absorption_improvement'
            })

        if not suggestions:
            return ""

        # Generate HTML with clickable suggestion chips
        html = """
<div style="background: #f3e5f5; padding: 20px; border-radius: 12px; border-left: 4px solid #9c27b0;">
    <h3 style="margin: 0 0 15px 0; color: #6a1b9a;">💡 Get Detailed Recommendations</h3>
    <p style="margin: 0 0 15px 0; color: #4a148c; font-size: 14px;">Click any suggestion below for detailed, actionable recommendations:</p>
    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
"""

        for suggestion in suggestions:
            # Create clickable suggestion chips
            html += f"""
        <button onclick="window.parent.postMessage({{type: 'ask_question', question: '{suggestion['question']}'}}, '*')"
                style="background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
                       color: white;
                       border: none;
                       padding: 10px 16px;
                       border-radius: 20px;
                       cursor: pointer;
                       font-size: 13px;
                       font-weight: 500;
                       box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                       transition: transform 0.2s;"
                onmouseover="this.style.transform='translateY(-2px)'"
                onmouseout="this.style.transform='translateY(0)'">
            {suggestion['question']} →
        </button>
"""

        html += """
    </div>
</div>
"""
        return html

    def _determine_layer(self, answer: str, project: Dict) -> str:
        """Determine which layer the answer came from"""
        answer_lower = answer.lower()

        # Check if answer contains L2 metric names
        l2_metrics = project.get('l2_metrics', {})
        for metric_name in l2_metrics.keys():
            if metric_name.lower() in answer_lower or metric_name.replace('Pct', '').replace('Cr', '').lower() in answer_lower:
                return "L2 (Calculated Metrics)"

        # Check if answer contains metadata field names
        metadata_fields = ['location', 'developer', 'launch', 'possession', 'rera']
        for field in metadata_fields:
            if field in answer_lower:
                return "Metadata"

        # Default to L1
        return "L1 (Attributes)"

    def _detect_aggregation_query(self, question: str, location_context: Optional[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Detect if the question is asking for aggregation across multiple projects

        Returns:
            Dictionary with aggregation info if detected, else None
            {
                "type": "sum|average|median|top_n|bottom_n|statistics",
                "attribute": "units|area|price|irr|npv|...",
                "attribute_path": "l1_attributes.projectSize",
                "n": 5 (for top_n/bottom_n queries)
            }
        """
        question_lower = question.lower()

        # Define attribute mappings (question keywords -> actual attribute path)
        attribute_mappings = {
            # Flattened fields from /api/projects endpoint
            "units": ("totalSupplyUnits", "Total Units"),
            "project size": ("totalSupplyUnits", "Total Units"),
            "price per sqft": ("currentPricePSF", "Price Per Sqft"),
            "psf": ("currentPricePSF", "Price Per Sqft"),

            # L2 Financial Metrics (nested)
            "irr": ("l2_metrics.irrPct", "IRR"),
            "npv": ("l2_metrics.npvCr", "NPV"),
            "roi": ("l2_metrics.roiPct", "ROI"),
            "payback period": ("l2_metrics.paybackPeriodYears", "Payback Period"),
        }

        # Detect aggregation type
        aggregation_type = None
        n_value = 5  # Default for top_n/bottom_n

        if any(keyword in question_lower for keyword in ["sum", "total", "add up", "altogether"]):
            aggregation_type = "sum"
        elif any(keyword in question_lower for keyword in ["average", "mean", "avg"]):
            aggregation_type = "average"
        elif "median" in question_lower:
            aggregation_type = "median"
        elif any(keyword in question_lower for keyword in ["top", "largest", "biggest", "highest"]):
            aggregation_type = "top_n"
            # Extract N if mentioned (e.g., "top 5", "top 10")
            import re
            match = re.search(r'top\s+(\d+)', question_lower)
            if match:
                n_value = int(match.group(1))
        elif any(keyword in question_lower for keyword in ["bottom", "smallest", "lowest"]):
            aggregation_type = "bottom_n"
            import re
            match = re.search(r'bottom\s+(\d+)', question_lower)
            if match:
                n_value = int(match.group(1))
        elif any(keyword in question_lower for keyword in ["statistics", "stats", "distribution", "std dev", "standard deviation", "variance"]):
            aggregation_type = "statistics"

        if not aggregation_type:
            return None  # Not an aggregation query

        # Detect which attribute is being aggregated
        for keyword, (attr_path, attr_name) in attribute_mappings.items():
            if keyword in question_lower:
                return {
                    "type": aggregation_type,
                    "attribute": keyword,
                    "attribute_path": attr_path,
                    "attribute_name": attr_name,
                    "n": n_value if aggregation_type in ["top_n", "bottom_n"] else None
                }

        # If no attribute detected, return None
        return None

    def _handle_aggregation_query(
        self,
        question: str,
        aggregation_info: Dict[str, Any],
        location_context: Optional[Dict[str, str]],
        admin_mode: bool
    ) -> Dict[str, Any]:
        """
        Handle aggregation queries using statistical service

        Args:
            question: Original user question
            aggregation_info: Dict from _detect_aggregation_query
            location_context: Location context (region, city)
            admin_mode: Admin mode flag
        """
        from app.services.statistical_service import get_statistical_service

        stat_service = get_statistical_service()

        # Extract region and city from location_context
        region = location_context.get("region") if location_context else None
        city = location_context.get("city") if location_context else None

        if not region and not city:
            return {
                "error": "Location context (region or city) is required for statistical queries",
                "query_type": "statistical",
                "guidance": "Please provide location_context with region or city"
            }

        agg_type = aggregation_info["type"]
        attr_path = aggregation_info["attribute_path"]
        attr_name = aggregation_info["attribute_name"]

        try:
            if agg_type in ["top_n", "bottom_n"]:
                # Handle top N / bottom N queries
                n = aggregation_info.get("n", 5)
                ascending = (agg_type == "bottom_n")

                result = stat_service.get_top_n_projects(
                    region=region,
                    city=city,
                    attribute_path=attr_path,
                    attribute_name=attr_name,
                    n=n,
                    ascending=ascending
                )

                # Format response conversationally
                answer = self._format_top_n_response(result, admin_mode)

            else:
                # Handle sum, average, median, statistics queries
                result = stat_service.aggregate_by_region(
                    region=region,
                    city=city,
                    attribute_path=attr_path,
                    attribute_name=attr_name
                )

                # Format response based on aggregation type
                answer = self._format_aggregation_response(result, agg_type, admin_mode)

            return {
                "answer": answer,
                "status": "success",
                "mode": "aggregation",
                "aggregation_type": agg_type,
                "region": region,
                "city": city
            }

        except Exception as e:
            return {
                "answer": f"Error calculating {agg_type} for {attr_name}: {str(e)}",
                "status": "error",
                "mode": "aggregation"
            }

    def _format_top_n_response(self, result: Dict[str, Any], admin_mode: bool) -> str:
        """Format top N / bottom N response conversationally"""
        if "error" in result:
            return f"I couldn't find projects in that region. {result['error']}"

        ranking_type = result["ranking_type"]
        n = result["n"]
        attr_name = result["attribute"]
        projects = result["projects"]
        region = result["region"]
        city = result["city"]

        if not projects:
            return f"I couldn't find any projects with {attr_name} data in {region}, {city}."

        # Conversational response
        response = f"Here are the **{ranking_type} {n} projects** by **{attr_name}** in **{region}, {city}** [Statistical Analysis - {city}]:\n\n"

        for i, proj in enumerate(projects, 1):
            response += f"{i}. **{proj['projectName']}** [Knowledge Graph - {proj['projectName']}]: {proj['value']:.2f}\n"

        response += f"\n*Analyzed across {result['total_projects']} projects in the region.*"

        return response

    def _format_aggregation_response(self, result: Dict[str, Any], agg_type: str, admin_mode: bool) -> str:
        """Format sum, average, median, statistics response conversationally"""
        if "error" in result:
            return f"I couldn't calculate the {agg_type}. {result['error']}"

        stats = result["statistics"]
        attr_name = result["attribute"]
        region = result["region"]
        city = result["city"]
        project_count = result["project_count"]

        if "error" in stats:
            return f"I couldn't calculate statistics for {attr_name}. {stats['error']}"

        # Build conversational response based on aggregation type
        response = f"Based on **{project_count} projects** in **{region}, {city}** [Statistical Analysis - {city}]:\n\n"

        if agg_type == "sum":
            response += f"The **total {attr_name}** across all projects is **{stats['sum']:.2f}** [Statistical Aggregation].\n\n"
        elif agg_type == "average":
            response += f"The **average {attr_name}** is **{stats['mean']:.2f}** [Statistical Aggregation].\n\n"
        elif agg_type == "median":
            response += f"The **median {attr_name}** is **{stats['median']:.2f}** [Statistical Aggregation].\n\n"
        elif agg_type == "statistics":
            response += f"**Statistical Summary for {attr_name}:**\n\n"
            response += f"- **Mean**: {stats['mean']:.2f} [Statistical Aggregation]\n"
            response += f"- **Median**: {stats['median']:.2f} [Statistical Aggregation]\n"
            response += f"- **Std Dev**: {stats['std_dev']:.2f} [Statistical Aggregation]\n"
            response += f"- **Min**: {stats['min']:.2f} [Statistical Aggregation]\n"
            response += f"- **Max**: {stats['max']:.2f} [Statistical Aggregation]\n"
            response += f"- **Range**: {stats['range']:.2f} [Statistical Aggregation]\n\n"

        # Add context
        response += f"**Additional Context:**\n"
        response += f"- Minimum: {stats['min']:.2f}\n"
        response += f"- Maximum: {stats['max']:.2f}\n"
        response += f"- Range: {stats['range']:.2f}\n"

        return response


# Singleton instance
_llm_service_instance: Optional[LLMService] = None


def get_llm_service(api_key: Optional[str] = None) -> LLMService:
    """Get or create LLMService singleton instance"""
    global _llm_service_instance

    if _llm_service_instance is None:
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not provided and not found in environment")

        _llm_service_instance = LLMService(api_key)

    return _llm_service_instance

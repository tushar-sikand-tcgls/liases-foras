"""
Default Configuration Values for Liases Foras Real Estate Analytics

This module centralizes all default values to eliminate hardcoding
and enable easy configuration management.
"""

from typing import Dict, Any, Tuple
from datetime import datetime


class DefaultConfig:
    """Centralized default configuration for all calculators and services"""

    # ===================================================================
    # FINANCIAL DEFAULTS
    # ===================================================================

    FINANCIAL = {
        "initial_investment": None,  # No default - must be provided
        "discount_rate": 0.12,  # 12% default discount rate
        "project_duration_months": 36,  # 3 years default
        "project_duration_years": 3,
        "absorption_range": (0.7, 1.3),  # 70% to 130% sensitivity
        "price_range": (0.9, 1.1),  # 90% to 110% price sensitivity
        "min_irr_constraint": 0.15,  # 15% minimum IRR
        "currency": "INR",
        "total_project_cost": None,  # No default - context dependent
    }

    # ===================================================================
    # LOCATION DEFAULTS
    # ===================================================================

    LOCATION = {
        "default_city": None,  # No default city - must be provided
        "default_region": None,  # No default region - must be provided
        "default_country": "India",
        "coordinate_precision": 6,  # Decimal places for lat/lng
    }

    # ===================================================================
    # DATA VERSION
    # ===================================================================

    DATA = {
        "current_version": "Q3_FY25",  # Dynamic - should be updated quarterly
        "supported_versions": ["Q1_FY25", "Q2_FY25", "Q3_FY25", "Q4_FY25"],
        "data_source": "liases-foras",
        "vector_db_collection": "city_insights",
    }

    # ===================================================================
    # STATISTICAL DEFAULTS
    # ===================================================================

    STATISTICAL = {
        "min_sample_size": {
            "mode": 1,
            "mean": 1,
            "median": 1,
            "std_dev": 2,
            "variance": 2,
            "normal_test": 8,
            "percentile": 1
        },
        "outlier_z_threshold": 2.5,  # Z-score threshold for outliers
        "volatility_cv_high": 30.0,  # CV% > 30 = high volatility
        "volatility_cv_low": 10.0,   # CV% < 10 = low volatility
        "confidence_levels": [0.68, 0.95, 0.997],  # 68%, 95%, 99.7%
        "percentiles": [10, 25, 50, 75, 90],  # Default percentiles
        "normality_p_value": 0.05,  # P-value threshold for normality test
    }

    # ===================================================================
    # OPTIMIZATION DEFAULTS
    # ===================================================================

    OPTIMIZATION = {
        "max_iterations": 1000,
        "tolerance": 1e-6,
        "optimization_method": "SLSQP",  # Sequential Least Squares Programming
        "unit_mix": {
            "1BHK": {"min": 0.0, "max": 0.5},  # 0-50% 1BHK units
            "2BHK": {"min": 0.2, "max": 0.8},  # 20-80% 2BHK units
            "3BHK": {"min": 0.1, "max": 0.6},  # 10-60% 3BHK units
        },
        "developer_marketability": 0.88,  # Default marketability score
    }

    # ===================================================================
    # API DEFAULTS
    # ===================================================================

    API = {
        "timeout_seconds": 30,
        "max_retries": 3,
        "batch_size": 100,
        "cache_ttl_seconds": 3600,  # 1 hour cache
        "max_response_size_mb": 10,
    }

    # ===================================================================
    # VECTOR SEARCH DEFAULTS
    # ===================================================================

    VECTOR_SEARCH = {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimension": 384,
        "similarity_metric": "cosine",
        "top_k_results": 5,
        "min_similarity_score": 0.7,
        "chunk_size": 500,
        "chunk_overlap": 50,
    }

    # ===================================================================
    # RANKING DEFAULTS
    # ===================================================================

    RANKING = {
        "default_top_n": 5,
        "max_top_n": 50,
        "default_sort_order": "descending",  # For top performers
    }

    # ===================================================================
    # ERROR CODES
    # ===================================================================

    ERROR_CODES = {
        # Statistical errors (200-299)
        201: "Empty dataset - No data provided for analysis",
        202: "Insufficient data - Need minimum samples for operation",
        203: "Non-numeric values - Dataset contains invalid entries",
        204: "Invalid percentile - Must be between 0 and 100",
        205: "Division by zero - Cannot compute with zero variance",
        206: "Invalid parameter - Check input parameters",

        # Calculator errors (300-399)
        301: "Missing required parameter",
        302: "Invalid calculation type",
        303: "Calculation failed",
        304: "Convergence failed in optimization",

        # Data errors (400-499)
        401: "Project not found",
        402: "Invalid location",
        403: "Data version not available",
        404: "Attribute path not found",

        # System errors (500-599)
        500: "Internal server error",
        501: "Service unavailable",
        502: "Database connection error",
        503: "Vector database error",
    }

    @classmethod
    def get_current_data_version(cls) -> str:
        """
        Get the current data version dynamically based on date

        Returns:
            Current quarter in format Q{1-4}_FY{YY}
        """
        now = datetime.now()
        month = now.month
        year = now.year

        # Determine quarter
        if month <= 3:
            quarter = "Q4"
            fiscal_year = year  # Jan-Mar is Q4 of previous FY
        elif month <= 6:
            quarter = "Q1"
            fiscal_year = year + 1  # Apr-Jun is Q1 of current FY
        elif month <= 9:
            quarter = "Q2"
            fiscal_year = year + 1  # Jul-Sep is Q2 of current FY
        else:
            quarter = "Q3"
            fiscal_year = year + 1  # Oct-Dec is Q3 of current FY

        return f"{quarter}_FY{str(fiscal_year)[-2:]}"

    @classmethod
    def get_default(cls, category: str, key: str, fallback: Any = None) -> Any:
        """
        Get a default value by category and key

        Args:
            category: Category name (FINANCIAL, LOCATION, etc.)
            key: Key within the category
            fallback: Value to return if key not found

        Returns:
            The default value or fallback
        """
        category_dict = getattr(cls, category.upper(), {})
        if isinstance(category_dict, dict):
            return category_dict.get(key, fallback)
        return fallback

    @classmethod
    def get_all_defaults(cls) -> Dict[str, Any]:
        """Get all default configurations as a dictionary"""
        return {
            "financial": cls.FINANCIAL,
            "location": cls.LOCATION,
            "data": cls.DATA,
            "statistical": cls.STATISTICAL,
            "optimization": cls.OPTIMIZATION,
            "api": cls.API,
            "vector_search": cls.VECTOR_SEARCH,
            "ranking": cls.RANKING,
            "error_codes": cls.ERROR_CODES,
        }


# Singleton instance for easy import
defaults = DefaultConfig()
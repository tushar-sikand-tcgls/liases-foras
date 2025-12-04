"""
CSS Styling Constants for Dynamic Widget System with Animations
"""

# =============================================================================
# CSS CLASSES WITH ANIMATIONS
# =============================================================================

CSS_STYLES = """
<style>
    /* === ANIMATIONS === */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-40px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }

    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
        }
        50% {
            box-shadow: 0 0 25px rgba(102, 126, 234, 0.9), 0 0 40px rgba(102, 126, 234, 0.7);
        }
    }

    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }

    @keyframes rotate {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    /* === INFO PANELS === */
    .info-panel {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-size: 200% 200%;
        border-left: 6px solid #ffd700;
        padding: 1.8rem;
        border-radius: 1.2rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.7s ease-out;
    }

    .info-panel::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.15), transparent);
        animation: shimmer 3s linear infinite;
    }

    .kv-row {
        display: flex;
        justify-content: space-between;
        padding: 0.85rem 0;
        border-bottom: 2px solid rgba(255, 255, 255, 0.25);
        animation: slideInLeft 0.5s ease-out;
        animation-fill-mode: both;
        position: relative;
        z-index: 1;
        transition: all 0.3s ease;
    }

    .kv-row:hover {
        padding-left: 10px;
        border-bottom-color: rgba(255, 215, 0, 0.6);
    }

    .kv-row:nth-child(1) { animation-delay: 0.1s; }
    .kv-row:nth-child(2) { animation-delay: 0.15s; }
    .kv-row:nth-child(3) { animation-delay: 0.2s; }
    .kv-row:nth-child(4) { animation-delay: 0.25s; }
    .kv-row:nth-child(5) { animation-delay: 0.3s; }
    .kv-row:nth-child(6) { animation-delay: 0.35s; }

    .kv-row:last-child {
        border-bottom: none;
    }

    .kv-key {
        font-weight: 600;
        color: #2d3748;
        text-shadow: none;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
    }

    .kv-value {
        color: #1a202c;
        font-weight: 700;
        text-shadow: none;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
    }

    /* === METRIC CARDS === */
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 2rem;
        box-shadow: 0 15px 50px rgba(245, 87, 108, 0.5);
        animation: fadeInUp 0.7s ease-out, float 3s ease-in-out infinite;
        transition: transform 0.4s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: rotate 10s linear infinite;
    }

    .metric-card:hover {
        transform: translateY(-10px) scale(1.03);
        box-shadow: 0 20px 60px rgba(245, 87, 108, 0.7);
    }

    /* === SCENARIO CARDS === */
    .scenario-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border: 3px solid transparent;
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.4s ease;
        animation: fadeInUp 0.7s ease-out;
        box-shadow: 0 6px 25px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }

    .scenario-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #f5576c);
        background-size: 300% 100%;
        animation: shimmer 3s linear infinite;
    }

    .scenario-card:hover {
        transform: translateX(15px) scale(1.02);
        border-color: #667eea;
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    }

    /* === BADGES === */
    .success-badge {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.6rem 1.4rem;
        border-radius: 3rem;
        font-size: 1rem;
        font-weight: 800;
        box-shadow: 0 6px 20px rgba(56, 239, 125, 0.5);
        animation: pulse 2.5s ease-in-out infinite;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .warning-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.6rem 1.4rem;
        border-radius: 3rem;
        font-size: 1rem;
        font-weight: 800;
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.5);
        animation: pulse 2.5s ease-in-out infinite;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .info-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.6rem 1.4rem;
        border-radius: 3rem;
        font-size: 1rem;
        font-weight: 800;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        animation: pulse 2.5s ease-in-out infinite;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* === SUCCESS BOX === */
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 6px solid #28a745;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 1rem;
        box-shadow: 0 6px 25px rgba(40, 167, 69, 0.2);
        animation: fadeInUp 0.6s ease-out;
    }

    /* === SCENARIO PANELS === */
    .scenario-panel-neutral {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 6px solid #1E88E5;
        padding: 1.5rem;
        border-radius: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 6px 25px rgba(30, 136, 229, 0.2);
        animation: slideInLeft 0.6s ease-out;
    }

    .scenario-panel-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 6px solid #28a745;
        padding: 1.5rem;
        border-radius: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 6px 25px rgba(40, 167, 69, 0.25);
        animation: slideInLeft 0.6s ease-out;
    }

    .scenario-panel-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
        border-left: 6px solid #ffc107;
        padding: 1.5rem;
        border-radius: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 6px 25px rgba(255, 193, 7, 0.25);
        animation: slideInLeft 0.6s ease-out;
    }

    /* === NESTED PANELS === */
    .nested-panel {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 2px solid #e9ecef;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }

    .nested-panel:hover {
        border-color: #667eea;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        transform: translateY(-3px);
    }

    /* === STREAMLIT OVERRIDES === */
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-radius: 1rem;
        overflow: hidden;
        animation: fadeInUp 0.5s ease-out;
    }

    div[data-testid="stExpander"] details summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 1rem;
        padding: 1.2rem !important;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }

    div[data-testid="stExpander"] details summary:hover {
        background: linear-gradient(135deg, #5568d3 0%, #653a8b 100%);
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
</style>
"""

# =============================================================================
# COLOR CONSTANTS
# =============================================================================

COLORS = {
    "primary": "#667eea",
    "primary_dark": "#764ba2",
    "success": "#38ef7d",
    "success_dark": "#11998e",
    "warning": "#f5576c",
    "warning_dark": "#f093fb",
    "danger": "#dc3545",
    "info": "#17a2b8",
    "neutral": "#6c757d",
    "gold": "#ffd700",

    # Scenario colors
    "base_case": "#1E88E5",
    "optimistic": "#38ef7d",
    "stress": "#f5576c",
    "conservative": "#ffc107",

    # Background colors
    "bg_neutral": "#f8f9fa",
    "bg_success": "#d4edda",
    "bg_warning": "#fff3cd",
    "bg_danger": "#f8d7da"
}

# =============================================================================
# DIVERSE ICONS
# =============================================================================

ICONS = {
    # Financial Metrics (Font-Awesome - Monochrome Theme Blue #667eea)
    "irr": '<i class="fas fa-gem"></i>',
    "npv": '<i class="fas fa-dollar-sign"></i>',
    "roi": '<i class="fas fa-chart-bar"></i>',
    "payback": '<i class="fas fa-clock"></i>',
    "profitability": '<i class="fas fa-bullseye"></i>',
    "sensitivity": '<i class="fas fa-sliders-h"></i>',

    # Market & Analysis
    "market": '<i class="fas fa-store"></i>',
    "opportunity": '<i class="fas fa-star"></i>',
    "scoring": '<i class="fas fa-star"></i>',
    "trend": '<i class="fas fa-chart-line"></i>',
    "growth": '<i class="fas fa-arrow-trend-up"></i>',
    "decline": '<i class="fas fa-arrow-trend-down"></i>',

    # Scenarios
    "base_case": '<i class="fas fa-dice"></i>',
    "optimistic": '<i class="fas fa-fire"></i>',
    "stress": '<i class="fas fa-bolt"></i>',
    "conservative": '<i class="fas fa-shield-alt"></i>',

    # Status Indicators
    "success": '<i class="fas fa-check-circle"></i>',
    "excellent": '<i class="fas fa-trophy"></i>',
    "good": '<i class="fas fa-thumbs-up"></i>',
    "warning": '<i class="fas fa-exclamation-triangle"></i>',
    "error": '<i class="fas fa-times-circle"></i>',
    "info": '<i class="fas fa-lightbulb"></i>',

    # Actions & Tools
    "target": '<i class="fas fa-bullseye"></i>',
    "calculation": '<i class="fas fa-calculator"></i>',
    "formula": '<i class="fas fa-square-root-alt"></i>',
    "provenance": '<i class="fas fa-search"></i>',
    "algorithm": '<i class="fas fa-cog"></i>',
    "optimization": '<i class="fas fa-sliders-h"></i>',

    # Units & Dimensions
    "time": '<i class="fas fa-clock"></i>',
    "money": '<i class="fas fa-money-bill"></i>',
    "units": '<i class="fas fa-building"></i>',
    "area": '<i class="fas fa-ruler-combined"></i>',
    "location": '<i class="fas fa-map-marker-alt"></i>',
    "city": '<i class="fas fa-city"></i>',

    # Data & Insights
    "chart": '<i class="fas fa-chart-bar"></i>',
    "graph": '<i class="fas fa-chart-line"></i>',
    "table": '<i class="fas fa-table"></i>',
    "data": '<i class="fas fa-database"></i>',
    "insight": '<i class="fas fa-eye"></i>',
    "analysis": '<i class="fas fa-microscope"></i>',

    # Real Estate Specific
    "building": '<i class="fas fa-building"></i>',
    "property": '<i class="fas fa-home"></i>',
    "unit_type": '<i class="fas fa-home"></i>',
    "developer": '<i class="fas fa-hard-hat"></i>',
    "sales": '<i class="fas fa-handshake"></i>',
    "absorption": '<i class="fas fa-chart-pie"></i>',

    # Special Effects
    "fire": '<i class="fas fa-fire"></i>',
    "star": '<i class="fas fa-star"></i>',
    "sparkle": '<i class="fas fa-sparkles"></i>',
    "rocket": '<i class="fas fa-rocket"></i>',
    "gem": '<i class="fas fa-gem"></i>',
    "trophy": '<i class="fas fa-trophy"></i>',
    "crown": '<i class="fas fa-crown"></i>',
    "lightning": '<i class="fas fa-bolt"></i>'
}

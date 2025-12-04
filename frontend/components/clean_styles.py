"""
Clean CSS Styles with Proper Color Palette
"""

# Color Palette
COLORS = {
    "white": "#FFFFFF",           # Background
    "navy_blue": "#133D6E",       # Buttons, Widgets (Navy Dark Blue)
    "light_orange": "#FFD700",    # Golden - Highlighting accents
    "black": "#000000",           # Primary font
    "gray": "#DDDDDD",            # Secondary font - mottos, slogans
    "pink": "#FFB6C1",            # Error backgrounds
    "light_green": "#90EE90",     # Success backgrounds
    "navy_hover": "#0F2F52",      # Darker navy for hover states
}

CLEAN_CSS_STYLES = f"""
<style>
    /* Global Styles */
    .stApp {{
        background-color: {COLORS['white']};
        padding-top: 0rem !important;
    }}

    /* Reduce top spacing */
    .main .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }}

    header {{
        background-color: transparent !important;
    }}

    /* Remove toolbar spacing */
    .stToolbar {{
        display: none;
    }}

    /* Remove default Streamlit styling */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {{
        color: {COLORS['black']};
        margin-top: 0.5rem !important;
    }}

    .stMarkdown p, .stMarkdown li {{
        color: {COLORS['black']};
    }}

    /* Secondary text */
    .secondary-text {{
        color: {COLORS['gray']};
        font-style: italic;
    }}

    /* Buttons with animations */
    .stButton > button {{
        background-color: {COLORS['navy_blue']};
        color: {COLORS['white']};
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(19, 61, 110, 0.2);
    }}

    .stButton > button:hover {{
        background-color: {COLORS['navy_hover']};
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(19, 61, 110, 0.4);
    }}

    .stButton > button:active {{
        transform: translateY(0px);
        box-shadow: 0 2px 6px rgba(19, 61, 110, 0.3);
    }}

    /* Text Input with rounded corners */
    .stTextInput > div > div > input {{
        background-color: {COLORS['white']};
        color: {COLORS['black']};
        border: 2px solid {COLORS['navy_blue']};
        border-radius: 10px;
        padding: 10px 15px;
        transition: all 0.3s ease;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['light_orange']};
        box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.2);
    }}

    /* Select Box */
    .stSelectbox > div > div {{
        background-color: {COLORS['white']};
        border: 2px solid {COLORS['navy_blue']};
        border-radius: 10px;
    }}

    /* Expander with animations */
    .streamlit-expanderHeader {{
        background-color: {COLORS['navy_blue']};
        color: {COLORS['white']};
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 600;
        padding: 12px 16px;
    }}

    .streamlit-expanderHeader:hover {{
        background-color: {COLORS['navy_hover']};
        box-shadow: 0 2px 8px rgba(19, 61, 110, 0.3);
    }}

    /* Success Message */
    .stSuccess {{
        background-color: {COLORS['light_green']};
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }}

    /* Error Message */
    .stError {{
        background-color: {COLORS['pink']};
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
    }}

    /* Info Message */
    .stInfo {{
        background-color: rgba(19, 61, 110, 0.1);
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 10px;
        border-left: 4px solid {COLORS['navy_blue']};
    }}

    /* Tabs with animations */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {COLORS['white']};
        border: 2px solid {COLORS['navy_blue']};
        color: {COLORS['navy_blue']};
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        transition: all 0.3s ease;
        font-weight: 600;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: rgba(19, 61, 110, 0.05);
        transform: translateY(-2px);
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['navy_blue']};
        color: {COLORS['white']};
        border-color: {COLORS['navy_blue']};
    }}

    /* Metric with styling */
    [data-testid="stMetricValue"] {{
        color: {COLORS['navy_blue']};
        font-weight: 700;
    }}

    [data-testid="stMetric"] {{
        background-color: rgba(19, 61, 110, 0.05);
        padding: 12px;
        border-radius: 10px;
        border: 2px solid rgba(19, 61, 110, 0.1);
        transition: all 0.3s ease;
    }}

    [data-testid="stMetric"]:hover {{
        border-color: {COLORS['navy_blue']};
        box-shadow: 0 2px 8px rgba(19, 61, 110, 0.15);
    }}

    /* Hide sidebar */
    [data-testid="stSidebar"] {{
        display: none;
    }}

    /* Chat messages */
    .stChatMessage {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['gray']};
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        transition: all 0.3s ease;
    }}

    .stChatMessage:hover {{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}

    /* Accent border for highlights */
    .accent-border {{
        border-left: 4px solid {COLORS['light_orange']};
        padding-left: 12px;
        border-radius: 0 8px 8px 0;
    }}

    /* Clean container */
    .clean-container {{
        background-color: {COLORS['white']};
        border: 2px solid rgba(19, 61, 110, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
    }}

    .clean-container:hover {{
        border-color: {COLORS['navy_blue']};
        box-shadow: 0 4px 12px rgba(19, 61, 110, 0.1);
    }}

    /* Column dividers with golden lines */
    [data-testid="column"] {{
        animation: fadeIn 0.5s ease-in;
        position: relative;
    }}

    /* Add golden border to right side of left columns */
    [data-testid="column"]:first-child {{
        border-right: 2px solid {COLORS['light_orange']};
        padding-right: 20px;
    }}

    [data-testid="column"]:last-child {{
        padding-left: 20px;
    }}

    /* Horizontal dividers */
    hr {{
        border: none;
        border-top: 2px solid {COLORS['light_orange']};
        margin: 1.5rem 0;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Font Awesome Icons - Monochrome Theme Blue */
    .fa, .fas, .far, .fal, .fab {{
        color: #667eea;  /* Theme blue for all icons */
    }}
</style>

<!-- Font Awesome CDN -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" integrity="sha512-z3gLpd7yknf1YoNbCzqRKc4qyor8gaKU1qmn+CShxbuBusANI9QpRohGBreCFkKxLhei6S9CQXFEbbKuqLg0DA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
"""

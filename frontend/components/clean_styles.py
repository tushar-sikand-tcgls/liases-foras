"""
Clean CSS Styles - ChatGPT-like Minimalist Black & White Theme
"""

# Color Palette - Minimalist Black & White
COLORS = {
    "white": "#FFFFFF",           # Background
    "black": "#000000",           # Primary font, borders, lines
    "light_gray": "#F7F7F8",      # Message backgrounds
    "border_gray": "#E5E5E5",     # Borders
    "text_gray": "#6B6B6B",       # Secondary text
    "hover_gray": "#F0F0F0",      # Hover states
}

CLEAN_CSS_STYLES = f"""
<style>
    /* Import ChatGPT-like font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Styles - ChatGPT-like */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: {COLORS['black']};
    }}

    .stApp {{
        background-color: {COLORS['white']};
        padding-top: 0rem !important;
        color: {COLORS['black']};
    }}

    /* Reduce top spacing */
    .main .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;  /* ChatGPT-like centered width */
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
        font-weight: 600;
    }}

    .stMarkdown p, .stMarkdown li {{
        color: {COLORS['black']};
        font-size: 16px;
        line-height: 1.6;
    }}

    /* Secondary text */
    .secondary-text {{
        color: {COLORS['text_gray']};
        font-style: normal;
        font-weight: 400;
    }}

    /* Minimal buttons - black outline */
    .stButton > button {{
        background-color: {COLORS['white']};
        color: {COLORS['black']};
        border: 1px solid {COLORS['black']};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        box-shadow: none;
    }}

    .stButton > button:hover {{
        background-color: {COLORS['light_gray']};
        border-color: {COLORS['black']};
        transform: none;
        box-shadow: none;
    }}

    .stButton > button:active {{
        transform: none;
        box-shadow: none;
    }}

    /* Text Input - minimal style */
    .stTextInput > div > div > input {{
        background-color: {COLORS['white']};
        color: {COLORS['black']};
        border: 1px solid {COLORS['border_gray']};
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 15px;
        transition: all 0.2s ease;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['black']};
        box-shadow: none;
        outline: none;
    }}

    /* Select Box - minimal */
    .stSelectbox > div > div {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['border_gray']};
        border-radius: 6px;
    }}

    /* Chat Input - ChatGPT style */
    .stChatInputContainer {{
        border: 1px solid {COLORS['border_gray']} !important;
        border-radius: 12px !important;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.05) !important;
    }}

    /* Expander - minimal */
    .streamlit-expanderHeader {{
        background-color: {COLORS['white']};
        color: {COLORS['black']} !important;
        border: 1px solid {COLORS['border_gray']};
        border-radius: 6px;
        transition: all 0.2s ease;
        font-weight: 500;
        padding: 10px 14px;
    }}

    .streamlit-expanderHeader:hover {{
        background-color: {COLORS['light_gray']};
        box-shadow: none;
    }}

    .streamlit-expanderHeader p {{
        color: {COLORS['black']} !important;
    }}

    /* Success Message - minimal */
    .stSuccess {{
        background-color: {COLORS['light_gray']};
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid {COLORS['black']};
    }}

    /* Error Message - minimal */
    .stError {{
        background-color: {COLORS['light_gray']};
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid {COLORS['black']};
    }}

    /* Info Message - minimal */
    .stInfo {{
        background-color: {COLORS['light_gray']};
        color: {COLORS['black']};
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid {COLORS['black']};
    }}

    /* Tabs - minimal */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px;
        border-bottom: 1px solid {COLORS['border_gray']};
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: {COLORS['text_gray']};
        border-radius: 0;
        padding: 10px 16px;
        transition: all 0.2s ease;
        font-weight: 500;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: transparent;
        color: {COLORS['black']};
        transform: none;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        color: {COLORS['black']};
        border-bottom: 2px solid {COLORS['black']};
    }}

    /* Metric - minimal */
    [data-testid="stMetricLabel"] {{
        color: {COLORS['black']} !important;
        font-weight: 500;
    }}

    [data-testid="stMetricValue"] {{
        color: {COLORS['black']};
        font-weight: 600;
    }}

    [data-testid="stMetric"] {{
        background-color: {COLORS['white']};
        padding: 12px;
        border-radius: 6px;
        border: 1px solid {COLORS['border_gray']};
        transition: all 0.2s ease;
    }}

    [data-testid="stMetric"]:hover {{
        border-color: {COLORS['black']};
        box-shadow: none;
    }}

    /* Hide sidebar */
    [data-testid="stSidebar"] {{
        display: none;
    }}

    /* Chat messages - ChatGPT style (NO AVATARS/ICONS) */
    .stChatMessage {{
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 16px 0 !important;
        margin: 0 !important;
        transition: none !important;
    }}

    /* Hide only the avatar column (first child with fixed width) */
    .stChatMessage > div:first-child {{
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Ensure content is visible and takes full width */
    .stChatMessage > div:last-child {{
        width: 100% !important;
        max-width: 100% !important;
        flex: 1 !important;
    }}

    /* User messages - EVEN indexed (user messages appear as 2nd, 4th, 6th after suggested questions) */
    div[data-testid="stChatMessage"]:nth-child(even) {{
        display: flex !important;
        justify-content: flex-end !important;
        align-items: flex-start !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(even) > div:last-child {{
        display: flex !important;
        justify-content: flex-end !important;
        width: 100% !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(even) > div:last-child > div {{
        background-color: {COLORS['light_gray']} !important;
        border-radius: 18px !important;
        padding: 9px 16px 19px 16px !important;
        max-width: 70% !important;
        margin-left: auto !important;
        display: flex !important;
        align-items: flex-start !important;
        text-align: left !important;
        min-height: 44px !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(even) > div:last-child > div > div {{
        display: flex !important;
        align-items: flex-start !important;
        width: 100% !important;
        margin-top: 5px !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(even) p {{
        margin: 0 !important;
        padding: 0 !important;
        color: {COLORS['black']} !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
    }}

    /* Assistant messages - ODD indexed (assistant responses appear as 3rd, 5th, 7th...) */
    div[data-testid="stChatMessage"]:nth-child(odd) {{
        display: flex !important;
        justify-content: center !important;
        align-items: flex-start !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(odd) > div:last-child {{
        display: block !important;
        width: 100% !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(odd) > div:last-child > div {{
        background-color: {COLORS['white']} !important;
        border-radius: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
    }}

    div[data-testid="stChatMessage"]:nth-child(odd) p {{
        color: {COLORS['black']} !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        margin: 0.5em 0 !important;
    }}

    .stChatMessage:hover {{
        box-shadow: none !important;
    }}

    /* Accent border - black */
    .accent-border {{
        border-left: 3px solid {COLORS['black']};
        padding-left: 12px;
        border-radius: 0;
    }}

    /* Clean container - minimal */
    .clean-container {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['border_gray']};
        border-radius: 6px;
        padding: 16px;
        margin: 12px 0;
        transition: all 0.2s ease;
    }}

    .clean-container:hover {{
        border-color: {COLORS['black']};
        box-shadow: none;
    }}

    /* Column dividers - black lines instead of yellow */
    [data-testid="column"] {{
        animation: none;
        position: relative;
    }}

    /* Black border instead of golden */
    [data-testid="column"]:first-child {{
        border-right: 1px solid {COLORS['border_gray']};
        padding-right: 20px;
    }}

    [data-testid="column"]:last-child {{
        padding-left: 20px;
    }}

    /* Horizontal dividers - black instead of yellow */
    hr {{
        border: none;
        border-top: 1px solid {COLORS['border_gray']};
        margin: 1.5rem 0;
    }}

    /* Remove animations */
    @keyframes fadeIn {{
        from {{ opacity: 1; transform: translateY(0); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* No icons needed */
    .fa, .fas, .far, .fal, .fab {{
        display: none !important;
    }}
</style>
"""

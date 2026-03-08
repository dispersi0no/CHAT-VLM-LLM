"""Custom CSS styles for Streamlit application."""

def get_custom_css() -> str:
    """
    Get custom CSS for modern Streamlit UI.
    
    Returns:
        CSS string for st.markdown
    """
    return """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Root variables */
    :root {
        --primary-color: #FF4B4B;
        --secondary-color: #0068C9;
        --background-color: #0E1117;
        --secondary-bg: #262730;
        --card-bg: #1E1E2E;
        --text-color: #FAFAFA;
        --text-secondary: #B0B0B0;
        --success-color: #00D26A;
        --warning-color: #FFB800;
        --error-color: #FF4B4B;
        --border-radius: 12px;
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
    }
    
    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main {
        padding: var(--spacing-lg);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-color);
    }
    
    h1 {
        font-size: 2.5rem;
        margin-bottom: var(--spacing-lg);
    }
    
    h2 {
        font-size: 2rem;
        margin-top: var(--spacing-xl);
        margin-bottom: var(--spacing-md);
    }
    
    h3 {
        font-size: 1.5rem;
        margin-top: var(--spacing-lg);
        margin-bottom: var(--spacing-sm);
    }
    
    /* Gradient text */
    .gradient-text {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Cards */
    .stCard, .info-card, .feature-card {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        margin: var(--spacing-md) 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .stCard:hover, .info-card:hover, .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(255, 75, 75, 0.2);
        border-color: var(--primary-color);
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: var(--border-radius);
        font-weight: 600;
        padding: var(--spacing-md) var(--spacing-lg);
        transition: all 0.3s ease;
        border: none;
        background: linear-gradient(135deg, var(--primary-color) 0%, #FF6B6B 100%);
        color: white;
        font-size: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Secondary button */
    .stButton.secondary > button {
        background: var(--secondary-bg);
        color: var(--text-color);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Upload area */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--primary-color);
        border-radius: var(--border-radius);
        padding: var(--spacing-xl);
        background: var(--card-bg);
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--secondary-color);
        background: var(--secondary-bg);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--secondary-bg) 0%, #1a1d26 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 500;
        font-size: 1rem;
        padding: var(--spacing-sm) 0;
    }
    
    /* Radio buttons */
    .stRadio > div {
        gap: var(--spacing-sm);
    }
    
    .stRadio > div > label {
        background: var(--card-bg);
        padding: var(--spacing-md);
        border-radius: var(--border-radius);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stRadio > div > label:hover {
        border-color: var(--primary-color);
        background: var(--secondary-bg);
    }
    
    /* Select box */
    .stSelectbox > div > div {
        background: var(--card-bg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius);
    }
    
    /* Text input */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--card-bg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius);
        color: var(--text-color);
        padding: var(--spacing-md);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.2);
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: var(--border-radius);
        background: var(--card-bg) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-md);
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: var(--spacing-md) var(--spacing-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-color);
    }
    
    /* Success/Error/Warning/Info messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: var(--border-radius);
        padding: var(--spacing-md);
        border-left: 4px solid;
    }
    
    .stSuccess {
        background: rgba(0, 210, 106, 0.1);
        border-left-color: var(--success-color);
    }
    
    .stError {
        background: rgba(255, 75, 75, 0.1);
        border-left-color: var(--error-color);
    }
    
    .stWarning {
        background: rgba(255, 184, 0, 0.1);
        border-left-color: var(--warning-color);
    }
    
    .stInfo {
        background: rgba(0, 104, 201, 0.1);
        border-left-color: var(--secondary-color);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--primary-color);
    }
    
    /* Divider */
    hr {
        margin: var(--spacing-xl) 0;
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: var(--spacing-md);
        margin: var(--spacing-sm) 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tables */
    table {
        border-collapse: separate;
        border-spacing: 0;
        border-radius: var(--border-radius);
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    thead {
        background: var(--secondary-bg);
    }
    
    th {
        padding: var(--spacing-md);
        text-align: left;
        font-weight: 600;
        color: var(--text-color);
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    td {
        padding: var(--spacing-md);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    tr:hover {
        background: var(--card-bg);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #FF6B6B;
    }
    
    </style>
    """
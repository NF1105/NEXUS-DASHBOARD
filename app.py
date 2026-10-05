import os
import json
import datetime
import html
import uuid
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from pypdf import PdfReader
import database as db
from ai_service import generate_study_response
from flashcard_service import generate_flashcards
from quick_reference_content import QUICK_REFERENCE_SUBJECTS
from quiz_service import (
    REFERENCE_SUBJECTS,
    format_reference_context,
    generate_quiz,
    get_reference_topics,
    match_reference_subject,
)

load_dotenv()

st.set_page_config(page_title="NEXUS-DASHBOARD", page_icon="⚡", layout="wide")

st.session_state.setdefault("nexus_splash_shown", False)
if not st.session_state.nexus_splash_shown:
    st.session_state.nexus_splash_shown = True
    st.html(
        """
        <div id="nexus-splash" role="status" aria-live="polite">
            <div class="splash-orbit splash-orbit-one"></div>
            <div class="splash-orbit splash-orbit-two"></div>
            <div class="splash-content">
                <div class="splash-mark" aria-hidden="true">N</div>
                <h1>NEXUS-DASHBOARD</h1>
                <p class="splash-credit">NF1105</p>
                <p class="splash-tagline">Study to your hearts content</p>
                <div class="splash-loader" aria-label="Loading NEXUS-DASHBOARD">
                    <span></span>
                </div>
                <button class="splash-skip" type="button">Enter workspace</button>
            </div>
        </div>
        <style>
            #nexus-splash {
                position: fixed;
                inset: 0;
                z-index: 999999;
                display: grid;
                place-items: center;
                overflow: hidden;
                background:
                    radial-gradient(ellipse at 50% 42%, rgba(90, 88, 214, 0.28), transparent 42%),
                    linear-gradient(145deg, #0b1020, #151a34 58%, #101629);
                color: #f8f8ff;
                font-family: "Segoe UI", Arial, sans-serif;
                opacity: 1;
                visibility: visible;
                transition: opacity 520ms ease, visibility 520ms ease;
            }
            #nexus-splash.splash-hidden {
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
            }
            #nexus-splash .splash-content {
                position: relative;
                z-index: 1;
                width: min(92vw, 560px);
                padding: 2rem;
                text-align: center;
                animation: nexus-rise 760ms cubic-bezier(.2, .75, .25, 1) both;
            }
            #nexus-splash .splash-mark {
                display: grid;
                width: 62px;
                height: 62px;
                margin: 0 auto 1.25rem;
                place-items: center;
                border: 1px solid rgba(196, 194, 255, .52);
                border-radius: 20px;
                background: linear-gradient(145deg, rgba(143, 139, 255, .32), rgba(143, 139, 255, .08));
                box-shadow: 0 0 42px rgba(117, 112, 255, .3), inset 0 1px rgba(255, 255, 255, .24);
                color: #fff;
                font-size: 2rem;
                font-weight: 800;
            }
            #nexus-splash h1 {
                margin: 0;
                color: #fff;
                font-size: clamp(3.5rem, 12vw, 6rem);
                font-weight: 800;
                letter-spacing: .24em;
                line-height: 1;
                text-indent: .24em;
                text-shadow: 0 0 38px rgba(156, 151, 255, .35);
            }
            #nexus-splash .splash-credit {
                margin: 1.4rem 0 0;
                color: #c9c8ff;
                font-size: .8rem;
                font-weight: 700;
                letter-spacing: .28em;
            }
            #nexus-splash .splash-tagline {
                margin: .9rem 0 0;
                color: #d4d8e8;
                font-size: clamp(1rem, 3vw, 1.2rem);
                font-weight: 400;
                letter-spacing: .025em;
            }
            #nexus-splash .splash-loader {
                width: min(210px, 56vw);
                height: 3px;
                margin: 2.2rem auto 0;
                overflow: hidden;
                border-radius: 999px;
                background: rgba(255, 255, 255, .13);
                animation: nexus-loader-dismiss 300ms ease 2s forwards;
            }
            #nexus-splash .splash-loader span {
                display: block;
                width: 42%;
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, #8c8aff, #d2caff);
                box-shadow: 0 0 16px rgba(160, 154, 255, .8);
                animation: nexus-load 1.15s ease-in-out infinite;
            }
            #nexus-splash .splash-skip {
                margin-top: 1.25rem;
                padding: .5rem .9rem;
                border: 1px solid rgba(226, 226, 255, .24);
                border-radius: 999px;
                background: rgba(255, 255, 255, .06);
                color: #d4d8e8;
                cursor: pointer;
                font: inherit;
                font-size: .78rem;
                transition: background 160ms ease, border-color 160ms ease;
            }
            #nexus-splash .splash-skip:hover,
            #nexus-splash .splash-skip:focus-visible {
                border-color: rgba(196, 194, 255, .72);
                background: rgba(143, 139, 255, .18);
                outline: none;
            }
            #nexus-splash .splash-orbit {
                position: absolute;
                top: 50%;
                left: 50%;
                width: min(74vw, 510px);
                aspect-ratio: 1;
                border: 1px solid rgba(201, 200, 255, .08);
                border-radius: 50%;
                transform: translate(-50%, -50%);
            }
            #nexus-splash .splash-orbit-two {
                width: min(94vw, 680px);
                border-color: rgba(201, 200, 255, .045);
            }
            @keyframes nexus-rise {
                from { opacity: 0; transform: translateY(14px) scale(.985); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }
            @keyframes nexus-load {
                from { transform: translateX(-120%); }
                to { transform: translateX(260%); }
            }
            @keyframes nexus-loader-dismiss {
                to { opacity: 0; visibility: hidden; }
            }
            @media (prefers-reduced-motion: reduce) {
                #nexus-splash .splash-content { animation: none; }
                #nexus-splash .splash-loader span { animation-duration: 2.8s; }
                #nexus-splash { transition-duration: 1ms; }
            }
        </style>
        <script>
            (() => {
                const splash = document.getElementById("nexus-splash");
                if (!splash) return;
                let dismissed = false;

                const dismiss = () => {
                    if (dismissed) return;
                    dismissed = true;
                    splash.classList.add("splash-hidden");
                    window.setTimeout(() => splash.remove(), 600);
                };

                splash.querySelector(".splash-skip").addEventListener("click", dismiss);
            })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )

db.init_db()

THEME_PRESETS = {
    "Dark": {
        "description": "A focused midnight workspace with cool, high-contrast accents.",
        "background": "#0d1220",
        "background_glow": "rgba(86, 107, 255, 0.14)",
        "surface": "#151c2d",
        "surface_alt": "#1b2438",
        "text": "#eef2ff",
        "muted": "#a0abc3",
        "border": "#2a354d",
        "accent": "#8b93ff",
        "accent_hover": "#a5aaff",
        "accent_soft": "#252949",
        "accent_text": "#d9dcff",
        "chart_secondary": "#39c7a4",
        "font": "'Segoe UI', sans-serif",
        "heading_font": "'Bahnschrift', 'Segoe UI', sans-serif",
        "radius": "10px",
        "card_radius": "13px",
        "shadow": "0 12px 30px rgba(0, 0, 0, 0.22)",
        "card_shadow": "0 8px 24px rgba(0, 0, 0, 0.18)",
        "design_css": """
            [data-testid="stMetric"] { background: linear-gradient(145deg, #192238, #141b2b); }
            [data-testid="stVerticalBlockBorderWrapper"] > div { background: #151c2d; }
            [data-testid="stExpander"] { background: #121a2a; }
            [data-testid="stChatMessage"] { background: #151c2d; }
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                background: linear-gradient(90deg, #8b93ff, #6ee7c0);
                box-shadow: 0 0 16px rgba(139, 147, 255, 0.35);
            }
        """,
    },
    "Blue": {
        "description": "A bold royal-blue workspace with crisp, confident contrast.",
        "background": "#eaf0ff",
        "background_glow": "rgba(42, 84, 190, 0.18)",
        "surface": "#f9fbff",
        "surface_alt": "#dce6ff",
        "text": "#14234a",
        "muted": "#52658f",
        "border": "#c6d3f1",
        "accent": "#234bb8",
        "accent_hover": "#18388f",
        "accent_soft": "#dce6ff",
        "accent_text": "#173276",
        "chart_secondary": "#22a6c7",
        "font": "Arial, sans-serif",
        "heading_font": "'Segoe UI', Arial, sans-serif",
        "radius": "7px",
        "card_radius": "12px",
        "shadow": "0 6px 18px rgba(29, 57, 120, 0.09)",
        "card_shadow": "0 8px 22px rgba(29, 57, 120, 0.11)",
        "design_css": """
            [data-testid="stMetric"] { border-top: 3px solid #234bb8; }
            [data-testid="stVerticalBlockBorderWrapper"] > div { box-shadow: 0 5px 18px rgba(29, 57, 120, 0.08); }
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                width: 4rem;
                height: 3px;
                background: linear-gradient(90deg, #18388f, #4f75da);
            }
        """,
    },
    "Purple": {
        "description": "A richer violet workspace with deeper accents and rounded surfaces.",
        "background": "#f0edff",
        "background_glow": "rgba(125, 91, 220, 0.2)",
        "surface": "#fcfbff",
        "surface_alt": "#e4dcff",
        "text": "#292044",
        "muted": "#665b83",
        "border": "#d8cff2",
        "accent": "#5934b5",
        "accent_hover": "#42268f",
        "accent_soft": "#e9e1ff",
        "accent_text": "#42268f",
        "chart_secondary": "#10b981",
        "font": "'Trebuchet MS', sans-serif",
        "heading_font": "'Trebuchet MS', sans-serif",
        "radius": "10px",
        "card_radius": "17px",
        "shadow": "0 8px 24px rgba(57, 39, 110, 0.075)",
        "card_shadow": "0 12px 34px rgba(57, 39, 110, 0.09)",
        "design_css": """
            [data-testid="stMetric"] { background: linear-gradient(145deg, #fcfbff 25%, #f2eeff 100%); }
            [data-testid="stVerticalBlockBorderWrapper"] > div { background: rgba(252, 251, 255, 0.96); }
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                background: linear-gradient(90deg, #5934b5, #a78bfa);
            }
        """,
    },
    "White": {
        "description": "A simple, neutral white workspace with clean black-and-gray details.",
        "background": "#ffffff",
        "background_glow": "rgba(226, 232, 240, 0.3)",
        "surface": "#ffffff",
        "surface_alt": "#f4f5f7",
        "text": "#202124",
        "muted": "#62666f",
        "border": "#e3e5e8",
        "accent": "#424852",
        "accent_hover": "#292d33",
        "accent_soft": "#f0f1f3",
        "accent_text": "#292d33",
        "chart_secondary": "#9ca3af",
        "font": "Arial, sans-serif",
        "heading_font": "Arial, sans-serif",
        "radius": "6px",
        "card_radius": "10px",
        "shadow": "0 4px 14px rgba(24, 28, 35, 0.045)",
        "card_shadow": "0 6px 18px rgba(24, 28, 35, 0.055)",
        "design_css": """
            [data-testid="stMetric"] { background: #ffffff; }
            [data-testid="stVerticalBlockBorderWrapper"] > div { box-shadow: 0 4px 16px rgba(24, 28, 35, 0.04); }
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                width: 2.5rem;
                height: 3px;
                background: #424852;
            }
        """,
    },
    "Golden": {
        "description": "A warm, bookish gold-and-cream theme with editorial typography.",
        "background": "#fbf6eb",
        "background_glow": "rgba(229, 184, 92, 0.17)",
        "surface": "#fffdf8",
        "surface_alt": "#f6edda",
        "text": "#342b1d",
        "muted": "#796b55",
        "border": "#e8dcc4",
        "accent": "#a96d08",
        "accent_hover": "#875506",
        "accent_soft": "#f5e8c9",
        "accent_text": "#754800",
        "chart_secondary": "#c39b43",
        "font": "Georgia, serif",
        "heading_font": "Georgia, serif",
        "radius": "6px",
        "card_radius": "8px",
        "shadow": "0 4px 14px rgba(87, 62, 22, 0.045)",
        "card_shadow": "0 5px 17px rgba(87, 62, 22, 0.055)",
        "design_css": """
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                width: 4.5rem;
                height: 2px;
                background: #a96d08;
            }
            [data-testid="stVerticalBlockBorderWrapper"] > div,
            .card-box { border-left: 3px solid #d6a445; }
            [data-testid="stMetricValue"] { font-family: Georgia, serif; }
        """,
    },
    "Red": {
        "description": "A bold crimson workspace with sharper edges and energetic contrast.",
        "background": "#fff6f5",
        "background_glow": "rgba(238, 96, 91, 0.14)",
        "surface": "#ffffff",
        "surface_alt": "#fff0ee",
        "text": "#321f25",
        "muted": "#80636a",
        "border": "#efd9d8",
        "accent": "#c8313d",
        "accent_hover": "#a92330",
        "accent_soft": "#ffebe9",
        "accent_text": "#98232c",
        "chart_secondary": "#ef806f",
        "font": "'Arial Narrow', Arial, sans-serif",
        "heading_font": "'Arial Narrow', 'Segoe UI', sans-serif",
        "radius": "5px",
        "card_radius": "9px",
        "shadow": "0 5px 16px rgba(126, 35, 45, 0.06)",
        "card_shadow": "0 8px 22px rgba(126, 35, 45, 0.075)",
        "design_css": """
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
                width: 4rem;
                height: 5px;
                background: linear-gradient(90deg, #c8313d, #f08268);
            }
            [data-testid="stVerticalBlockBorderWrapper"] > div,
            .card-box { border-top: 2px solid #c8313d; }
            [data-testid="stMetricValue"] { letter-spacing: 0; }
        """,
    },
}

st.session_state.setdefault("appearance_mode", "Purple")
if st.session_state.appearance_mode not in THEME_PRESETS:
    st.session_state.appearance_mode = "Purple"
active_theme = THEME_PRESETS[st.session_state.appearance_mode]
appearance_slot = st.sidebar.empty()

theme_css = """
    <style>
    :root {
        --nx-background: __BACKGROUND__;
        --nx-glow: __GLOW__;
        --nx-surface: __SURFACE__;
        --nx-surface-alt: __SURFACE_ALT__;
        --nx-text: __TEXT__;
        --nx-muted: __MUTED__;
        --nx-border: __BORDER__;
        --nx-accent: __ACCENT__;
        --nx-accent-hover: __ACCENT_HOVER__;
        --nx-accent-soft: __ACCENT_SOFT__;
        --nx-accent-text: __ACCENT_TEXT__;
        --nx-radius: __RADIUS__;
        --nx-card-radius: __CARD_RADIUS__;
        --nx-shadow: __SHADOW__;
        --nx-card-shadow: __CARD_SHADOW__;
        --nx-font: __FONT__;
        --nx-heading-font: __HEADING_FONT__;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at 82% 0%, var(--nx-glow), transparent 34rem),
            var(--nx-background);
        color: var(--nx-text);
        font-family: var(--nx-font);
    }
    .stApp p, .stApp label, .stApp [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] {
        color: var(--nx-text);
        font-family: var(--nx-font);
    }
    .stApp button, .stApp input, .stApp textarea, .stApp select,
    [data-testid="stSidebar"] button, [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea, [data-testid="stSidebar"] select,
    [data-baseweb="popover"] [role="option"] {
        font-family: var(--nx-font) !important;
    }
    [data-testid="stHeader"] {
        background: color-mix(in srgb, var(--nx-surface) 88%, transparent);
        border-bottom: 1px solid var(--nx-border);
        backdrop-filter: blur(14px);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--nx-surface), var(--nx-background));
        border-right: 1px solid var(--nx-border);
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
        border-radius: var(--nx-radius);
        background: var(--nx-surface);
        color: var(--nx-text);
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
        color: var(--nx-muted);
        font-weight: 600;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1440px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: var(--nx-text);
        letter-spacing: -0.04em;
        font-family: var(--nx-heading-font);
    }
    [data-testid="stMarkdownContainer"] h1 {
        color: var(--nx-text);
        letter-spacing: -0.045em;
        line-height: 1.15;
        padding-bottom: 0.15rem;
        font-family: var(--nx-heading-font);
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1::after {
        content: "";
        display: block;
        width: 3rem;
        height: 4px;
        margin-top: 0.8rem;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--nx-accent), var(--nx-accent-hover));
    }
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--nx-text);
        letter-spacing: -0.025em;
        font-family: var(--nx-heading-font);
    }
    [data-testid="stMarkdownContainer"] h2 {
        margin-top: 1.6rem;
    }
    [data-testid="stMarkdownContainer"] p {
        line-height: 1.65;
    }
    [data-testid="stMarkdownContainer"] a {
        color: var(--nx-accent);
        font-weight: 600;
        text-decoration-thickness: 1px;
        text-underline-offset: 3px;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 0.42rem 0.7rem;
        margin: 0.12rem 0;
        border: 1px solid transparent;
        border-radius: var(--nx-radius);
        transition: background-color 140ms ease, border-color 140ms ease,
            box-shadow 140ms ease, color 140ms ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: var(--nx-accent-soft);
        border-color: var(--nx-border);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: var(--nx-accent-soft);
        border-color: var(--nx-border);
        box-shadow: inset 3px 0 0 var(--nx-accent);
        color: var(--nx-accent-text);
    }
    [data-testid="stButton"] button {
        min-height: 2.65rem;
        border-radius: var(--nx-radius);
        font-weight: 600;
        background: var(--nx-surface);
        color: var(--nx-text);
        box-shadow: var(--nx-shadow);
        transition: background-color 140ms ease, border-color 140ms ease,
            color 140ms ease, transform 140ms ease, box-shadow 140ms ease;
    }
    [data-testid="stButton"] button:hover {
        border-color: var(--nx-accent);
        color: var(--nx-accent);
        transform: translateY(-1px);
        box-shadow: var(--nx-card-shadow);
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, var(--nx-accent-hover), var(--nx-accent));
        border-color: var(--nx-accent);
        color: #ffffff;
        box-shadow: var(--nx-card-shadow);
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        background: var(--nx-accent-hover);
        border-color: var(--nx-accent-hover);
        color: #ffffff;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [role="combobox"],
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input {
        border-radius: var(--nx-radius);
        background: var(--nx-surface);
        color: var(--nx-text);
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stSelectbox"] [role="combobox"]:focus {
        border-color: var(--nx-accent);
        box-shadow: 0 0 0 3px var(--nx-accent-soft);
    }
    [data-testid="stMetric"] {
        padding: 1.15rem 1.2rem;
        border: 1px solid var(--nx-border);
        border-radius: var(--nx-card-radius);
        background: var(--nx-surface);
        box-shadow: var(--nx-card-shadow);
    }
    [data-testid="stMetricLabel"] {
        color: var(--nx-muted);
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: var(--nx-text);
        font-weight: 700;
        letter-spacing: -0.035em;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: var(--nx-card-radius);
        border-color: var(--nx-border);
        background: var(--nx-surface);
        box-shadow: var(--nx-card-shadow);
    }
    [data-testid="stExpander"] {
        border: 1px solid var(--nx-border);
        border-radius: var(--nx-card-radius);
        background: var(--nx-surface);
        transition: border-color 140ms ease, box-shadow 140ms ease;
    }
    [data-testid="stExpander"]:hover {
        border-color: var(--nx-accent);
        box-shadow: var(--nx-shadow);
    }
    [data-testid="stTabs"] [role="tablist"] {
        gap: 0.35rem;
        border-bottom: 1px solid var(--nx-border);
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: var(--nx-radius) var(--nx-radius) 0 0;
        font-weight: 600;
        color: var(--nx-muted);
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--nx-accent);
    }
    [data-testid="stChatMessage"] {
        border: 1px solid var(--nx-border);
        border-radius: var(--nx-card-radius);
        background: var(--nx-surface);
        box-shadow: var(--nx-shadow);
    }
    [data-testid="stChatInput"] {
        border-radius: var(--nx-card-radius);
        background: var(--nx-surface);
        box-shadow: var(--nx-card-shadow);
    }
    .card-box {
        background: var(--nx-surface);
        border: 1px solid var(--nx-border);
        border-radius: var(--nx-card-radius);
        padding: 24px;
        margin-bottom: 15px;
        box-shadow: var(--nx-card-shadow);
    }
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, var(--nx-accent), var(--nx-accent-hover));
    }
    [data-testid="stAlert"] {
        border-radius: var(--nx-card-radius);
    }
    [data-testid="stCode"] {
        border-radius: var(--nx-card-radius);
        background: var(--nx-surface-alt);
    }
    [data-testid="stMarkdownContainer"] code {
        border-radius: 5px;
    }
    [data-testid="stSlider"] [role="slider"],
    [data-testid="stCheckbox"] input:checked + div {
        accent-color: var(--nx-accent);
    }
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        color: white;
    }
    .badge-high { background-color: #ef4444; }
    .badge-medium { background-color: #f59e0b; }
    .badge-low { background-color: #10b981; }
    @media (max-width: 800px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 1rem 2rem;
        }
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1 {
            font-size: 2rem;
        }
        .card-box {
            padding: 17px;
            border-radius: 14px;
        }
    }
    __DESIGN_CSS__
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
"""
theme_css = (
    theme_css.replace("__BACKGROUND__", active_theme["background"])
    .replace("__GLOW__", active_theme["background_glow"])
    .replace("__SURFACE__", active_theme["surface"])
    .replace("__SURFACE_ALT__", active_theme["surface_alt"])
    .replace("__TEXT__", active_theme["text"])
    .replace("__MUTED__", active_theme["muted"])
    .replace("__BORDER__", active_theme["border"])
    .replace("__ACCENT__", active_theme["accent"])
    .replace("__ACCENT_HOVER__", active_theme["accent_hover"])
    .replace("__ACCENT_SOFT__", active_theme["accent_soft"])
    .replace("__ACCENT_TEXT__", active_theme["accent_text"])
    .replace("__RADIUS__", active_theme["radius"])
    .replace("__CARD_RADIUS__", active_theme["card_radius"])
    .replace("__SHADOW__", active_theme["shadow"])
    .replace("__CARD_SHADOW__", active_theme["card_shadow"])
    .replace("__FONT__", active_theme["font"])
    .replace("__HEADING_FONT__", active_theme["heading_font"])
    .replace("__DESIGN_CSS__", active_theme["design_css"])
)
st.markdown(theme_css, unsafe_allow_html=True)

# Helper: Audio Voice Reader
def render_tts_button(text_to_read, label="🔊 Read Aloud"):
    component_id = f"tts-controls-{uuid.uuid4().hex}"
    speech_text = (
        json.dumps(text_to_read)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    html_code = f"""
        <div id="{component_id}" style="display: flex; gap: 8px; align-items: center;">
            <button type="button" class="tts-read" style="background: {active_theme['accent']}; color: white; border: none; padding: 7px 14px; border-radius: {active_theme['radius']}; cursor: pointer; font-weight: 600;">{html.escape(label)}</button>
            <button type="button" class="tts-stop" aria-label="Stop reading aloud" style="background: {active_theme['surface_alt']}; color: {active_theme['text']}; border: 1px solid {active_theme['border']}; padding: 7px 14px; border-radius: {active_theme['radius']}; cursor: pointer; font-weight: 600;">⏹ Stop</button>
        </div>
        <script>
        (() => {{
            const controls = document.getElementById("{component_id}");
            controls.querySelector(".tts-read").addEventListener("click", () => {{
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance({speech_text});
            window.speechSynthesis.speak(msg);
            }});
            controls.querySelector(".tts-stop").addEventListener("click", () => {{
                window.speechSynthesis.cancel();
            }});
        }})();
        </script>
    """
    st.html(html_code, width="content", unsafe_allow_javascript=True)

# Helper: Citation Generator
def generate_citation(title, url, author="Anonymous", year=None, style="MLA"):
    if not year: year = datetime.datetime.now().year
    today_str = datetime.datetime.now().strftime("%d %b. %Y")
    if style == "MLA": return f'{author}. "{title}." *Web Source*, {year}, {url}. Accessed {today_str}.'
    elif style == "APA": return f'{author}. ({year}). *{title}*. Retrieved from {url}'
    elif style == "Chicago": return f'{author}. "{title}." Last modified {year}. {url}.'

# Helper: Web Search
def search_online_sources(query):
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append({"title": r['title'], "link": r['href'], "snippet": r['body']})
        return results
    except Exception as e:
        return [{"title": "Search Error", "link": "#", "snippet": str(e)}]

def open_ai_assistant():
    st.session_state.nav_section = "🤖 AI Study Assistant"

def open_course_topics(subject_id):
    st.session_state.active_subject_id = subject_id
    st.session_state.topic_subject_id = subject_id
    st.session_state.nav_section = "📖 Topic Reader"

def format_search_context(results):
    return "\n\n".join(
        f"[{index}] {result['title']}\nURL: {result['link']}\n{result['snippet']}"
        for index, result in enumerate(results, start=1)
        if result.get("link") and result["link"] != "#"
    )

def render_source_links(results):
    for index, result in enumerate(results, start=1):
        if result.get("link") and result["link"] != "#":
            st.markdown(f"[{index}. {result['title']}]({result['link']})")
            st.caption(result["snippet"])

def activate_subject(subject_id):
    st.session_state.active_subject_id = subject_id

@st.fragment(run_every="1s")
def render_active_study_timer():
    started_at = st.session_state.get("study_timer_started_at")
    if started_at is None:
        return

    elapsed_seconds = max(0, int((datetime.datetime.now() - started_at).total_seconds()))
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    with st.container(border=True):
        st.markdown(f"**Studying: {st.session_state.study_timer_subject_name}**")
        st.metric("Elapsed time", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        if st.button("⏹ End study session", key="stop_study_session"):
            elapsed_seconds = max(
                1,
                int((datetime.datetime.now() - started_at).total_seconds()),
            )
            db.log_study_session(
                st.session_state.study_timer_subject_id,
                elapsed_seconds / 3600,
            )
            st.session_state.study_timer_started_at = None
            st.session_state.study_timer_subject_id = None
            st.session_state.study_timer_subject_name = None
            st.toast("Study session saved to your weekly progress.")
            st.rerun()

@st.fragment(run_every="30s")
def render_due_reading_reminders():
    now = datetime.datetime.now()
    for reminder in db.get_reading_reminders():
        scheduled_at = datetime.datetime.fromisoformat(reminder["scheduled_at"])
        if scheduled_at <= now:
            if not reminder["notified"]:
                db.mark_reading_reminder_notified(reminder["id"])
                st.toast(f"Reading time: {reminder['subject_name']} - {reminder['title']}")
            st.warning(
                f"Reading reminder: **{reminder['subject_name']}** - {reminder['title']}"
            )
            if st.button("Mark as read", key=f"complete_reminder_{reminder['id']}"):
                db.complete_reading_reminder(reminder["id"])
                st.toast("Reading reminder completed.")
                st.rerun()

# --- SIDEBAR: NAVIGATION SECTIONS & ACTIVE SUBJECT ---
with st.sidebar:
    st.title("⚡ NEXUS-DASHBOARD")
    st.caption("Structured Learning Workspace")
    with appearance_slot.container():
        st.selectbox(
            "Appearance",
            list(THEME_PRESETS),
            key="appearance_mode",
            format_func=lambda mode: {
                "Dark": "🌙 Dark",
                "Blue": "🌊 Blue",
                "Purple": "💜 Purple",
                "White": "⚪ White",
                "Golden": "✨ Golden",
                "Red": "🔴 Red",
            }[mode],
        )
        st.caption(THEME_PRESETS[st.session_state.appearance_mode]["description"])
    st.divider()

    # SECTION NAVIGATION
    st.subheader("🧭 Workspace Sections")
    nav_section = st.radio(
        "Go to Section:",
        [
            "📊 Dashboard & Analytics",
            "📚 Starter Courses & Subjects",
            "📂 Laptop File & Note Upload",
            "🎯 Quiz Generator & Practice",
            "🌐 Web Search & Citation Hub",
            "📖 Quick Knowledge Library",
            "📖 Topic Reader",
            "🤖 AI Study Assistant",
            "🧠 Flashcards",
        ],
        key="nav_section",
    )
    st.divider()

    environment_api_key = os.getenv("OPENAI_API_KEY", "")
    with st.expander(
        "🔐 OpenAI connection",
        expanded=not (
            environment_api_key
            or st.session_state.get("openai_api_key_input", "")
        ),
    ):
        st.text_input(
            "OpenAI API key",
            type="password",
            key="openai_api_key_input",
            placeholder="Paste your API key once",
            help="Used automatically for the AI Study Assistant, quiz generation, and flashcards.",
        )
        st.caption(
            "Stored only in this browser session, not in the NEXUS-DASHBOARD database. "
            "AI features send your prompts and selected source text to OpenAI."
        )
    api_key = environment_api_key or st.session_state.get("openai_api_key_input", "")
    if api_key:
        st.caption("OpenAI connected for this session.")
    else:
        st.caption("Add a key here to enable generated AI across the app.")
    st.divider()

    # Active Subject Selection
    subjects = db.get_subjects()
    if subjects:
        subject_ids = [subject["id"] for subject in subjects]
        if st.session_state.get("active_subject_id") not in subject_ids:
            st.session_state.active_subject_id = subject_ids[0]
        active_subject_id = st.selectbox(
            "Active Subject:",
            subject_ids,
            format_func=lambda subject_id: next(
                subject["name"] for subject in subjects if subject["id"] == subject_id
            ),
            key="active_subject_id",
        )
        active_subject = next(
            subject for subject in subjects if subject["id"] == active_subject_id
        )
        selected_subj_name = active_subject["name"]
    else:
        active_subject = None
        selected_subj_name = "Default"
        st.caption("No active subject")

    st.divider()
    st.subheader("🤖 Interactive AI Assistant")
    
    # Interactive AI Action Buttons
    if st.button("⚡ AI: Complete High Priority Tasks", use_container_width=True):
        tasks = db.get_tasks()
        for t in tasks:
            if t["priority"] == "High" and not t["done"]:
                db.update_task_status(t["id"], True)
        st.toast("AI completed all urgent tasks!")
        st.rerun()

    st.caption("Chat, read texts, or search the web with the study assistant.")
    st.button(
        "🤖 Open AI Study Assistant",
        key="open_ai_assistant",
        on_click=open_ai_assistant,
    )

render_due_reading_reminders()

# ==============================================================================
# SECTION 1: DASHBOARD & ANALYTICS
# ==============================================================================
if nav_section == "📊 Dashboard & Analytics":
    st.title("📊 Overview Dashboard")
    st.caption(f"Active Subject: **{selected_subj_name}**")

    if active_subject:
        if st.session_state.get("study_timer_started_at") is None:
            if st.button("▶ Start study session", key="start_study_session"):
                st.session_state.study_timer_started_at = datetime.datetime.now()
                st.session_state.study_timer_subject_id = active_subject["id"]
                st.session_state.study_timer_subject_name = active_subject["name"]
        if st.session_state.get("study_timer_started_at") is not None:
            render_active_study_timer()
    else:
        st.info("Add a subject before starting a study session.")

    st.subheader("📖 Reading reminders")
    if subjects:
        next_reminder = datetime.datetime.now() + datetime.timedelta(minutes=30)
        active_subject_index = next(
            (index for index, subject in enumerate(subjects) if active_subject and subject["id"] == active_subject["id"]),
            0,
        )
        with st.form("reading_reminder_form", border=True):
            reminder_subject = st.selectbox(
                "Subject",
                subjects,
                index=active_subject_index,
                format_func=lambda subject: subject["name"],
            )
            reading_focus = st.text_input(
                "Reading focus",
                placeholder="Chapter, article, or topic",
            )
            date_col, time_col = st.columns(2)
            with date_col:
                reminder_date = st.date_input("Date", value=next_reminder.date())
            with time_col:
                reminder_time = st.time_input(
                    "Time",
                    value=next_reminder.time().replace(second=0, microsecond=0),
                )
            schedule_reminder = st.form_submit_button("Schedule reminder")

        if schedule_reminder:
            scheduled_at = datetime.datetime.combine(reminder_date, reminder_time)
            if scheduled_at <= datetime.datetime.now():
                st.error("Choose a future date and time for this reminder.")
            else:
                db.add_reading_reminder(
                    reminder_subject["id"],
                    reading_focus.strip() or "Reading session",
                    scheduled_at.isoformat(timespec="minutes"),
                )
                st.toast("Reading reminder scheduled.")
                st.rerun()
    else:
        st.info("Add a subject before scheduling a reading reminder.")

    pending_reminders = db.get_reading_reminders()
    if pending_reminders:
        for reminder in pending_reminders:
            reminder_col, action_col = st.columns([4, 1])
            with reminder_col:
                reminder_datetime = datetime.datetime.fromisoformat(reminder["scheduled_at"])
                st.write(
                    f"**{reminder['subject_name']}**: {reminder['title']} "
                    f"· {reminder_datetime.strftime('%a, %b %d at %I:%M %p')}"
                )
            with action_col:
                if st.button("Cancel", key=f"cancel_reminder_{reminder['id']}"):
                    db.delete_reading_reminder(reminder["id"])
                    st.rerun()
    else:
        st.caption("No reading reminders scheduled.")
    
    study_df = db.get_study_hours_data()
    task_df = db.get_task_status_data()

    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown("**Weekly Study Hours Logged**")
        if not study_df.empty:
            fig = px.bar(study_df, x="Day", y="Hours", text_auto=".1f", color_discrete_sequence=[active_theme["accent"]])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=active_theme["muted"], family=active_theme["font"]), height=260)
            st.plotly_chart(fig, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown("**Task Progress**")
        fig2 = px.pie(task_df, names="Status", values="Count", hole=0.6, color_discrete_sequence=[active_theme["accent"], active_theme["chart_secondary"]])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color=active_theme["muted"], family=active_theme["font"]), height=260)
        st.plotly_chart(fig2, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    # Task List
    st.subheader("📋 Action Items")
    with st.form("new_task_form", border=True):
        task_title = st.text_input("Task", placeholder="What needs to get done?")
        task_col, date_col = st.columns(2)
        with task_col:
            task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        with date_col:
            task_due_date = st.date_input("Due date (optional)", value=None)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        if not task_title.strip():
            st.error("Enter a task before adding it.")
        else:
            db.add_task(
                task_title.strip(),
                task_priority,
                task_due_date.isoformat() if task_due_date else None,
            )
            st.toast("Task added.")
            st.rerun()

    for t in db.get_tasks():
        tc1, tc2, tc3 = st.columns([0.5, 3, 1])
        with tc1:
            done = st.checkbox("", value=t["done"], key=f"dash_tk_{t['id']}")
            if done != t["done"]:
                db.update_task_status(t["id"], done)
                st.rerun()
        with tc2:
            task_label = f"~~{t['title']}~~" if t["done"] else t["title"]
            if t["due_date"]:
                due_date_label = datetime.date.fromisoformat(t["due_date"]).strftime("%b %d, %Y")
                task_label += f" · Due {due_date_label}"
            st.write(task_label)
        with tc3: st.markdown(f'<span class="badge badge-{t["priority"].lower()}">{t["priority"]}</span>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 2: STARTER COURSES & SUBJECTS
# ==============================================================================
elif nav_section == "📚 Starter Courses & Subjects":
    st.title("📚 Starter Courses & Academic Catalog")
    st.caption("College-level course guides plus starter subjects across grade levels.")

    level_filter = st.radio(
        "Filter Grade Level:",
        ["College", "High School", "Middle School", "All levels"],
        horizontal=True,
    )
    filtered_subjects = db.get_subjects(
        level_filter=None if level_filter == "All levels" else level_filter
    )

    st.subheader("All subjects" if level_filter == "All levels" else f"{level_filter} Subjects")
    pending_subject_id = st.session_state.get("pending_subject_removal_id")
    pending_subject = next(
        (subject for subject in db.get_subjects() if subject["id"] == pending_subject_id),
        None,
    )
    if pending_subject:
        with st.container(border=True):
            st.warning(
                f"Remove **{pending_subject['name']}**? This also removes its notes, quizzes, reading reminders, and study history."
            )
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm removal", type="primary", key="confirm_subject_removal"):
                    if st.session_state.get("study_timer_subject_id") == pending_subject_id:
                        st.session_state.study_timer_started_at = None
                        st.session_state.study_timer_subject_id = None
                        st.session_state.study_timer_subject_name = None
                    db.delete_subject(pending_subject_id)
                    st.session_state.pending_subject_removal_id = None
                    st.toast(f"Removed {pending_subject['name']}.")
                    st.rerun()
            with cancel_col:
                if st.button("Keep subject", key="cancel_subject_removal"):
                    st.session_state.pending_subject_removal_id = None
                    st.rerun()
    elif pending_subject_id is not None:
        st.session_state.pending_subject_removal_id = None

    cols = st.columns(2)
    for idx, subj in enumerate(filtered_subjects):
        with cols[idx % 2]:
            st.markdown(f'<div class="card-box">', unsafe_allow_html=True)
            st.markdown(f"### 📘 {subj['name']}")
            st.caption(f"Target Level: {subj['level']}")
            notes_count = len(db.get_notes_for_subject(subj["id"]))
            st.write(f"**Uploaded Resources:** {notes_count} Notes/Files")
            course_topics = [
                topic
                for topic in db.get_reference_wiki_topics(subj["id"])
                if topic["title"] != "College course guide"
            ]
            if course_topics:
                st.caption(f"{len(course_topics)} guided topics")
                st.button(
                    "Explore course topics",
                    key=f"open_topics_{subj['id']}",
                    on_click=open_course_topics,
                    args=(subj["id"],),
                )
            else:
                for topic in db.get_reference_wiki_topics(subj["id"]):
                    st.write(topic["summary"])
                    with st.expander(topic["title"]):
                        st.write(topic["content"])
            st.button(
                f"Select '{subj['name']}' as Active",
                key=f"sel_{subj['id']}",
                on_click=activate_subject,
                args=(subj["id"],),
            )
            if st.button("Remove subject", key=f"remove_subject_{subj['id']}"):
                st.session_state.pending_subject_removal_id = subj["id"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("➕ Create Custom Course / Subject"):
        custom_name = st.text_input("Course Title")
        custom_lvl = st.selectbox("Grade Level", ["College", "High School", "Middle School"])
        if st.button("Add Course") and custom_name:
            db.add_subject(custom_name, custom_lvl)
            st.toast("New course added!")
            st.rerun()

# ============================================================================
# COURSE TOPICS: DEDICATED SUBJECT AND TOPIC READER
# ============================================================================
elif nav_section == "📖 Topic Reader":
    st.title("📖 Course Topic Reader")
    topic_subjects = [
        subject
        for subject in db.get_subjects()
        if any(
            topic["title"] != "College course guide"
            for topic in db.get_reference_wiki_topics(subject["id"])
        )
    ]
    topic_subject_ids = [subject["id"] for subject in topic_subjects]
    if not topic_subjects:
        st.info("No guided course topics are available yet.")
    else:
        default_subject_id = st.session_state.get("topic_subject_id")
        if default_subject_id not in topic_subject_ids:
            default_subject_id = topic_subject_ids[0]
            st.session_state.topic_subject_id = default_subject_id
        chosen_subject_id = st.selectbox(
            "Subject",
            topic_subject_ids,
            format_func=lambda subject_id: next(
                subject["name"] for subject in topic_subjects if subject["id"] == subject_id
            ),
            key="topic_subject_id",
        )
        chosen_subject = next(
            subject for subject in topic_subjects if subject["id"] == chosen_subject_id
        )
        topics = [
            topic
            for topic in db.get_reference_wiki_topics(chosen_subject_id)
            if topic["title"] != "College course guide"
        ]
        st.caption(f"{chosen_subject['level']} level · {len(topics)} topics")
        if topics:
            topic_tabs = st.tabs([topic["title"] for topic in topics])
            for topic_tab, topic in zip(topic_tabs, topics):
                with topic_tab:
                    st.subheader(topic["title"])
                    st.write(topic["summary"])
                    st.markdown(topic["content"])

# ============================================================================
# AI STUDY ASSISTANT: CHAT, TEXT READING, AND WEB RESEARCH
# ============================================================================
elif nav_section == "🤖 AI Study Assistant":
    st.title("🤖 AI Study Assistant")
    st.caption("Ask questions, understand course material, and research with linked sources.")

    if api_key:
        st.success("Generated AI is connected.")
    else:
        st.info("Web search works without a key. Add your API key in the sidebar for generated answers and text explanations.")

    assistant_mode = st.segmented_control(
        "Choose a tool",
        ["Chat", "Read a text", "Search the web"],
        default="Chat",
        key="assistant_mode",
    )

    if assistant_mode == "Chat":
        note_options = db.get_notes_for_subject(active_subject["id"]) if active_subject else []
        note_ids = [None] + [note["id"] for note in note_options]
        selected_note_id = st.selectbox(
            "Use a saved note as context (optional)",
            note_ids,
            format_func=lambda note_id: "No note" if note_id is None else next(
                note["title"] for note in note_options if note["id"] == note_id
            ),
            key="assistant_context_note_id",
        )
        search_before_answer = st.checkbox("Search the web for this question", key="assistant_search_chat")
        chat_history = db.get_chat_history()
        if chat_history and st.button(
            "Clear chat history",
            key="clear_ai_chat_history",
            help="Delete all saved messages from this assistant conversation.",
        ):
            db.clear_chat_history()
            st.toast("Previous AI chats cleared.")
            st.rerun()

        for message in chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if chat_history:
            st.caption("Continue the conversation")
            prompt_suggestions = [
                ("Give me an example", "Show me a practical, real-world example of that."),
                ("Quiz me", "Ask me one question to check my understanding. Wait for my answer before continuing."),
                ("Explain it more simply", "Explain that again in simpler terms, one step at a time."),
            ]
        else:
            st.caption("Not sure where to start? Pick a prompt or type your own.")
            prompt_suggestions = [
                ("Learn a topic", "Ask me what topic I want to understand and what I already know, then teach it step by step."),
                ("Quiz me", "Ask me what topic I want to practice, then quiz me one question at a time and wait for each answer."),
                ("Make a study plan", "Ask what I need to study and when my deadline is, then help me make a practical study plan."),
            ]

        suggestion_columns = st.columns(len(prompt_suggestions))
        for column, (label, suggested_prompt) in zip(suggestion_columns, prompt_suggestions):
            with column:
                if st.button(label, key=f"assistant_chat_suggestion_{label}"):
                    st.session_state.pending_chat_prompt = suggested_prompt
                    st.rerun()

        prompt = st.chat_input(
            "Ask about a concept, note, or research question",
            key="assistant_chat_input",
        )
        if prompt is None:
            prompt = st.session_state.pop("pending_chat_prompt", None)

        if prompt:
            history = db.get_chat_history()
            db.save_chat_message("user", prompt)
            context_parts = []
            if selected_note_id is not None:
                selected_note = next(note for note in note_options if note["id"] == selected_note_id)
                context_parts.append(
                    f"Saved note: {selected_note['title']}\n{selected_note['content'][:16000]}"
                )
            source_results = []
            if search_before_answer:
                with st.spinner("Searching for helpful sources..."):
                    source_results = search_online_sources(prompt)
                context_parts.append("Web search results:\n" + format_search_context(source_results))
            context = "\n\n".join(part for part in context_parts if part.strip())
            try:
                if api_key:
                    with st.spinner("Thinking through your question..."):
                        answer = generate_study_response(api_key, prompt, context, history)
                elif source_results and source_results[0]["title"] != "Search Error":
                    answer = "I found these pages. Add your API key in the sidebar to get a generated synthesis.\n\n"
                    answer += "\n\n".join(
                        f"**{result['title']}**\n\n{result['snippet']}\n\n{result['link']}"
                        for result in source_results
                    )
                else:
                    answer = "Add your OpenAI API key in the sidebar to enable generated answers. You can use Search the web without a key."
            except (RuntimeError, ValueError) as error:
                answer = f"I could not complete that request: {error}"
            if source_results and api_key and source_results[0]["title"] != "Search Error":
                answer += "\n\n**Sources**\n" + "\n".join(
                    f"[{index}. {result['title']}]({result['link']})"
                    for index, result in enumerate(source_results, start=1)
                )
            db.save_chat_message("assistant", answer)
            st.rerun()

    elif assistant_mode == "Read a text":
        text_source = st.radio(
            "Text source",
            ["Paste text", "Upload a file", "Saved subject note"],
            horizontal=True,
            key="assistant_text_source",
        )
        reading_text = ""
        if text_source == "Paste text":
            reading_text = st.text_area(
                "Text to read",
                height=240,
                placeholder="Paste a passage, article, or reading here.",
                key="assistant_pasted_text",
            )
        elif text_source == "Upload a file":
            reading_file = st.file_uploader(
                "Upload PDF, TXT, or Markdown",
                type=["pdf", "txt", "md"],
                key="assistant_reading_file",
            )
            if reading_file:
                try:
                    if reading_file.name.lower().endswith(".pdf"):
                        reading_text = "\n".join(
                            page.extract_text() or "" for page in PdfReader(reading_file).pages
                        )
                    else:
                        reading_text = reading_file.getvalue().decode("utf-8")
                except (UnicodeDecodeError, ValueError):
                    st.error("This file could not be read as text. Try UTF-8 text or another PDF.")
        else:
            saved_notes = db.get_notes_for_subject(active_subject["id"]) if active_subject else []
            if saved_notes:
                selected_note_id = st.selectbox(
                    "Saved note",
                    [note["id"] for note in saved_notes],
                    format_func=lambda note_id: next(
                        note["title"] for note in saved_notes if note["id"] == note_id
                    ),
                    key="assistant_reading_note_id",
                )
                reading_text = next(
                    note["content"] for note in saved_notes if note["id"] == selected_note_id
                )
            else:
                st.info("There are no saved notes for the active subject yet.")

        reading_action = st.selectbox(
            "What should the assistant do?",
            ["Explain clearly", "Summarize key ideas", "Extract key terms", "Create study questions"],
            key="assistant_reading_action",
        )
        if reading_text:
            st.caption(f"Loaded {len(reading_text):,} characters. The AI uses up to 24,000 characters per request.")
        if st.button("Analyze text", key="analyze_reading_text"):
            if not reading_text.strip():
                st.warning("Add or select some text first.")
            elif not api_key:
                st.warning("Add an API key above to generate an explanation. Your text stays in this app unless you submit it.")
                st.text_area("Text preview", reading_text[:3000], height=180, disabled=True)
            else:
                try:
                    with st.spinner("Reading and preparing your study guide..."):
                        response = generate_study_response(
                            api_key,
                            f"{reading_action}. Use headings and concrete examples where useful.",
                            reading_text,
                        )
                    st.markdown(response)
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))

    elif assistant_mode == "Search the web":
        search_query = st.text_input(
            "What do you want to research?",
            placeholder="Ask a question or enter a topic",
            key="assistant_web_query",
        )
        if st.button("Search online", key="assistant_web_search") and search_query.strip():
            with st.spinner("Searching for relevant pages..."):
                results = search_online_sources(search_query.strip())
            st.session_state.assistant_web_results = results
            st.session_state.assistant_web_summary = ""
            valid_results = results and results[0]["title"] != "Search Error"
            if valid_results and api_key:
                try:
                    with st.spinner("Synthesizing the sources..."):
                        st.session_state.assistant_web_summary = generate_study_response(
                            api_key,
                            "Answer the research question using only these search results. "
                            "Cite claims with the provided bracketed source numbers and mention uncertainty.",
                            format_search_context(results),
                        )
                except (RuntimeError, ValueError) as error:
                    st.session_state.assistant_web_summary = f"AI synthesis unavailable: {error}"

        web_results = st.session_state.get("assistant_web_results", [])
        if web_results:
            if web_results[0]["title"] == "Search Error":
                st.error(web_results[0]["snippet"])
            else:
                web_summary = st.session_state.get("assistant_web_summary", "")
                if web_summary:
                    st.markdown(web_summary)
                elif not api_key:
                    st.info("Search results are ready. Add an API key above to get an AI-generated synthesis.")
                st.subheader("Sources")
                render_source_links(web_results)

# ==============================================================================
# SECTION 3: LAPTOP FILE & NOTE UPLOAD
# ==============================================================================
elif nav_section == "📂 Laptop File & Note Upload":
    st.title("📂 Laptop Document & Note Upload Section")
    st.caption(f"Upload study files from your laptop for: **{selected_subj_name}**")

    uploaded_file = st.file_uploader("Select study document (.pdf, .txt, .md) from laptop", type=["pdf", "txt", "md"])
    if uploaded_file and active_subject:
        if st.button("Save File to Subject Database"):
            content = ""
            if uploaded_file.name.endswith(".pdf"):
                reader = PdfReader(uploaded_file)
                for page in reader.pages: content += page.extract_text() or ""
            else:
                content = uploaded_file.read().decode("utf-8")
            
            db.save_subject_note(active_subject["id"], uploaded_file.name, content)
            st.toast(f"File '{uploaded_file.name}' saved!")
            st.rerun()

    st.divider()
    st.subheader(f"Saved Files for {selected_subj_name}")
    notes = db.get_notes_for_subject(active_subject["id"]) if active_subject else []
    if notes:
        for n in notes:
            with st.expander(f"📄 {n['title']}"):
                st.write(n["content"][:1200] + ("..." if len(n["content"]) > 1200 else ""))
                render_tts_button(n["content"], label="🔊 Read Note Aloud")
    else:
        st.info("No documents uploaded for this subject yet.")

# ==============================================================================
# SECTION 4: AI QUESTION SETTING & QUIZ GENERATOR
# ==============================================================================
elif nav_section == "🎯 Quiz Generator & Practice":
    st.title("🎯 AI Question Generator & Practice Section")
    st.caption(
        f"Generate focused practice quizzes for **{selected_subj_name}**. "
        "Questions use your source material and the subject's key topics and equations."
    )

    question_count = st.slider(
        "Number of questions",
        min_value=1,
        max_value=15,
        value=10,
        key="quiz_question_count",
    )
    source_type = st.radio(
        "Source questions from:",
        ["Subject Topics & Key Equations", "Uploaded Laptop Notes", "Online Topic Query"],
        horizontal=True,
        key="quiz_source_type",
    )

    matched_subject = match_reference_subject(selected_subj_name)
    reference_subject = matched_subject
    if source_type == "Subject Topics & Key Equations" and reference_subject is None:
        reference_subject = st.selectbox(
            "Choose the subject reference guide",
            list(REFERENCE_SUBJECTS),
            index=None,
            placeholder="Select a subject",
            key="quiz_reference_subject",
        )

    reference_topics = get_reference_topics(reference_subject) if reference_subject else []
    focus_topic = None
    if source_type == "Subject Topics & Key Equations":
        topic_titles = ["Mixed key topics and equations"] + [
            title for title, _ in reference_topics
        ]
        focus_topic = st.selectbox(
            "Choose a topic to focus on",
            topic_titles,
            key="quiz_focus_topic",
        )
        if not reference_topics:
            st.warning("No reference topics are available for this subject.")

    if source_type == "Uploaded Laptop Notes":
        notes = db.get_notes_for_subject(active_subject["id"]) if active_subject else []
        if notes:
            note_titles = [n["title"] for n in notes]
            selected_note_title = st.selectbox("Select Note Source:", note_titles)
            selected_note = next(n for n in notes if n["title"] == selected_note_title)

            if st.button("⚡ Generate Quiz from Note") and active_subject:
                if not api_key:
                    st.error("Add your OpenAI API key in the sidebar to generate a quiz.")
                else:
                    note_context = (
                        f"Uploaded note: {selected_note_title}\n"
                        f"{selected_note['content'][:16000]}"
                    )
                    reference_context = format_reference_context(
                        matched_subject or selected_subj_name
                    )
                    context = "\n\n".join(
                        part for part in (note_context, reference_context) if part
                    )
                    try:
                        with st.spinner(f"Generating {question_count} questions..."):
                            quiz_questions = generate_quiz(
                                api_key,
                                selected_subj_name,
                                context,
                                question_count,
                                f"the uploaded note '{selected_note_title}' and key subject concepts",
                            )
                        db.save_quiz(
                            active_subject["id"],
                            f"Quiz: {selected_note_title} ({len(quiz_questions)} questions)",
                            json.dumps(quiz_questions),
                        )
                        st.toast("Quiz generated!")
                        st.rerun()
                    except (RuntimeError, ValueError) as error:
                        st.error(f"Could not generate the quiz: {error}")
        else:
            st.warning("Upload laptop notes in Section 3 first to generate note-based quizzes.")

    elif source_type == "Online Topic Query":
        topic_query = st.text_input("Enter Online Topic for Quiz Generation:", placeholder="e.g. Mitosis Phases or Organic Chemistry Reactions")
        if st.button("🔍 Search Web & Generate Quiz") and active_subject:
            if not topic_query.strip():
                st.warning("Enter a topic before generating a quiz.")
            elif not api_key:
                st.error("Add your OpenAI API key in the sidebar to generate a quiz.")
            else:
                web_data = search_online_sources(topic_query.strip())
                if not web_data:
                    st.warning("No search results were found. Try a different topic and search again.")
                elif web_data[0]["title"] == "Search Error":
                    st.error(f"Could not search for this topic: {web_data[0]['snippet']}")
                else:
                    web_context = format_search_context(web_data)
                    reference_context = format_reference_context(
                        matched_subject or selected_subj_name
                    )
                    context = "\n\n".join(
                        part for part in (web_context, reference_context) if part
                    )
                    try:
                        with st.spinner(f"Generating {question_count} questions..."):
                            quiz_questions = generate_quiz(
                                api_key,
                                selected_subj_name,
                                context,
                                question_count,
                                f"'{topic_query.strip()}' and key subject concepts",
                            )
                        db.save_quiz(
                            active_subject["id"],
                            f"Web Quiz: {topic_query.strip()} ({len(quiz_questions)} questions)",
                            json.dumps(quiz_questions),
                        )
                        st.toast("Web-sourced quiz generated!")
                        st.rerun()
                    except (RuntimeError, ValueError) as error:
                        st.error(f"Could not generate the quiz: {error}")

    elif source_type == "Subject Topics & Key Equations":
        if reference_topics and st.button("⚡ Generate Subject Quiz") and active_subject:
            if not api_key:
                st.error("Add your OpenAI API key in the sidebar to generate a quiz.")
            else:
                context = format_reference_context(reference_subject, focus_topic)
                quiz_title = (
                    f"{selected_subj_name}: {focus_topic} "
                    f"({question_count} questions)"
                )
                try:
                    with st.spinner(f"Generating {question_count} questions..."):
                        quiz_questions = generate_quiz(
                            api_key,
                            selected_subj_name,
                            context,
                            question_count,
                            focus_topic,
                        )
                    db.save_quiz(
                        active_subject["id"],
                        quiz_title,
                        json.dumps(quiz_questions),
                    )
                    st.toast("Subject quiz generated!")
                    st.rerun()
                except (RuntimeError, ValueError) as error:
                    st.error(f"Could not generate the quiz: {error}")

    # Display Practice Quizzes
    st.divider()
    st.subheader("📝 Practice Quizzes")
    quizzes = db.get_quizzes_for_subject(active_subject["id"]) if active_subject else []
    for q in quizzes:
        with st.expander(f"❓ {q['title']} (Created: {q['created_at'][:10]})"):
            q_data = json.loads(q["questions_json"])
            for idx, item in enumerate(q_data):
                st.write(f"**Q{idx+1}: {item['q']}**")
                user_ans = st.radio(f"Select Answer for Q{idx+1}:", item["options"], key=f"q_{q['id']}_{idx}")
                if st.button(f"Submit Q{idx+1}", key=f"sub_{q['id']}_{idx}"):
                    if user_ans == item["ans"]:
                        st.success("Correct!")
                    else:
                        st.error(f"Incorrect. Correct answer: {item['ans']}")
                    if item.get("explanation"):
                        st.caption(item["explanation"])
                render_tts_button(item["q"], label="🔊 Read Question Aloud")

# ==============================================================================
# SECTION 5: SPACED-REPETITION FLASHCARDS
# ==============================================================================
elif nav_section == "🧠 Flashcards":
    st.title("🧠 Flashcards")
    st.caption(
        f"Build a deck for **{selected_subj_name}** and review cards when they are due."
    )

    if not active_subject:
        st.info("Create or select a subject before adding flashcards.")
    else:
        flashcards = db.get_flashcards_for_subject(active_subject["id"])
        now = datetime.datetime.now()
        due_cards = [
            card
            for card in flashcards
            if datetime.datetime.fromisoformat(card["due_at"]) <= now
        ]
        reviewed_cards = sum(card["review_count"] > 0 for card in flashcards)
        metric_columns = st.columns(3)
        metric_columns[0].metric("Cards in deck", len(flashcards))
        metric_columns[1].metric("Due now", len(due_cards))
        metric_columns[2].metric("Reviewed", reviewed_cards)

        st.subheader("Create flashcards")
        creation_source = st.radio(
            "Create from",
            ["Saved note", "Paste text or AI answer"],
            horizontal=True,
            key="flashcard_creation_source",
        )
        source_text = ""
        source_label = ""

        if creation_source == "Saved note":
            saved_notes = db.get_notes_for_subject(active_subject["id"])
            if saved_notes:
                note_ids = [note["id"] for note in saved_notes]
                selected_note_id = st.selectbox(
                    "Choose a saved note",
                    note_ids,
                    format_func=lambda note_id: next(
                        note["title"] for note in saved_notes if note["id"] == note_id
                    ),
                    key="flashcard_note_id",
                )
                selected_note = next(
                    note for note in saved_notes if note["id"] == selected_note_id
                )
                source_text = selected_note["content"]
                source_label = f"Note: {selected_note['title']}"
            else:
                st.info("Upload a note in the Laptop File & Note Upload section first.")
        else:
            source_text = st.text_area(
                "Paste source text or an AI answer",
                height=180,
                key="flashcard_pasted_source",
                placeholder="Paste study material or an answer from the AI Study Assistant...",
            )
            source_label = "Pasted text"

        generated_card_count = st.slider(
            "Number of generated cards",
            min_value=2,
            max_value=20,
            value=8,
            key="flashcard_generation_count",
        )

        if st.button(
            "✨ Generate flashcards",
            key="generate_flashcards",
            disabled=not source_text.strip(),
        ):
            if not api_key:
                st.error("Add your OpenAI API key in the sidebar to generate flashcards.")
            else:
                try:
                    with st.spinner("Creating flashcards from your source..."):
                        cards_to_save = generate_flashcards(
                            api_key,
                            selected_subj_name,
                            source_text[:16000],
                            generated_card_count,
                        )
                    db.save_flashcards(
                        active_subject["id"],
                        source_label,
                        cards_to_save,
                    )
                    st.toast(f"Added {len(cards_to_save)} flashcards.")
                    st.rerun()
                except (RuntimeError, ValueError) as error:
                    st.error(f"Could not generate flashcards: {error}")

        with st.expander("Add a flashcard manually"):
            with st.form("manual_flashcard_form", clear_on_submit=True):
                manual_front = st.text_input("Front / question")
                manual_back = st.text_area("Back / answer")
                manual_submitted = st.form_submit_button("Add flashcard")
            if manual_submitted:
                if not manual_front.strip() or not manual_back.strip():
                    st.error("Enter both a question and an answer.")
                else:
                    db.save_flashcards(
                        active_subject["id"],
                        "Manual",
                        [{"front": manual_front.strip(), "back": manual_back.strip()}],
                    )
                    st.toast("Flashcard added to your deck.")
                    st.rerun()

        st.divider()
        st.subheader("Review due cards")
        if due_cards:
            current_card = due_cards[0]
            st.caption(f"Card 1 of {len(due_cards)} due")
            with st.container(border=True):
                st.markdown(f"### {current_card['front']}")
                if st.session_state.get("flashcard_revealed_id") == current_card["id"]:
                    st.divider()
                    st.markdown(current_card["back"])
                    st.caption(f"Source: {current_card['source']}")
                    st.caption(
                        "Again: 10 min · Hard: 1 day · Good: 3 days · Easy: 7 days"
                    )
                    rating_columns = st.columns(4)
                    for column, rating in zip(
                        rating_columns, ("Again", "Hard", "Good", "Easy")
                    ):
                        if column.button(
                            rating,
                            key=f"flashcard_rating_{current_card['id']}_{rating}",
                            width="stretch",
                        ):
                            db.review_flashcard(current_card["id"], rating)
                            st.session_state.flashcard_revealed_id = None
                            st.rerun()
                elif st.button(
                    "Show answer",
                    key=f"reveal_flashcard_{current_card['id']}",
                ):
                    st.session_state.flashcard_revealed_id = current_card["id"]
                    st.rerun()
        else:
            st.success("You’re all caught up! Come back when your cards are due.")

        if flashcards:
            with st.expander(f"View all {len(flashcards)} cards"):
                for card in flashcards:
                    with st.container(border=True):
                        st.markdown(f"**Q:** {card['front']}")
                        st.markdown(f"**A:** {card['back']}")
                        due_at = datetime.datetime.fromisoformat(card["due_at"])
                        due_label = (
                            "Due now"
                            if due_at <= now
                            else f"Due {due_at.strftime('%b %d, %I:%M %p')}"
                        )
                        st.caption(
                            f"{card['source']} · {due_label} · "
                            f"{card['review_count']} reviews"
                        )
                        if st.button(
                            "Delete card",
                            key=f"delete_flashcard_{card['id']}",
                        ):
                            db.delete_flashcard(card["id"])
                            if st.session_state.get("flashcard_revealed_id") == card["id"]:
                                st.session_state.flashcard_revealed_id = None
                            st.rerun()

# ==============================================================================
# SECTION 6: CITATION & WEB SEARCH HUB
# ==============================================================================
elif nav_section == "🌐 Web Search & Citation Hub":
    st.title("🌐 Online Web Sourcing & Citation Generator")
    st.caption("Search online academic solutions and format MLA, APA, or Chicago citations.")

    search_q = st.text_input("Enter research topic or question:", placeholder="e.g. Thermodynamics Laws")
    cite_style = st.selectbox("Select Citation Style:", ["MLA", "APA", "Chicago"])

    if st.button("🔍 Search & Format Citation") and search_q:
        results = search_online_sources(search_q)
        for res in results:
            st.markdown('<div class="card-box">', unsafe_allow_html=True)
            st.subheader(res["title"])
            st.write(res["snippet"])
            st.markdown(f"**Source:** [{res['link']}]({res['link']})")
            
            citation = generate_citation(res["title"], res["link"], style=cite_style)
            st.code(citation, language="markdown")
            render_tts_button(f"{res['title']}. {res['snippet']}", label="🔊 Read Aloud")
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 7: QUICK KNOWLEDGE LIBRARY
# ==============================================================================
elif nav_section == "📖 Quick Knowledge Library":
    st.title("📖 Quick Reference Knowledge Library")
    st.caption("Browse formulas and major topics across 10 subjects. Each subject includes at least 20 quick references.")

    wiki_category = st.selectbox(
        "Select subject",
        list(QUICK_REFERENCE_SUBJECTS),
        key="quick_reference_subject",
    )
    references = QUICK_REFERENCE_SUBJECTS[wiki_category]
    st.caption(f"{len(references)} formulas and major topics · {wiki_category}")
    reference_columns = st.columns(2)
    for index, (title, description) in enumerate(references, start=1):
        with reference_columns[(index - 1) % 2]:
            with st.container(border=True):
                st.markdown(f"**{index}. {title}**")
                st.write(description)

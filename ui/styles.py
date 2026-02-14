# -*- coding: utf-8 -*-
"""
Shared CSS styles for all Streamlit UI components.

Usage:
    from ui.styles import inject_custom_css
    inject_custom_css()
"""
import streamlit as st


def inject_custom_css() -> None:
    """Inject custom CSS styles into the Streamlit app."""
    st.markdown(
        """
        <style>
        /* ===== a) Basic Layout ===== */
        .block-container {
            padding-top: 1rem;
            max-width: 900px;
        }

        /* ===== b) Result Cards ===== */
        .result-card {
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        .result-card-capital {
            background: #ECFDF5;
            border-left: 5px solid #10B981;
        }
        .result-card-expense {
            background: #EFF6FF;
            border-left: 5px solid #3B82F6;
        }
        .result-card-guidance {
            background: #FEF3C7;
            border-left: 5px solid #F59E0B;
        }

        /* ===== c) Confidence Bar ===== */
        .confidence-bar {
            height: 8px;
            border-radius: 4px;
        }
        .confidence-high {
            background: #10B981;
        }
        .confidence-mid {
            background: #F59E0B;
        }
        .confidence-low {
            background: #EF4444;
        }

        /* ===== d) Button Enhancement ===== */
        .guidance-btn {
            min-height: 120px;
            border-radius: 12px;
            font-size: 1.1rem;
        }

        /* ===== e) Animation ===== */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        /* ===== f) Progress Step Indicator ===== */
        .step-indicator {
            display: flex;
            justify-content: center;
            gap: 2rem;
        }
        .step-active {
            color: #3B82F6;
            font-weight: bold;
        }
        .step-done {
            color: #10B981;
        }
        .step-pending {
            color: #9CA3AF;
        }

        /* ===== g) Gemini Badge ===== */
        .gemini-badge {
            background: linear-gradient(135deg, #4285F4, #EA4335);
            color: white;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
        }

        /* ===== h) Hero Section ===== */
        .hero {
            text-align: center;
            padding: 2rem 0 1rem;
        }
        .hero h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        /* ===== i) Skeleton Loading ===== */
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
        }

        /* ===== j) Disclaimer ===== */
        .disclaimer {
            font-size: 0.7rem;
            color: #4B5563;
            text-align: center;
        }

        /* ===== k) Streamlit Default Overrides ===== */
        [data-testid="stFileUploader"] section {
            border: 2px dashed #3B82F6;
            border-radius: 12px;
            padding: 2rem;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        /* ===== l) Guidance Choice Cards ===== */
        .guidance-choice {
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .guidance-choice:hover {
            border-color: #3B82F6;
            background: #F0F7FF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

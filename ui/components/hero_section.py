# -*- coding: utf-8 -*-
"""Hero section component for the fixed-asset judgment app."""
import streamlit as st


def _has_result() -> bool:
    """Check if a judgment result exists in session state."""
    return (
        "result" in st.session_state
        and st.session_state.result is not None
    )


def render_hero() -> None:
    """Render the hero section at the top of the app."""
    compact = _has_result()

    if compact:
        # Compact: title + badge in one line
        st.markdown(
            """
            <div class="hero" style="text-align:center;padding:0.5rem 0;">
                <h1 style="display:inline;font-size:1.4rem;margin:0;">固定資産判定 AI</h1>
                <span class="gemini-badge" style="margin-left:0.75rem;">Powered by Gemini 3 Pro</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Full hero
    # Determine active step
    step = 1  # default: upload active
    if _has_result():
        step = 3

    steps = [
        ("📤", "アップロード", 1),
        ("🤖", "AI判定", 2),
        ("✅", "結果確認", 3),
    ]

    step_html_parts = []
    for icon, label, num in steps:
        if num < step:
            css_class = "step-done"
        elif num == step:
            css_class = "step-active"
        else:
            css_class = "step-pending"
        step_html_parts.append(
            f'<span class="step-indicator {css_class}">{icon} {label}</span>'
        )

    arrow = '<span style="margin:0 0.5rem;color:#9CA3AF;font-size:1.2rem;">→</span>'
    steps_html = arrow.join(step_html_parts)

    st.markdown(
        f"""
        <div class="hero" style="text-align:center;padding:1.5rem 0 1rem;">
            <h1 style="font-size:2.2rem;margin:0 0 0.3rem;">固定資産判定 AI</h1>
            <p style="color:#6B7280;font-size:1.05rem;margin:0 0 0.6rem;">
                見積書をアップするだけ。資産か経費か、AIが判定します。
            </p>
            <span class="gemini-badge">Powered by Gemini 3 Pro</span>
            <div style="margin-top:1rem;display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:0.25rem;">
                {steps_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

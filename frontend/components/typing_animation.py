"""
Typing Animation Component for Streamlit

Provides a typing animation effect for displaying answers character-by-character,
making the UI feel more interactive and real-time.
"""

import streamlit as st
import time
from typing import Optional


def stream_text(
    text: str,
    container: Optional[st.delta_generator.DeltaGenerator] = None,
    typing_speed: float = 0.01,
    unsafe_allow_html: bool = True
) -> None:
    """
    Display text with typing animation effect

    Args:
        text: The text to display with typing animation
        container: Optional Streamlit container (st.empty()). If None, creates one.
        typing_speed: Delay in seconds between each character (default: 0.01 = 10ms)
        unsafe_allow_html: Whether to allow HTML in markdown rendering

    Example:
        >>> import streamlit as st
        >>> from frontend.components.typing_animation import stream_text
        >>>
        >>> answer = "The IRR for this project is 18.5%"
        >>> stream_text(answer)
    """
    if container is None:
        container = st.empty()

    displayed_text = ""

    # Handle HTML content specially - don't animate character-by-character
    # if it has complex HTML tags (tables, hyperlinks, etc)
    if unsafe_allow_html and ("<table" in text or "<tr" in text or "<a" in text or len(text) > 5000):
        # For complex HTML or very long text, display all at once
        container.markdown(text, unsafe_allow_html=True)
        return

    # Typing animation for regular text/simple HTML
    for char in text:
        displayed_text += char
        container.markdown(displayed_text, unsafe_allow_html=unsafe_allow_html)
        time.sleep(typing_speed)


def stream_text_by_words(
    text: str,
    container: Optional[st.delta_generator.DeltaGenerator] = None,
    words_per_update: int = 3,
    delay_between_updates: float = 0.05,
    unsafe_allow_html: bool = True
) -> None:
    """
    Display text with word-by-word animation (faster than character-by-character)

    This is more efficient for long answers and looks more natural.

    Args:
        text: The text to display
        container: Optional Streamlit container. If None, creates one.
        words_per_update: Number of words to add per update (default: 3)
        delay_between_updates: Delay in seconds between updates (default: 0.05 = 50ms)
        unsafe_allow_html: Whether to allow HTML in markdown rendering

    Example:
        >>> stream_text_by_words(
        ...     "The average selling price is ₹4,200 per square foot",
        ...     words_per_update=2,
        ...     delay_between_updates=0.1
        ... )
    """
    if container is None:
        container = st.empty()

    # Handle complex HTML - don't animate
    if unsafe_allow_html and ("<table" in text or "<tr" in text or "<a" in text or len(text) > 5000):
        container.markdown(text, unsafe_allow_html=True)
        return

    # FIXED: Split text into words while preserving newlines and whitespace
    # Use regex to split on whitespace but keep the whitespace as separate tokens
    import re
    tokens = re.split(r'(\s+)', text)  # Split on whitespace but keep it in results

    # Remove empty strings
    tokens = [t for t in tokens if t]

    displayed_tokens = []

    for i in range(0, len(tokens), words_per_update):
        # Add next batch of tokens (includes words and whitespace)
        batch = tokens[i:i + words_per_update]
        displayed_tokens.extend(batch)

        # Join WITHOUT adding spaces (tokens already have whitespace preserved)
        displayed_text = "".join(displayed_tokens)
        container.markdown(displayed_text, unsafe_allow_html=unsafe_allow_html)

        # Small delay between batches
        if i + words_per_update < len(tokens):  # Don't delay after last batch
            time.sleep(delay_between_updates)


def stream_with_spinner(
    text: str,
    container: Optional[st.delta_generator.DeltaGenerator] = None,
    show_thinking: bool = True,
    thinking_duration: float = 0.5,
    typing_speed: float = 0.01,
    unsafe_allow_html: bool = True
) -> None:
    """
    Display text with typing animation, optionally showing a "thinking" spinner first

    Args:
        text: The text to display
        container: Optional Streamlit container
        show_thinking: Whether to show a brief "thinking" animation first
        thinking_duration: How long to show thinking spinner (seconds)
        typing_speed: Typing speed for character-by-character animation
        unsafe_allow_html: Whether to allow HTML in markdown

    Example:
        >>> stream_with_spinner(
        ...     "Here's your answer...",
        ...     show_thinking=True,
        ...     thinking_duration=1.0
        ... )
    """
    if container is None:
        container = st.empty()

    # Show thinking animation
    if show_thinking:
        with container:
            st.markdown("🤔 _Analyzing..._")
        time.sleep(thinking_duration)

    # Clear and start typing animation
    stream_text(text, container, typing_speed, unsafe_allow_html)


class StreamingDisplay:
    """
    Reusable streaming display component with multiple animation modes

    Usage:
        >>> display = StreamingDisplay(mode="words")
        >>> display.show(answer_text)
    """

    def __init__(
        self,
        mode: str = "words",  # "chars", "words", "instant"
        typing_speed: float = 0.01,
        words_per_update: int = 3,
        show_thinking: bool = False
    ):
        """
        Initialize streaming display

        Args:
            mode: Animation mode - "chars" (character-by-character),
                  "words" (word-by-word), or "instant" (no animation)
            typing_speed: Speed for character mode (seconds per character)
            words_per_update: Words per batch for word mode
            show_thinking: Whether to show thinking spinner before display
        """
        self.mode = mode
        self.typing_speed = typing_speed
        self.words_per_update = words_per_update
        self.show_thinking = show_thinking

    def show(
        self,
        text: str,
        container: Optional[st.delta_generator.DeltaGenerator] = None,
        unsafe_allow_html: bool = True
    ) -> None:
        """
        Display text using configured animation mode

        Args:
            text: Text to display
            container: Optional Streamlit container
            unsafe_allow_html: Whether to allow HTML in markdown
        """
        if container is None:
            container = st.empty()

        # Show thinking animation if enabled
        if self.show_thinking:
            with container:
                st.markdown("🤔 _Composing answer..._")
            time.sleep(0.5)

        # Display based on mode
        if self.mode == "instant":
            container.markdown(text, unsafe_allow_html=unsafe_allow_html)
        elif self.mode == "chars":
            stream_text(text, container, self.typing_speed, unsafe_allow_html)
        elif self.mode == "words":
            stream_text_by_words(
                text,
                container,
                self.words_per_update,
                delay_between_updates=0.05,
                unsafe_allow_html=unsafe_allow_html
            )
        else:
            # Fallback to instant
            container.markdown(text, unsafe_allow_html=unsafe_allow_html)


# Convenience function for quick integration
def display_with_typing(
    text: str,
    mode: str = "words",
    unsafe_allow_html: bool = True
) -> None:
    """
    Quick helper to display text with typing animation

    Args:
        text: Text to display
        mode: "chars", "words", or "instant"
        unsafe_allow_html: Whether to allow HTML

    Example:
        >>> from frontend.components.typing_animation import display_with_typing
        >>> display_with_typing(answer, mode="words")
    """
    display = StreamingDisplay(mode=mode)
    display.show(text, unsafe_allow_html=unsafe_allow_html)

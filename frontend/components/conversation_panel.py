"""
Conversation History Panel for Streamlit

Provides UI components for displaying and managing conversation history
with context preservation across multiple queries.
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


class ConversationPanel:
    """
    Panel for displaying conversation history and context
    """

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize conversation panel

        Args:
            api_base_url: Base URL for API calls
        """
        self.api_base_url = api_base_url

        # Initialize session state
        if "conversation_session_id" not in st.session_state:
            st.session_state.conversation_session_id = None
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = {}

    def render_sidebar(self) -> None:
        """
        Render conversation panel in sidebar
        """
        with st.sidebar:
            st.header("💬 Conversation History")

            # Session management
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🆕 New Session", use_container_width=True):
                    self.create_new_session()
            with col2:
                if st.button("🗑️ Clear", use_container_width=True):
                    self.clear_conversation()

            # Display session info
            if st.session_state.conversation_session_id:
                st.caption(f"Session: {st.session_state.conversation_session_id[:8]}...")

                # Display context
                if st.session_state.conversation_context:
                    with st.expander("📊 Context", expanded=False):
                        self.render_context()

                # Display history
                if st.session_state.conversation_history:
                    st.divider()
                    self.render_history()

                # Suggested queries
                self.render_suggestions()

    def render_main_panel(self) -> None:
        """
        Render conversation panel in main area
        """
        st.header("💬 Conversation History")

        # Session controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🆕 New Conversation"):
                self.create_new_session()
        with col2:
            if st.button("💾 Save Conversation"):
                self.save_conversation()
        with col3:
            if st.button("📥 Load Previous"):
                self.show_session_list()

        # Current session display
        if st.session_state.conversation_session_id:
            # Context summary
            with st.container():
                st.subheader("Context Summary")
                self.render_context_detailed()

            # Conversation flow
            st.subheader("Conversation Flow")
            self.render_conversation_flow()

    def create_new_session(self) -> None:
        """Create a new conversation session"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/conversation/create",
                json={
                    "user_id": st.session_state.get("user_id"),
                    "title": f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "tags": ["streamlit", "interactive"],
                    "max_context_window": 10
                }
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.conversation_session_id = data["session_id"]
                st.session_state.conversation_history = []
                st.session_state.conversation_context = {}
                st.success("New conversation started!")
            else:
                st.error(f"Failed to create session: {response.text}")

        except Exception as e:
            st.error(f"Error creating session: {e}")

    def send_message(self, content: str, context_override: Optional[Dict] = None) -> Dict:
        """
        Send a message and get response

        Args:
            content: Message content
            context_override: Optional context override

        Returns:
            Response data
        """
        if not st.session_state.conversation_session_id:
            self.create_new_session()

        try:
            response = requests.post(
                f"{self.api_base_url}/api/conversation/message",
                json={
                    "session_id": st.session_state.conversation_session_id,
                    "content": content,
                    "context_override": context_override
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Update history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": data["assistant_response"],
                    "timestamp": datetime.now().isoformat(),
                    "result": data.get("result")
                })

                # Update context
                st.session_state.conversation_context = data.get("context_summary", {})

                return data
            else:
                st.error(f"Failed to send message: {response.text}")
                return {}

        except Exception as e:
            st.error(f"Error sending message: {e}")
            return {}

    def get_context(self) -> Dict:
        """Get current conversation context"""
        if not st.session_state.conversation_session_id:
            return {}

        try:
            response = requests.get(
                f"{self.api_base_url}/api/conversation/context/{st.session_state.conversation_session_id}",
                params={
                    "include_full_history": False,
                    "include_memory": True,
                    "max_messages": 10
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception:
            return {}

    def render_history(self) -> None:
        """Render conversation history"""
        for i, msg in enumerate(st.session_state.conversation_history[-10:]):  # Last 10 messages
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                with st.chat_message("user"):
                    st.write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
                    if msg.get("result"):
                        with st.expander("📊 Details", expanded=False):
                            st.json(msg["result"])

    def render_conversation_flow(self) -> None:
        """Render detailed conversation flow"""
        for i, msg in enumerate(st.session_state.conversation_history):
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")

            col1, col2 = st.columns([1, 4])
            with col1:
                st.caption(f"{role.title()}")
                if timestamp:
                    st.caption(timestamp[:10])
            with col2:
                if role == "user":
                    st.info(content)
                else:
                    st.success(content)
                    if msg.get("result"):
                        result = msg["result"]
                        if isinstance(result, dict):
                            if "value" in result:
                                st.metric(
                                    label=result.get("metric", "Result"),
                                    value=f"{result['value']} {result.get('unit', '')}"
                                )
                            else:
                                st.json(result)

    def render_context(self) -> None:
        """Render context summary"""
        ctx = st.session_state.conversation_context

        if "current_project" in ctx and ctx["current_project"]:
            st.write(f"📁 Project: **{ctx['current_project']}**")
        if "current_location" in ctx and ctx["current_location"]:
            st.write(f"📍 Location: **{ctx['current_location']}**")
        if "turn_count" in ctx:
            st.write(f"🔄 Turns: **{ctx['turn_count']}**")

        # Recent metrics
        if "recent_metrics" in ctx and ctx["recent_metrics"]:
            st.write("📊 Recent Metrics:")
            for metric, data in ctx["recent_metrics"].items():
                st.caption(f"• {metric}: {data.get('value')} {data.get('unit', '')}")

    def render_context_detailed(self) -> None:
        """Render detailed context information"""
        ctx = st.session_state.conversation_context

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Current Project", ctx.get("current_project", "None"))
            if "established_facts" in ctx:
                facts = ctx["established_facts"]
                if facts:
                    st.write("**Established Facts:**")
                    for key, value in facts.items():
                        st.caption(f"• {key}: {value}")

        with col2:
            st.metric("Current Location", ctx.get("current_location", "None"))
            if "mentioned_entities" in ctx:
                entities = ctx["mentioned_entities"]
                if entities.get("locations"):
                    st.write("**Mentioned Locations:**")
                    for loc in entities["locations"]:
                        st.caption(f"• {loc}")

        with col3:
            st.metric("Turn Count", ctx.get("turn_count", 0))
            if "mentioned_entities" in ctx:
                entities = ctx["mentioned_entities"]
                if entities.get("metrics"):
                    st.write("**Discussed Metrics:**")
                    for metric in entities["metrics"]:
                        st.caption(f"• {metric}")

    def render_suggestions(self) -> None:
        """Render suggested queries"""
        context_data = self.get_context()
        suggestions = context_data.get("suggested_next_queries", [])

        if suggestions:
            st.divider()
            st.caption("💡 Suggested Queries:")
            for suggestion in suggestions[:3]:
                if st.button(f"→ {suggestion}", key=f"sugg_{suggestion[:20]}"):
                    # This would trigger the query
                    st.session_state.pending_query = suggestion

    def clear_conversation(self) -> None:
        """Clear current conversation"""
        st.session_state.conversation_history = []
        st.session_state.conversation_context = {}
        st.success("Conversation cleared!")

    def save_conversation(self) -> None:
        """Save current conversation"""
        if st.session_state.conversation_session_id:
            # The conversation is already auto-saved on the backend
            st.success(f"Conversation saved (ID: {st.session_state.conversation_session_id[:8]}...)")

    def show_session_list(self) -> None:
        """Show list of available sessions"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/conversation/sessions",
                params={"limit": 10}
            )

            if response.status_code == 200:
                sessions = response.json()

                if sessions:
                    st.subheader("Previous Sessions")
                    for session in sessions:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"**{session.get('title', 'Untitled')}**")
                            if session.get("summary"):
                                st.caption(session["summary"])
                        with col2:
                            st.caption(f"Turns: {session.get('turn_count', 0)}")
                            st.caption(session.get("updated_at", "")[:10])
                        with col3:
                            if st.button("Load", key=f"load_{session['session_id']}"):
                                self.load_session(session["session_id"])
                else:
                    st.info("No previous sessions found")

        except Exception as e:
            st.error(f"Error loading sessions: {e}")

    def load_session(self, session_id: str) -> None:
        """Load a specific session"""
        try:
            context_data = self.get_context()
            if context_data:
                st.session_state.conversation_session_id = session_id
                st.session_state.conversation_context = context_data.get("context_summary", {})

                # Load recent messages
                messages = context_data.get("recent_messages", [])
                st.session_state.conversation_history = [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg.get("timestamp"),
                        "result": {
                            "value": msg.get("result_value"),
                            "unit": msg.get("result_unit")
                        } if msg.get("result_value") else None
                    }
                    for msg in messages
                ]

                st.success("Session loaded!")
                st.rerun()

        except Exception as e:
            st.error(f"Error loading session: {e}")


def render_conversation_interface():
    """
    Render the complete conversation interface

    This can be used in the main Streamlit app
    """
    panel = ConversationPanel()

    # Check if there's a pending query from suggestions
    if "pending_query" in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query
        return query

    return None
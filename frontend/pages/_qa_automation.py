"""
QA Automation - Auto-Healing Testing UI

Streamlit interface for controlling the test-debug-fix-regression cycle
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.testing.test_service import AutoHealingTestService
from app.testing.test_models import TestStatus
from app.testing.report_generator import HTMLReportGenerator
from app.testing.claude_code_connector import claude_code_connector
from app.testing.fix_applier import fix_applier

# Page config
st.set_page_config(
    page_title="QA Automation",
    page_icon="🤖",
    layout="wide"
)

# PRODUCTION GUARD: Block access if not in development/testing mode
ENABLE_QA_AUTOMATION = os.getenv("ENABLE_QA_AUTOMATION", "false").lower() == "true"

if not ENABLE_QA_AUTOMATION:
    st.error("🚫 QA Automation is not available in production mode")
    st.info("This feature is only accessible in development/testing environments.")
    st.markdown("---")
    st.markdown("Set `ENABLE_QA_AUTOMATION=true` in your `.env` file to enable this feature.")

    if st.button("← Return to ATLAS", key="return_to_atlas"):
        st.switch_page("streamlit_app.py")

    st.stop()  # Halt execution

# CODE VERSION - increment this to force session state reset after code changes
CODE_VERSION = 4  # Incremented: ID fix + thread safety improvements

# Initialize session state
if 'code_version' not in st.session_state or st.session_state.code_version != CODE_VERSION:
    # Clear everything on version mismatch
    st.session_state.clear()
    st.session_state.code_version = CODE_VERSION
    st.session_state.service = None
    st.session_state.current_run = None
    st.session_state.run_history = []
    st.session_state.duration_history = []
    st.session_state.excel_path = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases.xlsx"

if 'service' not in st.session_state:
    st.session_state.service = None
if 'current_run' not in st.session_state:
    st.session_state.current_run = None
if 'run_history' not in st.session_state:
    st.session_state.run_history = []
if 'excel_path' not in st.session_state:
    st.session_state.excel_path = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases.xlsx"
if 'duration_history' not in st.session_state:
    st.session_state.duration_history = []  # Track historic test run durations

# Header with back button
col_back, col_title = st.columns([1, 9])

with col_back:
    if st.button("← ATLAS", key="back_to_atlas", help="Back to ATLAS main page"):
        st.switch_page("streamlit_app.py")

with col_title:
    st.title("🤖 QA Automation - Auto-Healing Testing System")
    st.markdown("**Automated test-debug-fix-regression cycle for BDD test cases**")

st.divider()

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Excel file path
    excel_path = st.text_input(
        "Excel File Path",
        value=st.session_state.excel_path,
        help="Path to BDD_Test_Cases.xlsx"
    )
    st.session_state.excel_path = excel_path

    # Initialize service button
    if st.button("🔄 Initialize Service", use_container_width=True):
        try:
            # Create new service instance
            st.session_state.service = AutoHealingTestService(excel_path)
            test_cases = st.session_state.service.load_test_cases()
            st.success(f"✓ Loaded {len(test_cases)} test cases")
            st.info(f"Code version: {CODE_VERSION}")
        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

    st.divider()

    # Service status
    if st.session_state.service:
        st.success("🟢 Service Ready")
        if st.session_state.service.test_cases:
            st.metric("Test Cases Loaded", len(st.session_state.service.test_cases))
        st.caption(f"Code Version: {CODE_VERSION}")
    else:
        st.warning("🟡 Service Not Initialized")
        st.info("👆 Click 'Initialize Service' above to load test cases")

    # Emergency reset button
    if st.button("🔴 Emergency Reset (Clear All State)", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.success("✅ All state cleared! Page will reload...")
        st.rerun()

    st.divider()

    # Run history
    st.header("📊 Run History")
    if st.session_state.run_history:
        for run_id in reversed(st.session_state.run_history[-5:]):  # Last 5
            st.text(f"• {run_id}")
    else:
        st.text("No runs yet")

# Main content
if not st.session_state.service:
    st.info("👈 Initialize the service using the sidebar to get started")
    st.stop()

# Tab layout
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Control Panel", "📊 Dashboard", "📋 Test Details", "📧 HTML Report", "🔧 Settings"])

# ============================================================================
# TAB 1: CONTROL PANEL
# ============================================================================
with tab1:
    st.header("Control Panel")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Phase 1: Initial Test Run")
        st.markdown("Execute all test cases and validate results")

        run_id_initial = st.text_input("Run ID", value="initial", key="run_id_initial")
        auto_heal_initial = st.checkbox("Auto-heal failures", value=True, key="auto_heal_initial")
        use_parallel_initial = st.checkbox("Parallel execution (batches)", value=False, key="parallel_initial",
                                          help="Execute tests in parallel batches with rate limiting. Default: OFF (sequential is more stable in Streamlit)")

        if st.button("▶️ Start Initial Test Run", type="primary", use_container_width=True):
            # Calculate estimated duration from history
            avg_duration = None
            if st.session_state.duration_history:
                avg_duration = sum(st.session_state.duration_history) / len(st.session_state.duration_history)
                est_time_str = f"~{avg_duration/60:.1f} min"
            else:
                # Default estimates
                if use_parallel_initial:
                    est_time_str = "~3-5 min"
                else:
                    est_time_str = "~10-15 min"

            with st.spinner(f"Running tests... Estimated time: {est_time_str}"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_text = st.empty()

                try:
                    import time
                    start_time = time.time()

                    # Run test cycle
                    test_run = st.session_state.service.run_test_cycle(
                        run_id=run_id_initial,
                        auto_heal=auto_heal_initial,
                        use_parallel=use_parallel_initial
                    )

                    # Calculate actual duration
                    actual_duration = time.time() - start_time

                    # Update progress
                    progress_bar.progress(100)
                    status_text.success("✓ Test run complete!")
                    time_text.success(f"⏱️ Completed in {actual_duration/60:.1f} minutes")

                    # Store in session state and history
                    st.session_state.current_run = test_run
                    st.session_state.run_history.append(run_id_initial)
                    st.session_state.duration_history.append(actual_duration)

                    # Keep only last 10 durations for averaging
                    if len(st.session_state.duration_history) > 10:
                        st.session_state.duration_history = st.session_state.duration_history[-10:]

                    # Show summary
                    st.success(f"""
                    ### Results Summary
                    - **Total Tests**: {test_run.summary.total_tests}
                    - **Passed**: {test_run.summary.passed} ({test_run.summary.pass_rate:.1f}%)
                    - **Failed**: {test_run.summary.failed}
                    - **Auto-fixed**: {test_run.summary.auto_fixed_count}
                    - **Duration**: {actual_duration/60:.1f} min ({actual_duration:.1f}s)
                    """)

                except Exception as e:
                    error_msg = str(e)
                    if "ValidationError" in str(type(e)) or "model_type" in error_msg:
                        st.error("❌ Stale session detected - code was updated but session not refreshed")
                        st.warning("🔄 **Fix:** Click the '🔴 Emergency Reset' button in the sidebar, then click 'Initialize Service' again")
                        st.info("This happens when code is updated while the app is running. A fresh reload fixes it.")
                    else:
                        st.error(f"Error during test run: {e}")
                    import traceback
                    with st.expander("📋 Full Error Details"):
                        st.code(traceback.format_exc())

    with col2:
        st.subheader("🔄 Phase 2: Regression Test")
        st.markdown("Re-test after auto-healing to validate fixes")

        run_id_regression = st.text_input("Run ID", value="regression_1", key="run_id_regression")
        previous_run_id = st.selectbox(
            "Compare to",
            options=st.session_state.run_history if st.session_state.run_history else ["initial"],
            key="previous_run_id"
        )
        use_parallel_regression = st.checkbox("Parallel execution (batches)", value=False, key="parallel_regression",
                                              help="Default: OFF (sequential is more stable in Streamlit)")

        if st.button("▶️ Start Regression Test", type="secondary", use_container_width=True):
            # Calculate estimated duration from history
            if st.session_state.duration_history:
                avg_duration = sum(st.session_state.duration_history) / len(st.session_state.duration_history)
                est_time_str = f"~{avg_duration/60:.1f} min"
            else:
                # Default estimates
                if use_parallel_regression:
                    est_time_str = "~3-5 min"
                else:
                    est_time_str = "~10-15 min"

            with st.spinner(f"Running regression tests... Estimated time: {est_time_str}"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_text = st.empty()

                try:
                    import time
                    start_time = time.time()

                    # Run regression
                    regression_run = st.session_state.service.run_regression(
                        run_id=run_id_regression,
                        previous_run_id=previous_run_id,
                        use_parallel=use_parallel_regression
                    )

                    # Calculate actual duration
                    actual_duration = time.time() - start_time

                    progress_bar.progress(100)
                    status_text.success("✓ Regression complete!")
                    time_text.success(f"⏱️ Completed in {actual_duration/60:.1f} minutes")

                    # Store in session state and history
                    st.session_state.current_run = regression_run
                    st.session_state.run_history.append(run_id_regression)
                    st.session_state.duration_history.append(actual_duration)

                    # Keep only last 10 durations for averaging
                    if len(st.session_state.duration_history) > 10:
                        st.session_state.duration_history = st.session_state.duration_history[-10:]

                    # Show comparison
                    prev_run = st.session_state.service.runs.get(previous_run_id)
                    if prev_run:
                        delta_pass_rate = regression_run.summary.pass_rate - prev_run.summary.pass_rate

                        st.success(f"""
                        ### Regression Summary
                        - **Pass Rate**: {regression_run.summary.pass_rate:.1f}% (Δ {delta_pass_rate:+.1f}%)
                        - **Improved**: {len(regression_run.improved_tests)} tests
                        - **Regressed**: {len(regression_run.regressed_tests)} tests
                        - **Duration**: {actual_duration/60:.1f} min ({actual_duration:.1f}s)
                        """)

                except Exception as e:
                    error_msg = str(e)
                    if "ValidationError" in str(type(e)) or "model_type" in error_msg:
                        st.error("❌ Stale session detected - code was updated but session not refreshed")
                        st.warning("🔄 **Fix:** Click the '🔴 Emergency Reset' button in the sidebar, then click 'Initialize Service' again")
                        st.info("This happens when code is updated while the app is running. A fresh reload fixes it.")
                    else:
                        st.error(f"Error during regression: {e}")
                    import traceback
                    with st.expander("📋 Full Error Details"):
                        st.code(traceback.format_exc())

    st.divider()

    # AI-Developer Integration
    st.subheader("🤖 AI-Developer Auto-Fix")
    st.markdown("**Invoke Claude Code to intelligently debug and fix test failures**")

    if st.session_state.current_run and st.session_state.current_run.summary.failed > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"💡 {st.session_state.current_run.summary.failed} failed tests can be analyzed by Claude Code")

            if st.button("🧠 Create Debug Session for Claude Code", use_container_width=True, type="primary"):
                try:
                    session_file = claude_code_connector.create_debug_session(
                        st.session_state.current_run,
                        session_name=None  # Auto-generate name
                    )

                    st.success(f"✅ Debug session created successfully!")
                    st.code(f"Session files:\n  - {session_file}\n  - {session_file.with_suffix('.md')}", language=None)

                    st.markdown("""
                    ### Next Steps:

                    1. **Open your terminal** where Claude Code is running
                    2. **Run the command:**
                       ```
                       /fix-qa-tests
                       ```
                    3. **Claude Code will:**
                       - Analyze all test failures
                       - Generate intelligent fixes
                       - Write fixes to the debug session file

                    4. **Return here and click** "Apply Claude Code Fixes" button →
                    """)

                    # Store session file path in session state
                    st.session_state.latest_debug_session = str(session_file.stem)

                except Exception as e:
                    st.error(f"Error creating debug session: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        with col2:
            # Check for completed debug sessions
            pending_sessions = claude_code_connector.get_pending_sessions()

            if 'latest_debug_session' in st.session_state or pending_sessions:
                st.warning("⏳ Debug session ready for Claude Code review")

                # Allow user to manually specify session name
                session_to_apply = st.text_input(
                    "Debug Session Name",
                    value=st.session_state.get('latest_debug_session', pending_sessions[0] if pending_sessions else ""),
                    help="The debug session to apply fixes from"
                )

                if st.button("📥 Apply Claude Code Fixes", use_container_width=True):
                    try:
                        # Load the debug session
                        session_data = claude_code_connector.load_debug_session(session_to_apply)

                        if session_data.get("status") != "completed":
                            st.warning(f"⚠️ Debug session status: {session_data.get('status')}")
                            st.info("Run `/fix-qa-tests` in Claude Code terminal first")
                        elif not session_data.get("fixes"):
                            st.warning("No fixes found in debug session")
                        else:
                            # Apply fixes
                            fixes = session_data["fixes"]
                            st.success(f"Found {len(fixes)} fixes from Claude Code!")

                            # Show fixes preview
                            with st.expander("Preview Fixes"):
                                for fix in fixes:
                                    st.markdown(f"""
                                    **Test #{fix['test_id']}** - {fix['fix_type']}
                                    - Confidence: {fix['confidence']}
                                    - Needs Review: {fix.get('needs_review', False)}
                                    - Reason: {fix['reason']}
                                    """)

                            min_confidence = st.slider(
                                "Minimum Confidence Threshold",
                                min_value=0.0,
                                max_value=1.0,
                                value=0.5,
                                step=0.1,
                                help="Only apply fixes with confidence >= this threshold"
                            )

                            if st.button("✅ Confirm and Apply Fixes", type="primary"):
                                try:
                                    # Apply fixes to test cases
                                    updated_cases, stats = fix_applier.apply_fixes_to_test_cases(
                                        st.session_state.service.test_cases,
                                        fixes,
                                        min_confidence=min_confidence
                                    )

                                    # Update service with fixed test cases
                                    st.session_state.service.test_cases = updated_cases

                                    # Save to Excel
                                    st.session_state.service.save_test_cases()

                                    # Show results
                                    st.success(f"""
                                    ✅ Fixes Applied Successfully!

                                    - Total fixes from Claude Code: {stats['total_fixes']}
                                    - Applied: {stats['applied']}
                                    - Skipped (low confidence): {stats['skipped_low_confidence']}
                                    - Skipped (validation errors): {stats['skipped_validation']}
                                    - Needs manual review: {stats['needs_review']}
                                    """)

                                    # Show validation errors if any
                                    if fix_applier.validation_errors:
                                        with st.expander("⚠️ Validation Warnings"):
                                            for error in fix_applier.validation_errors:
                                                st.warning(error)

                                    st.info("💡 Run a regression test to see if the fixes improved results!")

                                except Exception as e:
                                    st.error(f"Error applying fixes: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())

                    except FileNotFoundError:
                        st.error(f"Debug session '{session_to_apply}' not found")
                    except Exception as e:
                        st.error(f"Error loading debug session: {e}")
            else:
                st.info("Create a debug session first")

    elif st.session_state.current_run:
        st.success("✅ All tests passed! No failures to fix.")
    else:
        st.info("Run a test cycle first to enable Claude Code auto-fix")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Reload Test Cases", use_container_width=True):
            try:
                test_cases = st.session_state.service.load_test_cases()
                st.success(f"✓ Reloaded {len(test_cases)} test cases")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("💾 Save to Excel", use_container_width=True):
            try:
                st.session_state.service.save_test_cases()
                st.success("✓ Saved to Excel")
            except Exception as e:
                st.error(f"Error: {e}")

    with col3:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.run_history = []
            st.session_state.current_run = None
            st.success("✓ History cleared")

# ============================================================================
# TAB 2: DASHBOARD
# ============================================================================
with tab2:
    st.header("Dashboard")

    if not st.session_state.current_run:
        st.info("Run a test cycle to see dashboard")
    else:
        run = st.session_state.current_run
        summary = run.summary

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Pass Rate",
                f"{summary.pass_rate:.1f}%",
                delta=None
            )

        with col2:
            st.metric(
                "Total Tests",
                summary.total_tests,
                delta=None
            )

        with col3:
            st.metric(
                "Passed",
                summary.passed,
                delta=f"{summary.passed - summary.failed}"
            )

        with col4:
            st.metric(
                "Auto-Fixed",
                summary.auto_fixed_count,
                delta=None
            )

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Pass/Fail pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Passed', 'Failed'],
                values=[summary.passed, summary.failed],
                marker=dict(colors=['#00cc66', '#ff4444']),
                hole=0.4
            )])
            fig_pie.update_layout(
                title="Test Results Distribution",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # By type bar chart
            type_data = pd.DataFrame({
                'Type': ['Objective', 'Subjective', 'Calculated'],
                'Passed': [summary.objective_passed, summary.subjective_passed, summary.calculated_passed],
                'Failed': [
                    summary.objective_total - summary.objective_passed,
                    summary.subjective_total - summary.subjective_passed,
                    summary.calculated_total - summary.calculated_passed
                ]
            })

            fig_bar = go.Figure(data=[
                go.Bar(name='Passed', x=type_data['Type'], y=type_data['Passed'], marker_color='#00cc66'),
                go.Bar(name='Failed', x=type_data['Type'], y=type_data['Failed'], marker_color='#ff4444')
            ])
            fig_bar.update_layout(
                title="Results by Test Type",
                barmode='stack',
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # Failure breakdown
        st.subheader("Failure Analysis")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Inclusion Failures", summary.fail_inclusion)

        with col2:
            st.metric("Similarity Failures", summary.fail_similarity)

        with col3:
            st.metric("Needs Review", summary.needs_review_count)

        # Similarity score distribution
        similarity_scores = [r.validation.similarity_score for r in run.results]
        fig_hist = px.histogram(
            x=similarity_scores,
            nbins=20,
            title="Similarity Score Distribution",
            labels={'x': 'Similarity Score', 'y': 'Count'}
        )
        fig_hist.add_vline(x=0.7, line_dash="dash", line_color="red", annotation_text="Common Threshold (0.7)")
        st.plotly_chart(fig_hist, use_container_width=True)

# ============================================================================
# TAB 3: TEST DETAILS
# ============================================================================
with tab3:
    st.header("Test Case Details")

    if not st.session_state.current_run:
        st.info("Run a test cycle to see test details")
    else:
        run = st.session_state.current_run

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "PASS", "FAIL", "FAIL_INCLUSION", "FAIL_SIMILARITY"]
            )

        with col2:
            type_filter = st.selectbox(
                "Filter by Type",
                options=["All", "Objective", "Subjective (All)", "Subjective (Project)",
                        "Subjective (Developer)", "Subjective (Location)", "Calculated (All)",
                        "Calculated (Financial)"]
            )

        with col3:
            auto_fixed_filter = st.selectbox(
                "Filter by Auto-Fix",
                options=["All", "Auto-Fixed", "Not Fixed", "Needs Review"]
            )

        # Apply filters
        filtered_results = run.results

        if status_filter != "All":
            filtered_results = [r for r in filtered_results if r.status.value == status_filter]

        if type_filter != "All":
            # Handle grouped categories (e.g., "Subjective (All)" matches any subjective)
            if type_filter == "Subjective (All)":
                filtered_results = [r for r in filtered_results if r.test_case.type.value.startswith("Subjective")]
            elif type_filter == "Calculated (All)":
                filtered_results = [r for r in filtered_results if r.test_case.type.value.startswith("Calculated")]
            else:
                # Exact match for specific types
                filtered_results = [r for r in filtered_results if r.test_case.type.value == type_filter]

        if auto_fixed_filter == "Auto-Fixed":
            filtered_results = [r for r in filtered_results if r.test_case.auto_fixed]
        elif auto_fixed_filter == "Not Fixed":
            filtered_results = [r for r in filtered_results if not r.test_case.auto_fixed]
        elif auto_fixed_filter == "Needs Review":
            filtered_results = [r for r in filtered_results if r.test_case.needs_review]

        st.text(f"Showing {len(filtered_results)} of {len(run.results)} tests")

        # Test table
        test_data = []
        for result in filtered_results:
            tc = result.test_case
            test_data.append({
                'ID': tc.test_id,
                'Type': tc.type.value,
                'Prompt': tc.prompt[:60] + "..." if len(tc.prompt) > 60 else tc.prompt,
                'Status': result.status.value,
                'Similarity': f"{result.validation.similarity_score:.3f}",
                'Expected': tc.expected_answer_include[:40] + "..." if len(tc.expected_answer_include) > 40 else tc.expected_answer_include,
                'Actual': result.model_answer[:40] + "..." if len(result.model_answer) > 40 else result.model_answer,
                'Auto-Fixed': '✓' if tc.auto_fixed else '',
                'Review': '⚠️' if tc.needs_review else ''
            })

        df = pd.DataFrame(test_data)

        # Display with color coding
        def highlight_status(row):
            if row['Status'] == 'PASS':
                return ['background-color: #ccffcc'] * len(row)
            else:
                return ['background-color: #ffcccc'] * len(row)

        if not df.empty:
            st.dataframe(
                df.style.apply(highlight_status, axis=1),
                use_container_width=True,
                height=600
            )

            # Detailed view of selected test
            st.divider()
            st.subheader("Detailed Test View")

            test_id = st.number_input("Select Test ID", min_value=0, max_value=len(run.results)-1, value=0)

            selected_result = run.results[test_id]
            selected_tc = selected_result.test_case

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Test Case Info**")
                st.text(f"ID: {selected_tc.test_id}")
                st.text(f"Type: {selected_tc.type.value}")
                st.text(f"Row: {selected_tc.row_number}")

                st.markdown("**Status**")
                status_color = "green" if selected_result.passed else "red"
                st.markdown(f":{status_color}[{selected_result.status.value}]")

                st.markdown("**Validation**")
                st.text(f"Inclusion: {'✓' if selected_result.validation.inclusion_passed else '✗'}")
                st.text(f"Similarity: {selected_result.validation.similarity_score:.3f} / {selected_result.validation.similarity_threshold:.3f}")

                if selected_tc.auto_fixed:
                    st.markdown("**Auto-Fix**")
                    st.info(f"Reason: {selected_tc.fix_reason}")
                    if selected_tc.needs_review:
                        st.warning("⚠️ Needs Manual Review")

            with col2:
                st.markdown("**Prompt**")
                st.code(selected_tc.prompt, language=None)

                st.markdown("**Expected Answer Should Include**")
                st.code(selected_tc.expected_answer_include, language=None)

                if selected_tc.expected_answer_include_original:
                    st.markdown("**Original Expected Answer**")
                    st.code(selected_tc.expected_answer_include_original, language=None)

            st.markdown("**Model Answer**")
            st.code(selected_result.model_answer, language=None)

            st.markdown("**Good Answer (Reference)**")
            st.code(selected_tc.good_answer, language=None)

            st.markdown("**Validation Explanations**")
            st.text(f"Inclusion: {selected_result.validation.inclusion_explanation}")
            st.text(f"Similarity: {selected_result.validation.similarity_explanation}")
        else:
            st.warning("No tests match the current filters")

# ============================================================================
# TAB 4: HTML REPORT
# ============================================================================
with tab4:
    st.header("📧 HTML Email Report")

    if not st.session_state.current_run:
        st.info("Run a test cycle to generate HTML report")
    else:
        run = st.session_state.current_run

        st.markdown("""
        **Email-Friendly Report**

        This report is optimized for email clients with:
        - Inline CSS styling
        - Hideable test details
        - Color-coded status indicators
        - Professional formatting
        """)

        st.divider()

        # Report generation options
        col1, col2 = st.columns(2)

        with col1:
            include_grid = st.checkbox("Include test grid", value=True,
                                      help="Include detailed test results table")

        with col2:
            # Select comparison run
            comparison_run_id = None
            if len(st.session_state.service.runs) > 1:
                comparison_run_id = st.selectbox(
                    "Compare to (optional)",
                    options=["None"] + list(st.session_state.service.runs.keys()),
                    key="comparison_run"
                )
                if comparison_run_id == "None":
                    comparison_run_id = None

        # Generate HTML report
        if st.button("🔄 Generate HTML Report", use_container_width=True):
            with st.spinner("Generating HTML report..."):
                try:
                    report_gen = HTMLReportGenerator()
                    previous_run = None
                    if comparison_run_id:
                        previous_run = st.session_state.service.runs.get(comparison_run_id)

                    html_report = report_gen.generate_email_report(
                        test_run=run,
                        include_editable_grid=include_grid,
                        previous_run=previous_run
                    )

                    # Store in session state
                    st.session_state.html_report = html_report
                    st.success("✓ HTML report generated!")

                except Exception as e:
                    st.error(f"Error generating report: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        st.divider()

        # Display and download HTML report
        if 'html_report' in st.session_state:
            st.subheader("Preview & Download")

            # Download button
            st.download_button(
                label="📥 Download HTML Report",
                data=st.session_state.html_report,
                file_name=f"test_report_{run.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )

            st.divider()

            # Preview with tabs
            preview_tab1, preview_tab2 = st.tabs(["📊 Rendered Preview", "📝 HTML Source"])

            with preview_tab1:
                st.markdown("**Interactive Preview:**")
                # Render HTML in iframe
                import streamlit.components.v1 as components
                components.html(st.session_state.html_report, height=800, scrolling=True)

            with preview_tab2:
                st.markdown("**HTML Source Code:**")
                st.code(st.session_state.html_report, language="html")

                # Copy to clipboard helper
                st.caption("💡 Tip: Copy this HTML and paste directly into your email client's HTML editor")

        else:
            st.info("Click 'Generate HTML Report' to create the report")

# ============================================================================
# TAB 5: SETTINGS
# ============================================================================
with tab5:
    st.header("Settings & Info")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")
        st.text(f"Excel Path: {st.session_state.excel_path}")

        if st.session_state.service:
            st.text(f"Test Cases: {len(st.session_state.service.test_cases)}")
            st.text(f"Runs: {len(st.session_state.service.runs)}")

            st.divider()

            st.subheader("Parallel Execution Settings")
            st.text(f"Max Workers: {st.session_state.service.max_workers}")
            st.text(f"Batch Size: {st.session_state.service.batch_size}")
            st.text(f"Rate Limit: {st.session_state.service.rate_limiter.max_calls_per_minute} calls/min")

        st.divider()

        st.subheader("System Info")
        st.text("Components:")
        st.text("  ✓ Test Service")
        st.text("  ✓ Validator (Inclusion + Similarity)")
        st.text("  ✓ Auto-Healer")
        st.text("  ✓ Query Orchestrator")
        st.text("  ✓ Parallel Batch Executor")
        st.text("  ✓ Rate Limiter (Gemini API)")
        st.text("  ✓ HTML Report Generator")

    with col2:
        st.subheader("Documentation")
        st.markdown("""
        **Quick Guide:**
        1. Initialize service (sidebar)
        2. Enable parallel execution for faster runs
        3. Run initial test cycle with auto-healing
        4. Review results in dashboard
        5. Generate and download HTML report
        6. **Use Claude Code auto-fix for intelligent debugging** ⭐
        7. Run regression to validate fixes
        8. Compare improvements

        **Color Codes:**
        - 🟢 Green: Passed tests
        - 🔴 Red: Failed tests
        - ⚠️ Yellow: Needs review

        **Performance:**
        - Parallel execution: 5 workers, 10 tests/batch
        - Rate limiting: 60 calls/min (Gemini API)
        - Expected duration: 3-5 min for 121 tests

        **Claude Code Integration (UltraThink):**
        - **Slash Command:** `/fix-qa-tests`
        - Intelligent semantic analysis of failures
        - High-quality fixes with confidence scores
        - 85-95% fix accuracy vs 60-70% traditional
        - See CLAUDE_CODE_AUTO_HEALING.md for full guide

        **Export Data:**
        - Results saved to Excel automatically
        - HTML reports downloadable
        - Debug sessions in data/debug_sessions/
        - View history in sidebar
        """)

        if st.button("📖 View Full Documentation"):
            st.info("See ULTRATHINK_USAGE_GUIDE.md for complete documentation")

# Footer
st.divider()
st.caption("QA Automation - Auto-Healing Testing System | Built with hexagonal architecture + LangGraph")

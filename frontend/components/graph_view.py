"""
Knowledge Graph Visualization Component
Displays v4 JSON-based knowledge graph with interactive visualization
Uses FastAPI endpoint - NO Neo4j database required
"""

import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, date


def convert_to_json_serializable(obj):
    """Convert DateTime and other types to JSON-serializable formats"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


def load_mock_graph_data() -> Dict:
    """Load graph data from FastAPI knowledge graph endpoint"""
    api_url = "http://localhost:8000/api/knowledge-graph/visualization"

    try:
        import requests
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error: {response.status_code}")
            return {'nodes': [], 'edges': [], 'stats': {}}
    except Exception as e:
        st.error(f"Error loading graph data from API: {e}")
        return {'nodes': [], 'edges': [], 'stats': {}}


def render_graph_visualization(graph_data: Dict):
    """Render knowledge graph using vis.js or networkx"""

    if not graph_data['nodes']:
        st.warning("No graph data available")
        return

    # Display layer-wise stats
    if graph_data.get('stats'):
        st.markdown("**Knowledge Graph Statistics (Layer-wise)**")

        # Layer 0-2 stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("L0: Dimensions", graph_data['stats'].get('l0_dimensions', 0))
        with col2:
            st.metric("Projects (Blue)", graph_data['stats'].get('l1_projects', 0))
        with col3:
            st.metric("L1 Attributes (Green)", graph_data['stats'].get('l1_attributes', 0))
        with col4:
            st.metric("L2 Metrics (Yellow)", graph_data['stats'].get('l2_metrics', 0))

        # Graph totals
        col5, col6 = st.columns(2)
        with col5:
            st.metric("Total Nodes", graph_data['stats'].get('total_nodes', 0))
        with col6:
            st.metric("Total Edges", graph_data['stats'].get('total_edges', 0))

    st.markdown("---")

    # L0: Dimension Definitions (Collapsible)
    with st.expander("🔍 **L0: Dimension Definitions** (Click to view actual data)", expanded=False):
        st.markdown("**Layer 0 - Fundamental Dimensions (U, L², T, CF)**")

        # Filter L0 nodes (layer is integer 0)
        l0_nodes = [n for n in graph_data['nodes'] if n.get('layer') == 0 or n.get('type') == 'L0_Dimension']

        if l0_nodes:
            st.markdown(f"Total L0 Dimensions: **{len(l0_nodes)}**")

            for node in l0_nodes:
                with st.container():
                    st.markdown(f"##### {node['label']}")

                    # Display dimension metadata
                    st.json({
                        'type': node.get('type'),
                        'layer': node.get('layer'),
                        'description': f"Base dimension for knowledge graph"
                    })

                    st.markdown("---")
        else:
            st.warning("No L0 dimension data available. Try clicking '🔄 Reload Data' button above.")

    # L1: Raw Data (Collapsible)
    with st.expander("📊 **L1: Raw Input Data** (Click to view actual data)", expanded=False):
        st.markdown("**Layer 1 - Raw data from PDF with nested structure**")

        # Filter L1 nodes (layer is integer 1)
        l1_nodes = [n for n in graph_data['nodes'] if n.get('layer') == 1]

        if l1_nodes:
            st.markdown(f"Total L1 Data Nodes: **{len(l1_nodes)}**")

            # Group by node type
            projects = [n for n in l1_nodes if n['type'] == 'Project_L1']
            attributes = [n for n in l1_nodes if n['type'] == 'L1_Attribute']

            # Display Projects with Full Metadata
            if projects:
                st.markdown(f"#### 📍 Projects ({len(projects)}) - Full Metadata")
                for idx, node in enumerate(projects, 1):
                    with st.container():
                        st.markdown(f"**{idx}. {node['label']}**")

                        # Display project metadata in structured format
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Project ID:** {node.get('projectId', 'N/A')}")
                            st.markdown(f"**Developer:** {node.get('developerName', 'N/A')}")
                            st.markdown(f"**Location:** {node.get('location', 'N/A')}")
                        with col2:
                            st.markdown(f"**Launch Date:** {node.get('launchDate', 'N/A')}")
                            st.markdown(f"**Possession Date:** {node.get('possessionDate', 'N/A')}")
                            st.markdown(f"**RERA Registered:** {node.get('reraRegistered', 'N/A')}")

                        # Technical details (compact display)
                        st.caption(f"🔧 Technical: id={node.get('id')}, type={node.get('type')}, layer={node.get('layer')}")
                        st.markdown("---")

            # Display ALL L1 Attributes (nested format) - NO LIMIT
            if attributes:
                st.markdown(f"#### 📊 L1 Attributes ({len(attributes)}) - Nested Format")
                st.markdown("*All attributes with dimensional relationships*")

                # Show ALL attributes with nested structure
                for idx, node in enumerate(attributes, 1):
                    with st.container():
                        st.markdown(f"**{idx}. {node['label']}**")

                        # Display nested attribute structure
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Value:** {node.get('value', 'N/A')}")
                        with col2:
                            st.markdown(f"**Unit:** {node.get('unit', 'N/A')}")
                        with col3:
                            st.markdown(f"**Dimension:** {node.get('dimension', 'N/A')}")

                        st.markdown("---")
        else:
            st.warning("No L1 raw data available. Try clicking '🔄 Reload Data' button above.")

    # L2: Calculated Financial Metrics (Collapsible)
    with st.expander("💰 **L2: Calculated Financial Metrics** (Click to view actual data)", expanded=False):
        st.markdown("**Layer 2 - Financial metrics calculated from L1 data (NON-LLM)**")

        # Filter L2 nodes (layer is integer 2)
        l2_nodes = [n for n in graph_data['nodes'] if n.get('layer') == 2]

        if l2_nodes:
            st.markdown(f"Total L2 Metric Nodes: **{len(l2_nodes)}**")

            # Group by project (extract project ID from node ID)
            l2_by_project = {}
            for node in l2_nodes:
                # Extract project ID from node ID (format: proj_X_l2_metricName)
                node_id = node.get('id', '')
                if '_l2_' in node_id:
                    proj_id = node_id.split('_l2_')[0]
                    if proj_id not in l2_by_project:
                        l2_by_project[proj_id] = []
                    l2_by_project[proj_id].append(node)

            # Display L2 metrics by project
            for proj_id, metrics in l2_by_project.items():
                # Find project name
                project_nodes = [n for n in graph_data['nodes'] if n.get('id') == proj_id]
                project_name = project_nodes[0].get('label', 'Unknown') if project_nodes else 'Unknown'

                st.markdown(f"#### 💼 {project_name} - L2 Metrics ({len(metrics)})")

                for idx, node in enumerate(metrics, 1):
                    with st.container():
                        st.markdown(f"**{idx}. {node['label']}**")

                        # Display metric details in structured format
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Value:** {node.get('value', 'N/A')}")
                        with col2:
                            st.markdown(f"**Unit:** {node.get('unit', 'N/A')}")
                        with col3:
                            st.markdown(f"**Dimension:** {node.get('dimension', 'N/A')}")

                        # Show calculation formula if available
                        if node.get('calculation'):
                            st.caption("📐 Calculation:")
                            st.code(node.get('calculation'), language='text')

                        st.markdown("---")
        else:
            st.warning("No L2 metrics available. Try clicking '🔄 Reload Data' button above.")

    st.markdown("---")

    # Create vis.js network HTML
    # Convert DateTime objects to JSON-serializable strings
    nodes_json = json.dumps(convert_to_json_serializable(graph_data['nodes']))
    edges_json = json.dumps(convert_to_json_serializable(graph_data['edges']))

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 600px;
                border: 1px solid #ccc;
                background-color: #fafafa;
            }}
            .node-info {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: white;
                padding: 10px;
                border: 1px solid #1e3c72;
                border-radius: 5px;
                max-width: 300px;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <div id="nodeInfo" class="node-info" style="display:none;">
            <h4 id="nodeName"></h4>
            <p id="nodeDetails"></p>
        </div>

        <script type="text/javascript">
            // Graph data
            const nodesData = {nodes_json};
            const edgesData = {edges_json};

            // Transform to vis.js format
            const nodes = new vis.DataSet(nodesData.map(n => ({{
                id: n.id,
                label: n.label,
                group: n.group,
                color: n.color,
                size: n.size,
                font: {{ color: '#333', size: 12 }},
                title: n.label + ' (' + n.type + ')',
                data: n.data
            }})));

            const edges = new vis.DataSet(edgesData.map(e => ({{
                from: e.source,
                to: e.target,
                label: e.label,
                color: {{ color: e.color }},
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                font: {{ size: 10, align: 'middle' }}
            }})));

            // Create network
            const container = document.getElementById('mynetwork');
            const data = {{ nodes: nodes, edges: edges }};
            const options = {{
                nodes: {{
                    shape: 'dot',
                    borderWidth: 2,
                    borderWidthSelected: 4,
                    shadow: true
                }},
                edges: {{
                    smooth: {{
                        type: 'continuous',
                        roundness: 0.5
                    }},
                    width: 2
                }},
                physics: {{
                    stabilization: {{ iterations: 200 }},
                    barnesHut: {{
                        gravitationalConstant: -8000,
                        springConstant: 0.04,
                        springLength: 150
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100,
                    navigationButtons: true,
                    keyboard: true
                }}
            }};

            const network = new vis.Network(container, data, options);

            // Node click handler
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);

                    const infoDiv = document.getElementById('nodeInfo');
                    document.getElementById('nodeName').textContent = node.label;

                    let details = 'Type: ' + node.title + '<br>';
                    if (node.data) {{
                        if (node.data.U) {{
                            details += 'Total Units: ' + node.data.U.total_units + '<br>';
                        }}
                        if (node.data.CF) {{
                            details += 'Current PSF: ₹' + node.data.CF.current_price_psf + '<br>';
                        }}
                    }}

                    document.getElementById('nodeDetails').innerHTML = details;
                    infoDiv.style.display = 'block';
                }} else {{
                    document.getElementById('nodeInfo').style.display = 'none';
                }}
            }});
        </script>
    </body>
    </html>
    """

    st.components.v1.html(html_code, height=650, scrolling=False)


def render_knowledge_graph_view():
    """Main function to render knowledge graph visualization"""

    # Header with reload button
    col_title, col_reload = st.columns([4, 1])

    with col_title:
        st.markdown("### Knowledge Graph Visualization")
        st.markdown("Explore the relationships between Projects, Developers, and Locations")

    with col_reload:
        st.write("")  # Spacing
        if st.button("🔄 Reload Data", type="primary", use_container_width=True):
            with st.spinner("Reloading data (PDF → Nested JSON + L2 + L3)..."):
                try:
                    import requests
                    response = requests.post(
                        "http://localhost:8000/api/data/refresh",
                        timeout=180
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success(f"✓ Data reloaded in {result.get('duration_seconds', 0):.1f}s")
                            st.rerun()  # Refresh the graph view
                        else:
                            st.error(f"✗ Reload failed: {result.get('message')}")
                    else:
                        st.error(f"API error: {response.status_code}")
                except requests.exceptions.Timeout:
                    st.error("Reload timed out after 3 minutes")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.markdown("---")

    # Load graph data from FastAPI endpoint (NO NEO4J)
    try:
        with st.spinner("Loading knowledge graph from API..."):
            import requests
            response = requests.get("http://localhost:8000/api/knowledge-graph/visualization", timeout=10)

            if response.status_code == 200:
                graph_data = response.json()
                st.success("✅ Knowledge graph loaded from v4 nested JSON")
            else:
                st.error(f"API error: {response.status_code}")
                return
    except Exception as e:
        st.error(f"❌ **Cannot load knowledge graph from API**")
        st.error(f"**Error:** {str(e)}")
        st.markdown("**Troubleshooting:**")
        st.markdown("- Ensure FastAPI server is running on http://localhost:8000")
        st.markdown("- Check data has been extracted: /api/data/status")
        return

    # Render visualization
    if graph_data['nodes']:
        render_graph_visualization(graph_data)

        # Layer-wise Legend
        st.markdown("---")
        st.markdown("**Layer-wise Architecture Legend:**")

        # Layer colors
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("⚪ **L0: Dimensions** - Gray nodes (#9E9E9E)")
            st.markdown("Base dimensional units: U, L², T, C")
        with col2:
            st.markdown("🔵 **Projects (L1)** - Blue nodes (#2196F3)")
            st.markdown("Core metadata: name, developer, location, dates, RERA")
        with col3:
            st.markdown("🟢 **L1 Attributes** - Green nodes (#4CAF50)")
            st.markdown("Numeric values with dimensional relationships")
        with col4:
            st.markdown("🟡 **L2 Metrics** - Yellow nodes (#FFC107)")
            st.markdown("Calculated financials: NPV, IRR, ROI, Payback")

        # Instructions
        with st.expander("How to use"):
            st.markdown("""
            **Interactions:**
            - **Click** on a node to see details
            - **Drag** nodes to rearrange the graph
            - **Scroll** to zoom in/out
            - **Right-click & drag** to pan the view
            - **Hover** over nodes for quick info

            **Navigation:**
            - Use the navigation buttons in the bottom-right corner
            - Press 'S' to fit the graph to the screen

            **Layer Architecture (L0 → L1 → L2):**
            - **L0 (Gray):** Dimension definitions - The fundamental vocabulary (U=Units, L²=Area, T=Time, C=Cash Flow)
            - **Projects (Blue):** Core project metadata - Name, developer, location, launch/possession dates, RERA status
            - **L1 Attributes (Green):** Raw numeric data from PDF - Values with dimensional relationships (IS, NUMERATOR, DENOMINATOR, INVERSE_OF)
            - **L2 Metrics (Yellow):** Financial metrics calculated from L1 (NON-LLM) - NPV, IRR, ROI, Payback Period, Absorption Rate

            **Relationships:**
            - L1 Attributes → Projects (HAS_L1_ATTRIBUTE) - Green nodes linked to blue project nodes
            - L1 Attributes → L0 Dimensions (IS/NUMERATOR/DENOMINATOR/INVERSE_OF) - Explicit dimensional relationships
            - L2 Metrics → Projects (HAS_L2_METRIC) - Yellow nodes linked to blue project nodes
            - L2 Metrics → L0 Dimensions (IS/NUMERATOR/DENOMINATOR) - Based on calculated dimension

            **Data Expandable Sections (Above Graph):**
            - **L0 Section:** View base dimension definitions
            - **L1 Section:** View ALL project metadata and ALL L1 attributes (no limit)
            - **L2 Section:** View all calculated financial metrics with formulas
            """)
    else:
        st.error("No graph data available. Click '🔄 Reload Data' button above to extract from PDF.")

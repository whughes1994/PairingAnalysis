#!/usr/bin/env python3
"""
QA Annotations Tool

Allows QA reviewers to mark issues, add comments, and track corrections.
Creates an audit trail of all human-in-the-loop corrections.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="QA Annotations",
    page_icon="📝",
    layout="wide"
)

# ============================================================================
# ANNOTATION STORAGE
# ============================================================================

ANNOTATIONS_DIR = Path("qa_annotations")
ANNOTATIONS_DIR.mkdir(exist_ok=True)

def get_annotation_file(json_filename: str) -> Path:
    """Get annotation file path for a given JSON file."""
    base_name = Path(json_filename).stem
    return ANNOTATIONS_DIR / f"{base_name}_annotations.json"

def load_annotations(json_filename: str) -> list:
    """Load existing annotations for a JSON file."""
    annotation_file = get_annotation_file(json_filename)

    if annotation_file.exists():
        with open(annotation_file, 'r') as f:
            return json.load(f)
    return []

def save_annotations(json_filename: str, annotations: list):
    """Save annotations to file."""
    annotation_file = get_annotation_file(json_filename)

    with open(annotation_file, 'w') as f:
        json.dump(annotations, indent=2, fp=f)

    st.success(f"Saved to {annotation_file}")

# ============================================================================
# MAIN APP
# ============================================================================

st.title("📝 QA Annotations & Issue Tracking")
st.markdown("Document parsing issues and track corrections")

# File selection
st.sidebar.header("📁 File Selection")

json_dir = Path("output")
json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []

if not json_files:
    st.error("No JSON files found in 'output' directory")
    st.stop()

selected_json = st.sidebar.selectbox(
    "Select Parsed JSON",
    options=json_files,
    format_func=lambda x: x.name
)

# Load annotations
annotations = load_annotations(selected_json.name)

st.sidebar.markdown("---")
st.sidebar.header("📊 Annotation Stats")
st.sidebar.metric("Total Annotations", len(annotations))

issue_types = {}
for ann in annotations:
    issue_type = ann.get('issue_type', 'Unknown')
    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

for issue_type, count in sorted(issue_types.items()):
    st.sidebar.write(f"- {issue_type}: {count}")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["➕ Add Annotation", "📋 View Annotations", "📊 Export Report"])

# ============================================================================
# TAB 1: ADD ANNOTATION
# ============================================================================

with tab1:
    st.header("➕ Add New Annotation")

    with st.form("annotation_form"):
        col1, col2 = st.columns(2)

        with col1:
            pairing_id = st.text_input(
                "Pairing ID",
                help="ID of the pairing with the issue (e.g., O8001)"
            )

            issue_type = st.selectbox(
                "Issue Type",
                options=[
                    "Missing Data",
                    "Incorrect Time",
                    "Wrong Station Code",
                    "Incorrect Flight Number",
                    "Missing Leg",
                    "Extra Leg",
                    "Wrong Equipment",
                    "Incorrect Layover",
                    "FTM/TTL Mismatch",
                    "Date Error",
                    "Formatting Issue",
                    "Other"
                ]
            )

            severity = st.select_slider(
                "Severity",
                options=["Low", "Medium", "High", "Critical"]
            )

        with col2:
            field_affected = st.text_input(
                "Field Affected",
                help="Specific field with the issue (e.g., departure_time, station_code)"
            )

            expected_value = st.text_input(
                "Expected Value (from PDF)",
                help="What the value should be according to the PDF"
            )

            actual_value = st.text_input(
                "Actual Value (in JSON)",
                help="What was actually parsed"
            )

        description = st.text_area(
            "Issue Description",
            help="Detailed description of the issue",
            height=100
        )

        notes = st.text_area(
            "Additional Notes",
            help="Any additional context or observations",
            height=100
        )

        submitted = st.form_submit_button("💾 Save Annotation")

        if submitted:
            if not pairing_id:
                st.error("Pairing ID is required")
            else:
                annotation = {
                    'id': f"ANN-{len(annotations) + 1:04d}",
                    'timestamp': datetime.now().isoformat(),
                    'json_file': selected_json.name,
                    'pairing_id': pairing_id,
                    'issue_type': issue_type,
                    'severity': severity,
                    'field_affected': field_affected,
                    'expected_value': expected_value,
                    'actual_value': actual_value,
                    'description': description,
                    'notes': notes,
                    'status': 'Open',
                    'reviewer': 'Human QA'
                }

                annotations.append(annotation)
                save_annotations(selected_json.name, annotations)

                st.success(f"✅ Annotation {annotation['id']} saved!")
                st.rerun()

# ============================================================================
# TAB 2: VIEW ANNOTATIONS
# ============================================================================

with tab2:
    st.header("📋 View Annotations")

    if not annotations:
        st.info("No annotations yet. Use the 'Add Annotation' tab to create your first annotation.")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_type = st.multiselect(
                "Filter by Issue Type",
                options=list(set(ann['issue_type'] for ann in annotations)),
                default=None
            )

        with col2:
            filter_severity = st.multiselect(
                "Filter by Severity",
                options=["Low", "Medium", "High", "Critical"],
                default=None
            )

        with col3:
            filter_status = st.multiselect(
                "Filter by Status",
                options=["Open", "In Progress", "Resolved", "Won't Fix"],
                default=["Open", "In Progress"]
            )

        # Apply filters
        filtered = annotations

        if filter_type:
            filtered = [a for a in filtered if a['issue_type'] in filter_type]

        if filter_severity:
            filtered = [a for a in filtered if a['severity'] in filter_severity]

        if filter_status:
            filtered = [a for a in filtered if a.get('status', 'Open') in filter_status]

        # Sort by timestamp (newest first)
        filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)

        st.write(f"Showing {len(filtered)} of {len(annotations)} annotations")

        # Display annotations
        for ann in filtered:
            severity_color = {
                'Low': '🟢',
                'Medium': '🟡',
                'High': '🟠',
                'Critical': '🔴'
            }

            with st.expander(
                f"{severity_color.get(ann['severity'], '⚪')} {ann['id']} - {ann['pairing_id']} - {ann['issue_type']}",
                expanded=False
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Details:**")
                    st.write(f"**Pairing ID:** {ann['pairing_id']}")
                    st.write(f"**Issue Type:** {ann['issue_type']}")
                    st.write(f"**Severity:** {ann['severity']}")
                    st.write(f"**Status:** {ann.get('status', 'Open')}")
                    st.write(f"**Field:** {ann.get('field_affected', 'N/A')}")

                    if ann.get('description'):
                        st.markdown("**Description:**")
                        st.info(ann['description'])

                with col2:
                    st.markdown("**Values:**")

                    if ann.get('expected_value'):
                        st.success(f"**Expected (PDF):** {ann['expected_value']}")

                    if ann.get('actual_value'):
                        st.error(f"**Actual (Parsed):** {ann['actual_value']}")

                    if ann.get('notes'):
                        st.markdown("**Notes:**")
                        st.text_area(
                            "Notes",
                            value=ann['notes'],
                            height=100,
                            disabled=True,
                            key=f"notes_{ann['id']}"
                        )

                st.caption(f"Created: {ann.get('timestamp', 'Unknown')} | Reviewer: {ann.get('reviewer', 'Unknown')}")

                # Update status
                new_status = st.selectbox(
                    "Update Status",
                    options=["Open", "In Progress", "Resolved", "Won't Fix"],
                    index=["Open", "In Progress", "Resolved", "Won't Fix"].index(ann.get('status', 'Open')),
                    key=f"status_{ann['id']}"
                )

                if st.button(f"Update Status to {new_status}", key=f"update_{ann['id']}"):
                    # Find and update annotation
                    for a in annotations:
                        if a['id'] == ann['id']:
                            a['status'] = new_status
                            a['updated_at'] = datetime.now().isoformat()
                            break

                    save_annotations(selected_json.name, annotations)
                    st.success(f"Status updated to {new_status}")
                    st.rerun()

# ============================================================================
# TAB 3: EXPORT REPORT
# ============================================================================

with tab3:
    st.header("📊 Export Annotation Report")

    if not annotations:
        st.info("No annotations to export")
    else:
        # Summary statistics
        st.subheader("Summary Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Issues", len(annotations))

        with col2:
            open_issues = len([a for a in annotations if a.get('status', 'Open') == 'Open'])
            st.metric("Open Issues", open_issues)

        with col3:
            resolved = len([a for a in annotations if a.get('status') == 'Resolved'])
            st.metric("Resolved", resolved)

        with col4:
            critical = len([a for a in annotations if a.get('severity') == 'Critical'])
            st.metric("Critical", critical, delta_color="inverse")

        # Issue breakdown
        st.subheader("Issue Breakdown")

        # By type
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**By Issue Type:**")
            type_counts = {}
            for ann in annotations:
                issue_type = ann.get('issue_type', 'Unknown')
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

            type_df = pd.DataFrame([
                {'Issue Type': k, 'Count': v}
                for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ])

            st.dataframe(type_df, hide_index=True, use_container_width=True)

        with col2:
            st.markdown("**By Severity:**")
            severity_counts = {}
            for ann in annotations:
                severity = ann.get('severity', 'Unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            severity_df = pd.DataFrame([
                {'Severity': k, 'Count': v}
                for k, v in sorted(severity_counts.items())
            ])

            st.dataframe(severity_df, hide_index=True, use_container_width=True)

        # Affected pairings
        st.subheader("Most Affected Pairings")

        pairing_counts = {}
        for ann in annotations:
            pairing_id = ann.get('pairing_id', 'Unknown')
            pairing_counts[pairing_id] = pairing_counts.get(pairing_id, 0) + 1

        pairing_df = pd.DataFrame([
            {'Pairing ID': k, 'Issues': v}
            for k, v in sorted(pairing_counts.items(), key=lambda x: x[1], reverse=True)
        ][:20])  # Top 20

        st.dataframe(pairing_df, hide_index=True, use_container_width=True)

        # Export options
        st.markdown("---")
        st.subheader("📥 Export Options")

        col1, col2 = st.columns(2)

        with col1:
            # Export as CSV
            csv_data = []
            for ann in annotations:
                csv_data.append({
                    'ID': ann.get('id'),
                    'Timestamp': ann.get('timestamp'),
                    'Pairing ID': ann.get('pairing_id'),
                    'Issue Type': ann.get('issue_type'),
                    'Severity': ann.get('severity'),
                    'Status': ann.get('status', 'Open'),
                    'Field': ann.get('field_affected'),
                    'Expected': ann.get('expected_value'),
                    'Actual': ann.get('actual_value'),
                    'Description': ann.get('description'),
                    'Notes': ann.get('notes')
                })

            csv_df = pd.DataFrame(csv_data)
            csv = csv_df.to_csv(index=False)

            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"qa_annotations_{selected_json.stem}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col2:
            # Export as JSON
            report = {
                'report_date': datetime.now().isoformat(),
                'json_file': selected_json.name,
                'summary': {
                    'total_annotations': len(annotations),
                    'open_issues': len([a for a in annotations if a.get('status', 'Open') == 'Open']),
                    'resolved': len([a for a in annotations if a.get('status') == 'Resolved']),
                    'critical': len([a for a in annotations if a.get('severity') == 'Critical'])
                },
                'annotations': annotations
            }

            report_json = json.dumps(report, indent=2)

            st.download_button(
                label="📥 Download as JSON",
                data=report_json,
                file_name=f"qa_report_{selected_json.stem}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(f"Annotation file: {get_annotation_file(selected_json.name)}")

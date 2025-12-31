#!/usr/bin/env python3
"""
QA Workbench for Pairing Parser

Interactive tool for human-in-the-loop quality assurance of parsed pairing data.
Displays PDF source alongside parsed JSON for side-by-side comparison and correction.
"""

import streamlit as st
import json
import pdfplumber
from pathlib import Path
import pandas as pd
from datetime import datetime
import re

st.set_page_config(
    page_title="Pairing Parser QA Workbench",
    page_icon="🔍",
    layout="wide"
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data
def extract_pdf_text(pdf_path: str) -> dict:
    """Extract text from PDF by page."""
    pages = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            pages[i] = page.extract_text() or ''
    return pages

@st.cache_data
def load_json_data(json_path: str) -> dict:
    """Load parsed JSON data."""
    with open(json_path, 'r') as f:
        return json.load(f)

def find_in_pdf(text: str, search_term: str, context_lines: int = 3) -> list:
    """Find search term in PDF text and return with context."""
    results = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if search_term.upper() in line.upper():
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = '\n'.join(lines[start:end])
            results.append({
                'line_number': i + 1,
                'context': context,
                'matched_line': line
            })

    return results

def highlight_text(text: str, search_term: str) -> str:
    """Highlight search term in text."""
    if not search_term:
        return text

    pattern = re.compile(f'({re.escape(search_term)})', re.IGNORECASE)
    return pattern.sub(r'**\1**', text)

# ============================================================================
# MAIN APP
# ============================================================================

st.title("🔍 Pairing Parser QA Workbench")
st.markdown("Interactive quality assurance tool for validating parsed pairing data")

# File selection
st.sidebar.header("📁 File Selection")

# PDF file selector
pdf_dir = Path("Pairing Source Docs")
pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []

if not pdf_files:
    st.error("No PDF files found in 'Pairing Source Docs' directory")
    st.stop()

selected_pdf = st.sidebar.selectbox(
    "Select PDF",
    options=pdf_files,
    format_func=lambda x: x.name
)

# JSON file selector
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

# Load data
pdf_text_by_page = extract_pdf_text(str(selected_pdf))
all_pdf_text = '\n'.join(pdf_text_by_page.values())
parsed_data = load_json_data(str(selected_json))

# Normalize data structure
if 'data' in parsed_data:
    bid_periods = parsed_data['data']
else:
    bid_periods = parsed_data.get('bid_periods', [])

st.sidebar.markdown("---")
st.sidebar.header("🎯 QA Mode")

qa_mode = st.sidebar.radio(
    "Select QA Focus",
    options=[
        "Overview",
        "Fleet Totals",
        "Individual Pairing",
        "Search & Compare",
        "Validation Report"
    ]
)

# ============================================================================
# OVERVIEW MODE
# ============================================================================

if qa_mode == "Overview":
    st.header("📊 Data Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 PDF Source")
        st.metric("Total Pages", len(pdf_text_by_page))
        st.metric("Total Characters", len(all_pdf_text))

        # Show first page preview
        with st.expander("Preview First Page", expanded=True):
            first_page = pdf_text_by_page.get(0, '')
            st.text_area(
                "Page 1",
                value=first_page[:2000] + "..." if len(first_page) > 2000 else first_page,
                height=400,
                disabled=True
            )

    with col2:
        st.subheader("📋 Parsed Data")
        st.metric("Bid Periods (Fleets)", len(bid_periods))

        total_pairings = sum(len(bp.get('pairings', [])) for bp in bid_periods)
        st.metric("Total Pairings", total_pairings)

        total_legs = 0
        for bp in bid_periods:
            for pairing in bp.get('pairings', []):
                for dp in pairing.get('duty_periods', []):
                    total_legs += len(dp.get('legs', []))
        st.metric("Total Legs", total_legs)

        # Fleet breakdown
        with st.expander("Fleet Breakdown", expanded=True):
            fleet_data = []
            for bp in bid_periods:
                fleet_data.append({
                    'Fleet': bp.get('fleet'),
                    'Base': bp.get('base'),
                    'Pairings': len(bp.get('pairings', [])),
                    'FTM': bp.get('ftm'),
                    'TTL': bp.get('ttl')
                })

            if fleet_data:
                st.dataframe(
                    pd.DataFrame(fleet_data),
                    hide_index=True,
                    use_container_width=True
                )

# ============================================================================
# FLEET TOTALS MODE
# ============================================================================

elif qa_mode == "Fleet Totals":
    st.header("🎯 Fleet Totals Validation")
    st.markdown("Compare FTM/TTL totals between PDF and parsed data")

    # Extract totals from PDF
    totals_pattern = re.compile(
        r'([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)'
    )
    pdf_totals = totals_pattern.findall(all_pdf_text)

    for base, fleet, ftm, ttl in pdf_totals:
        st.subheader(f"Fleet {fleet}")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("**PDF Source**")
            st.code(f"Base: {base}\nFTM: {ftm}\nTTL: {ttl}")

        with col2:
            st.markdown("**Parsed Data**")

            # Find matching bid period
            matching_bp = None
            for bp in bid_periods:
                if bp.get('fleet') == fleet:
                    matching_bp = bp
                    break

            if matching_bp:
                parsed_ftm = matching_bp.get('ftm', 'N/A')
                parsed_ttl = matching_bp.get('ttl', 'N/A')
                parsed_base = matching_bp.get('base', 'N/A')

                st.code(f"Base: {parsed_base}\nFTM: {parsed_ftm}\nTTL: {parsed_ttl}")
            else:
                st.error("Not found in parsed data")

        with col3:
            st.markdown("**Status**")

            if matching_bp:
                ftm_match = parsed_ftm == ftm
                ttl_match = parsed_ttl == ttl

                st.write(f"FTM: {'✅' if ftm_match else '❌'}")
                st.write(f"TTL: {'✅' if ttl_match else '❌'}")

                if ftm_match and ttl_match:
                    st.success("Perfect match!")
                else:
                    st.error("Mismatch detected")
            else:
                st.error("Missing from parsed data")

        # Show PDF context
        with st.expander(f"Show PDF Context for Fleet {fleet}"):
            search_results = find_in_pdf(all_pdf_text, f"{fleet} FTM-", context_lines=5)

            for result in search_results:
                st.text_area(
                    f"Line {result['line_number']}",
                    value=result['context'],
                    height=200,
                    disabled=True
                )

        st.markdown("---")

# ============================================================================
# INDIVIDUAL PAIRING MODE
# ============================================================================

elif qa_mode == "Individual Pairing":
    st.header("🔎 Individual Pairing Inspection")

    # Build pairing list
    all_pairings = []
    for bp in bid_periods:
        fleet = bp.get('fleet')
        for pairing in bp.get('pairings', []):
            all_pairings.append({
                'id': pairing.get('id'),
                'fleet': fleet,
                'days': pairing.get('days'),
                'credit_minutes': pairing.get('credit_minutes'),
                'pairing_data': pairing
            })

    if not all_pairings:
        st.warning("No pairings found in parsed data")
        st.stop()

    # Pairing selector
    selected_pairing = st.selectbox(
        "Select Pairing to Inspect",
        options=all_pairings,
        format_func=lambda x: f"{x['id']} - Fleet {x['fleet']} - {x['days']}D - {x['credit_minutes']/60:.1f}h"
    )

    if selected_pairing:
        pairing_id = selected_pairing['id']
        pairing_data = selected_pairing['pairing_data']

        st.subheader(f"Pairing {pairing_id}")

        # Side by side comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📄 PDF Source")

            # Search for pairing in PDF
            search_results = find_in_pdf(all_pdf_text, pairing_id, context_lines=10)

            if search_results:
                for idx, result in enumerate(search_results):
                    with st.expander(f"Occurrence {idx + 1} (Line {result['line_number']})", expanded=(idx == 0)):
                        highlighted = highlight_text(result['context'], pairing_id)
                        st.markdown(highlighted)
            else:
                st.warning(f"Pairing {pairing_id} not found in PDF text")

        with col2:
            st.markdown("### 📋 Parsed Data")

            # Display parsed data in readable format
            st.json({
                'id': pairing_data.get('id'),
                'fleet': selected_pairing['fleet'],
                'days': pairing_data.get('days'),
                'category': pairing_data.get('pairing_category'),
                'credit_minutes': pairing_data.get('credit_minutes'),
                'flight_time_minutes': pairing_data.get('flight_time_minutes'),
                'effective_date': pairing_data.get('effective_date'),
                'through_date': pairing_data.get('through_date')
            })

            # Duty periods summary
            st.markdown("#### Duty Periods")

            duty_periods = pairing_data.get('duty_periods', [])
            for dp_idx, dp in enumerate(duty_periods):
                legs = dp.get('legs', [])

                with st.expander(f"Day {dp_idx + 1} - {len(legs)} legs", expanded=(dp_idx == 0)):
                    st.write(f"**Report:** {dp.get('report_time_formatted', dp.get('report_time'))}")
                    st.write(f"**Release:** {dp.get('release_time_formatted', dp.get('release_time'))}")
                    st.write(f"**Layover:** {dp.get('layover_station', 'None')}")

                    if dp.get('hotel'):
                        st.info(f"🏨 {dp.get('hotel')}")

                    # Legs table
                    legs_data = []
                    for leg in legs:
                        legs_data.append({
                            'Flight': f"{'DH ' if leg.get('deadhead') else ''}{leg.get('flight_number', '')}",
                            'Route': f"{leg.get('departure_station')} → {leg.get('arrival_station')}",
                            'Dept': leg.get('departure_time_formatted', leg.get('departure_time')),
                            'Arr': leg.get('arrival_time_formatted', leg.get('arrival_time')),
                            'Flight Time': leg.get('flight_time'),
                            'Equipment': leg.get('equipment')
                        })

                    if legs_data:
                        st.dataframe(pd.DataFrame(legs_data), hide_index=True, use_container_width=True)

# ============================================================================
# SEARCH & COMPARE MODE
# ============================================================================

elif qa_mode == "Search & Compare":
    st.header("🔍 Search & Compare")
    st.markdown("Search for any text in both PDF and parsed data")

    search_term = st.text_input("Enter search term (pairing ID, station code, flight number, etc.)")

    if search_term:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 PDF Matches")

            pdf_results = find_in_pdf(all_pdf_text, search_term, context_lines=3)

            if pdf_results:
                st.success(f"Found {len(pdf_results)} matches in PDF")

                for idx, result in enumerate(pdf_results[:20]):  # Limit to first 20
                    with st.expander(f"Match {idx + 1} (Line {result['line_number']})"):
                        highlighted = highlight_text(result['context'], search_term)
                        st.markdown(highlighted)
            else:
                st.info("No matches found in PDF")

        with col2:
            st.subheader("📋 Parsed Data Matches")

            # Search in parsed data
            matches = []

            for bp in bid_periods:
                fleet = bp.get('fleet')

                for pairing in bp.get('pairings', []):
                    pairing_str = json.dumps(pairing, default=str)

                    if search_term.upper() in pairing_str.upper():
                        matches.append({
                            'fleet': fleet,
                            'pairing_id': pairing.get('id'),
                            'days': pairing.get('days'),
                            'credit_hours': pairing.get('credit_minutes', 0) / 60
                        })

            if matches:
                st.success(f"Found {len(matches)} pairings with matches")

                matches_df = pd.DataFrame(matches)
                st.dataframe(
                    matches_df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        'fleet': 'Fleet',
                        'pairing_id': 'Pairing ID',
                        'days': 'Days',
                        'credit_hours': st.column_config.NumberColumn('Credit (h)', format='%.1f')
                    }
                )
            else:
                st.info("No matches found in parsed data")

# ============================================================================
# VALIDATION REPORT MODE
# ============================================================================

elif qa_mode == "Validation Report":
    st.header("✅ Validation Report")
    st.markdown("Automated validation checks comparing PDF to parsed data")

    issues = []
    warnings = []

    # Check 1: Fleet count
    st.subheader("1. Fleet Count Validation")

    totals_pattern = re.compile(r'[A-Z]{3}\s+[0-9]{2,3}[A-Z]?\s+FTM-\s*[\d:,]+\s+TTL-\s*[\d:,]+')
    pdf_fleet_count = len(totals_pattern.findall(all_pdf_text))
    parsed_fleet_count = len(bid_periods)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("PDF Fleets", pdf_fleet_count)
    with col2:
        st.metric("Parsed Fleets", parsed_fleet_count)

    if pdf_fleet_count == parsed_fleet_count:
        st.success("✅ Fleet count matches")
    else:
        st.error("❌ Fleet count mismatch")
        issues.append(f"Fleet count: PDF has {pdf_fleet_count}, parsed has {parsed_fleet_count}")

    # Check 2: FTM/TTL totals
    st.subheader("2. FTM/TTL Totals Validation")

    totals_pattern = re.compile(
        r'([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)'
    )
    pdf_totals = totals_pattern.findall(all_pdf_text)

    totals_match = 0
    totals_mismatch = 0

    for base, fleet, ftm, ttl in pdf_totals:
        matching_bp = next((bp for bp in bid_periods if bp.get('fleet') == fleet), None)

        if matching_bp:
            if matching_bp.get('ftm') == ftm and matching_bp.get('ttl') == ttl:
                totals_match += 1
            else:
                totals_mismatch += 1
                issues.append(f"Fleet {fleet}: FTM/TTL mismatch")
        else:
            issues.append(f"Fleet {fleet} found in PDF but not in parsed data")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Totals Match", totals_match, delta=None)
    with col2:
        st.metric("Totals Mismatch", totals_mismatch, delta=None, delta_color="inverse")

    if totals_mismatch == 0:
        st.success("✅ All FTM/TTL totals match")
    else:
        st.error(f"❌ {totals_mismatch} FTM/TTL mismatches found")

    # Check 3: Data completeness
    st.subheader("3. Data Completeness")

    total_pairings = sum(len(bp.get('pairings', [])) for bp in bid_periods)

    pairings_with_issues = 0

    for bp in bid_periods:
        for pairing in bp.get('pairings', []):
            # Check required fields
            if not pairing.get('id'):
                pairings_with_issues += 1
            if not pairing.get('duty_periods'):
                pairings_with_issues += 1
                warnings.append(f"Pairing {pairing.get('id', 'Unknown')} has no duty periods")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pairings", total_pairings)
    with col2:
        st.metric("Pairings with Issues", pairings_with_issues, delta_color="inverse")

    if pairings_with_issues == 0:
        st.success("✅ All pairings have required data")
    else:
        st.warning(f"⚠️ {pairings_with_issues} pairings have data issues")

    # Summary
    st.markdown("---")
    st.subheader("📊 Summary")

    col1, col2 = st.columns(2)

    with col1:
        if issues:
            st.error(f"**{len(issues)} Critical Issues Found:**")
            for issue in issues:
                st.write(f"- {issue}")
        else:
            st.success("**No critical issues found!**")

    with col2:
        if warnings:
            st.warning(f"**{len(warnings)} Warnings:**")
            for warning in warnings[:10]:  # Show first 10
                st.write(f"- {warning}")
            if len(warnings) > 10:
                st.write(f"... and {len(warnings) - 10} more")
        else:
            st.info("**No warnings**")

# ============================================================================
# FOOTER
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Export")

if st.sidebar.button("📥 Download Full Report"):
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'pdf_file': str(selected_pdf),
        'json_file': str(selected_json),
        'summary': {
            'bid_periods': len(bid_periods),
            'total_pairings': sum(len(bp.get('pairings', [])) for bp in bid_periods)
        }
    }

    report_json = json.dumps(report, indent=2)
    st.sidebar.download_button(
        label="Download JSON Report",
        data=report_json,
        file_name=f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

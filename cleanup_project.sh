#!/bin/bash
# Project Cleanup Script
# This script removes unnecessary files and organizes the project structure

echo "=========================================="
echo "Pairing Parser - Project Cleanup"
echo "=========================================="
echo ""

# Ask for confirmation
read -p "This will delete old files and backups. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "Starting cleanup..."

# Create archive directory for old docs
mkdir -p archive/old_docs
mkdir -p archive/old_scripts

# Move obsolete markdown files to archive
echo "Archiving old documentation..."
mv DASHBOARD_GUIDE.md archive/old_docs/ 2>/dev/null
mv DASHBOARD_QUICKSTART.md archive/old_docs/ 2>/dev/null
mv DASHBOARD_SETUP.md archive/old_docs/ 2>/dev/null
mv FILTER_FEATURES_ADDED.md archive/old_docs/ 2>/dev/null
mv FINAL_STATUS.md archive/old_docs/ 2>/dev/null
mv GET_STARTED.md archive/old_docs/ 2>/dev/null
mv IMPLEMENTATION_SUMMARY.md archive/old_docs/ 2>/dev/null
mv INSTALL_NOW.md archive/old_docs/ 2>/dev/null
mv LAYOVER_FILTERS_GUIDE.md archive/old_docs/ 2>/dev/null
mv LAYOVER_QUERIES.md archive/old_docs/ 2>/dev/null
mv MONGODB_QUICKSTART.md archive/old_docs/ 2>/dev/null
mv MONGODB_SETUP.md archive/old_docs/ 2>/dev/null
mv MONGODB_UPSERT_COMPLETE.md archive/old_docs/ 2>/dev/null
mv PARSER_FIXES_2025-12-27.md archive/old_docs/ 2>/dev/null
mv PROJECT_COMPLETE.md archive/old_docs/ 2>/dev/null
mv PROJECT_OVERVIEW.md archive/old_docs/ 2>/dev/null
mv PROOF_OF_CONCEPT.md archive/old_docs/ 2>/dev/null
mv QA_GUIDE.md archive/old_docs/ 2>/dev/null
mv QA_QUICK_REFERENCE.md archive/old_docs/ 2>/dev/null
mv QUICK_START.md archive/old_docs/ 2>/dev/null
mv README_DASHBOARD.md archive/old_docs/ 2>/dev/null
mv REPARSE_COMPLETE.md archive/old_docs/ 2>/dev/null
mv START_HERE.md archive/old_docs/ 2>/dev/null
mv UX_DEADHEAD_FIX.md archive/old_docs/ 2>/dev/null
mv VALIDATION_GUIDE.md archive/old_docs/ 2>/dev/null
mv deploy_streamlit_cloud.md archive/old_docs/ 2>/dev/null

# Move obsolete Python scripts to archive
echo "Archiving old scripts..."
mv analytics_examples.py archive/old_scripts/ 2>/dev/null
mv check_connection.py archive/old_scripts/ 2>/dev/null
mv dashboard.py archive/old_scripts/ 2>/dev/null
mv dashboard_with_maps.py archive/old_scripts/ 2>/dev/null
mv debug_duty_periods.py archive/old_scripts/ 2>/dev/null
mv debug_pairing.py archive/old_scripts/ 2>/dev/null
mv fix_layover_stations.py archive/old_scripts/ 2>/dev/null
mv fix_layover_stations_v2.py archive/old_scripts/ 2>/dev/null
mv fix_layover_stations_v3.py archive/old_scripts/ 2>/dev/null
mv qa_annotations.py archive/old_scripts/ 2>/dev/null
mv qa_workbench.py archive/old_scripts/ 2>/dev/null
mv quick_compare.py archive/old_scripts/ 2>/dev/null
mv test_dashboard_ready.py archive/old_scripts/ 2>/dev/null
mv test_installation.py archive/old_scripts/ 2>/dev/null
mv test_layover_logic.py archive/old_scripts/ 2>/dev/null
mv test_mongodb_connection.py archive/old_scripts/ 2>/dev/null
mv test_parser_only.py archive/old_scripts/ 2>/dev/null
mv validate_output.py archive/old_scripts/ 2>/dev/null
mv validate_parsing.py archive/old_scripts/ 2>/dev/null

# Move obsolete shell scripts to archive
mv process_all.sh archive/old_scripts/ 2>/dev/null
mv run_parser.sh archive/old_scripts/ 2>/dev/null
mv setup_path.sh archive/old_scripts/ 2>/dev/null
mv stop_streamlit.sh archive/old_scripts/ 2>/dev/null

# Move obsolete MongoDB query files to archive
mv debug_queries.mongodb.js archive/old_scripts/ 2>/dev/null
mv example_queries.mongodb.js archive/old_scripts/ 2>/dev/null
mv test_queries.mongodb.js archive/old_scripts/ 2>/dev/null

# Move old test PDF to archive
mv ORDDSLMini.pdf archive/old_scripts/ 2>/dev/null

# Remove backup JSON files
echo "Removing backup JSON files..."
rm -f output/*.backup_*.json

# Remove test JSON files
echo "Removing test JSON files..."
rm -f output/test.json
rm -f output/ORD_test.json

# Clean up Python cache
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# Clean up .DS_Store files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Archived files are in:"
echo "  - archive/old_docs/     (old documentation)"
echo "  - archive/old_scripts/  (old Python/shell scripts)"
echo ""
echo "Current project structure:"
echo "  - src/                  (parser source code)"
echo "  - output/               (parsed JSON files)"
echo "  - unified_dashboard.py  (main dashboard)"
echo "  - batch_process.py      (batch processing)"
echo "  - mongodb_import.py     (MongoDB import)"
echo "  - README.md             (project documentation)"
echo ""

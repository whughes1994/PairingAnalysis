# Pairing Parser - Makefile
# Quick commands for common tasks

.PHONY: help install test process-test process-all clean

help:
	@echo "Pairing Parser - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies"
	@echo "  make test         - Run installation test"
	@echo ""
	@echo "Processing:"
	@echo "  make process-test - Process ORDDSLMini.pdf (test)"
	@echo "  make process-all  - Process all PDF files"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean output and logs"
	@echo "  make show-files   - List all PDF files"
	@echo "  make show-output  - List processed files"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Installation complete!"

test:
	@echo "Running installation test..."
	python test_installation.py

process-test:
	@echo "Processing test file (ORDDSLMini.pdf)..."
	python src/main.py -i ORDDSLMini.pdf -o output/test.json -v

process-all:
	@echo "Processing all PDF files..."
	@./process_all.sh

clean:
	@echo "Cleaning output and logs..."
	rm -rf output/*.json
	rm -rf logs/*.log
	@echo "✓ Clean complete!"

show-files:
	@echo "PDF files in Pairing Source Docs:"
	@ls -lh "Pairing Source Docs"/*.pdf

show-output:
	@echo "Processed JSON files:"
	@ls -lh output/*.json 2>/dev/null || echo "No output files yet"

# Individual file processing shortcuts
process-ord:
	python src/main.py -i "Pairing Source Docs/ORDDSL.pdf" -o output/ORD.json

process-den:
	python src/main.py -i "Pairing Source Docs/DENDSL.pdf" -o output/DEN.json

process-iah:
	python src/main.py -i "Pairing Source Docs/IAHDSL.pdf" -o output/IAH.json

process-ewr:
	python src/main.py -i "Pairing Source Docs/EWRDSL.pdf" -o output/EWR.json

process-sfo:
	python src/main.py -i "Pairing Source Docs/SFODSL.pdf" -o output/SFO.json

process-lax:
	python src/main.py -i "Pairing Source Docs/LAXDSL.pdf" -o output/LAX.json

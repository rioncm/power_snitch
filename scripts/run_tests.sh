#!/bin/bash

# Test Runner Script
# This script runs all tests for Power Snitch

# Exit on error
set -e

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error function
error() {
    log "ERROR: $1"
    exit 1
}

# Create test directory if it doesn't exist
if [ ! -d "tests" ]; then
    log "Creating tests directory..."
    mkdir -p tests
fi

# Create test log directory if it doesn't exist
if [ ! -d "test_logs" ]; then
    log "Creating test logs directory..."
    mkdir -p test_logs
fi

# Run unit tests
log "Running unit tests..."
python3 -m unittest tests/test_nut_service.py -v 2>&1 | tee test_logs/unit_tests.log

# Run integration tests
log "Running integration tests..."
python3 -m unittest tests/test_nut_integration.py -v 2>&1 | tee test_logs/integration_tests.log

# Check test results
if [ $? -eq 0 ]; then
    log "All tests passed successfully"
else
    error "Tests failed. Check test_logs directory for details."
fi 
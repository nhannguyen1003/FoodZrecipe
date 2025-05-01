#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Add project root to PYTHONPATH
export PYTHONPATH="$(dirname "$(dirname "$(realpath "$0")")")":$PYTHONPATH

# Define test directories
TEST_ROOT="$(dirname "$(realpath "$0")")"
UNITTEST_DIR="$TEST_ROOT/unittest"
INTEG_DIR="$TEST_ROOT/integ"

# Define test categories and their associated patterns
CONNECTION_PATTERN="test_db_connection.py"
USER_PATTERN="test_user*.py test_auth*.py test_recipe_cascade*.py"
SEARCH_PATTERN="test_recipe_lsh*.py test_search*.py test_recipe*.py"
REPO_PATTERN="test_repository*.py"
SEED_PATTERN="test_seed*.py test_recipe_data*.py test_recipe_quality*.py"
INTEG_PATTERN="test_*.py"
CATEGORY_PATTERN="test_category*.py"

# Function to find test files based on patterns
find_test_files() {
    local search_dir="$1"
    local patterns="$2"
    local results=""
    
    for pattern in $patterns; do
        # Check if pattern contains path separators
        if [[ "$pattern" == */* ]]; then
            # Pattern already includes path - use it as is from TEST_ROOT
            local files=$(find "$TEST_ROOT" -path "*$pattern" 2>/dev/null)
        else
            # Simple pattern - search in specified directory
            local files=$(find "$search_dir" -name "$pattern" 2>/dev/null)
        fi
        
        # Add to results if any files found
        if [[ -n "$files" ]]; then
            if [[ -n "$results" ]]; then
                results="$results $files"
            else
                results="$files"
            fi
        fi
    done
    
    echo "$results"
}

# Function to find test files across all test directories
find_test_files_all_dirs() {
    local patterns="$1"
    local results=""
    
    # Search in all test directories for the pattern
    for dir in "$UNITTEST_DIR" "$INTEG_DIR" "$CATEGORY_DIR"; do
        local files=$(find_test_files "$dir" "$patterns")
        if [[ -n "$files" ]]; then
            if [[ -n "$results" ]]; then
                results="$results $files"
            else
                results="$files"
            fi
        fi
    done
    
    echo "$results"
}

# Build the test file lists based on patterns
CONNECTION_TESTS=$(find_test_files "$UNITTEST_DIR" "$CONNECTION_PATTERN")
USER_TESTS=$(find_test_files "$UNITTEST_DIR" "$USER_PATTERN")
SEARCH_TESTS=$(find_test_files "$UNITTEST_DIR" "$SEARCH_PATTERN")
REPO_TESTS=$(find_test_files_all_dirs "$REPO_PATTERN")
SEED_TESTS=$(find_test_files "$UNITTEST_DIR" "$SEED_PATTERN")
INTEG_TESTS=$(find_test_files "$INTEG_DIR" "$INTEG_PATTERN")
CATEGORY_TESTS=$(find_test_files "$CATEGORY_DIR" "$CATEGORY_PATTERN")

# Combine all test files
ALL_TESTS="$CONNECTION_TESTS $USER_TESTS $SEARCH_TESTS $REPO_TESTS $SEED_TESTS $INTEG_TESTS $CATEGORY_TESTS"

# List of all categories (excluding "all")
CATEGORIES=("connection" "user" "search" "repo" "seed" "integ" "category")

show_categories() {
    echo -e "${BLUE}Available test categories:${NC}"
    
    echo -e "  - ${YELLOW}connection:${NC}"
    for file in $CONNECTION_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}user:${NC}"
    for file in $USER_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}search:${NC}"
    for file in $SEARCH_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}repo:${NC}"
    for file in $REPO_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}seed:${NC}"
    for file in $SEED_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}integ:${NC}"
    for file in $INTEG_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}category:${NC}"
    for file in $CATEGORY_TESTS; do
        echo -e "      $(basename "$file")"
    done
    
    echo -e "  - ${YELLOW}all:${NC} (all tests from categories above)"
}

get_tests_for_category() {
    local category=$1
    
    case "$category" in
        "connection") echo "$CONNECTION_TESTS" ;;
        "user") echo "$USER_TESTS" ;;
        "search") echo "$SEARCH_TESTS" ;;
        "repo") echo "$REPO_TESTS" ;;
        "seed") echo "$SEED_TESTS" ;;
        "integ") echo "$INTEG_TESTS" ;;
        "category") echo "$CATEGORY_TESTS" ;;
        "all") echo "$ALL_TESTS" ;;
        *) echo "" ;;
    esac
}

run_tests() {
    local category=$1
    local files=$(get_tests_for_category "$category")
    
    # Check if it's a valid category
    if [[ -z "$files" ]]; then
        echo -e "${RED}Error: Unknown test category '$category'${NC}"
        show_categories
        exit 1
    fi
    
    # Display the category and files
    echo -e "${BLUE}========== Running Tests: $category ==========${NC}"
    echo -e "${YELLOW}Test files:${NC}"
    for file in $files; do
        echo "  - $(basename "$file")"
    done
    echo
    
    # Run the tests
    python -m pytest $files -v
    
    # Check exit status
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests in category '$category' passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests in category '$category' failed!${NC}"
        return 1
    fi
}

run_all_categories() {
    local overall_exit_code=0
    
    echo -e "${BLUE}========== Running All Test Categories ==========${NC}"
    
    # Loop through all categories except "all" to avoid duplication
    for category in "${CATEGORIES[@]}"; do
        echo -e "\n${YELLOW}========================================${NC}"
        run_tests "$category"
        
        # Track exit code but continue running all categories
        if [ $? -ne 0 ]; then
            overall_exit_code=1
        fi
    done
    
    echo -e "\n${BLUE}========== All Test Categories Complete ==========${NC}"
    
    if [ $overall_exit_code -eq 0 ]; then
        echo -e "${GREEN}All test categories passed successfully!${NC}"
    else
        echo -e "${RED}Some test categories failed. See above for details.${NC}"
    fi
    
    return $overall_exit_code
}

# Main script execution
if [[ $# -eq 0 ]]; then
    # No arguments provided, run all categories
    run_all_categories
    exit $?
fi

# If the argument is 'list', just show the categories
if [[ "$1" == "list" ]]; then
    show_categories
    exit 0
fi

# Run the tests for the specified category
run_tests "$1"
exit $? 
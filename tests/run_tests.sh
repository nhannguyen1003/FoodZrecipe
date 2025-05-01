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

# Function to get test files matching a pattern
get_files() {
    local dir="$1"
    local pattern="$2"
    find "$dir" -name "$pattern" 2>/dev/null
}

# Get test files for each category
get_connection_tests() {
    get_files "$UNITTEST_DIR" "test_db_connection.py"
}

get_user_tests() {
    get_files "$UNITTEST_DIR" "test_user*.py"
}

get_search_tests() {
    get_files "$TEST_ROOT" "test_search*.py"
}

get_repo_tests() {
    get_files "$TEST_ROOT" "test_repository.py"
}

get_seed_tests() {
    get_files "$UNITTEST_DIR" "test_seed*.py"
}

get_category_tests() {
    get_files "$TEST_ROOT" "test_category*.py"
}

get_all_tests() {
    get_connection_tests
    get_user_tests
    get_search_tests
    get_repo_tests
    get_seed_tests
    get_category_tests
}

# Show available test categories
show_category_tests() {
    local category="$1"
    local tests
    
    echo -e "  - ${YELLOW}${category}:${NC}"
    
    case "$category" in
        "connection") tests=$(get_connection_tests) ;;
        "user") tests=$(get_user_tests) ;;
        "search") tests=$(get_search_tests) ;;
        "repo") tests=$(get_repo_tests) ;;
        "seed") tests=$(get_seed_tests) ;;
        "category") tests=$(get_category_tests) ;;
        *) tests="" ;;
    esac
    
    if [[ -z "$tests" ]]; then
        echo -e "      (no tests found)"
    else
        while IFS= read -r file; do
            echo -e "      $(basename "$file")"
        done <<< "$tests"
    fi
}

show_categories() {
    echo -e "${BLUE}Available test categories:${NC}"
    
    show_category_tests "connection"
    show_category_tests "user"
    show_category_tests "search" 
    show_category_tests "repo"
    show_category_tests "seed"
    show_category_tests "category"
    
    echo -e "  - ${YELLOW}all:${NC} (all tests from categories above)"
}

# Run tests for a specific category
run_tests() {
    local category="$1"
    local test_files
    
    case "$category" in
        "connection") test_files=$(get_connection_tests) ;;
        "user") test_files=$(get_user_tests) ;;
        "search") test_files=$(get_search_tests) ;;
        "repo") test_files=$(get_repo_tests) ;;
        "seed") test_files=$(get_seed_tests) ;;
        "category") test_files=$(get_category_tests) ;;
        "all") test_files=$(get_all_tests) ;;
        *) test_files="" ;;
    esac
    
    # Check if category exists and has tests
    if [[ -z "$test_files" ]]; then
        echo -e "${RED}Error: Unknown test category '$category' or no tests found${NC}"
        show_categories
        exit 1
    fi
    
    # Display category and test files
    echo -e "${BLUE}========== Running Tests: $category ==========${NC}"
    echo -e "${YELLOW}Test files:${NC}"
    
    # Create a temporary file for the Python test script with properly quoted paths
    local temp_file=$(mktemp)
    echo "import pytest" > "$temp_file"
    echo "import sys" >> "$temp_file"
    echo "test_files = [" >> "$temp_file"
    
    # Process each file separately
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            echo "  - $(basename "$file")"
            # Add properly quoted path to test_files array in Python script
            echo "    r'$file'," >> "$temp_file"
        fi
    done <<< "$test_files"
    
    echo "]" >> "$temp_file"
    echo "sys.exit(pytest.main(test_files + ['-v']))" >> "$temp_file"
    echo
    
    # Run the tests using the Python script which has properly quoted paths
    echo "Running tests for $category..."
    python "$temp_file"
    
    # Store the result and clean up
    local result=$?
    rm -f "$temp_file"
    
    # Check result
    if [ $result -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests in category '$category' passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests in category '$category' failed!${NC}"
        return 1
    fi
}

# Run all categories
run_all_categories() {
    local all_categories=("connection" "user" "search" "repo" "seed" "category")
    local overall_result=0
    
    echo -e "${BLUE}========== Running All Test Categories ==========${NC}"
    
    for category in "${all_categories[@]}"; do
        local test_files
        
        case "$category" in
            "connection") test_files=$(get_connection_tests) ;;
            "user") test_files=$(get_user_tests) ;;
            "search") test_files=$(get_search_tests) ;;
            "repo") test_files=$(get_repo_tests) ;;
            "seed") test_files=$(get_seed_tests) ;;
            "category") test_files=$(get_category_tests) ;;
            *) test_files="" ;;
        esac
        
        # Skip empty categories
        if [[ -z "$test_files" ]]; then
            echo -e "\n${YELLOW}========================================${NC}"
            echo -e "${BLUE}Skipping empty category: $category${NC}"
            continue
        fi
        
        echo -e "\n${YELLOW}========================================${NC}"
        run_tests "$category"
        
        # Track overall result
        if [ $? -ne 0 ]; then
            overall_result=1
        fi
    done
    
    echo -e "\n${BLUE}========== All Test Categories Complete ==========${NC}"
    
    if [ $overall_result -eq 0 ]; then
        echo -e "${GREEN}All test categories passed successfully!${NC}"
    else
        echo -e "${RED}Some test categories failed. See above for details.${NC}"
    fi
    
    return $overall_result
}

# Main script execution
if [[ $# -eq 0 ]]; then
    # No arguments, run all categories
    run_all_categories
    exit $?
fi

# Check for 'list' command
if [[ "$1" == "list" ]]; then
    show_categories
    exit 0
fi

# Run specified category
run_tests "$1"
exit $? 
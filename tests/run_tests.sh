#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Add project root to PYTHONPATH
export PYTHONPATH="$(dirname "$(dirname "$(realpath "$0")")")":$PYTHONPATH

# Define test categories and their associated files
# Using simple variables instead of associative arrays for compatibility
CONNECTION_TESTS="tests/test_db_connection.py"
USER_TESTS="tests/test_user_model.py tests/test_auth.py tests/test_recipe_cascade.py"
SEARCH_TESTS="tests/test_recipe_lsh.py tests/test_search.py tests/test_recipe.py"
REPO_TESTS="tests/test_repository.py"
# ALL_TESTS is a combination of all other test categories
ALL_TESTS="$CONNECTION_TESTS $USER_TESTS $SEARCH_TESTS $REPO_TESTS"

# List of all categories (excluding "all")
CATEGORIES=("connection" "user" "search" "repo")

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
    
    echo -e "  - ${YELLOW}all:${NC}"
    for file in $ALL_TESTS; do
        echo -e "      $(basename "$file")"
    done
}

get_tests_for_category() {
    local category=$1
    
    case "$category" in
        "connection") echo "$CONNECTION_TESTS" ;;
        "user") echo "$USER_TESTS" ;;
        "search") echo "$SEARCH_TESTS" ;;
        "repo") echo "$REPO_TESTS" ;;
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
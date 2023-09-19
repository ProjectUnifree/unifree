#!/usr/bin/env bash
#
# launch.sh
#

export PROJECT_NAME="${PROJECT_NAME:-unifree}"

#########################################################
# Override variables as needed.                         #
# This is the only section that should be modified.     #
#########################################################

setup_defaults()
{
    export INSTALL_DIR="${INSTALL_DIR:-$1}"
    export CLONE_DIR="${CLONE_DIR:-$2}"
    export USE_VENV="${USE_VENV:-true}"
    export VENV_DIR="${VENV_DIR:-${CLONE_DIR}/venv}"

    export PROJECT_GIT_URL="${PROJECT_GIT_URL:-https://github.com/ProjectUnifree/unifree.git}"
    export PROJECT_GIT_BRANCH="${PROJECT_GIT_BRANCH:-main}"

    export GIT_CMD="${GIT_CMD:-git}"
    export PYTHON_CMD="${PYTHON_CMD:-python3}"
    export PIP_CMD="${PIP_CMD:-pip3}"
    export PIP_REQUIREMENTS_FILE="${PIP_REQUIREMENTS_FILE:-${CLONE_DIR}/requirements.txt}"
}

#########################################################
# End of variables to override.                         #
# Do not modify anything below this line.               #
#########################################################

### Helper Functions

usage() {
    echo "Usage: ./launch.sh <config_name> <source_directory> <destination_directory>"
    echo "  config_name can be one of: 'godot','unreal'."
    echo "  The environment variable OPENAI_API_KEY must also be defined."
    exit 1
}

check_empty() {
    if [[ -z "$1" ]]; then
        echo "$2 cannot be empty."
        usage
    fi
}

remove_trailing_slash_if_needed() {
    local input="$1"

    # Use parameter expansion to remove trailing slash (if present)
    echo "${input%/}"
}

is_already_cloned_repo() {
    local dir="$1"
    if [[ -f "${dir}/unifree/free.py" ]]; then
        return 0  # project files exist
    else
        return 1  # project files don't exist
    fi
}

is_cmd_installed() {
    if ! command -v "${1}" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

cd_and_assert() {
    cd "$1" || print_red "Could not change directory to $1"
}

print_red() {
    local input="$1"
    echo -e "\033[1;31m${input}\033[0m"
    exit 1
}

print_green() {
    local input="$1"
    echo -e "\033[1;32m${input}\033[0m"
}

print_blue() {
    local input="$1"
    echo -e "\033[1;34m${input}\033[0m"
}

print_delimiter() {
    echo "------------------------------------------------------------"
    echo ""
}

fail_if_root() {
    if [[ "$EUID" -eq 0 ]]; then
        print_red "Please do not run this script as root."
    fi
}

assert_dependencies_installed() {
    if is_cmd_installed "${GIT_CMD}"; then
        print_red "Git is not installed. Given command was (${GIT_CMD}). Please install git and try again."
    fi

    if is_cmd_installed "${PYTHON_CMD}"; then
        print_red "Python is not installed. Please install python and try again."
    fi

    if ! "${PYTHON_CMD}" -c "import venv"; then
        print_red "Python venv is not installed. Please install python venv and try again."
    fi
}

activate_venv() {
    if [[ "${USE_VENV}" != "true" ]]; then
        return
    fi

    print_blue "Creating and activating python venv..."
    "${PYTHON_CMD}" -m venv "${VENV_DIR}"
    source "${VENV_DIR}/bin/activate"
}

install_and_activate_venv_if_needed() {
    if [[ -f "${CLONE_DIR}/.installed" ]]; then
        print_blue "Already installed."

        activate_venv
        cd_and_assert "${CLONE_DIR}"

        return
    fi

    assert_dependencies_installed

    print_blue "Installing to ${INSTALL_DIR}..."

    cd_and_assert "${INSTALL_DIR}"
    cd "${SRC_DIR}"

    if is_already_cloned_repo "$SRC_DIR"; then
        echo "Already cloned repo."
    else
        print_blue "Cloning git repo ${PROJECT_GIT_URL} to ${CLONE_DIR}..."

        if [[ -d "${CLONE_DIR}" ]]; then
            print_green "Directory ${CLONE_DIR} already exists."
        else
            "${GIT_CMD}" clone -b "${PROJECT_GIT_BRANCH}" "${PROJECT_GIT_URL}" "${CLONE_DIR}"
        fi
    fi

    print_delimiter

    activate_venv
    cd_and_assert "${CLONE_DIR}"

    "${PIP_CMD}" install -r "${PIP_REQUIREMENTS_FILE}"

    if [[ -d "${CLONE_DIR}/vendor/tree-sitter-c-sharp" ]]; then
        print_green "Directory ${CLONE_DIR}/vendor/tree-sitter-c-sharp already exists. Skipping cloning..."
    else
        echo "Cloning git repo tree-sitter-c-sharp..."
        mkdir -p "${CLONE_DIR}/vendor"
        "${GIT_CMD}" clone https://github.com/tree-sitter/tree-sitter-c-sharp.git "${CLONE_DIR}/vendor/tree-sitter-c-sharp"
    fi

    # Create the `.installed` file to indicate this process is complete.
    touch .installed
    echo "Installation done."
}

### Start of main script.

set -e

# Load arguments to variables. These can be empty if we're just installing.
export CONFIG_NAME="$1"
export ORIGIN_DIR="$2"
export DEST_DIR="$3"

# Load the setup config based on OS type
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Mac OS"
fi

# Check if the script is being run as root
fail_if_root

print_delimiter

# Get the absolute path of the directory where this script is located
SRC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if is_already_cloned_repo "$SRC_DIR"; then
    export DEFAULT_CLONE_DIR="${SRC_DIR}"
else
    export DEFAULT_CLONE_DIR="${SRC_DIR}/${PROJECT_NAME}"
fi

setup_defaults "${SRC_DIR}" "${DEFAULT_CLONE_DIR}"
export INSTALL_DIR="$(remove_trailing_slash_if_needed ${INSTALL_DIR})"
export CLONE_DIR="$(remove_trailing_slash_if_needed ${CLONE_DIR})"

install_and_activate_venv_if_needed

print_delimiter

# Exit if arguments aren't defined.
if [[ -z "${ORIGIN_DIR}" ]]; then
    print_green "Installing only, run with ./launch.sh <config_name> <source_directory> <destination_directory>."
    exit 0
fi

check_empty "${CONFIG_NAME}" "Argument <config_name>"
check_empty "${ORIGIN_DIR}" "Argument <source_directory>"
check_empty "${DEST_DIR}" "Argument <destination_directory>"
check_empty "${OPENAI_API_KEY}" "Environment variable OPENAI_API_KEY"

# Define PYTHONPATH so unifree import works in Python.
export PYTHONPATH="${CLONE_DIR}"

set -x
"${PYTHON_CMD}" "${CLONE_DIR}/unifree/free.py" \
                -c "${CONFIG_NAME}" \
                -k "${OPENAI_API_KEY}" \
                -s "${ORIGIN_DIR}" \
                -d "${DEST_DIR}"

#!/usr/bin/env bash
set -e

export PROJECT_NAME="${PROJECT_NAME:-unifree}"

# Get the absolute path of the directory where this script is located
SRC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

setup_defaults()
{

    #########################################################
    # Override variables as needed                          #
    # This is the only section that should be modified      #
    #########################################################
    export INSTALL_DIR="${INSTALL_DIR:-$1}"
    export CLONE_DIR="${CLONE_DIR:-$2}"
    export USE_VENV="${USE_VENV:-true}"
    export VENV_DIR="${VENV_DIR:-${CLONE_DIR}/venv}"

    # TODO: move this to the https repo once it is public
    export PROJECT_GIT_URL="${PROJECT_GIT_URL:-git@github.com:ProjectUnifree/unifree.git}"

    # TODO: move this to the release branch or tag once it is public
    export PROJECT_GIT_BRANCH="${PROJECT_GIT_URL:-main}"

    export GIT_CMD="${GIT_CMD:-git}"
    export PYTHON_CMD="${PYTHON_CMD:-python3}"
    export PIP_CMD="${PIP_CMD:-pip3}"
    export PIP_REQUIREMENTS_FILE="${PIP_REQUIREMENTS_FILE:-${CLONE_DIR}/requirements.txt}"
    #########################################################
    # end of variables to override                          #
    #########################################################

}










#########################################################
# Do not modify anything below this line                #
#########################################################

# Load the setup config based on OS type
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Mac OS"
fi

#########################################################
# helper functions                                      #
#########################################################
remove_trailing_slash() {
    local input="$1"

    # Use parameter expansion to remove trailing slash (if present)
    echo "${input%/}"
}

is_already_cloned_repo() {
    local dir="$1"
    if [ -f "${1}/unifree/free.py" ]; then
        return 0  # project files exist
    else
        return 1  # project files exist
    fi
}

is_cmd_installed() {
    if ! command -v "${1}" &> /dev/null
    then
        return 0
    else
        return 1
    fi
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
    if [ "$EUID" -eq 0 ]; then
        print_red "Please do not run this script as root."
    fi
}

activate_venv() {
    if [[ "${USE_VENV}" == "true" ]]; then
        # create and activate venv
        print_blue "Creating and activating python venv"
        "${PYTHON_CMD}" -m venv "${VENV_DIR}"
        source "${VENV_DIR}/bin/activate"
    fi
}

#########################################################
# end of helper functions                               #
#########################################################



# Check if the script is being run as root
fail_if_root

print_delimiter

if is_already_cloned_repo $SRC_DIR; then
    export DEFAULT_CLONE_DIR="${SRC_DIR}"
else
    export DEFAULT_CLONE_DIR="${SRC_DIR}/${PROJECT_NAME}"
fi

setup_defaults "${SRC_DIR}" "${DEFAULT_CLONE_DIR}"

export CONFIG_NAME="$1"
export ORIGIN_DIR="$2"
export DEST_DIR="$3"

if [[ -f "${CLONE_DIR}/.installed" ]]; then
    print_blue "Already installed."
    activate_venv
    cd "${CLONE_DIR}" || print_red "Could not change directory to ${CLONE_DIR}"
    print_delimiter
else

    # Check if git is installed
    if is_cmd_installed "${GIT_CMD}"; then
        print_red "Git is not installed. Given command was (${GIT_CMD}). Please install git and try again."
    fi

    # Check if python is installed
    if is_cmd_installed "${PYTHON_CMD}" -eq 1 ]]; then
        print_red "Python is not installed. Please install python and try again."
    fi

    # check if python venv is installed
    "${PYTHON_CMD}" -c "import venv"
    if [[ "$?" -ne 0 ]] ; then
        print_red "Python venv is not installed. Please install python venv and try again."
    fi

    print_blue "Installing to ${INSTALL_DIR}"

    export INSTALL_DIR="$(remove_trailing_slash ${INSTALL_DIR})"
    cd "${INSTALL_DIR}" || print_red "Could not change directory to ${INSTALL_DIR}"
    cd "${SRC_DIR}"

    if is_already_cloned_repo $SRC_DIR; then
        echo "Already cloned repo"
    else
        export CLONE_DIR="$(remove_trailing_slash ${CLONE_DIR})"
        print_blue "Cloning git repo ${PROJECT_GIT_URL} to ${CLONE_DIR}"

        if [[ -d "${CLONE_DIR}" ]]; then
            print_green "Directory ${CLONE_DIR} already exists."
        else
            "${GIT_CMD}" clone -b "${PROJECT_GIT_BRANCH}" "${PROJECT_GIT_URL}" "${CLONE_DIR}"
        fi
    fi

    cd "${CLONE_DIR}" || print_red "Could not change directory to ${CLONE_DIR}"
    cd "${SRC_DIR}"

    print_delimiter

    activate_venv

    "${PIP_CMD}" install -r "${PIP_REQUIREMENTS_FILE}"
    mkdir -p "${CLONE_DIR}/vendor"
    if [[ -d "${CLONE_DIR}/vendor/tree-sitter-c-sharp" ]]; then
        print_green "Directory ${CLONE_DIR}/vendor/tree-sitter-c-sharp already exists. Skipping cloning"
    else
        "${GIT_CMD}" clone https://github.com/tree-sitter/tree-sitter-c-sharp.git "${CLONE_DIR}/vendor/tree-sitter-c-sharp"
    fi

    touch .installed

    if [[ -z "${ORIGIN_DIR}" ]]; then
        print_green "Installing only, run with \"$0 <source_dir> <destination_dir>\""
        exit 0
    fi
fi

export PYTHONPATH="${CLONE_DIR}"

usage_msg="Usage: $0 <config_name> <source_dir> <destination_dir>"

if [[ -z "${CONFIG_NAME}" ]]; then
    print_red "$usage_msg"
fi

if [[ -z "${ORIGIN_DIR}" ]]; then
    print_red "$usage_msg"
fi

if [[ -z "${DEST_DIR}" ]]; then
    print_red "$usage_msg"
fi

if [[ -z "${OPENAI_API_KEY}" ]]; then
    print_red "The environment variable OPENAI_API_KEY is not set. Please set it and try again."
fi

set -x
"${PYTHON_CMD}" "${CLONE_DIR}/unifree/free.py" -c "${CONFIG_NAME}" -k "${OPENAI_API_KEY}" -s "${ORIGIN_DIR}" -d "${DEST_DIR}"

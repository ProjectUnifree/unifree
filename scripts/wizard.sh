#!/usr/bin/env bash
set -e
#########################################
#               Please Read!            #
# This script will not run standalone,  #
# please use launch.sh.                 #
#########################################

#########################################################
# helper functions                                      #
#########################################################

print_user_input_query() {
    local question="$1"
    local default_answer="$2"
    local msg="\033[1;36m${question}\033[0m"
    [[ ! -z "$default_answer" ]] && msg="${msg} [\033[2;37m${default_answer}\033[0m]"
    msg="${msg}:"
    echo -e "${msg}"
}

#########################################################
# end of helper functions                               #
#########################################################

# Wizard Code
AVAILABLE_CONFIGS=("godot" "unreal")

print_green "Welcome to the unifree Wizard!"
print_green "Please answer a couple of questions so that we can get you started!"

# Ask for OpenAPI Key
if [[ -z "$OPENAI_API_KEY" ]]; then
    while [[ $OPENAI_API_KEY_TMP = "" ]]; do
        print_user_input_query "What is your OpenAPI key?"
        read OPENAI_API_KEY_TMP
    done
    OPENAI_API_KEY="${OPENAI_API_KEY_TMP}"
else
    print_user_input_query "What is your OpenAPI key?" "${OPENAI_API_KEY}"
    read OPENAI_API_KEY_TMP
    : ${OPENAI_API_KEY_TMP:=$OPENAI_API_KEY}
fi

# Ask for the source Unity path
while [[ $ORIGIN_DIR = "" ]]; do
    print_user_input_query "Full path of the source Unity project"
    read ORIGIN_DIR
    # TODO: check if directory exists?
done

# Ask for the Destenation path
while [[ $DEST_DIR = "" ]]; do
    print_user_input_query "Full path of the target destination path"
    read DEST_DIR
    # TODO: check if directory exists?
done


# Ask for the target engine
while [[ $CONFIG_NAME = "" ]]; do
    print_user_input_query "What language would you like to translate it to?"
    for idx in "${!AVAILABLE_CONFIGS[@]}"; do
        echo -e "   [${idx}] ${AVAILABLE_CONFIGS[$idx]}"
    done
    read CONFIG_NAME

    # Check wether the user actually selected an exists config
    expr='^[0123456789]+$'
    if [[ $CONFIG_NAME =~ $expr && -n "${AVAILABLE_CONFIGS[$CONFIG_NAME]}" ]]; then
        CONFIG_NAME="${AVAILABLE_CONFIGS[$CONFIG_NAME]}"
    else
        echo -e "\033[1;31mUnknwon input ${CONFIG_NAME}.\033[0m"
        CONFIG_NAME=""
    fi
done

print_delimiter

# Print all variables
REQUIRED_PARAMS=("OPENAI_API_KEY" "ORIGIN_DIR" "DEST_DIR" "CONFIG_NAME")
print_green "Parameters for launch:"
for i in "${REQUIRED_PARAMS[@]}"; do
    echo -e "${i}=${!i}"
done

# Continue script with selected parameters
expr='^[YyNn]$'
while [[ ! $RUN_SCRIPT =~ $expr ]]; do
    print_user_input_query "Do you want to continue with these paramters? [y/n]"
    read RUN_SCRIPT
done

expr='^[Nn]$'
if [[ $RUN_SCRIPT =~ $expr ]]; then
    print_green "You can run the following command with the supplied parameters later:"
    echo -e "OPENAI_API_KEY=${OPENAI_API_KEY} ./launch.sh ${CONFIG_NAME} ${ORIGIN_DIR} ${DEST_DIR}"
    exit 0
fi
#!/bin/bash
red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
reset=`tput sgr0`

# Create the virtual environment
if [ -d "venv" ]; then
    echo "${green}Virtual environment exists${reset}"
else
    echo "${yellow}Creating Virtual environment${reset}"
    virtualenv --python=python3.8 venv
    echo "${green}Virtual environment created${reset}"
fi

# Update virtual environment
printf "\n${yellow}Updating virtual environment${reset}\n"
venv/bin/pip install -r production_requirements.txt
printf "\n${green}Virtual environment updated${reset}\n\n"

echo "${green}Installation has finished.${reset}"

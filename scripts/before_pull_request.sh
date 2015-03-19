#!/usr/bin/env bash

# BEFORE PULL REQUEST 3000 v0.1
#
# This bash script will do couple of things for you:
#  - validate all modified files if they are according to PEP8 and Booktype JavaScript standard
#  - try to create new Booktype instance
#  - try to initialise new Booktype instance

# Configuration part

SCRIPT_PATH=$(cd `dirname "${BASH_SOURCE[0]}"` && cd .. && pwd)

#DEPLOY_DIRECTORY="/tmp/"
DEPLOY_DIRECTORY=`mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir'`/
INSTANCE_NAME="bk20"
BOOKTYPE_INSTALL="${SCRIPT_PATH}/"

diff_method=1

function pause(){
   read -t 10 -p "$*"
}

# Cleanup function
function cleanup {
 echo -e "\n\n[*] Cleaning up $DEPLOY_DIRECTORY"

 rm -rf $DEPLOY_DIRECTORY
}

# Execute command and check return code
function execute_command {
  $1

  if [ $? -ne 0 ]; then
   echo -e "\n\nError detection"
   echo -e "==========================================================="
   echo -e "You have either canceled this script or we failed to finish"
   echo -e "one of the tasks. If it is second please check what it is"
   echo -e "and fix it before sending Pull Request."

   exit 1
  fi
}

# Create Python Virtual Environment
function create_virtual {
  NAME="${DEPLOY_DIRECTORY}${INSTANCE_NAME}"
  execute_command "virtualenv --distribute $NAME"
}

# Install requirements for development profile
function install_requirements {
  execute_command "pip install -r ${BOOKTYPE_INSTALL}requirements/dev.txt"
}

# Create Booktype project
function create_instance {
  NAME="${DEPLOY_DIRECTORY}${INSTANCE_NAME}/${INSTANCE_NAME}"
  execute_command "${BOOKTYPE_INSTALL}scripts/createbooktype  --database sqlite $NAME"
}

# Initialise Booktype project
# TODO:
#   - use something else instead of createsuperuser
function init_instance {
  execute_command "./manage.py syncdb --noinput"
  execute_command "./manage.py migrate"
  execute_command "./manage.py createsuperuser"
  execute_command "./manage.py update_permissions"
  execute_command "./manage.py update_default_roles"
  execute_command "./manage.py collectstatic"
}

# Start Booktype tests
function start_tests {
  cd "${BOOKTYPE_INSTALL}tests"

  execute_command "./start_tests.sh"
  execute_command "./start_functests.sh"
  execute_command "./start_seleniumtests.sh"
}

# Check changed files if they are according to Booktype standard
function git_changes {
  num=0

  case $diff_method in
   1) COMMAND="git diff --name-only --staged"
      echo -e "[*] Checking only staged files"
      ;;
   2) COMMAND="git diff --name-only"
      echo -e "[*] Checking only non staged files"
      ;;
   3) COMMAND="git status --porcelain | sed s/^...//"
      echo -e "[*] Checking all modified files"
      ;;
  esac

   while read line ; do 
     FILE_NAME=${line}

     if [[ $line == *.py ]]; then

       CHANGES=$( pep8 -qq --count --ignore=E501 --exclude='*migrations*' "${BOOKTYPE_INSTALL}${FILE_NAME}" 2>&1 )

       if [[ $CHANGES -gt 0 ]]; then
         echo "    [PEP8]   ${BOOKTYPE_INSTALL}${FILE_NAME}"
         ((num++))
       fi
    fi
   
    if [[ $line == *.js ]]; then
     CHANGES=$( jshint --config ${BOOKTYPE_INSTALL}scripts/jshintrc "${BOOKTYPE_INSTALL}${FILE_NAME}" 2>&1 > /dev/null )
    
     if [[ $? -ne 0 ]]; then
         echo "    [jshint] ${BOOKTYPE_INSTALL}${FILE_NAME}"
         ((num++))
     fi
    fi
  done<<EOF
$(eval $COMMAND)
EOF

  if [[ $num -eq 0 ]]; then
    echo -e "    Seems like all the files are according to PEP8 and Booktype JavaScript standard."
  else
    echo -e "\n    Some of the files are not according to PEP8 or Booktype JavaScript standard. Fix the style only in your code."
    echo -e "    Create new ticket if style is broken in someone else's code and fix it later.\n"
    echo -e "    Please check:"
    echo -e "        - http://legacy.python.org/dev/peps/pep-0008/"
    echo -e "        - Booktype docs 'docs/development/style.rst'"
    echo -e "        - Booktype docs 'docs/development/js_style.rst'"
  fi

  echo
}

function show_help {
  echo "BEFORE PULL REQUEST 3000"
  echo "------------------------------------------------------------------"
  echo "It is recommended to run this utility before sending pull request."
  echo ""
  echo "Arguments:"
  echo "  -s) check staged files [default]"
  echo "  -n) check non staged files"
  echo "  -m) check modified files"
}

function app_exists {
  $1 >/dev/null 2>&1 

  if [[ $? -eq 127 ]]; then
    echo -e "[ERROR] Application $1 does not exists. Please install it before you continue."
    exit 1
  fi
}

function check_dependencies {
  app_exists git
  app_exists pep8
  app_exists jshint
}

# Parse the arguments

while getopts "h?snm" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    s) diff_method=1 # STAGED
        ;;
    n) diff_method=2 # NOT STAGED
        ;;
    m) diff_method=3 # MODIFIED
        ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

echo "BEFORE PULL REQUEST 3000"
echo "--------------------------------------------------------"

trap cleanup 0
trap cleanup ERR

# Check if we have installed dependencies
check_dependencies

# Check for the modified files
git_changes

# Start with demo instance deployment
pause "Press [Enter] key to start deployment..."

# Create Python Virtual Environment
echo -e "\n[*] Creating Virtual Environment"
create_virtual

cd "${DEPLOY_DIRECTORY}${INSTANCE_NAME}/"

# Activate  environment
echo -e "\n[*] Activate Virtual Environment"
source bin/activate

# Install required python packages
echo -e "\n[*] Install required python packages"
install_requirements

# Create Booktype instance
echo -e "\n[*] Create Booktype instance"
create_instance

cd ${DEPLOY_DIRECTORY}${INSTANCE_NAME}/${INSTANCE_NAME}

# Initialise Booktype instance
echo -e "\n[*] Initialise Booktype instance"
init_instance

# Start the tests
echo -e "\n[*] Start the tests"
start_tests

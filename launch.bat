::
:: launch.bat
::

@echo off
setlocal enabledelayedexpansion

set PROJECT_NAME=unifree
:: Assuming the script's location is the current directory
set SRC_DIR=%~dp0

:: #######################################################
:: Override variables as needed                          #
:: This is the only section that should be modified      #
:: #######################################################

set INSTALL_DIR=%SRC_DIR%
set CLONE_DIR=%INSTALL_DIR%\%PROJECT_NAME%
set VENV_DIR=%CLONE_DIR%\venv
set USE_VENV=true
set PROJECT_GIT_URL="https://github.com/ProjectUnifree/unifree.git"
set PROJECT_GIT_BRANCH=main
set PYTHON_CMD=python.exe

:: #######################################################
:: End of variables to override                          #
:: Do not modify anything below this line                #
:: #######################################################

goto Start

:: Helper Functions

:Usage
    echo "Usage: launch.bat <openai_api_key> <config_name> <source_directory> <destination_directory>"
    echo "  config_name can be one of: 'godot' 'unreal'."
    :: The following line returns to where this label was 'call'ed.
    goto:eof

:Check_Empty
    if "%~1"=="" (
        echo "%~2 cannot be empty."
        call :Usage
        :: Mark that we should exit from the script. Exit only works from the top level.
        set %~3=1
    )
    goto:eof

:Try_Install_Dependencies
    :: Check for git installation
    where git >nul 2>&1
    if %errorlevel% neq 0 (
        echo Git is not found.

        where winget >nul 2>&1
        if %errorlevel% neq 0 (
            echo Please install Git and try again.
            set %~1=1
            goto:eof
        ) else (
            echo Installing Git ...
            winget install Git.Git
        )
    )

    :: Check for python installation
    where "%PYTHON_CMD%" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python is not found.

        where winget >nul 2>&1
        if %errorlevel% neq 0 (
            echo Please install Python and try again.
            set %~1=1
            goto:eof
        ) else (
            echo Installing Python ...
            winget install Python.Python.3.11
        )
    )

    :: Check that pip is installed
    "%PYTHON_CMD%" -m ensurepip
    if %errorlevel% neq 0 (
        echo Installing pip ...
        "%PYTHON_CMD%" -m ensurepip --upgrade
    )

    goto:eof

:Activate_Venv
    if "%USE_VENV%"=="true" (
        echo Creating and activating venv ...
        "%PYTHON_CMD%" -m venv "%VENV_DIR%"
        call "%VENV_DIR%\Scripts\activate.bat"
    )

    goto:eof

:Install_And_Activate_Venv_If_Needed
    if exist "%CLONE_DIR%\.installed" (
        echo Project is already installed.
        
        cd "%CLONE_DIR%"
        call :Activate_Venv

        goto:eof
    )

    call :Try_Install_Dependencies SHOULD_EXIT
    if !SHOULD_EXIT! neq 0 exit /b 1

    :: Clone repo if not exists
    if exist "%CLONE_DIR%\unifree\free.py" (
        echo Directory "%CLONE_DIR%" already exists.
    ) else (
        echo Cloning git repo "%PROJECT_GIT_URL%" to "%CLONE_DIR%"
        git clone -b "%PROJECT_GIT_BRANCH%" "%PROJECT_GIT_URL%" "%CLONE_DIR%"
    )

    cd "%CLONE_DIR%"

    call :Activate_Venv

    pip.exe install -r requirements.txt

    if exist "%CLONE_DIR%\vendor\tree-sitter-c-sharp" (
        echo "Directory %CLONE_DIR%\vendor\tree-sitter-c-sharp already exists. Skipping cloning..."
    ) else (
        echo Cloning git repo tree-sitter-c-sharp...
        mkdir "%CLONE_DIR%\vendor\tree-sitter-c-sharp"
        git clone https://github.com/tree-sitter/tree-sitter-c-sharp.git "%CLONE_DIR%\vendor\tree-sitter-c-sharp"
    )

    :: touch .installed file
    echo %date% %time% > .installed
    echo Installation done.

    goto:eof

:Start

echo ------------------------------------------------------------

set OPENAI_API_KEY=%1
set CONFIG_NAME=%2
set ORIGIN_DIR=%3
set DEST_DIR=%4

if exist "%SRC_DIR%\.git" (
    echo Source directory is a git repo, assuming source directory is project source
    set CLONE_DIR=%SRC_DIR%
    set VENV_DIR=!CLONE_DIR!\venv
)

call :Install_And_Activate_Venv_If_Needed

echo ------------------------------------------------------------

:: Exit if no arguments are defined.
if "%OPENAI_API_KEY%"=="" (
    echo "Installing only, run with launch.bat <openai_api_key> <config_name> <source_directory> <destination_directory>."
    exit /b 0
)

call :Check_Empty "%OPENAI_API_KEY%" "Argument - Open AI Api Key" SHOULD_EXIT
if !SHOULD_EXIT! neq 0 exit /b 1

call :Check_Empty "%CONFIG_NAME%" "Argument - Config Name" SHOULD_EXIT
if !SHOULD_EXIT! neq 0 exit /b 1

call :Check_Empty "%ORIGIN_DIR%" "Argument - Origin Directory" SHOULD_EXIT
if !SHOULD_EXIT! neq 0 exit /b 1

call :Check_Empty "%DEST_DIR%" "Argument - Destination Directory" SHOULD_EXIT
if !SHOULD_EXIT! neq 0 exit /b 1

:run_main

set PYTHONPATH=%PYTHONPATH%;!CLONE_DIR!

@echo on
"%PYTHON_CMD%" "%CLONE_DIR%\unifree\free.py" -c "%CONFIG_NAME%" -k "%OPENAI_API_KEY%" -s "%ORIGIN_DIR%" -d "%DEST_DIR%"

exit /b

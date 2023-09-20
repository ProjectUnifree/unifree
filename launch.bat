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
:: TODO: switch to http repo after public
set PROJECT_GIT_URL="https://github.com/dpayne/test.git"
set PROJECT_GIT_BRANCH=main
set PYTHON_CMD=python.exe

:: #######################################################
:: end of variables to override                          #
:: #######################################################

echo ------------------------------------------------------------
echo.

set CONFIG_NAME=%1
set OPENAI_API_KEY=%2
set ORIGIN_DIR=%3
set DEST_DIR=%4

set USAGE_MSG="Usage: %0 <openai_api_key> <config_name> <source_dir> <dest_dir>"

if exist "%CLONE_DIR%\.installed" (
    echo Project is already installed.
    cd "%CLONE_DIR%"
    :: activate venv if exists
    if %USE_VENV%=="true" (
        if exist "%VENV_DIR%\Scripts\activate.bat" (
            echo Activating venv ...
            call "%VENV_DIR%\Scripts\activate.bat"
        )
    )
    goto :run_main
else (
    if "%OPENAI_API_KEY%"=="" (
        echo %USAGE_MSG%
        exit /b 1
    )

    if "%CONFIG_NAME%"=="" (
        echo %USAGE_MSG%
        exit /b 1
    )

    if "%ORIGIN_DIR%"=="" (
        echo %USAGE_MSG%
        exit /b 1
    )

    if "%DEST_DIR%"=="" (
        echo %USAGE_MSG%
        exit /b 1
    )
)

if exist "%SRC_DIR%\.git" (
    echo Source directory is a git repo, assuming source directory is project source
    set CLONE_DIR=%SRC_DIR%
)

:: Check for git installation
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not found.
    goto :install_git
) else (
    goto :git_check_done
)

:install_git

where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo Please install Git and try again.
    exit /b 1
) else (
    echo Installing Git ...
    winget install Git.Git
)

:git_check_done

:: Clone repo if not exists
if not exist "%CLONE_DIR%\unifree\free.py" (
    echo Cloning git repo "%PROJECT_GIT_URL%" to "%CLONE_DIR%"
    git clone -b "%PROJECT_GIT_BRANCH%" "%PROJECT_GIT_URL%" "%CLONE_DIR%"

) else (
    echo Directory "%CLONE_DIR%" already exists.
)

cd "%CLONE_DIR%"

:: Check for python installation
where "%PYTHON_CMD%" >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found.
    goto :install_python
) else (
    goto :python_check_done
)

:install_python

where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo Please install Python and try again.
    exit /b 1
) else (
    echo Installing Python ...
    winget install Python.Python.3.11
)

:python_check_done

if %USE_VENV%=="true" (
    :: Setup venv
    "%PYTHON_CMD%" -m venv "%VENV_DIR%"
    "%VENV_DIR%\Scripts\activate"
)

:: Check that pip is installed
"%PYTHON_CMD%" -m ensurepip
if %errorlevel% neq 0 (
    echo Installing pip ...
    "%PYTHON_CMD%" -m ensurepip --upgrade
)

pip.exe install -r requirements.txt

echo Cloning git repo tree sitter
if not exist "%CLONE_DIR%\vendor\tree-sitter-c-sharp" mkdir "%CLONE_DIR%\vendor\tree-sitter-c-sharp"
git clone https://github.com/tree-sitter/tree-sitter-c-sharp.git "%CLONE_DIR%\vendor\tree-sitter-c-sharp"

:: touch .installed file
echo %date% %time% > .installed
echo Installation done

if "%OPENAI_API_KEY%"=="" (
	echo %USAGE_MSG%
	exit /b 0
)

if "%CONFIG_NAME%"=="" (
	echo %USAGE_MSG%
	exit /b 0
)

if "%ORIGIN_DIR%"=="" (
	echo %USAGE_MSG%
	exit /b 0
)

if "%DEST_DIR%"=="" (
	echo %USAGE_MSG%
	exit /b 1
)

:run_main

@echo on
"%PYTHON_CMD%" "%CLONE_DIR%\unifree\free.py" -c "%CONFIG_NAME%" -k "%OPENAI_API_KEY%" -s "%ORIGIN_DIR%" -d "%DEST_DIR%"

exit /b

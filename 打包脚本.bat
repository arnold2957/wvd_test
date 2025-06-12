@echo OFF
setlocal

set "ANACONDA_PATH=C:\P\Anaconda"

:: 激活Anaconda基础环境
echo Activating Anaconda base environment...
call "%ANACONDA_PATH%\Scripts\activate.bat" base
if errorlevel 1 (
    echo Failed to activate base environment.
    pause
    exit /b 1
)

echo Initializing virtualenvwrapper...
call "%ANACONDA_PATH%\Scripts\virtualenvwrapper.bat"
if errorlevel 1 (
    echo Failed to initialize virtualenvwrapper.
    pause
    exit /b 1
)

echo Activating virtual environment 'vpy' using workon...
call workon vpy
if not defined VIRTUAL_ENV (
    echo Failed to activate virtual environment 'vpy' with workon.
    echo Ensure 'vpy' exists and WORKON_HOME is set correctly.
    pause
    exit /b 1
)
echo Successfully activated 'vpy'. VIRTUAL_ENV is %VIRTUAL_ENV%

echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)



pyinstaller --onedir script.py -n wvd_test

if errorlevel 1 (
    echo Failed to run pyinstaller.
    pause
    exit /b 1
)

echo Script finished.
pause
endlocal
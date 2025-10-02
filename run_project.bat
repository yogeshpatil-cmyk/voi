@echo off
REM ===============================
REM Step 0: Navigate to project folder
REM ===============================
cd /d "C:\Users\sir.yogesh\voi"

REM ===============================
REM Step 1: Initialize Git if not exists
REM ===============================
IF NOT EXIST ".git" (
    git init
    echo Git repository initialized.
) ELSE (
    echo Git repository already exists.
)

REM ===============================
REM Step 2: Configure Git user (only if needed)
REM ===============================
git config --global user.name "yogeshpatil-cmyk"
git config --global user.email "yogesh.patil@finxpert.org"

REM ===============================
REM Step 3: Add files
REM ===============================
git add .

REM ===============================
REM Step 4: Commit changes (if any)
REM ===============================
git diff --cached --quiet
IF %ERRORLEVEL% NEQ 0 (
    git commit -m "Update project files: Streamlit app, dashboard, and supporting files"
    echo Changes committed.
) ELSE (
    echo No changes to commit.
)

REM ===============================
REM Step 5: Set branch to main
REM ===============================
git branch -M main

REM ===============================
REM Step 6: Add GitHub remote if not exists
REM Replace URL with your repo
REM ===============================
git remote | findstr /i "origin" >nul
IF %ERRORLEVEL% NEQ 0 (
    git remote add origin https://github.com/yogeshpatil-cmyk/voi.git
    echo GitHub remote added.
) ELSE (
    echo GitHub remote already exists.
)

REM ===============================
REM Step 7: Push to GitHub
REM ===============================
git push -u origin main

REM ===============================
REM Step 8: Run Streamlit Apps
REM ===============================
start "" streamlit run streamlit_app.py
timeout /t 5
start "" streamlit run dashboard.py

echo ===============================
echo All done! Streamlit apps are running.
echo ===============================
pause

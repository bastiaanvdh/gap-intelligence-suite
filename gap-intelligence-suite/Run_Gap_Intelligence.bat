@echo off
REM Gap Intelligence Suite Launcher
REM ================================

cd /d "C:\Path\To\Projects\Gap Intelligence"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           GAP INTELLIGENCE SUITE v1.0                        ║
echo ║           DemoShop.example Competitor Analysis Tool                    ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.
echo Kies een optie:
echo.
echo [1] Run FULL workflow (crawl + detect + brief) ~15 min
echo [2] Alleen CRAWL competitors                   ~10 min
echo [3] Alleen DETECT gaps                         ~1 min
echo [4] Alleen GENERATE briefs                     ~3 min
echo [5] Open briefs folder
echo [6] Open logs
echo [Q] Quit
echo.

set /p choice="Keuze: "

if "%choice%"=="1" goto full
if "%choice%"=="2" goto crawl
if "%choice%"=="3" goto detect
if "%choice%"=="4" goto brief
if "%choice%"=="5" goto openbriefs
if "%choice%"=="6" goto openlogs
if /i "%choice%"=="q" goto end
goto end

:full
echo.
echo Starting FULL workflow...
python gap_intelligence.py
goto finish

:crawl
echo.
echo Starting CRAWL...
python gap_intelligence.py crawl
goto finish

:detect
echo.
echo Starting DETECT...
python gap_intelligence.py detect
goto finish

:brief
echo.
echo Starting BRIEF generation...
python gap_intelligence.py brief
goto finish

:openbriefs
explorer "output\content_briefs"
goto end

:openlogs
notepad "logs\gap_intelligence.log"
goto end

:finish
echo.
echo ═══════════════════════════════════════════════════════════════
echo DONE!
echo ═══════════════════════════════════════════════════════════════
echo.
echo Briefs: output\content_briefs\
echo Logs:   logs\gap_intelligence.log
echo.
pause
goto end

:end

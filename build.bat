@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo [1/2] 生成网页版 ...
python src\make_web.py || goto :err

echo.
echo [2/2] 打包 exe ...
python -m PyInstaller --onefile -w --name "EazyWatermarker" ^
  --add-data "%CD%\logos;logos" ^
  --collect-all svglib --collect-all rlPyCairo ^
  --exclude-module numpy --exclude-module scipy --exclude-module pandas ^
  --exclude-module matplotlib --exclude-module cv2 --exclude-module IPython ^
  --exclude-module pytest ^
  --distpath "dist" --workpath "build\pyi" --specpath "build\pyi" ^
  src\gui.py || goto :err

echo.
echo 完成：
echo   网页版  build\web\index.html
echo   可执行  dist\EazyWatermarker.exe
pause
exit /b 0

:err
echo.
echo 出错了，看上面的输出。
pause
exit /b 1

@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo.
echo   🎛️  合成器助手 v1.0
echo   ====================
echo   知识库：..\知识库 (296 个片段)
echo   引擎：BM25 + DeepSeek LLM
echo.
echo   【配置 API Key（可选）】
echo   复制 .env.example 为 .env, 填入你的 DeepSeek Key
echo   不配置也能用检索模式查看片段
echo.
echo   启动后请访问: http://127.0.0.1:5050
echo.

python -m app.app
pause

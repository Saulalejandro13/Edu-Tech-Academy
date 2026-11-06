@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [EduTech] Creando entorno virtual...
    py -m venv .venv
    if errorlevel 1 (echo No se pudo crear el entorno. Instala Python 3.11+ & pause & exit /b 1)
)
echo [EduTech] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 (echo ERROR al instalar dependencias. Revisa la conexion a Internet. & pause & exit /b 1)
set PYTHONPATH=src
set DEMO_SEED=1
set DEMO_PASSWORD=DemoSegura2026!
set DATABASE_URL=sqlite:///./edutech.db
echo.
echo EduTech Academy v2 - cinco perfiles con cuentas individuales
echo http://127.0.0.1:8000
 echo Cuentas demo en el README - Contrasena: DemoSegura2026!
echo Para detener, presiona Ctrl+C en esta ventana.
echo.
echo Abre http://127.0.0.1:8000 DESPUES de ver "Application startup complete".
".venv\Scripts\python.exe" -m uvicorn edutech.api.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 (echo No se pudo iniciar. Revisa los mensajes de error anteriores.)
pause

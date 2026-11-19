@echo off
setlocal
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"

rem Usa el Python del entorno virtual si existe; si no, el Python del sistema.
if not exist "%PYTHON%" (
  for /f "delims=" %%P in ('where python 2^>nul') do set "PYTHON_FALLBACK=%%P"
)
if not exist "%PYTHON%" (
  if defined PYTHON_FALLBACK set "PYTHON=%PYTHON_FALLBACK%"
)
if not exist "%PYTHON%" (
  echo No se encontro Python para el backend.
  echo Consulta backend\README.md para instalar los requisitos.
  pause
  exit /b 1
)

echo Cargando rutas y tarifas en qrpass.db...
pushd "%BACKEND_DIR%"
"%PYTHON%" -m app.management import-catalog
if errorlevel 1 (
  popd
  echo No se pudo cargar el catalogo inicial en qrpass.db.
  pause
  exit /b 1
)
popd

set "QR_PASS_SERVE_FRONTEND=1"
set "QR_PASS_CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000"

start "QrPass API" /D "%BACKEND_DIR%" cmd /k ""%PYTHON%" -m uvicorn app.core.main:app --host 127.0.0.1 --port 8000"

echo Esperando a que la API sirva el frontend...
powershell -NoProfile -Command "$limit = (Get-Date).AddSeconds(30); do { try { $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/login.html' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 1 } while ((Get-Date) -lt $limit); exit 1"
if errorlevel 1 (
  echo No se pudo iniciar QrPass en el puerto 8000.
  echo Revisa la ventana QrPass API y comprueba que el puerto este libre.
  pause
  exit /b 1
)

start "" "http://127.0.0.1:8000"

rem El tunel es opcional: solo hace falta para abrir QrPass desde el celular.
set "CLOUDFLARED="
for /f "delims=" %%C in ('where cloudflared 2^>nul') do set "CLOUDFLARED=%%C"
if not defined CLOUDFLARED set "CLOUDFLARED=%ProgramFiles(x86)%\cloudflared\cloudflared.exe"
if not exist "%CLOUDFLARED%" (
  echo.
  echo QrPass ya esta abierto en http://127.0.0.1:8000
  echo cloudflared no esta instalado, asi que no se creo el enlace para el celular.
  echo Para probar desde el celular instala Cloudflare Tunnel y vuelve a ejecutar este archivo.
  echo.
  echo Deja abiertas las dos ventanas mientras uses QrPass.
  pause
  exit /b 0
)

echo.
echo Copia el enlace https://...trycloudflare.com que aparecera a continuacion.
echo Manten esta ventana abierta mientras uses QrPass desde el celular.
echo Este enlace temporal es publico; usalo solo para pruebas.
echo.
"%CLOUDFLARED%" tunnel --url http://localhost:8000

echo.
echo El tunel termino. Cierra tambien la ventana QrPass API para detener el servidor.
pause

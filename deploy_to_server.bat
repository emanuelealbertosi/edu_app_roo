@echo off
SETLOCAL

REM --- Configurazione Server ---
SET SERVER_IP=217.154.2.9
SET SERVER_USER=root
SET DEPLOY_SCRIPT_REMOTE_PATH=/root/deploy_env_only.sh
SET CONFIG_FILES_REMOTE_DIR=/root/edu_app_deployment

REM --- File da copiare (devono essere nella stessa directory di questo .bat) ---
SET COMPOSE_FILE=docker-compose.prod.static.yml
SET NGINX_CONF_MAIN=nginx.conf
SET INDEX_HTML_STATIC=index.html
SET LOGO_FILE=logo.png
SET DEPLOY_SCRIPT_LOCAL=deploy_env_only.sh

ECHO Copia dei file sul server %SERVER_IP% come utente %SERVER_USER%...
ECHO.

REM Creazione della directory di configurazione sul server (se non esiste)
ECHO NOTA: Ti verra' chiesta la password per ogni operazione di copia (scp) e per i blocchi di comandi remoti (ssh).
ECHO Per evitare richieste multiple di password, la soluzione migliore e' configurare l'autenticazione a chiave SSH.
ECHO.

REM --- Comandi remoti iniziali (mkdir, chown) eseguiti in una singola sessione SSH ---
ECHO Esecuzione comandi remoti preliminari sul server (mkdir, chown)...
ssh %SERVER_USER%@%SERVER_IP% "mkdir -p %CONFIG_FILES_REMOTE_DIR% && chown %SERVER_USER%:%SERVER_USER% %CONFIG_FILES_REMOTE_DIR%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO Errore durante la creazione della directory remota o impostazione permessi.
    GOTO :EOF
)
ECHO Directory remota %CONFIG_FILES_REMOTE_DIR% pronta.
ECHO.

REM --- Copia dei file di configurazione (ogni scp chiedera' la password) ---
ECHO Copia di %COMPOSE_FILE% in %CONFIG_FILES_REMOTE_DIR%/ ...
scp .\%COMPOSE_FILE% %SERVER_USER%@%SERVER_IP%:%CONFIG_FILES_REMOTE_DIR%/%COMPOSE_FILE%
IF %ERRORLEVEL% NEQ 0 (ECHO Errore durante la copia di %COMPOSE_FILE%. & GOTO :EOF)

ECHO Copia di %NGINX_CONF_MAIN% in %CONFIG_FILES_REMOTE_DIR%/ ...
scp .\%NGINX_CONF_MAIN% %SERVER_USER%@%SERVER_IP%:%CONFIG_FILES_REMOTE_DIR%/%NGINX_CONF_MAIN%
IF %ERRORLEVEL% NEQ 0 (ECHO Errore durante la copia di %NGINX_CONF_MAIN%. & GOTO :EOF)

ECHO Copia di %INDEX_HTML_STATIC% in %CONFIG_FILES_REMOTE_DIR%/ ...
scp .\%INDEX_HTML_STATIC% %SERVER_USER%@%SERVER_IP%:%CONFIG_FILES_REMOTE_DIR%/%INDEX_HTML_STATIC%
IF %ERRORLEVEL% NEQ 0 (ECHO Errore durante la copia di %INDEX_HTML_STATIC%. & GOTO :EOF)

ECHO Copia di %LOGO_FILE% in %CONFIG_FILES_REMOTE_DIR%/ ...
scp .\%LOGO_FILE% %SERVER_USER%@%SERVER_IP%:%CONFIG_FILES_REMOTE_DIR%/%LOGO_FILE%
IF %ERRORLEVEL% NEQ 0 (ECHO Errore durante la copia di %LOGO_FILE%. & GOTO :EOF)

ECHO.
REM --- Copia dello script di deployment (scp chiedera' la password) ---
ECHO Copia di %DEPLOY_SCRIPT_LOCAL% in %DEPLOY_SCRIPT_REMOTE_PATH% ...
scp .\%DEPLOY_SCRIPT_LOCAL% %SERVER_USER%@%SERVER_IP%:%DEPLOY_SCRIPT_REMOTE_PATH%
IF %ERRORLEVEL% NEQ 0 (ECHO Errore durante la copia di %DEPLOY_SCRIPT_LOCAL%. & GOTO :EOF)

ECHO.
REM --- Comandi remoti finali (dos2unix e chmod) in una singola sessione SSH ---
ECHO Esecuzione comandi remoti finali sullo script %DEPLOY_SCRIPT_REMOTE_PATH% (dos2unix, chmod)...
ssh %SERVER_USER%@%SERVER_IP% "dos2unix %DEPLOY_SCRIPT_REMOTE_PATH% && chmod +x %DEPLOY_SCRIPT_REMOTE_PATH%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO Errore durante dos2unix o chmod sul server.
    ECHO Assicurati che 'dos2unix' sia installato. Lo script potrebbe non essere eseguibile.
    GOTO :EOF
)

ECHO.
ECHO --- Operazioni completate ---
ECHO I file sono stati copiati e lo script di deployment e' stato reso eseguibile.
ECHO Ora puoi connetterti al server via SSH ed eseguire:
ECHO %DEPLOY_SCRIPT_REMOTE_PATH%
ECHO dalla directory %CONFIG_FILES_REMOTE_DIR% (o come configurato nello script di deploy).

ENDLOCAL
GOTO :EOF

:EOF
ECHO.
ECHO Script terminato con errori.
ENDLOCAL
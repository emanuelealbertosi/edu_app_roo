@echo off
SETLOCAL

REM --- Configurazione ---
SET DOCKER_USERNAME=albertosiemanuele
SET IMAGE_PREFIX=edu-app-
SET BACKEND_IMAGE_NAME=%IMAGE_PREFIX%backend
SET FRONTEND_STUDENT_IMAGE_NAME=%IMAGE_PREFIX%frontend-student
SET FRONTEND_TEACHER_IMAGE_NAME=%IMAGE_PREFIX%frontend-teacher
SET FRONTEND_LESSONS_IMAGE_NAME=%IMAGE_PREFIX%frontend-lessons

SET BACKEND_CONTEXT=.
SET FRONTEND_STUDENT_CONTEXT=./frontend-student
SET FRONTEND_TEACHER_CONTEXT=./frontend-teacher
SET FRONTEND_LESSONS_CONTEXT=./frontend-lessons
REM --- Fine Configurazione ---

REM Controlla se il tag è stato fornito come argomento
IF "%~1"=="" (
    echo.
    echo ERROR: Tag non fornito.
    echo.
    echo Uso: %~n0 NOME_TAG
    echo Esempio: %~n0 v1.0.0
    echo.
    exit /b 1
)

SET IMAGE_TAG=%1

echo ======================================================================
echo BUILD E PUSH IMMAGINI DOCKER (con prefisso %IMAGE_PREFIX%)
echo ======================================================================
echo Username Docker Hub: %DOCKER_USERNAME%
echo Tag da utilizzare:   %IMAGE_TAG%
echo ----------------------------------------------------------------------
echo.

REM Login a Docker Hub
echo Effettuando il login a Docker Hub per %DOCKER_USERNAME%...
docker login
SET LOGIN_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: LOGIN_ERRORLEVEL catturato e': [%LOGIN_ERRORLEVEL%]
IF %LOGIN_ERRORLEVEL% EQU 0 (
    echo DEBUG: LOGIN_ERRORLEVEL e' 0. Login OK.
) ELSE (
    echo DEBUG: LOGIN_ERRORLEVEL NON e' 0. Valore: [%LOGIN_ERRORLEVEL%]. Entro nel blocco errore login.
    echo.
    echo ERROR: Login a Docker Hub fallito o annullato con ERRORLEVEL %LOGIN_ERRORLEVEL%.
    echo Impossibile procedere.
    echo.
    exit /b 1
)
echo Login effettuato con successo.
echo.

REM --- Backend ---
SET SERVICE_NAME=Backend
SET IMAGE_FULL_NAME=%DOCKER_USERNAME%/%BACKEND_IMAGE_NAME%:%IMAGE_TAG%
SET CURRENT_BUILD_CONTEXT=%BACKEND_CONTEXT%
echo --- Inizio %SERVICE_NAME% (%IMAGE_PREFIX%backend) ---
echo Building "%IMAGE_FULL_NAME%" from context "%CURRENT_BUILD_CONTEXT%"...
echo Executing: docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
SET BUILD_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: BUILD_ERRORLEVEL catturato per %SERVICE_NAME% e': [%BUILD_ERRORLEVEL%]
IF %BUILD_ERRORLEVEL% EQU 0 (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% e' 0. Build OK. Procedo.
) ELSE (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%BUILD_ERRORLEVEL%]. Entro nel blocco errore build.
    echo.
    echo ERROR: Build di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %BUILD_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Build di %SERVICE_NAME% completato.
echo.
echo Pushing "%IMAGE_FULL_NAME%" su Docker Hub...
docker push "%IMAGE_FULL_NAME%"
SET PUSH_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: PUSH_ERRORLEVEL catturato per %SERVICE_NAME% e': [%PUSH_ERRORLEVEL%]
IF %PUSH_ERRORLEVEL% EQU 0 (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% e' 0. Push OK.
) ELSE (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%PUSH_ERRORLEVEL%]. Entro nel blocco errore push.
    echo.
    echo ERROR: Push di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %PUSH_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Push di %SERVICE_NAME% completato.
echo --- Fine %SERVICE_NAME% ---
echo.

REM --- Frontend Studente ---
SET SERVICE_NAME=Frontend Studente
SET IMAGE_FULL_NAME=%DOCKER_USERNAME%/%FRONTEND_STUDENT_IMAGE_NAME%:%IMAGE_TAG%
SET CURRENT_BUILD_CONTEXT=%FRONTEND_STUDENT_CONTEXT%
echo --- Inizio %SERVICE_NAME% (%IMAGE_PREFIX%frontend-student) ---
echo Building "%IMAGE_FULL_NAME%" from context "%CURRENT_BUILD_CONTEXT%"...
echo Executing: docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
SET BUILD_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: BUILD_ERRORLEVEL catturato per %SERVICE_NAME% e': [%BUILD_ERRORLEVEL%]
IF %BUILD_ERRORLEVEL% EQU 0 (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% e' 0. Build OK. Procedo.
) ELSE (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%BUILD_ERRORLEVEL%]. Entro nel blocco errore build.
    echo.
    echo ERROR: Build di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %BUILD_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Build di %SERVICE_NAME% completato.
echo.
echo Pushing "%IMAGE_FULL_NAME%" su Docker Hub...
docker push "%IMAGE_FULL_NAME%"
SET PUSH_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: PUSH_ERRORLEVEL catturato per %SERVICE_NAME% e': [%PUSH_ERRORLEVEL%]
IF %PUSH_ERRORLEVEL% EQU 0 (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% e' 0. Push OK.
) ELSE (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%PUSH_ERRORLEVEL%]. Entro nel blocco errore push.
    echo.
    echo ERROR: Push di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %PUSH_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Push di %SERVICE_NAME% completato.
echo --- Fine %SERVICE_NAME% ---
echo.

REM --- Frontend Docente ---
SET SERVICE_NAME=Frontend Docente
SET IMAGE_FULL_NAME=%DOCKER_USERNAME%/%FRONTEND_TEACHER_IMAGE_NAME%:%IMAGE_TAG%
SET CURRENT_BUILD_CONTEXT=%FRONTEND_TEACHER_CONTEXT%
echo --- Inizio %SERVICE_NAME% (%IMAGE_PREFIX%frontend-teacher) ---
echo Building "%IMAGE_FULL_NAME%" from context "%CURRENT_BUILD_CONTEXT%"...
echo Executing: docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
SET BUILD_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: BUILD_ERRORLEVEL catturato per %SERVICE_NAME% e': [%BUILD_ERRORLEVEL%]
IF %BUILD_ERRORLEVEL% EQU 0 (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% e' 0. Build OK. Procedo.
) ELSE (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%BUILD_ERRORLEVEL%]. Entro nel blocco errore build.
    echo.
    echo ERROR: Build di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %BUILD_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Build di %SERVICE_NAME% completato.
echo.
echo Pushing "%IMAGE_FULL_NAME%" su Docker Hub...
docker push "%IMAGE_FULL_NAME%"
SET PUSH_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: PUSH_ERRORLEVEL catturato per %SERVICE_NAME% e': [%PUSH_ERRORLEVEL%]
IF %PUSH_ERRORLEVEL% EQU 0 (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% e' 0. Push OK.
) ELSE (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%PUSH_ERRORLEVEL%]. Entro nel blocco errore push.
    echo.
    echo ERROR: Push di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %PUSH_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Push di %SERVICE_NAME% completato.
echo --- Fine %SERVICE_NAME% ---
echo.

REM --- Frontend Lezioni ---
SET SERVICE_NAME=Frontend Lezioni
SET IMAGE_FULL_NAME=%DOCKER_USERNAME%/%FRONTEND_LESSONS_IMAGE_NAME%:%IMAGE_TAG%
SET CURRENT_BUILD_CONTEXT=%FRONTEND_LESSONS_CONTEXT%
echo --- Inizio %SERVICE_NAME% (%IMAGE_PREFIX%frontend-lessons) ---
echo Building "%IMAGE_FULL_NAME%" from context "%CURRENT_BUILD_CONTEXT%"...
echo Executing: docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
docker build -t "%IMAGE_FULL_NAME%" "%CURRENT_BUILD_CONTEXT%"
SET BUILD_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: BUILD_ERRORLEVEL catturato per %SERVICE_NAME% e': [%BUILD_ERRORLEVEL%]
IF %BUILD_ERRORLEVEL% EQU 0 (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% e' 0. Build OK. Procedo.
) ELSE (
    echo DEBUG: BUILD_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%BUILD_ERRORLEVEL%]. Entro nel blocco errore build.
    echo.
    echo ERROR: Build di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %BUILD_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Build di %SERVICE_NAME% completato.
echo.
echo Pushing "%IMAGE_FULL_NAME%" su Docker Hub...
docker push "%IMAGE_FULL_NAME%"
SET PUSH_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: PUSH_ERRORLEVEL catturato per %SERVICE_NAME% e': [%PUSH_ERRORLEVEL%]
IF %PUSH_ERRORLEVEL% EQU 0 (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% e' 0. Push OK.
) ELSE (
    echo DEBUG: PUSH_ERRORLEVEL per %SERVICE_NAME% NON e' 0. Valore: [%PUSH_ERRORLEVEL%]. Entro nel blocco errore push.
    echo.
    echo ERROR: Push di %SERVICE_NAME% ("%IMAGE_FULL_NAME%") fallito con ERRORLEVEL %PUSH_ERRORLEVEL%.
    echo Script interrotto.
    echo.
    exit /b 1
)
echo Push di %SERVICE_NAME% completato.
echo --- Fine %SERVICE_NAME% ---
echo.

echo ======================================================================
echo TUTTE LE OPERAZIONI COMPLETATE CON SUCCESSO!
echo ======================================================================
echo Immagini buildate e pushatet con TAG: %IMAGE_TAG%
echo Username Docker Hub: %DOCKER_USERNAME%
echo Prefisso Immagine: %IMAGE_PREFIX%
echo.

ENDLOCAL
exit /b 0
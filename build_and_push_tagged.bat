@echo off
SETLOCAL

REM --- Configurazione ---
SET DOCKER_USERNAME=albertosiemanuele
SET BACKEND_IMAGE_NAME=backend
SET FRONTEND_STUDENT_IMAGE_NAME=frontend-student
SET FRONTEND_TEACHER_IMAGE_NAME=frontend-teacher
SET FRONTEND_LESSONS_IMAGE_NAME=frontend-lessons

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
echo BUILD E PUSH IMMAGINI DOCKER
echo ======================================================================
echo Username Docker Hub: %DOCKER_USERNAME%
echo Tag da utilizzare:   %IMAGE_TAG%
echo ----------------------------------------------------------------------
echo.

REM Login a Docker Hub
echo Effettuando il login a Docker Hub per %DOCKER_USERNAME%...
docker login
IF ERRORLEVEL 1 (
    echo.
    echo ERROR: Login a Docker Hub fallito o annullato.
    echo Impossibile procedere con il push delle immagini.
    echo.
    exit /b 1
)
echo Login effettuato con successo.
echo.

REM Funzione per buildare e pushare (simulata, dato che batch non ha funzioni vere e proprie)
:BUILD_AND_PUSH_SERVICE
    SET SERVICE_NAME=%~1
    SET IMAGE_FULL_NAME=%~2
    SET BUILD_CONTEXT=%~3

    echo --- Inizio %SERVICE_NAME% ---
    echo Building %IMAGE_FULL_NAME%...
    docker build -t %IMAGE_FULL_NAME% %BUILD_CONTEXT%
    IF ERRORLEVEL 1 (
        echo.
        echo ERROR: Build di %SERVICE_NAME% (%IMAGE_FULL_NAME%) fallito.
        echo Script interrotto.
        echo.
        exit /b 1
    )
    echo Build di %SERVICE_NAME% completato.
    echo.
    echo Pushing %IMAGE_FULL_NAME% su Docker Hub...
    docker push %IMAGE_FULL_NAME%
    IF ERRORLEVEL 1 (
        echo.
        echo ERROR: Push di %SERVICE_NAME% (%IMAGE_FULL_NAME%) fallito.
        echo Script interrotto.
        echo.
        exit /b 1
    )
    echo Push di %SERVICE_NAME% completato.
    echo --- Fine %SERVICE_NAME% ---
    echo.
GOTO :EOF

REM Build e Push per ogni servizio
CALL :BUILD_AND_PUSH_SERVICE "Backend" "%DOCKER_USERNAME%/%BACKEND_IMAGE_NAME%:%IMAGE_TAG%" "%BACKEND_CONTEXT%"
CALL :BUILD_AND_PUSH_SERVICE "Frontend Studente" "%DOCKER_USERNAME%/%FRONTEND_STUDENT_IMAGE_NAME%:%IMAGE_TAG%" "%FRONTEND_STUDENT_CONTEXT%"
CALL :BUILD_AND_PUSH_SERVICE "Frontend Docente" "%DOCKER_USERNAME%/%FRONTEND_TEACHER_IMAGE_NAME%:%IMAGE_TAG%" "%FRONTEND_TEACHER_CONTEXT%"
CALL :BUILD_AND_PUSH_SERVICE "Frontend Lezioni" "%DOCKER_USERNAME%/%FRONTEND_LESSONS_IMAGE_NAME%:%IMAGE_TAG%" "%FRONTEND_LESSONS_CONTEXT%"

echo ======================================================================
echo TUTTE LE OPERAZIONI COMPLETATE CON SUCCESSO!
echo ======================================================================
echo Immagini buildate e pushatet con TAG: %IMAGE_TAG%
echo Username Docker Hub: %DOCKER_USERNAME%
echo.

ENDLOCAL
exit /b 0
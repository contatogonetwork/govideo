@echo off
REM Script de manutenção para GONETWORK AI
REM Este script deve ser agendado para execução periódica

echo Iniciando manutenção do GONETWORK AI em %date% %time%
echo -----------------------------------------------------

cd /d "C:\govideo"
python -m utils.maintenance

echo -----------------------------------------------------
echo Manutenção concluída em %date% %time%

pause

import pytest
from unittest.mock import MagicMock, patch
from galt.engine import orchestrator as runner

# FIX: Apuntamos a 'generate_dashboard' que es el nombre real en tu código
@patch('galt.engine.orchestrator.dashboard_generator.generate_dashboard')
@patch('galt.engine.orchestrator.status_manager.update_status')
@patch('subprocess.Popen')
@patch('builtins.open')
def test_run_security_flow_structure(mock_open, mock_subprocess, mock_update_status, mock_generate_dashboard):
    """
    Test Integration: verifica el flujo principal mockeando dependencias externas.
    Asegura que el sistema reporta SCANNING al inicio y IDLE/ERROR al final.
    """
    # 1. Configurar Mocks
    # Simulamos que el generador devuelve una ruta de archivo
    mock_generate_dashboard.return_value = "c:\\mock\\report.html"
    
    # Simulamos que los sensores (subprocess) devuelven JSON vacío "[]"
    process_mock = MagicMock()
    process_mock.communicate.return_value = ('[]', '')
    mock_subprocess.return_value = process_mock

    # Simulamos los argumentos de línea de comandos para que no pida input manual
    with patch('argparse.ArgumentParser.parse_args') as mock_args:
        args = MagicMock()
        args.auto = True # Modo automático para saltar preguntas
        mock_args.return_value = args

        # 2. EJECUTAR EL RUNNER
        print("DEBUG: Iniciando runner.run_security_flow() bajo test...")
        runner.run_security_flow()

        # 3. VERIFICACIONES
        # Extraemos todos los estados que se enviaron a update_status
        # call_args_list devuelve una lista de llamadas. args[0] es el estado.
        states_called = []
        if mock_update_status.call_count > 0:
            states_called = [call.args[0] for call in mock_update_status.call_args_list]
        
        print(f"DEBUG: Estados reportados por el runner: {states_called}")

        # Validaciones
        # Verificamos que al menos se haya intentado poner en SCANNING
        assert "SCANNING" in states_called, f"ERROR: No se reportó estado SCANNING. Estados: {states_called}"
        
        # Verificamos que terminó (IDLE o ERROR son aceptables como fin)
        finished_correctly = "IDLE" in states_called or "ERROR" in states_called
        assert finished_correctly, f"ERROR: El flujo no terminó en reposo. Estados: {states_called}"
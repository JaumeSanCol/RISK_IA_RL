"""
VALIDACIÓN, TESTING Y TROUBLESHOOTING
=====================================

Este archivo te ayuda a validar la instalación y diagnosticar problemas.
"""

import os
import sys

# ==============================================================================
# SCRIPT DE VALIDACIÓN DEL ENTORNO
# ==============================================================================

def check_installation():
    """
    Verifica que todos los archivos y dependencias estén en su lugar.
    Ejecuta desde el directorio PPO/.
    """
    
    print("="*70)
    print("VALIDACIÓN DE INSTALACIÓN - RL SIMULATION")
    print("="*70)
    
    issues = []
    warnings = []
    
    # 1. Archivos requeridos
    print("\n[1] Verificando archivos...")
    required_files = [
        ('ppo_loader.py', 'Cargador de modelos PPO'),
        ('play_rl_vs_rl.py', 'Script: RL vs RL'),
        ('play_rl_vs_heuristics.py', 'Script: RL vs Heurísticas'),
        ('risk_gym_env.py', 'Entorno de gymnas'),
        ('README_RL_SIMULATION.md', 'Documentación'),
    ]
    
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"  ✓ {filename:30} - {description}")
        else:
            print(f"  ✗ {filename:30} - {description}")
            issues.append(f"Falta archivo: {filename}")
    
    # 2. Directorios
    print("\n[2] Verificando directorios...")
    required_dirs = [
        ('logs_ppo', 'Modelos entrenados'),
        ('../ai', 'IAs heurísticas'),
        ('../logs', 'Logs de partidas'),
    ]
    
    for dirname, description in required_dirs:
        if os.path.isdir(dirname):
            # Contar archivos si es logs_ppo o ai
            if 'logs_ppo' in dirname:
                models = [f for f in os.listdir(dirname) if f.endswith('.zip')]
                print(f"  ✓ {dirname:30} - {description} ({len(models)} modelos)")
                if len(models) == 0:
                    warnings.append(
                        f"No hay modelos en {dirname}/. "
                        "Entrena primero con train_ppo.py"
                    )
            elif 'ai' in dirname:
                ais = [f for f in os.listdir(dirname) if f.endswith('.py')]
                print(f"  ✓ {dirname:30} - {description} ({len(ais)} IAs heurísticas)")
            else:
                print(f"  ✓ {dirname:30} - {description}")
        else:
            print(f"  ✗ {dirname:30} - {description}")
            issues.append(f"Falta directorio: {dirname}")
    
    # 3. Dependencias Python
    print("\n[3] Verificando dependencias...")
    dependencies = [
        ('numpy', 'NumPy'),
        ('gymnasium', 'Gymnasium'),
        ('sb3_contrib', 'Stable-Baselines3 Contrib'),
        ('stable_baselines3', 'Stable-Baselines3'),
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:30} - {description}")
        except ImportError:
            print(f"  ✗ {module_name:30} - {description}")
            issues.append(f"Falta librería: {module_name}")
    
    # 4. Verificar que parent_dir sea accesible
    print("\n[4] Verificando acceso a parent_dir...")
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    if os.path.exists(os.path.join(parent_dir, 'risktools.py')):
        print(f"  ✓ risktools.py encontrado en parent_dir")
    else:
        print(f"  ✗ risktools.py NO encontrado")
        issues.append("No puedo acceder a risktools.py en parent_dir")
    
    if os.path.exists(os.path.join(parent_dir, 'world.zip')):
        print(f"  ✓ world.zip encontrado en parent_dir")
    else:
        print(f"  ✗ world.zip NO encontrado")
        issues.append("No puedo acceder a world.zip en parent_dir")
    
    # 5. Resumen
    print("\n" + "="*70)
    if not issues:
        print("✓ VALIDACIÓN EXITOSA")
        if warnings:
            print(f"\n⚠ {len(warnings)} ADVERTENCIAS:")
            for w in warnings:
                print(f"  - {w}")
    else:
        print(f"✗ {len(issues)} PROBLEMAS ENCONTRADOS:")
        for i in issues:
            print(f"  - {i}")
        if warnings:
            print(f"\n⚠ {len(warnings)} ADVERTENCIAS:")
            for w in warnings:
                print(f"  - {w}")
    print("="*70)
    
    return len(issues) == 0


# ==============================================================================
# TEST RÁPIDO: Cargar un modelo PPO
# ==============================================================================

def test_ppo_loading():
    """
    Intenta cargar el primer modelo PPO encontrado.
    Útil para verificar que el sistema funciona.
    """
    
    print("\n" + "="*70)
    print("TEST: Cargando modelo PPO")
    print("="*70)
    
    try:
        from ppo_loader import PPOPlayer
        
        # Buscar un modelo
        models_dir = 'logs_ppo'
        if not os.path.exists(models_dir):
            print("✗ No existe directorio logs_ppo/")
            return False
        
        models = [f for f in os.listdir(models_dir) if f.endswith('.zip')]
        if not models:
            print("✗ No hay modelos .zip en logs_ppo/")
            return False
        
        model_path = os.path.join(models_dir, models[0])
        print(f"Cargando: {model_path}")
        
        ppo = PPOPlayer(model_path, player_name="TestAgent")
        print(f"✓ Modelo cargado exitosamente: {ppo}")
        
        # Verificar que tiene el método getAction
        if hasattr(ppo, 'getAction'):
            print("✓ Método getAction() disponible")
        else:
            print("✗ Método getAction() NO disponible")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error al cargar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST RÁPIDO: Acceso a risktools
# ==============================================================================

def test_risktools_access():
    """
    Verifica que se puede acceder a risktools y cargar el tablero.
    """
    
    print("\n" + "="*70)
    print("TEST: Acceso a risktools")
    print("="*70)
    
    try:
        # Necesitamos subir un nivel
        parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        import risktools
        print("✓ risktools importado exitosamente")
        
        # Intentar cargar tablero
        try:
            board = risktools.loadBoard("world.zip")
            print(f"✓ Tablero cargado: {len(board.territories)} territorios")
        except Exception as e:
            print(f"✗ No se pudo cargar world.zip: {e}")
            # Intentar desde parent_dir
            world_path = os.path.join(parent_dir, "world.zip")
            if os.path.exists(world_path):
                os.chdir(parent_dir)
                board = risktools.loadBoard("world.zip")
                print(f"✓ Tablero cargado desde parent_dir: {len(board.territories)} territorios")
            else:
                return False
        
        # Verificar RiskPlayer
        player = risktools.RiskPlayer("Test", 0, 0, False, 100, 50, 0.5)
        print(f"✓ RiskPlayer creado: {player.name}")
        
        # Verificar getInitialState
        state = risktools.getInitialState(board)
        print(f"✓ Estado inicial generado: {state.turn_type}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en risktools: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# DIAGNÓSTICO COMPLETO
# ==============================================================================

def run_full_diagnostics():
    """
    Ejecuta todos los tests de validación.
    """
    
    print("\n")
    print("*" * 70)
    print("*" + " "*68 + "*")
    print("*" + " DIAGNÓSTICO COMPLETO DEL SISTEMA RL SIMULATION ".center(68) + "*")
    print("*" + " "*68 + "*")
    print("*" * 70)
    
    results = {
        'installation': check_installation(),
        'ppo_loading': test_ppo_loading(),
        'risktools': test_risktools_access(),
    }
    
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASADO" if passed else "✗ FALLIDO"
        print(f"  {test_name:20} : {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ TODOS LOS TESTS PASADOS - LISTO PARA USAR")
        print("\nSiguientes pasos:")
        print("  1. python play_rl_vs_rl.py logs_ppo/modelo.zip -n 1 -v")
        print("  2. Abre los logs en risk_game_viewer.py")
    else:
        print("✗ ALGUNOS TESTS FALLIERON - VER ARRIBA PARA DETALLES")
        print("\nRecomendaciones:")
        print("  1. Lee las advertencias/errores arriba")
        print("  2. Consulta README_RL_SIMULATION.md sección Troubleshooting")
        print("  3. Ejecuta desde directorio PPO/")
    print("="*70 + "\n")
    
    return all_passed


# ==============================================================================
# GUÍA DE TROUBLESHOOTING INTERACTIVA
# ==============================================================================

def interactive_troubleshooting():
    """
    Guía interactiva para resolver problemas comunes.
    """
    
    print("\n" + "="*70)
    print("GUÍA INTERACTIVA DE TROUBLESHOOTING")
    print("="*70)
    
    issues = {
        '1': {
            'title': 'Error: ModuleNotFoundError: No module named "risktools"',
            'solutions': [
                'Asegúrate de estar en el directorio PPO/',
                'cd PPO',
                'Verifica que exista ../risktools.py',
            ]
        },
        '2': {
            'title': 'Error: FileNotFoundError: Modelo no encontrado',
            'solutions': [
                'Verifica que el archivo .zip existe en logs_ppo/',
                'ls logs_ppo/',
                'Usa ruta relativa desde PPO/',
                'Ejemplo: python play_rl_vs_rl.py logs_ppo/modelo.zip',
            ]
        },
        '3': {
            'title': 'Error: world.zip no encontrado',
            'solutions': [
                'Asegúrate de que ../world.zip existe',
                'Verifica que estás en el directorio PPO/',
                'Si no existe, copia desde la carpeta raíz del proyecto',
            ]
        },
        '4': {
            'title': 'Las IAs juegan acciones inválidas constantemente',
            'solutions': [
                'El modelo puede no estar entrenado correctamente',
                'Intenta reentrenar con train_ppo.py',
                'Reduce los hiperparámetros de dificultad en risk_gym_env.py',
                'Usa -v para ver dónde falla',
            ]
        },
        '5': {
            'title': 'Las partidas terminan muy rápido (1-2 turnos)',
            'solutions': [
                'Hay un error en el bucle del juego',
                'Ejecuta con -v para debug',
                'Verifica que simulateAction() devuelve estados válidos',
            ]
        },
        '6': {
            'title': 'ImportError: cannot import name "RiskTotalControlEnv"',
            'solutions': [
                'Verifica que risk_gym_env.py está en PPO/',
                'Si no existe, restaura desde backup',
                'Restaurar: cp backup_ia/risk_gym_env.py .',
            ]
        },
        '7': {
            'title': 'La GUI no abre los logs generados',
            'solutions': [
                'Verifica que los logs estén en ../logs/',
                'Usa ruta absoluta al risk_game_viewer.py',
                'Revisa que el archivo .log no está corrupto',
                'Prueba con un log conocido que funcione',
            ]
        },
    }
    
    print("\nProblemas comunes:\n")
    for key, issue in issues.items():
        print(f"{key}. {issue['title']}")
    
    print("\nSelecciona número (o 'q' para salir):")
    choice = input("> ").strip()
    
    if choice == 'q':
        return
    
    if choice in issues:
        print("\n" + "-"*70)
        print(f"PROBLEMA: {issues[choice]['title']}")
        print("-"*70)
        print("\nSOLUCIONES:\n")
        for i, solution in enumerate(issues[choice]['solutions'], 1):
            print(f"  {i}. {solution}")
        print()


# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validación y diagnóstico del sistema RL Simulation'
    )
    parser.add_argument(
        'command',
        nargs='?',
        default='all',
        choices=['all', 'install', 'ppo', 'risktools', 'troubleshoot'],
        help='Qué test ejecutar'
    )
    
    args = parser.parse_args()
    
    if args.command == 'all':
        run_full_diagnostics()
    elif args.command == 'install':
        check_installation()
    elif args.command == 'ppo':
        test_ppo_loading()
    elif args.command == 'risktools':
        test_risktools_access()
    elif args.command == 'troubleshoot':
        interactive_troubleshooting()

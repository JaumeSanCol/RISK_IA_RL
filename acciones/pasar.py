from clases.action import RiskAction

def getPasarActions(): # no necesita un simulate
    """Pasamos el turno"""
    return [RiskAction('Pasar', None, None, None)]
  

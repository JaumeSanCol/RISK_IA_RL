# Valores Iniciales

ECON_START=50                   # Dinero Inicial
HAPP_START=50                   # Felicidad Inicial %
DEVP_START=0.1                  # Desarrollo Inicial

IMPUESTOS=1
PENL_DVP_REVOL=-0.5              # Penalización en el desarrollo por Revuelta
PENL_DVP_AUTRT=PENL_DVP_REVOL*2 # Penalización por recurrir al autoritarismo frente a una revuelta
# Acciones

SOLDADOS_PRC=10                 # Precio de contratar un soldado

INVERTIR_PRC=5                  # Precio de Invertir
INVERTIR_DEVP=0.1               # Aumento de desarrollo por inversón

FESTIN_PRC=5                    # Precio de ralizar un Festín
FESTIN_HAPP=5                   # Aumento de feicidad por festín

COMERCIO_DEVP=10                # Ganancia de oro por desarrollo

CASINO_PRC=5                    # Apuesta mínima que puedes hacer en el casino

# Bonos -> Aumentos que se producen por una acción no relacionada directamente.

BONO_HAPP_ECON_EXC=15           # Bono de felicidad por ser el vecino más rico
BONO_HAPP_ECON_MED=5            # Bono de felicidad por no ser el vecino más pobre
BONO_HAPP_ECON_MAL=-10          # Bono de felicidad por ser el vecino más pobre    

BONO_HAPP_HAPP=10               # Bono de felicidad por ser feliz/infeliz

BONO_HAPP_DEVP_EXC=10           # Bono de felicidad por ser el vecino más desarrollado
BONO_HAPP_DEVP_MED=2            # Bono de felicidad por no ser el vecino más desarrollado

BONO_HAPP_SOLD_EXC=15           # Bono de felicidad por tener más soldados en la frontera que los vecinos
BONO_HAPP_SOLD_MED=5            # Bono de felicidad por tener una cantidad razonable de soldados en las fronteras
BONO_HAPP_SOLD_MAL=-20          # Bono de felicidad por tener menos soldados en la frontera que los vecinos

BONO_HAPP_ATTACK_WIN=5          # Bono de felicidad por ganar un ataque ofensivo
BONO_HAPP_ATTACK_LOSS=-10       # Bono de felicidad por perder un ataque ofensivo

BONO_HAPP_DEFEND_WIN=10         # Bono de felicidad por ganar un ataque defensivo
BONO_HAPP_DEFEND_LOSS=-5        # Bono de felicidad por perder un ataque defensivo

BONO_HAPP_AUTRT=30              # Bono de felicidad por sufrir autoritarismo (demasiado miedo para revelarse)

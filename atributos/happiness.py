from config_atrib import *
from atributos.soldados import *
import random
from turnos.turnos import *

def updateHappinessFinTurno(state):
    """ Al final del turno actualiza el valor de happiness del jugador actual en función de los atributos (dinero,felicidad, desarrollo, soldados...)
        Solo se mide en comparación con aquellos paises con los que comparte frontera
    """
    delta_happiness=0
    vecinos=getVecinos(state)

    # ECONOMIA: Si el pais es más rico que sus vecinos, la felicidad aumenta, sino, baja
    lista_de_economias = [state.players[jugador].economy for jugador in vecinos]
    economia_jugador=state.players[state.current_player].economy
    # print(f"ECONOMIAS:{lista_de_economias}, Economia jugador:{economia_jugador}, "+
    # "Vecino más rico: {max(lista_de_economias)}, vecino más pobre: {min(lista_de_economias)}")
    if len(lista_de_economias)>0:
        if economia_jugador>max(lista_de_economias):
            delta_happiness+=BONO_HAPP_ECON_MED
        elif economia_jugador>min(lista_de_economias):
            delta_happiness+=BONO_HAPP_ECON_MED
        else:
            delta_happiness+=BONO_HAPP_ECON_MAL

    # FELICIDAD: Si la gente es feliz, es un poco más feliz, si es infeliz, se vuelve mucho más infeliz

    felicidad_jugador=state.players[state.current_player].happiness
    varianza=(felicidad_jugador-50)/50
    delta_happiness+=int(varianza*BONO_HAPP_HAPP)

    # DESARROLLO: Si el pais está más desarrolla que sus vecinos, la felicidad aumenta, 
    # pero no baja en caso contrario (Los tontos no sabes que son tontos)

    lista_de_development = [state.players[jugador].development for jugador in vecinos]
    development_jugador=state.players[state.current_player].development
    #print(f"ECONOMIAS:{lista_de_economias}, Economia jugador:{economia_jugador},"+
    # " Vecino más rico: {max(lista_de_economias)}, vecino más pobre: {min(lista_de_economias)}")
    if len(lista_de_development)>0:
        if development_jugador>max(lista_de_development):
            delta_happiness+=BONO_HAPP_DEVP_MED
        elif development_jugador>min(lista_de_development):
            delta_happiness+=BONO_HAPP_DEVP_MED

    # SOLDADOS: Si alguno de los paises enemigos tiene posicionadas en la frontera más tropas que las que tiene el 
    # país en su totalidad => Peligro, Baja mucho la felicidad.
    diferencias=[]
    enemigos=tropas_enemigas_frontera(state)
    aliados=tropas_aliadas_frontera(state)
    for key in list(enemigos.keys()):
        diferencias.append(enemigos[key]/aliados)
    #print(f"El jugador tiene {aliados} tropas en la frontera y los enemigos tienen:{enemigos}")
    if len(diferencias)>0:
        if max(diferencias)<0.5:
            delta_happiness+=BONO_HAPP_SOLD_EXC
        elif max(diferencias)<2:
            delta_happiness+=BONO_HAPP_SOLD_MED
        else:
            delta_happiness+=BONO_HAPP_SOLD_MAL  

    nueva_felicidad=min(max(felicidad_jugador+delta_happiness,0),100)
    state.players[state.current_player].happiness=int(nueva_felicidad)
    checkRevolucion(state,state.current_player)


def updateHappiness(state,player,delta):
    """ Actualiza los el valor de la felicidad de un jugador, sea su turno o no"""
    felicidad_jugador=state.players[player].happiness
    nueva_felicidad=min(max(felicidad_jugador+delta,0),100)
    state.players[player].happiness=int(nueva_felicidad)
    checkRevolucion(state,player)

        

def checkRevolucion(state,player):
    if state.players[player].game_over:
        return
    felicidad_jugador=state.players[player].happiness
    if felicidad_jugador==0:
        tropas_player=tropas_jugador(state,player)
        territorios_player=state.owners.count(player)
        
        if tropas_player>2*territorios_player:
            #print(f"El jugador {state.players[player].name} ha sufrido una revuelta pero se ha impuesto el ejercito.")
            state.players[player].happiness+=BONO_HAPP_AUTRT
            state.players[player].development+=PENL_DVP_REVOL
            state.players[player].development=max(state.players[player].development,0)

            # Pierde un soldado en todo territorio con tropas > 1
            for i in range(len(state.owners)):
                if state.owners[i] == player:
                    if state.armies[i]>1:
                        state.armies[i]=state.armies[i]-1
        else:
            if random.random() < 0.7:
                #print(f"El jugador {state.players[player].name} ha sido derrocado y sucumbe al caos")
                state.owners=[ None if x == player else x for x in state.owners]
                state.players[player].game_over=True
                state.players[player].name="Muerto"
            else:
                lista_titulos = [
                    "República", 
                    "Confederación", 
                    "Imperio", 
                    "Reino", 
                    "Unión", 
                    "Federación", 
                    "Estado Libre", 
                    "Gran Ducado", 
                    "Principado", 
                    "Hegemonía", 
                    "Junta", 
                    "Comuna"
                ]

                current_full_name = state.players[player].name
                base_name = current_full_name
                titulo_actual = None

                for titulo in lista_titulos:
                    prefix = titulo + " de "
                    if current_full_name.startswith(prefix):
                        base_name = current_full_name.split(prefix, 1)[1]
                        titulo_actual = titulo
                        break

                opciones_validas = [t for t in lista_titulos if t != titulo_actual]

                nuevo_titulo = random.choice(opciones_validas)

                new_name = "{} de {}".format(nuevo_titulo, base_name)

                state.players[player].happiness = HAPP_START
                state.players[player].development += PENL_DVP_REVOL
                state.players[player].development=max(state.players[player].development,0)
                state.players[player].name = new_name
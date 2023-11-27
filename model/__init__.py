from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import math
from random import randint
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

import json
import numpy as np
import pandas as pd
import time
import datetime
import random

from logging import NullHandler

def get_grid(model):
    '''
    descripcion...
    '''
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
      cell_content, (x, y) = cell
      for obj in cell_content:
        if isinstance(obj, Persona):
          grid[x][y] = 1
        elif isinstance(obj, Estacion):
          grid[x][y] = 2
        elif isinstance(obj, Vagon):
          grid[x][y] = 3
    return grid

class Persona(Agent):
    '''
    Agente persona, tiene como objetivo llegar a su estación destino
    '''
    def __init__(self, unique_id, model, estacionInicialID, estacionInicial, posicionInicial, estado, id_estacion):
        super().__init__(unique_id, model)
        # definir atributos
        self.estacionInicialID = estacionInicialID
        self.estacionInicial = estacionInicial
        self.estacionDestino = estacionInicial
        self.posicionInicial = posicionInicial
        self.posicionDestino = (0,0)
        self.estado = estado
        self.id_estacion = id_estacion
        self.yaCreoEstacionDestino = False


    def moveToTarget(self, destino):
      newX = self.pos[0]
      newY = self.pos[1]
      if(self.pos[0] < destino[0] and self.pos[0] < self.model.grid.width-1):
        newX = self.pos[0] + 1
      elif(self.pos[0] > destino[0] and self.pos[0] > 0):
        newX = self.pos[0] - 1
      if(self.pos[1] < destino[1] and self.pos[0] < self.model.grid.height-1):
        newY = self.pos[1] + 1
      elif(self.pos[1] > destino[1] and self.pos[1] > 0):
            newY = self.pos[1] - 1
      return (newX, newY)

    def step(self):
      if self.yaCreoEstacionDestino == False:
        self.estacionDestino = self.estacionInicial
        while self.estacionDestino == self.estacionInicial:
          cualEstacionDestinoID = randint(0,self.model.estaciones-1)
          self.estacionDestino = self.model.estacionesListadas[cualEstacionDestinoID]

        self.posicionDestino = (self.posicionInicial[0], self.posicionInicial[1] + ((cualEstacionDestinoID - self.estacionInicialID) * self.model.estacionSize))

        self.yaCreoEstacionDestino = True

      if self.estado == "en_estacion":
        self.model.grid.move_agent(self, self.moveToTarget(self.estacionInicial.pos))


        puedeSubirse = False
        checarAgentesEstacion = self.model.grid.get_cell_list_contents([(self.pos[0], self.pos[1])])
        for indAgente in checarAgentesEstacion:
          if isinstance(indAgente, Estacion):
            if indAgente.tipo == "Entrada":
              puedeSubirse = True
        otrosAgentes = self.model.grid.get_cell_list_contents([(self.pos[0]-1, self.pos[1])])
        for indAgente in otrosAgentes:
          if isinstance(indAgente, Vagon):
            if indAgente.capacidadActual < indAgente.capacidadMaxima and indAgente.stepsActuales > 1 and puedeSubirse == True:
              indAgente.capacidadActual += 1
              indAgente.pasajeros.append(self)
              self.model.grid.move_agent(self, indAgente.pos)
              self.estado = "en_tren"
        pass
      elif self.estado == "en_tren":
        pass
      elif self.estado == "en_destino":
        self.model.grid.move_agent(self, self.moveToTarget(self.posicionDestino))
      else:
        e = 3
        pass
      #print(f"{self.unique_id} Posición X: {self.pos[0]} Posición Y: {self.pos[1]} Estado: {self.estado}")


      personaDatos = {
          "unique_id": self.unique_id,
          "estado": self.estado,
          "x": self.pos[0],
          "y": self.pos[1]
      }
      self.model.datosParaElJson.append(personaDatos)

class Tren(Agent):
    '''
    Agente tren
    Recoge y deja agentes de tipo Persona en las distintas estaciones, tiene
    como objetivo completar la ruta visitando todas las estaciones
    '''
    def __init__(self, unique_id, model, vagones, stepsDeEspera):
        super().__init__(unique_id, model)
        self.vagones = vagones
        self.stepsDeEspera = stepsDeEspera
        self.esperaLock = False
        self.stepsActuales = -1

    def MoverVagones(self):
      for vI in range(3):
        nuevaUbi = (0, self.vagones[vI].pos[1] + 1)
        if nuevaUbi[1] < self.model.grid.height - 1:
          self.model.grid.move_agent(self.vagones[vI], nuevaUbi)
        else:
          self.model.grid.move_agent(self.vagones[vI], (0,0))
        if len(self.vagones[vI].pasajeros) > 0:
          for pasajero in self.vagones[vI].pasajeros:
            self.model.grid.move_agent(pasajero, nuevaUbi)

    # Si llega a una estación de salida y entrada se detiene
    def step(self):
      # Mover los tres vagones hasta llegar al limite
      if self.stepsActuales <= -1:
        self.MoverVagones()
      else:
        self.stepsActuales -= 1

      for vagon in self.vagones:
        otrosAgentes = self.model.grid.get_cell_list_contents([(vagon.pos[0] + 1, vagon.pos[1])])
        for indAgente in otrosAgentes:
          if isinstance(indAgente, Estacion):
            if self.esperaLock == False:
              self.stepsActuales = self.stepsDeEspera
              self.esperaLock = True
            if self.stepsActuales == 0:
              self.MoverVagones()
              self.esperaLock = False
            if indAgente.tipo == "Salida":
              for pasajero in vagon.pasajeros:
                if pasajero.estacionDestino == indAgente:
                  pasajero.estado = "en_destino"
                  self.model.grid.move_agent(pasajero, (pasajero.pos[0] + 1, pasajero.pos[1]))
                  vagon.pasajeros.remove(pasajero)
                  vagon.capacidadActual -= 1




      # Le pasa el tren sus stepsActuales a todos los vagones
      for vI in range(3):
        self.vagones[vI].stepsActuales = self.stepsActuales
        vagonesDatos = {
          "unique_id": self.vagones[vI].unique_id,
          "x": self.vagones[vI].pos[0],
          "y": self.vagones[vI].pos[1]
        }
        self.model.datosParaElJson.append(vagonesDatos)
        #print(f"{self.vagones[vI].unique_id} Posición X: {self.vagones[vI].pos[0]} Posición Y: {self.vagones[vI].pos[1]}")

      pass

class Vagon(Agent):
  def __init__(self, unique_id, model, capacidadMaxima):
        super().__init__(unique_id, model)
        self.capacidadMaxima = capacidadMaxima
        self.capacidadActual = 0
        self.pasajeros = []
        self.stepsActuales = -1



class Estacion(Agent):
    '''
    Agente estacion
    Contiene un número de personas total en base a la densidad poblacional de su ubicación
    '''
    def __init__(self, unique_id, model, nombre, numPersonas, tipo):
        super().__init__(unique_id, model)
        # definir atributos
        self.nombre = nombre
        self.numPersonas = numPersonas
        self.tipo = tipo # String = (Entrada, Salida, Spawn)

    def step(self):
        # Acciones de la estación en cada paso
        pass

class Mapa(Model):
    """
    Modelo mapa, representa el mapa de la ruta como una cuadricula
    """
    def __init__(
        self, 
        estaciones: int, 
        estacionSize: int, 
        stepsDeEspera: int, 
        capacidadVagon: int, 
        personasEnEstacion: int
        ):
        """
          maxSteps: maximos steps que tendrá la simulacón.
          estaciiones: int numero de estaciones,
          estacionSize:
        """

        self.grid = MultiGrid(estacionSize + 1, (estacionSize * estaciones), False)
        self.schedule = SimultaneousActivation(self)
        self.current_step = 0
        self.estaciones = estaciones
        self.estacionSize = estacionSize
        self.stepsDeEspera = stepsDeEspera
        self.capacidadVagon = capacidadVagon
        self.personasEnEstacion = personasEnEstacion
        self.estacionesListadas = []
        # JSON
        self.datosParaElJson = []
        # JSON
        self.resetSteps = 0
        self.datacollector = DataCollector(model_reporters={"Grid": get_grid})

        # Agregar dimensiones a la lista para el JSON
        for esInd in range(self.estaciones):
          dimensionesDatos = {
            "unique_id": "Estacion," + str(esInd),
            "IzqSup": (1,(0 + (self.estacionSize * esInd))),
            "IzqInf": (self.estacionSize,(0 + (self.estacionSize * esInd))),
            "DerSup": (1, ((self.estacionSize - 1) + (self.estacionSize * esInd))),
            "DerInf": (self.estacionSize, ((self.estacionSize - 1) + (self.estacionSize * esInd)))
          }
          self.datosParaElJson.append(dimensionesDatos)



        for agent in self.schedule.agents[:]:
            # Eliminar el agente del grid y del schedule
            self.grid.remove_agent(agent)
            self.schedule.remove(agent)

        vagonesList = []
        for vagon in range(3):
          vagonObj = Vagon(unique_id="Vagon " + str(vagon), model=self, capacidadMaxima=self.capacidadVagon)
          self.grid.place_agent(vagonObj, (0, vagon))
          self.schedule.add(vagonObj)
          vagonesList.append(vagonObj)

        # Crear tren
        tren = Tren(unique_id="Tren", model=self, vagones=vagonesList, stepsDeEspera=self.stepsDeEspera)
        self.grid.place_agent(tren, (0, 0))
        self.schedule.add(tren)


        # Crear estaciones
        for e in range(self.estaciones):
          for eTipo in range(2):
            tipoSeleccionado = "Salida"
            if eTipo >= 1:
              tipoSeleccionado = "Entrada"
            estacionObj = Estacion(unique_id="Estacion " + str(e) + tipoSeleccionado, model=self, nombre=f"Estacion{e}", numPersonas=randint(0, 50), tipo=tipoSeleccionado)
            if eTipo == 0:
              self.estacionesListadas.append(estacionObj)
            ubicacion = (1,int((self.estacionSize/3)*(eTipo+1)) + (e * self.estacionSize))
            self.grid.place_agent(estacionObj, ubicacion)
            self.schedule.add(estacionObj)


            # Crear personas en la estación
          for p in range(personasEnEstacion):
            randomPosX = randint(2, self.estacionSize)
            randomPosY = randint(0, self.estacionSize-1)
            ubiPersona = (randomPosX, randomPosY + (e * self.estacionSize))

            personaObj = Persona(unique_id= "Persona " + str(p) + " / E" + str(e), model=self, estacionInicialID=e, estacionInicial= estacionObj, posicionInicial=ubiPersona, estado="en_estacion", id_estacion= e)
            self.grid.place_agent(personaObj, ubiPersona)
            self.schedule.add(personaObj)


    def agregarDatosAlJson(self):
      json_filename = "dataTres.json"
      try:
        with open(json_filename, 'r') as archivo:
          datos = json.load(archivo)
      except FileNotFoundError:
        # Si el archivo no existe, se creará uno nuevo
        datos = {}
      diccionario = {}
      for datoIndividual in self.datosParaElJson:
        #print(datoIndividual)
        diccionario[datoIndividual["unique_id"]] = datoIndividual
      datos.update(diccionario)
      return datos

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

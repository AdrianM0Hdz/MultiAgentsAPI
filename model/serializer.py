"""
Serliaizer that takes a model as an argument and returns 
a serializable dictionary
"""
from . import *

def serialize_pos(pos: Tuple[int, int]) -> dict:
  return {
      "x": pos[0], 
      "y": pos[1]
  } 

def serialize_person(person: Person) -> dict:
  return {
      "id": person.unique_id, 
      "estacionDestino": person.target_station,
      "tiempoEnLlegarADestino": person.time_to_arrive, 
      "arrived": person.arrived
  }

def serialize_wagon(wagon: Wagon) -> dict: 
  return {
     "pos": serialize_pos(wagon.pos), 
     "personas": list(map(serialize_person, wagon.people))
  }

def serialize_section(section: StationSection) -> dict: 
  return {
      "pos": serialize_pos(section.pos),
      "personas": list(map(serialize_person, section.people))
  }

def serialize_station(station: Station) -> dict: 
  return {
      "id": station.unique_id, 
      "secciones": list(map(serialize_section, station.sections))
  }

def serialize_model(tm: TrainModel) -> dict:
  train = {
      "vagon1": serialize_wagon(tm.train.wagons[0]),
      "vagon2": serialize_wagon(tm.train.wagons[1]),
      "vagon3": serialize_wagon(tm.train.wagons[2])
  }
  stations = list(map(serialize_station, tm.stations))
  return {
      "tren": train, 
      "estaciones": stations
  }
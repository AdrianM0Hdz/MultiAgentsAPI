from mesa import Agent, Model

from mesa.space import MultiGrid

from mesa.time import SimultaneousActivation

from mesa.datacollection import DataCollector
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

import numpy as np
import pandas as pd

import time
import datetime
import random
from enum import Enum
from typing import List, Tuple
from dataclasses import dataclass
from uuid import uuid1


@dataclass(frozen=True)
class StationDescription: 
  pos_of_first_section: Tuple[int, int]
  people_per_section: int

@dataclass(frozen=True)
class TrainDescription: 
  await_time: int # steps awaited at each station
  wagon_capacity: int


def get_grid(model):
    '''
    descripcion...
    '''
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
      cell_content, (x, y) = cell
      grid[x][y] = 0
      for obj in cell_content:
        grid[x][y] = 1
    return grid

class Person(Agent): 
  def __init__(
      self,
      unique_id: str, 
      model: Model,  
      target_station: str
    ):
    super().__init__(unique_id, model)
 
    self.target_station = target_station
    self.arrived = False 
    self.time_to_arrive = 0 # number of steps taken to arrive to destination

  def step(self):
    if self.arrived == False:
      self.time_to_arrive += 1

class TrainState(Enum):
  IN_MOVEMENT = "IN_MOVEMENT"
  STOPPED = "STOPPED"

class Wagon(Agent):
  def __init__(
        self,
        state: TrainState, 
        unique_id: str, 
        model: Model,
        relative_position: int, 
        pos: Tuple[int, int]
      ):
      super().__init__(unique_id, model)
      self.state = state
      self.people = []
      self.relative_position = relative_position 
      self.pos = pos

  def step(self):
    """
    TODO: check if adjacent to a station section of equal relative position and
    if so discharge while train state is equal to discharging
    """
    for person in self.people: 
      person.step()

    if self.state == TrainState.STOPPED: 
      agents_below = self.model.grid[self.pos[0]][self.pos[1]-1]
      station_section = None
      for agent in agents_below: 
        if agent.relative_position == self.relative_position:
          station_section = agent
      
      descending = list(filter(lambda person: person.target_station == station_section.station_id, self.people))
      station_section.people = [*station_section.people, *(descending[:2])]
      ascending = list(filter(lambda person: person.target_station != station_section.station_id, station_section.people))
      
      self.people = list(filter(lambda person: person not in descending, self.people))
      self.people = [*self.people, *(ascending[:2])]

      station_section.people = list(filter(lambda person: person not in ascending, station_section.people))


class Train(Agent):
  def __init__(
        self,
        unique_id: str, 
        model: Model, 
        wagons: List[Wagon],
        await_time: int, 
        wagon_capacity: int
      ):
      super().__init__(unique_id, model)
      self.wagons = wagons 
      self.await_time = await_time
      self.stop_counter = 0
      self.wagon_capacity = wagon_capacity
      self.state = TrainState.IN_MOVEMENT

  @classmethod
  def build_from_description(cls, model: Model, train_description: TrainDescription) -> "Train":
      wagons = []
      for i in range(3):
        wagon = Wagon(TrainState.IN_MOVEMENT, str(uuid1()), model, i, (i, 1))
        model.grid.place_agent(wagon, wagon.pos)
        wagons.append(wagon)
      return cls(str(uuid1()), model, wagons, train_description.await_time, train_description.wagon_capacity)

  def step(self):
    for wagon in self.wagons: 
      wagon.step()
    if self.state == TrainState.IN_MOVEMENT:
      # check if we have been aligned with a station
      train_aligned = True
      for wagon in self.wagons: 
        wagon_aligned = False
        agents_beside_wagon = self.model.grid[wagon.pos[0]][wagon.pos[1]-1]
        for agent in agents_beside_wagon: 
          if agent.relative_position == wagon.relative_position:
            wagon_aligned = True 
        train_aligned = wagon_aligned and train_aligned 
      
      if train_aligned: 
          self.state = TrainState.STOPPED
          self.stop_couter = 0
          for wagon in self.wagons: wagon.state = TrainState.STOPPED
      else: 
          for wagon in self.wagons[::-1]:
            self.model.grid.place_agent(wagon, (wagon.pos[0]+1, wagon.pos[1]))
      
    if self.state == TrainState.STOPPED: 
        if self.stop_counter >= self.await_time: 
          self.state = TrainState.IN_MOVEMENT
          for wagon in self.wagons: wagon.state = TrainState.IN_MOVEMENT
          for wagon in self.wagons[::-1]:
            self.model.grid.place_agent(wagon, (wagon.pos[0]+1, wagon.pos[1]))
        else: 
          self.stop_counter += 1

class StationSection(Agent):
  def __init__(
        self, 
        unique_id: str, 
        model: Model,
        station_id: str,
        relative_position: int, 
        pos: Tuple[int, int],
        people: List[Person]
      ):
      super().__init__(unique_id, model)
      self.unique_id = unique_id 
      self.model = model 
      self.station_id = station_id
      self.relative_position = relative_position
      self.people = people
      self.pos = pos

  @classmethod 
  def build_from_description(
        cls, 
        model: Model,
        station_id: str,
        n_people: int, 
        relative_position: int,
        possible_people_destinations: List[str],
        pos: Tuple[int, int],
      ) -> "StationSection":
    people = []
    for _ in range(n_people): 
      people.append(
          Person(
              str(uuid1()), 
              model, 
              random.sample(possible_people_destinations, 1)[0]    
          )
      )
    return cls(str(uuid1()), model, station_id, relative_position, pos, people)

  def step(self):
    for person in self.people: 
      person.step()
      if person.target_station == self.station_id: 
        person.arrived = True

class Station(Agent):
  def __init__(
        self, 
        unique_id: str, 
        model: Model, 
        sections: List[StationSection]
      ):
    super().__init__(unique_id, model)
    self.sections = sections

  @classmethod 
  def build_from_description(
        cls, 
        unique_id: str,
        model: Model, 
        description: StationDescription, 
        possible_people_destinations: List[str] 
      ) -> "Station":
      sections = []
      
      for i in range(3): 
        
        station_section = StationSection.build_from_description(
                                              model,
                                              unique_id, 
                                              description.people_per_section, 
                                              i,
                                              possible_people_destinations,
                                              (description.pos_of_first_section[0]+i, description.pos_of_first_section[1])
            )
        model.grid.place_agent(station_section, station_section.pos)
        sections.append(station_section)
      
      return cls(
          unique_id, model, sections
      )

  def step(self):
    for section in self.sections: 
      section.step()

class TrainModel(Model):

  def __init__(
      self,
      train_description: TrainDescription, 
      station_descriptions: List[StationDescription],
      width: int=700, 
      height: int=2
     ):
    assert height >= 2
    assert width >= 3
    
    self.grid = MultiGrid(width, height, False) 
    self.schedule = SimultaneousActivation(self) 
    self.datacollector = DataCollector(
        model_reporters={
            "Grid": get_grid
        }
    )

    self.station_ids = []
    for _ in range(len(station_descriptions)): 
      self.station_ids.append(str(uuid1()))

    self.stations = []
    for i, station_description in enumerate(station_descriptions):
      station = Station.build_from_description(
                          self.station_ids[i], 
                          self, 
                          station_description, 
                          self.station_ids[i:]
                )
      self.schedule.add(station)
      self.stations.append(station)

    self.train = Train.build_from_description(self, train_description)
    self.schedule.add(self.train)

  def step(self):
    self.datacollector.collect(self)
    self.schedule.step()
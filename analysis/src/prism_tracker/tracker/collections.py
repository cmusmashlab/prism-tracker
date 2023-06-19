from typing import Dict, List, Optional


class Step:
    def __init__(self, index: int, mean_time: float, std_time: float):
        self.index = index
        self.mean_time = mean_time
        self.std_time = std_time

    def __repr__(self):
        return f's{self.index}'


class Graph:
    def __init__(self, steps: List[Step], edges: Dict[Step, Dict[Step, float]]):
        self.steps = steps
        self.edges = edges
        self.start = self.steps[0]
        self.end = self.steps[-1]


class HiddenState:
    def __init__(self, step_index: int, time: int):
        self.step_index = step_index
        self.time = time

    def __repr__(self):
        return f'{self.step_index}_{self.time}'


class HiddenTransition:
    def __init__(self, next_step_index: int, probability: float):
        self.next_step_index = next_step_index
        self.probability = probability


class ViterbiEntry:
    def __init__(self, probability: float, history: List[HiddenState]):
        self.probability = probability
        self.history = history

    def __repr__(self):
        return f'{self.history}@{self.probability}'

    @property
    def last_state(self) -> Optional[HiddenState]:
        if len(self.history) == 0:
            return None
        return self.history[-1]

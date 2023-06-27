from typing import Optional, List, Dict, Tuple, Iterable, Any, Iterator

import numpy as np
import numpy.typing as npt
from scipy import stats


from .collections import ViterbiEntry, HiddenState, HiddenTransition, Graph
from .params import MAX_TIME


class ViterbiTracker:
    def __init__(self, graph: Graph, start_step_indices: Optional[List[int]] = None):
        """
        Args:
        * graph (Graph): a graph object built using build_graph(), which represents transitions between the different steps in a procedure.
        * start_step_indices (Optional[List[int]]): a list of integers representing the indices of the starting step.
        """
        self.start_step_indices = start_step_indices
        self.curr_entries: Optional[Dict[int, ViterbiEntry]] = None

        # use list-based matrix to accelerate
        self.steps = sorted(graph.steps, key=lambda step: step.index)
        max_step_index = max([step.index for step in graph.steps])

        # (from_step_index, time_frame) -> List[transition]
        self.transitions: List[List[List[HiddenTransition]]] = [[[] for time in range(MAX_TIME)]
                                                                for _ in range(max_step_index + 1)]

        for step in self.steps:
            # cdf represents the (reversed) probability of staying on the step at the time
            prob = 1 - stats.norm.cdf(range(MAX_TIME), loc=step.mean_time, scale=step.std_time)

            for time in range(0, MAX_TIME - 1):
                escape_prob = 1 - prob[time + 1] / prob[time]
                if np.isnan(escape_prob):
                    continue

                # use log-probability to avoid underflow
                self.transitions[step.index][time].append(HiddenTransition(step.index, np.log(1 - escape_prob)))
                for dest_step, dest_prob in graph.edges.get(step, {}).items():
                    self.transitions[step.index][time].append(
                        HiddenTransition(dest_step.index, np.log(escape_prob * dest_prob)))

    def __get_best_entry__(self, entries: Iterable[ViterbiEntry]) -> Tuple[float, List[int]]:
        """
        This method selects the best entry from a list of ViterbiEntry based on probability.

        Args:
        * entries (Iterable[ViterbiEntry]): a list of ViterbiEntry to choose from.

        Returns:
        * probability (float): a float value of the probability of the best entry.
        * steps (List[int]): a list of integers representing the step indices in the best entry's history.
        """
        entries = sorted(entries, key=lambda entry: entry.probability, reverse=True)
        return entries[0].probability, [state.step_index for state in entries[0].history]

    def initialize(self, observation: List[float], confusion_matrix: List[List[float]]) -> Tuple[float, List[int]]:
        """
        This methods performs initialization for the Viterbi algorithm.

        Args:
        * observation (List[float]): a list of the observation probabilities of each step at the initial frame.
        * confusion_matrix (List[List[float]]): a matrix containing the confusion probabilities between each step in a procedure.

        Returns:
        * probability (float): a float value of the probability of the best entry.
        * steps (List[int]): a list of integers representing the step indices in the best entry's history.
        """
        self.curr_entries = {}  # dict[step_index, entry]

        # initialize: we don't assume knowing which step to start
        for current_step in self.steps:
            acc_prob = 0.0
            for observed_step, prob in zip(self.steps, confusion_matrix[current_step.index]):
                if self.start_step_indices is None or current_step.index in self.start_step_indices:
                    acc_prob += prob * observation[observed_step.index]
            self.curr_entries[current_step.index] = ViterbiEntry(np.log(acc_prob), [HiddenState(current_step.index, 0)])

        return self.__get_best_entry__(self.curr_entries.values())

    def forward(self, observation: List[float], confusion_matrix: List[List[float]],
                oracle_next_step: Optional[int] = None, oracle_prohibited_steps: Optional[List[int]] = None) -> Tuple[float, List[int]]:
        """
        This method calculates the Viterbi forward algorithm for a single frame given the current prediction entries.

        Args:
        * observation (List[float]): a list of the observation probabilities of each step at the current frame.
        * confusion_matrix (List[List[float]]): a matrix containing the confusion probabilities between each step in a procedure.
        * oracle_next_step (Optional[int]): an integer representing the next step.
        * oracle_prohibited_steps (Optional[List[int]]): a list of integers representing the steps that cannot be transited at the current frame.

        Returns:
        * probability (float): a float value of the probability of the best entry.
        * steps (List[int]): a list of integers representing the step indices in the best entry's history.
        """
        if self.curr_entries is None:
            raise ValueError('You must call initialize() first')

        next_entries: Dict[int, ViterbiEntry] = {}  # dict[step_index, entry]
        observed_probs: Dict[int, float] = {}  # dict[step_index, prob]

        for actual_step in self.steps:  # precalculate the influence of the confusion matrix
            observed_probs[actual_step.index] = 0
            for observed_step, prob in zip(self.steps, confusion_matrix[actual_step.index]):
                observed_probs[actual_step.index] += prob * observation[observed_step.index]
            observed_probs[actual_step.index] = np.log(observed_probs[actual_step.index])

        for curr_state_index, curr_entry in self.curr_entries.items():
            for transition in self.transitions[curr_state_index][curr_entry.last_state.time]:
                if oracle_next_step is not None:
                    if oracle_next_step == curr_state_index:  # too early to transit
                        continue
                    elif oracle_next_step != transition.next_step_index:  # the next step should be a different one
                        continue
                elif curr_state_index != transition.next_step_index and \
                        transition.next_step_index in oracle_prohibited_steps:  # cannot transit now
                    continue

                prob = curr_entry.probability + transition.probability + observed_probs[transition.next_step_index]
                if transition.next_step_index in next_entries \
                   and prob < next_entries[transition.next_step_index].probability:
                    continue

                if curr_state_index == transition.next_step_index:
                    next_state = HiddenState(transition.next_step_index, curr_entry.last_state.time + 1)
                else:
                    next_state = HiddenState(transition.next_step_index, 0)

                next_entries[transition.next_step_index] = ViterbiEntry(prob, curr_entry.history + [next_state])

        self.curr_entries = next_entries
        return self.__get_best_entry__(self.curr_entries.values())

    def predict(self, observations: List[List[float]], confusion_matrix: List[List[float]],
                oracle: Optional[Dict[int, List[int]]] = None) -> Iterator[Tuple[float, List[int]]]:
        """
        This function is used for predicting the steps of a procedure using the complete observation data.

        Args:
        * observations (List[List[float]]): a numpy array containing the observation probabilities with dimensions representing the steps and time frames.
        * confusion_matrix (List[List[float]]): a matrix containing the confusion probabilities between each step in a procedure.
        * oracle (Optional[Dict[int, List[int]]]): an optional dictionary where the keys are the step indices and the values are lists of the correct transition time frames of each step.

        For each time frame, returns:
        * probability (float): a float value of the probability of the best entry.
        * steps (List[int]): a list of integers representing the step indices in the best entry's history.
        """
        oracle = {} if oracle is None else oracle

        yield self.initialize([observation[0] for observation in observations], confusion_matrix)

        # dp: basic viterbi algorithm
        for time in range(1, len(observations[0])):
            oracle_next_step = (list(filter(lambda step_index: time in oracle[step_index], oracle.keys())) + [None])[0]
            oracle_prohibited_steps = list(filter(lambda step_index: step_index != oracle_next_step, oracle.keys()))
            yield self.forward([observation[time] for observation in observations], confusion_matrix,
                               oracle_next_step=oracle_next_step, oracle_prohibited_steps=oracle_prohibited_steps)

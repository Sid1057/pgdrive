import math
from typing import Tuple, Sequence, Union

import numpy as np

from pgdrive.component.lane.abs_lane import AbstractLane
from pgdrive.constants import LineType
from pgdrive.utils.math_utils import norm


class StraightLane(AbstractLane):
    """A lane going in straight line."""
    def __init__(
        self,
        start: Union[np.ndarray, Sequence[float]],
        end: Union[np.ndarray, Sequence[float]],
        width: float = AbstractLane.DEFAULT_WIDTH,
        line_types: Tuple[LineType, LineType] = (LineType.BROKEN, LineType.BROKEN),
        forbidden: bool = False,
        speed_limit: float = 1000,
        priority: int = 0
    ) -> None:
        """
        New straight lane.

        :param start: the lane starting position [m]
        :param end: the lane ending position [m]
        :param width: the lane width [m]
        :param line_types: the type of lines on both sides of the lane
        :param forbidden: is changing to this lane forbidden
        :param priority: priority level of the lane, for determining who has right of way
        """
        super(StraightLane, self).__init__()
        self.set_speed_limit(speed_limit)
        self.start = np.array(start)
        self.end = np.array(end)
        self.width = width
        self.line_types = line_types or [LineType.BROKEN, LineType.BROKEN]
        self.forbidden = forbidden
        self.priority = priority
        self.length = norm((self.end - self.start)[0], (self.end - self.start)[1])
        self.heading = math.atan2(self.end[1] - self.start[1], self.end[0] - self.start[0])
        self.direction = (self.end - self.start) / self.length
        self.direction_lateral = np.array([-self.direction[1], self.direction[0]])

    def update_properties(self):
        super(StraightLane, self).__init__()
        self.length = norm((self.end - self.start)[0], (self.end - self.start)[1])
        self.heading = math.atan2(self.end[1] - self.start[1], self.end[0] - self.start[0])
        self.direction = (self.end - self.start) / self.length
        self.direction_lateral = np.array([-self.direction[1], self.direction[0]])

    def position(self, longitudinal: float, lateral: float) -> np.ndarray:
        return self.start + longitudinal * self.direction + lateral * self.direction_lateral

    def heading_at(self, longitudinal: float) -> float:
        return self.heading

    def width_at(self, longitudinal: float) -> float:
        return self.width

    def local_coordinates(self, position: Tuple[float, float]) -> Tuple[float, float]:
        delta_x = position[0] - self.start[0]
        delta_y = position[1] - self.start[1]
        longitudinal = delta_x * self.direction[0] + delta_y * self.direction[1]
        lateral = delta_x * self.direction_lateral[0] + delta_y * self.direction_lateral[1]
        return float(longitudinal), float(lateral)

    def reset_start_end(self, start: Union[np.ndarray, Sequence[float]], end: Union[np.ndarray, Sequence[float]]):
        super(StraightLane, self).__init__()
        self.start = start
        self.end = end
        self.update_properties()

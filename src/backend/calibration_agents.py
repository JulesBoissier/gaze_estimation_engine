import math
from abc import ABC, abstractmethod
from typing import List, Tuple

from src.backend.calibration_map import CalibrationMap


class CalibrationAgent(ABC):
    """
    Abstract base class for calibration agents.
    """

    @abstractmethod
    def calculate_point_of_regard(
        self, head_x: float, head_y: float, theta: float, phi: float
    ) -> Tuple[float, float]:
        """
        Calculate the point of regard on the screen.

        Args:
            theta (float): The horizontal gaze angle.
            phi (float): The vertical gaze angle.

        Returns:
            Tuple[float, float]: Screen coordinates (x, y).
        """
        pass


class InterpolationAgent(CalibrationAgent):
    """
    An interpolation based implementation of a CalibrationAgent assuming static head position.
    """

    def __init__(self):
        """
        Initialize the InterpolationAgent.
        """
        self.initialize_cal_map()

    def initialize_cal_map(self):
        self.calibration_map = CalibrationMap()

    def calibration_step(
        self,
        monitor_x: float,
        monitor_y: float,
        head_x: float,
        head_y: float,
        theta: float,
        phi: float,
    ):
        """
        Add a calibration point during the calibration process.

        Args:
            x (float): X coordinate on the screen.
            y (float): Y coordinate on the screen.
            theta (float): Horizontal gaze angle.
            phi (float): Vertical gaze angle.
        """
        self.calibration_map.add_calibration_point(
            monitor_x, monitor_y, head_x, head_y, theta, phi
        )

    def _interpolate(
        self,
        position: float,
        angle: float,
        calibration_coordinates: List[float],
        calibration_angles: List[float],
    ) -> float:
        """
        Interpolate the screen coordinate based on calibration data.

        Args:
            angle (float): The gaze angle to interpolate.
            calibration_coordinates (List[float]): Corresponding screen coordinates.
            calibration_angles (List[float]): Corresponding gaze angles.

        Returns:
            float: Interpolated screen coordinate.
        """
        # TODO: Multiply position and orientation in interpolation.
        epsilon = 1e-6
        distances = [
            math.sqrt((angle - calib_angle) ** 2) for calib_angle in calibration_angles
        ]
        weights = [1 / (distance + epsilon) for distance in distances]
        numerator = sum(w * coord for w, coord in zip(weights, calibration_coordinates))
        return numerator / sum(weights)

    def calculate_point_of_regard(
        self, head_x: float, head_y: float, theta: float, phi: float
    ) -> Tuple[float, float]:
        """
        Calculate the screen coordinates for a given gaze angle.

        Args:
            theta (float): Horizontal gaze angle.
            phi (float): Vertical gaze angle.

        Returns:
            Tuple[float, float]: Screen coordinates (x, y).
        """
        x_screen = self._interpolate(
            head_x,
            theta,
            self.calibration_map.monitor_x_values,
            self.calibration_map.theta_values,
        )
        y_screen = self._interpolate(
            head_y,
            phi,
            self.calibration_map.monitor_y_values,
            self.calibration_map.phi_values,
        )
        return x_screen, y_screen

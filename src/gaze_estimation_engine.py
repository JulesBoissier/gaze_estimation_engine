from typing import List, Tuple

import numpy as np

from src.calibration_agents import CalibrationAgent
from src.calibration_data_store import CalibrationDataStore
from src.gaze_net import GazeNet


class GazeEstimationEngine:
    """
    A class responsible for estimating gaze positions using GazeNet and CalibrationAgent.
    """

    def __init__(
        self, gaze_net: GazeNet, cal_agent: CalibrationAgent, cds=CalibrationDataStore
    ):
        """
        Initialize the GazeEstimationEngine.

        Args:
            gaze_net (GazeNet): An instance of GazeNet for predicting gaze vectors.
            cal_agent (CalibrationAgent): An instance of CalibrationAgent for calibration tasks.
            cds (CalibrationDataStore): An instance of CalibrationDataStore for storing and retrieving calibration profiles.
        """
        self.gaze_net = gaze_net
        self.cal_agent = cal_agent
        self.cds = cds

    def save_profile(self, name):
        self.cds.save_profile(name, self.cal_agent.calibration_map)

    def load_profile(self, id):
        self.cal_agent.calibration_map = self.cds.load_profile(id)

    def list_profiles(self):
        return self.cds.list_profiles()

    def delete_profile(self, id):
        self.cds.delete_profile(id)

    def run_single_calibration_step(self, x: float, y: float, frame: np.ndarray):
        """
        Perform a single calibration step using GazeNet and CalibrationAgent.

        Args:
            x (float): X coordinate on the screen.
            y (float): Y coordinate on the screen.
            frame (np.ndarray): The input image for gaze prediction.
        """
        _, _, theta, phi = self.gaze_net.predict_gaze_vector(frame)
        self.cal_agent.calibration_step(x, y, theta, phi)

    def run_calibration_steps(
        self, calibration_data: List[Tuple[int, int, np.ndarray]]
    ):
        """
        Perform calibration steps for provided data.

        Args:
            calibration_data (List[Tuple[int, int, np.ndarray]]): List of tuples containing
            x, y screen coordinates and corresponding image data.
        """
        for calibration_point in calibration_data:
            try:
                self.run_single_calibration_step(
                    calibration_point[0], calibration_point[1], calibration_point[2]
                )
            except Exception as e:
                print(f"Calibration step failed for point {calibration_point}: {e}")

    def predict_gaze_position(self, image: np.ndarray) -> Tuple[float, float]:
        """
        Predict the gaze position on the screen for a given image.

        Args:
            image (np.ndarray): The input image for gaze prediction.

        Returns:
            Tuple[float, float]: The predicted screen coordinates (x, y).
        """
        _, _, theta, phi = self.gaze_net.predict_gaze_vector(image)

        try:
            screen_x, screen_y = self.cal_agent.calculate_point_of_regard(theta, phi)

        except ZeroDivisionError:
            print("Calibration profile is empty.")
            screen_x, screen_y = None, None
        return screen_x, screen_y

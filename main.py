import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel

from src.calibration_agents import NaiveCalibrationAgent
from src.calibration_data_store import CalibrationDataStore
from src.gaze_estimation_engine import GazeEstimationEngine
from src.gaze_net import GazeNet

# Dictionary to hold the GazeEstimationEngine instance
resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the GazeEstimationEngine

    nca = NaiveCalibrationAgent(db_path=None)
    cds = CalibrationDataStore()
    gn = GazeNet(filepath=os.path.join("models", "L2CSNet_gaze360.pkl"))
    resources["gaze_engine"] = GazeEstimationEngine(gn, nca, cds)
    try:
        yield
    finally:
        # Clean up the GazeEstimationEngine
        resources["gaze_engine"].shutdown()
        resources.clear()


app = FastAPI(lifespan=lifespan)


### Pydantic Models for Responses ###
class ProfileResponse(BaseModel):
    id: int
    profile_name: str
    updated_at: datetime


class ProfileListResponse(BaseModel):
    profiles: List[ProfileResponse]


class GazePredictionResponse(BaseModel):
    prediction: List[float]


@app.post("/save_profile")
def save_current_profile(name: str):
    gaze_engine = resources.get("gaze_engine")
    gaze_engine.save_profile("profile_name")
    return {"message": f"Profile '{name}' saved successfully."}


@app.get("/list_profiles")
def list_calibration_profiles():
    gaze_engine = resources.get("gaze_engine")
    profiles = gaze_engine.list_profiles()
    return ProfileListResponse(profiles=profiles)


@app.post("/load_profile")
def load_calibration_profile(profile_id: int):
    gaze_engine = resources.get("gaze_engine")
    gaze_engine.load_profile(profile_id)
    return {"message": "Profile loaded successfully."}


@app.post("/delete_profile")
def delete_calibration_profile(profile_id: int):
    gaze_engine = resources.get("gaze_engine")
    gaze_engine.delete_profile(profile_id)
    return {"message": "Profile deleted successfully."}


@app.post("/cal_point")
async def add_calibration_point(
    x: float = Form(...),  # Explicitly define x as a form field
    y: float = Form(...),  # Explicitly define y as a form field
    file: UploadFile = File(...),  # Accept the uploaded image
):
    # Read the uploaded file's content as bytes
    image_bytes = await file.read()

    # Convert bytes to a NumPy array
    nparr = np.frombuffer(image_bytes, np.uint8)

    # Decode the image array into an OpenCV image (BGR format)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gaze_engine = resources.get("gaze_engine")

    gaze_engine.run_single_calibration_step(x, y, frame)
    return {
        "message": f"Calibration point added successfully with parameters x: {x}, y: {y}."
    }


@app.post("/predict")
async def predict_point_of_regard(
    file: UploadFile = File(...),  # Accept the uploaded image
):
    # Read the uploaded file's content as bytes
    image_bytes = await file.read()

    # Convert bytes to a NumPy array
    nparr = np.frombuffer(image_bytes, np.uint8)

    # Decode the image array into an OpenCV image (BGR format)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gaze_engine = resources.get("gaze_engine")
    predictions = gaze_engine.predict_gaze_position(frame)

    return GazePredictionResponse(predictions=predictions)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

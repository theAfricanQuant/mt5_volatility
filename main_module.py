
#
# (c) Ricky Macharm, MScFE
# https://SisengAI.com
#

import sqlite3

from config import settings
from retrieve_data import SQLiteRepo
from fastapi import FastAPI
from model import GarchModel
from pydantic import BaseModel


# `FitIn` class
class FitIn(BaseModel):
    ticker: str
    use_new_data: bool
    n_observations: int
    p: int
    q: int


#  `FitOut` class
class FitOut(FitIn):
    success: bool
    message: str


#  `PredictIn` class
class PredictIn(BaseModel):
    ticker: str
    n_days: int


#  `PredictOut` class
class PredictOut(PredictIn):
    success: bool
    forecast: dict
    message: str



def build_model(ticker: str, use_new_data: bool = False) -> GarchModel:

    # Create DB connection
    connection = sqlite3.connect(settings.db_name, check_same_thread=False)

    # Create `SQLRepository`
    repo = SQLiteRepo(connection=connection)

    # Create model & Return model
    return GarchModel(ticker=ticker, use_new_data=use_new_data, repo=repo)




app = FastAPI()



# `"/hello" path with 200 status code
@app.get("/hello", status_code=200)
def hello():
    """Return dictionary with greeting message."""
    return {"message":"Hello World, I am live!"}



#  `"/fit" path, 200 status code
@app.post("/fit", status_code=200, response_model=FitOut)
def fit_model(request: FitIn):

    """Fit model, return confirmation message.

    Parameters
    ----------
    request : FitIn

    Returns
    ------
    dict
        Must conform to `FitOut` class
    """
    # Create `response` dictionary from `request`
    response = request.dict()

    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, 
                            use_new_data=request.use_new_data)

        # Wrangle data
        model.calc_returns(n_observations=request.n_observations)

        # Fit model
        model.fit(p=request.p, q=request.q)

        # Save model
        filename = model.dump()

        # Add `"success"` key to `response`
        response["success"] = True

        # Add `"message"` key to `response` with `filename`
        response["message"] = f"Trained and saved '{filename}'. Metrics: AIC {model.aic}, BIC {model.bic}."
        
    # Create except block
    except Exception as e:
        # Add `"success"` key to `response`
        response["success"] = False

        # Add `"message"` key to `response` with error message
        response["message"] = str(e)

    # Return response
    return response


#  `"/predict" path, 200 status code
@app.post("/predict", status_code=200, response_model=PredictOut)
def get_prediction(request: PredictIn):

    # Create `response` dictionary from `request`
    response = request.dict()

    # Create try block to handle exceptions
    try:
        # Build model with `build_model` function
        model = build_model(ticker=request.ticker, use_new_data=False)

        # Load stored model
        model.load()

        # Generate prediction
        prediction = model.predict_volatility(horizon=request.n_days)

        # Add `"success"` key to `response`
        response["success"] = True

        # Add `"forecast"` key to `response`
        response["forecast"] = prediction

        # Add `"message"` key to `response`
        response["message"] = ""

    # Create except block
    except Exception as e:
        
        # Add `"success"` key to `response`
        response["success"] = False

        # Add `"forecast"` key to `response`
        response["forecast"] = {}

        #  Add `"message"` key to `response`
        response["message"] = str(e)

    # Return response
    return response

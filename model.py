
#
# (c) Ricky Macharm, MScFE
# https://SisengAI.com
#


import os
from glob import glob

from pathlib import Path
import pandas as pd
from arch import arch_model
from config import settings
from retrieve_data import MT5_Data, SQLiteRepo
import joblib

class GarchModel:
    """Class for training GARCH model and generating predictions.

    Atttributes
    -----------
    ticker : str
        Ticker symbol of the equity whose volatility will be predicted.
    repo : SQLRepository
        The repository where the training data will be stored.
    use_new_data : bool
        Whether to download new data from the AlphaVantage API to train
        the model or to use the existing data stored in the repository.
    model_directory : str
        Path for directory where trained models will be stored.

    Methods
    -------
    wrangle_data
        Generate equity returns from data in database.
    fit
        Fit model to training data.
    predict
        Generate volatilty forecast from trained model.
    dump
        Save trained model to file.
    load
        Load trained model from file.
    """

    def __init__(self, ticker, repo, use_new_data):
    
        self.ticker = ticker
        self.repo = repo
        self.use_new_data = use_new_data
        self.model_directory = settings.model_directory

    def calc_returns(self, n_observations):

        """Extract data from database (or get from our mt5 broker), transform it
        for training model, and attach it to `self.data`.

        Parameters
        ----------
        n_observations : int
            Number of observations to retrieve from database

        Returns
        -------
        None
        """
        # Add new data to database if required
        if self.use_new_data:
            # instantiate an API Class
            api = MT5_Data()
            # Get data
            new_data = api.ticker_data(ticker=self.ticker)
            # insert data in repo
            self.repo.insert_table(
                table_name=self.ticker, records=new_data,
                if_exists="replace"
            )

        # Pull data from SQL database & Clean data, attach to class as `data` attribute
        self.data = ((self.repo.
            read_table(table_name=self.ticker, limit=n_observations+1)
            .assign(returns = lambda x: 100*x["close"].pct_change())
            .dropna())["returns"]
             )

    def fit(self, p, q):

        """Create model, fit to `self.data`, and attach to `self.model` attribute.
        For assignment, also assigns adds metrics to `self.aic` and `self.bic`.

        Parameters
        ----------
        p : int
            Lag order of the symmetric innovation

        q : ind
            Lag order of lagged volatility

        Returns
        -------
        None
        """
        # Train Model, attach to `self.model`
        self.model = arch_model(self.data, p=p, q=q, rescale=False).fit(disp=0)
        self.aic = self.model.aic
        self.bic = self.model.bic
        

    def __clean_prediction(self, prediction):

        """Reformat model prediction to JSON.

        Parameters
        ----------
        prediction : pd.DataFrame
            Variance from a `ARCHModelForecast`

        Returns
        -------
        dict
            Forecast of volatility. Each key is date in ISO 8601 format.
            Each value is predicted volatility.
        """
         #  Calculate forecast start date
        start = prediction.index[0] + pd.DateOffset(days=1)

        # Create date range
        prediction_dates = pd.bdate_range(start=start, periods=prediction.shape[1])

        # Create prediction index labels, ISO 8601 format
        prediction_index = [d.isoformat() for d in prediction_dates]


        # Extract predictions from DataFrame, get square root
        data = prediction.values.flatten() ** .5

        # Combine `data` and `prediction_index` into Series & Return Series as dictionary
        return pd.Series(data, index=prediction_index).to_dict()

    def predict_volatility(self, horizon):

        """Predict volatility using `self.model`

        Parameters
        ----------
        horizon : int
            Horizon of forecast, by default 5.

        Returns
        -------
        dict
            Forecast of volatility. Each key is date in ISO 8601 format.
            Each value is predicted volatility.
        """
        # Generate variance forecast from `self.model`
        prediction = self.model.forecast(horizon=horizon, reindex=False).variance

        # Format prediction with `self.__clean_predction` & Return `prediction_formatted`
        
        return self.__clean_prediction(prediction)

    def dump(self):

        """Save model to `self.model_directory` with timestamp.

        Returns
        -------
        str
            filepath where model was saved.
        """
        # Create timestamp in ISO format
        timestamp = (pd.Timestamp.now()
             .isoformat()
             .replace(":", ".")
            )
        
        # Create directory if it doesn't exist
        os.makedirs(self.model_directory, exist_ok=True)
        # Create filepath, including `self.model_directory`
        filepath =  Path(f"{self.model_directory}/{self.ticker}_{timestamp}.pkl")
        
        # Save `self.model`
        joblib.dump(self.model, filepath)
    
        
        # Return filepath
        return str(filepath)

    def load(self):

        """Load most recent model in `self.model_directory` for `self.ticker`,
        attach to `self.model` attribute.

        """
        # Create pattern for glob search
        pattern = str(Path(f"{self.model_directory}/{self.ticker}*.pkl"))
        

        # Try to find path of latest model
        try:
            model_path = sorted(glob(pattern))[-1]

        # Handle possible `IndexError`
        except IndexError:
            raise Exception(f"There are no trained models for {self.ticker}")

        # Load model & attach to `self.model`
        self.model = joblib.load(model_path)
        
        

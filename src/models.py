"""
Machine learning models for financial prediction.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class FinancialPredictor:
    """Base class for financial prediction models."""
    
    def __init__(self, model_type='linear', test_size=0.2, random_state=42):
        """
        Initialize predictor.
        
        Args:
            model_type (str): Type of model ('linear', 'random_forest', 'gradient_boosting')
            test_size (float): Test set size
            random_state (int): Random state for reproducibility
        """
        self.model_type = model_type
        self.test_size = test_size
        self.random_state = random_state
        self.model = self._create_model()
        self.history = {}
    
    def _create_model(self):
        """Create the specified model."""
        if self.model_type == 'linear':
            return LinearRegression()
        elif self.model_type == 'random_forest':
            return RandomForestRegressor(random_state=self.random_state, n_estimators=100)
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingRegressor(random_state=self.random_state, n_estimators=100)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(self, X, y):
        """
        Train the model.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target variable
        
        Returns:
            dict: Training metrics
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )
        
        self.model.fit(X_train, y_train)
        
        # Store training history
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        self.history = {
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
            'train_mae': mean_absolute_error(y_train, train_pred),
            'test_mae': mean_absolute_error(y_test, test_pred),
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_test, test_pred),
        }
        
        return self.history
    
    def predict(self, X):
        """
        Make predictions.
        
        Args:
            X (pd.DataFrame): Feature matrix
        
        Returns:
            np.ndarray: Predictions
        """
        return self.model.predict(X)
    
    def get_feature_importance(self):
        """
        Get feature importance if available.
        
        Returns:
            dict: Feature importance mapping
        """
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(range(len(self.model.feature_importances_)), 
                          self.model.feature_importances_))
        elif hasattr(self.model, 'coef_'):
            return dict(zip(range(len(self.model.coef_)), self.model.coef_))
        else:
            return None


class EnsemblePredictor:
    """Ensemble of multiple predictors."""
    
    def __init__(self, model_types=['linear', 'random_forest', 'gradient_boosting']):
        """
        Initialize ensemble.
        
        Args:
            model_types (list): List of model types to combine
        """
        self.predictors = {
            model_type: FinancialPredictor(model_type=model_type)
            for model_type in model_types
        }
    
    def train(self, X, y):
        """
        Train all models.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target variable
        
        Returns:
            dict: Training metrics for all models
        """
        results = {}
        for model_type, predictor in self.predictors.items():
            results[model_type] = predictor.train(X, y)
        return results
    
    def predict(self, X):
        """
        Make ensemble predictions (average).
        
        Args:
            X (pd.DataFrame): Feature matrix
        
        Returns:
            np.ndarray: Ensemble predictions
        """
        predictions = np.column_stack([
            predictor.predict(X) 
            for predictor in self.predictors.values()
        ])
        return np.mean(predictions, axis=1)

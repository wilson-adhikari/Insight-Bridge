"""Duplicates Handler Module"""
import pandas as pd
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class DuplicateHandler:
    """Handle duplicate rows in dataframes"""
    
    def remove(self, df: pd.DataFrame, subset: Optional[List[str]] = None, keep: str = 'first') -> pd.DataFrame:
        """Remove duplicate rows"""
        df = df.copy()
        before = len(df)
        df = df.drop_duplicates(subset=subset, keep=keep)
        after = len(df)
        
        logger.info(f"Removed {before - after} duplicate rows from {before} total rows")
        return df
    
    @staticmethod
    def get_duplicate_report(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Generate duplicate rows report"""
        duplicates = df[df.duplicated(subset=subset, keep=False)]
        
        if len(duplicates) > 0:
            logger.info(f"Found {len(duplicates)} duplicate rows")
            return duplicates.sort_values(by=subset if subset else list(df.columns))
        else:
            logger.info("No duplicates found")
            return pd.DataFrame()
    
    @staticmethod
    def find_partial_duplicates(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Find duplicate rows based on specific columns"""
        duplicates = df[df.duplicated(subset=columns, keep=False)]
        return duplicates.sort_values(by=columns)

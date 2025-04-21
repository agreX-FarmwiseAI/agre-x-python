import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
import os
import logging
import json

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """
    Utility class for processing Excel files
    """
    @staticmethod
    def read_excel(file_path: str, sheet_name: Optional[Union[str, int]] = 0) -> Tuple[bool, Union[pd.DataFrame, str]]:
        """
        Read data from an Excel file
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name or index of the sheet to read
        
        Returns:
            Tuple of (success, data or error message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return True, df
        
        except Exception as e:
            error_msg = f"Error reading Excel file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def write_excel(data: pd.DataFrame, file_path: str, sheet_name: str = "Sheet1") -> Tuple[bool, Optional[str]]:
        """
        Write data to an Excel file
        
        Args:
            data: DataFrame to write
            file_path: Path to save the Excel file
            sheet_name: Name of the sheet
        
        Returns:
            Tuple of (success, error message if any)
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to Excel file
            data.to_excel(file_path, sheet_name=sheet_name, index=False)
            return True, None
        
        except Exception as e:
            error_msg = f"Error writing Excel file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def dataframe_to_json(df: pd.DataFrame) -> str:
        """
        Convert a DataFrame to JSON string
        
        Args:
            df: DataFrame to convert
        
        Returns:
            JSON string
        """
        return df.to_json(orient="records")
    
    @staticmethod
    def dataframe_to_dict(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert a DataFrame to a list of dictionaries
        
        Args:
            df: DataFrame to convert
        
        Returns:
            List of dictionaries
        """
        return df.to_dict(orient="records")
    
    @staticmethod
    def json_to_dataframe(json_str: str) -> pd.DataFrame:
        """
        Convert a JSON string to a DataFrame
        
        Args:
            json_str: JSON string to convert
        
        Returns:
            DataFrame
        """
        return pd.read_json(json_str, orient="records")
    
    @staticmethod
    def dict_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a list of dictionaries to a DataFrame
        
        Args:
            data: List of dictionaries to convert
        
        Returns:
            DataFrame
        """
        return pd.DataFrame(data)


# Example usage
if __name__ == "__main__":
    # Example data
    data = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35],
        "City": ["New York", "London", "Paris"]
    })
    
    # Write to Excel
    success, error = ExcelProcessor.write_excel(data, "example.xlsx")
    if success:
        print("Excel file written successfully")
    else:
        print(f"Error: {error}")
    
    # Read from Excel
    success, result = ExcelProcessor.read_excel("example.xlsx")
    if success:
        print("Excel file read successfully")
        print(result)
    else:
        print(f"Error: {result}")
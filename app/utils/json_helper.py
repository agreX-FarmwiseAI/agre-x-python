import json
from typing import Dict, Any, List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class JsonHelper:
    """
    Utility class for JSON operations
    """
    @staticmethod
    def parse_json(json_str: str) -> Union[Dict[str, Any], List[Any], None]:
        """
        Parse a JSON string
        
        Args:
            json_str: JSON string to parse
        
        Returns:
            Parsed JSON or None if parsing fails
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            return None
    
    @staticmethod
    def to_json(data: Union[Dict[str, Any], List[Any]]) -> Optional[str]:
        """
        Convert data to a JSON string
        
        Args:
            data: Data to convert
        
        Returns:
            JSON string or None if conversion fails
        """
        try:
            return json.dumps(data)
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}")
            return None
    
    @staticmethod
    def read_json_file(file_path: str) -> Union[Dict[str, Any], List[Any], None]:
        """
        Read a JSON file
        
        Args:
            file_path: Path to the JSON file
        
        Returns:
            Parsed JSON or None if reading fails
        """
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file: {str(e)}")
            return None
    
    @staticmethod
    def write_json_file(file_path: str, data: Union[Dict[str, Any], List[Any]]) -> bool:
        """
        Write data to a JSON file
        
        Args:
            file_path: Path to save the JSON file
            data: Data to write
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file: {str(e)}")
            return False
    
    @staticmethod
    def merge_json(json1: Dict[str, Any], json2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two JSON objects
        
        Args:
            json1: First JSON object
            json2: Second JSON object
        
        Returns:
            Merged JSON object
        """
        result = json1.copy()
        result.update(json2)
        return result
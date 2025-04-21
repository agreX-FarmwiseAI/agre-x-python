import subprocess
import os
import logging
import json
from typing import Dict, Any, Optional, Tuple, List, Union

from app.core.config import settings

logger = logging.getLogger(__name__)


class PythonService:
    """
    Service for executing Python scripts
    """
    @staticmethod
    def run_script(
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        """
        Run a Python script
        
        Args:
            script_path: Path to the script
            args: List of arguments to pass to the script
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (success, output or error message)
        """
        try:
            # Check if script exists
            if not os.path.exists(script_path):
                return False, f"Script not found: {script_path}"
            
            # Build command
            command = [settings.PYTHON_EXECUTABLE, script_path]
            if args:
                command.extend(args)
            
            # Run script
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                return False, f"Script execution timed out after {timeout} seconds"
            
            # Check return code
            if process.returncode != 0:
                return False, f"Script execution failed with error: {stderr}"
            
            # Try to parse output as JSON
            try:
                output = json.loads(stdout)
                return True, output
            except json.JSONDecodeError:
                # Return output as string if not JSON
                return True, stdout.strip()
        
        except Exception as e:
            error_msg = f"Error running Python script: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def run_model_training(
        model_type: str,
        parameters: Dict[str, Any],
        data_path: str,
        output_path: str
    ) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        """
        Run a model training job
        
        Args:
            model_type: Type of model to train
            parameters: Model parameters
            data_path: Path to training data
            output_path: Path to save the model
        
        Returns:
            Tuple of (success, output or error message)
        """
        try:
            # Create temporary JSON file with parameters
            params_file = f"{output_path}.params.json"
            with open(params_file, "w") as f:
                json.dump({
                    "model_type": model_type,
                    "parameters": parameters,
                    "data_path": data_path,
                    "output_path": output_path
                }, f)
            
            # Run training script
            script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "train_model.py")
            return PythonService.run_script(script_path, [params_file])
        
        except Exception as e:
            error_msg = f"Error setting up model training: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        finally:
            # Clean up parameters file
            if os.path.exists(params_file):
                os.remove(params_file)
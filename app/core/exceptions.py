from fastapi import HTTPException
from typing import Any, Dict, Optional


class ResourceNotFoundException(Exception):
    """
    Exception raised when a resource is not found.
    """
    def __init__(self, resource_type: str, resource_id: Any):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = f"{resource_type} with id {resource_id} not found"
        super().__init__(self.message)


class ErrorResponse:
    """
    Standard error response class
    """
    def __init__(
        self,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        result = {
            "message": self.message,
            "status_code": self.status_code
        }
        if self.details:
            result["details"] = self.details
        return result

    @classmethod
    def from_exception(cls, exc: Exception, status_code: int = 500) -> "ErrorResponse":
        return cls(
            message=str(exc),
            status_code=status_code
        )


def get_resource_not_found_exception(resource_type: str, resource_id: Any) -> HTTPException:
    """
    Create a HTTPException for resource not found
    """
    return HTTPException(
        status_code=404,
        detail=f"{resource_type} with id {resource_id} not found"
    )
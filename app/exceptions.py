class ApplicationError(Exception):
    def __init__(self, status_code=500, message="an error occurred", errors=None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.errors = errors

class NotFoundError(ApplicationError):
    def __init__(self, message="resource not found"):
        super().__init__(404, message)

# Usage example:
try:
    # Some code that may raise an error
    raise NotFoundError("This resource was not found")
except NotFoundError as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")

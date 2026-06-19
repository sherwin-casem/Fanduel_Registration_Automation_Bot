class AutomationError(Exception):
    """Base error for automation failures."""


class AutomationStopped(AutomationError):
    """Raised when a user requests the current automation run to stop."""

    def __init__(self):
        super().__init__("Automation stopped by user")


class AccountAlreadyExists(AutomationError):
    """Raised when the site routes an email to the existing-account flow."""

    def __init__(self):
        super().__init__("Account already exist")

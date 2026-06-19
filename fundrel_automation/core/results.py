from dataclasses import dataclass

from .errors import AccountAlreadyExists


RESULT_CREATED = "created"
RESULT_SUCCESS_NOT_CREATED = "success_not_created"
RESULT_WE_FOUND_ANOTHER_ACCOUNT = "we_found_another_account"
RESULT_SERVICE_NOT_AVAILABLE = "service_not_available"
RESULT_UNABLE_TO_VERIFY = "unable_to_verify"
RESULT_ERROR = "error"
ACCOUNT_ALREADY_EXISTS_MESSAGE = "Account already exist"

@dataclass(frozen=True)
class AutomationOutcome:
    success: bool
    created: bool
    reason: str
    screenshot_prefix: str
    skipped: bool = False
    we_found_another_account: bool = False
    service_not_available: bool = False
    unable_to_verify: bool = False


def outcome_from_result(is_created, result_status):
    if result_status == RESULT_WE_FOUND_ANOTHER_ACCOUNT:
        return AutomationOutcome(
            success=True,
            created=False,
            reason="We found another account",
            screenshot_prefix=RESULT_WE_FOUND_ANOTHER_ACCOUNT,
            we_found_another_account=True,
        )

    if result_status == RESULT_SERVICE_NOT_AVAILABLE:
        return AutomationOutcome(
            success=True,
            created=False,
            reason="Service not available",
            screenshot_prefix="service_not_available",
            service_not_available=True,
        )

    if result_status == RESULT_UNABLE_TO_VERIFY:
        return AutomationOutcome(
            success=True,
            created=False,
            reason="Unable to verify data",
            screenshot_prefix=RESULT_UNABLE_TO_VERIFY,
            unable_to_verify=True,
        )

    if result_status == RESULT_SUCCESS_NOT_CREATED:
        return AutomationOutcome(
            success=True,
            created=False,
            reason="Finished without creating account (standard success fallback).",
            screenshot_prefix="success",
        )

    return AutomationOutcome(
        success=True,
        created=bool(is_created),
        reason="Successfully completed.",
        screenshot_prefix="success",
    )


def outcome_from_exception(exc):
    reason = str(exc)
    if isinstance(exc, AccountAlreadyExists) or ACCOUNT_ALREADY_EXISTS_MESSAGE in reason:
        return AutomationOutcome(
            success=False,
            created=False,
            reason=reason,
            screenshot_prefix="error",
            skipped=True,
        )

    return AutomationOutcome(
        success=False,
        created=False,
        reason=reason,
        screenshot_prefix=RESULT_ERROR,
    )


def apply_outcome_to_account(account, outcome, screenshot_path, username=None, timestamp=None):
    account["ran"] = True
    account["success"] = outcome.success
    account["created"] = outcome.created
    account["skipped"] = outcome.skipped
    account["we_found_another_account"] = outcome.we_found_another_account
    account["service_not_available"] = outcome.service_not_available
    account["unable_to_verify"] = outcome.unable_to_verify
    account["reason"] = outcome.reason
    account["screenshot"] = screenshot_path

    if username is not None:
        account["username"] = username
    if timestamp is not None:
        account["timestamp"] = timestamp

    return account

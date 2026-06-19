STATUS_PENDING = "Pending"
STATUS_CREATED = "Created"
STATUS_FAILED = "Failed"
STATUS_SKIPPED = "Skipped"
STATUS_ANOTHER_ACCOUNT = "Another Account"
STATUS_SERVICE_UNAVAILABLE = "Service Unavailable"
STATUS_UNABLE_TO_VERIFY = "Unable to Verify"

TAB_STATUS_MAP = {
    "pending": STATUS_PENDING,
    "created": STATUS_CREATED,
    "failed": STATUS_FAILED,
    "skipped": STATUS_SKIPPED,
    "another_account": STATUS_ANOTHER_ACCOUNT,
    "service_unavailable": STATUS_SERVICE_UNAVAILABLE,
    "unable_to_verify": STATUS_UNABLE_TO_VERIFY,
}


def classify_account(account):
    if account.get("skipped"):
        return STATUS_SKIPPED
    if account.get("unable_to_verify"):
        return STATUS_UNABLE_TO_VERIFY
    if account.get("we_found_another_account"):
        return STATUS_ANOTHER_ACCOUNT
    if account.get("service_not_available"):
        return STATUS_SERVICE_UNAVAILABLE
    if account.get("ran"):
        return STATUS_CREATED if account.get("created") else STATUS_FAILED
    return STATUS_PENDING


def reset_to_pending(account):
    for key in (
        "ran",
        "success",
        "created",
        "skipped",
        "we_found_another_account",
        "service_not_available",
        "unable_to_verify",
    ):
        account[key] = False

    account["reason"] = ""
    account.pop("screenshot", None)
    account.pop("timestamp", None)
    return account


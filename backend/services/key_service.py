import keyring

_SERVICE = "multiyou"


def store_api_key(model_id: int, api_key: str) -> None:
    keyring.set_password(_SERVICE, f"model_{model_id}", api_key)


def get_api_key(model_id: int) -> str | None:
    return keyring.get_password(_SERVICE, f"model_{model_id}")


def delete_api_key(model_id: int) -> None:
    try:
        keyring.delete_password(_SERVICE, f"model_{model_id}")
    except Exception:
        pass

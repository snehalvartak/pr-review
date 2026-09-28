import requests


def fetch(url, timeout=5):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

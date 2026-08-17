class MapboxStaticMapProvider:
    def __init__(self, access_token: str):
        self._access_token = access_token

    def map_url(self, lat: float, lon: float, zoom: int = 16, width: int = 600, height: int = 400) -> str:
        return (
            f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/"
            f"pin-s+ff0000({lon},{lat})/{lon},{lat},{zoom}/{width}x{height}"
            f"?access_token={self._access_token}"
        )

    def satellite_url(self, lat: float, lon: float, zoom: int = 18, width: int = 600, height: int = 400) -> str:
        return (
            f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"
            f"{lon},{lat},{zoom}/{width}x{height}"
            f"?access_token={self._access_token}"
        )

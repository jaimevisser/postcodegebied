import json
import os

class PolyCache():
    def __init__(self, filename: str, property: str) -> None:
        self.cache = {}
        self.filename = filename
        self.property = property

        if os.path.exists(self.filename):
            with open(self.filename, "r") as file:
                self.cache = json.load(file)

    def update(self, poly: dict) -> None:
        self.cache[self.key(poly)] = poly[self.property]

        with open(self.filename, "w") as file:
            json.dump(self.cache, file)

    def update_all(self, postal_codes: list[dict]) -> None:
        for pc in postal_codes:
            self.cache[self.key(pc)] = pc.get(self.property,[])

        with open(self.filename, "w") as file:
            json.dump(self.cache, file)

    def key(self, postal_code):
        return f"{postal_code['start']}-{postal_code['end']}"
    
    def get_cached(self, postal_codes):
        cached = [pc for pc in postal_codes if self.key(pc) in self.cache]
        uncached = [pc for pc in postal_codes if self.key(pc) not in self.cache]

        for pc in cached:
            pc[self.property] = self.cache[self.key(pc)]

        return cached, uncached

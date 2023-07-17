import osmium
import numpy as np
from scipy.spatial import ConvexHull
import yaml
import json
from web_server import start_web_server


class PostalCodeHandler(osmium.SimpleHandler):
    def __init__(self, postal_code_ranges):
        super(PostalCodeHandler, self).__init__()
        self.point_clouds = {}
        self.postal_code_ranges = postal_code_ranges

    def node(self, n):
        if postal_code_tag in n.tags and self._is_valid_postal_code(n.tags[postal_code_tag]):
            postal_code = int(n.tags[postal_code_tag][:4])  # Extract first four digits of postal code
            for (start, end) in self.postal_code_ranges:
                if start <= postal_code <= end:
                    if (start, end) not in self.point_clouds:
                        self.point_clouds[(start, end)] = []
                    self.point_clouds[(start, end)].append((n.location.lon, n.location.lat))
                    break

    def _is_valid_postal_code(self, postal_code):
        code = postal_code[:4]  # Extract first four digits of postal code
        return code.isdigit()


def extract_points(xml_file, postal_code_ranges):
    handler = PostalCodeHandler(postal_code_ranges)
    handler.apply_file(xml_file)
    return handler.point_clouds


def calculate_outer_boundaries(point_clouds):
    polygons = {}

    if not point_clouds:
        raise ValueError("No points found for the given postal code ranges.")

    for (start, end), points in point_clouds.items():
        points_array = np.array(points)
        hull = ConvexHull(points_array)
        polygons[(start, end)] = points_array[hull.vertices]

    return polygons


def generate_geojson(polygons, geojson_file):
    features = []
    for (start, end), points in polygons.items():
        feature = {
            "type": "Feature",
            "properties": {
                "start": start,
                "end": end
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [points.tolist()]
            }
        }
        features.append(feature)

    data = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(geojson_file, "w") as file:
        json.dump(data, file)


if __name__ == '__main__':
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    xml_file = config['xml_file']
    postal_code_ranges = [(int(r['start']), int(r['end'])) for r in config['postal_code_ranges']]
    postal_code_tag = config['postal_code_tag']
    geojson_file = "polygons.geojson"
    web_server_port = 8000

    try:
        point_clouds = extract_points(xml_file, postal_code_ranges)
        polygons = calculate_outer_boundaries(point_clouds)
        generate_geojson(polygons, geojson_file)
        print(f"GeoJSON file saved as {geojson_file}")

        start_web_server(web_server_port)
    except ValueError as e:
        print(e)

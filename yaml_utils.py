import yaml
import numpy as np


def save_polygons_to_yaml(polygons, yaml_file):
    data = []
    for (start, end), points in polygons.items():
        points_data = [{'lat': float(lat), 'lon': float(lon)} for lon, lat in points]
        data.append({'start': start, 'end': end, 'points': points_data})
    with open(yaml_file, "w") as file:
        yaml.dump({'polygons': data}, file)


def load_polygons_from_yaml(yaml_file):
    with open(yaml_file, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    polygons = {}
    for item in data['polygons']:
        start = item['start']
        end = item['end']
        points = np.array([(float(point['lon']), float(point['lat'])) for point in item['points']])
        polygons[(start, end)] = points
    return polygons

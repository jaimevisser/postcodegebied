import os
import osmium
import numpy as np
import alphashape
from shapely.geometry import MultiPolygon
import yaml
import json
import re
from polycache import PolyCache
from web_server import start_web_server
import concurrent.futures
from gen_postal_codes import gen_postal_codes

polycache = PolyCache("data/polycache.json",'coordinates')
pointcache = PolyCache("data/pointcache.json", 'points')

def key(postal_code):
    return f"{postal_code['start']}-{postal_code['end']}"

class PostalCodeHandler(osmium.SimpleHandler):
    def __init__(self, postal_code_ranges):
        super(PostalCodeHandler, self).__init__()
        self.postal_code_ranges = postal_code_ranges
        self.pc_count = 0
        self.node_count = 0

    def node(self, n):
        self.node_count+=1
        if postal_code_tag in n.tags:
            if self._is_valid_postal_code(n.tags[postal_code_tag]):
                self.pc_count+=1
                postal_code = int(n.tags[postal_code_tag][:4])  # Extract first four digits of postal code
                for pcr in self.postal_code_ranges:
                    if int(pcr['start']) <= postal_code <= int(pcr['end']):
                        if 'points' not in pcr:
                            pcr['points'] = []
                        pcr['points'].append((n.location.lon, n.location.lat))
                        break

    def _is_valid_postal_code(self, postal_code):
        pattern = r"[0-9]{4} ?[A-Za-z]{2}"
        return re.match(pattern, postal_code) is not None

def extract_points(xml_file, postal_code_ranges):
    cached, uncached = pointcache.get_cached(postal_code_ranges)
    print(f"{len(cached)} cached pointclouds reused, {len(uncached)} uncached")

    if len(uncached) > 0:
        handler = PostalCodeHandler(uncached)
        handler.apply_file(xml_file)
        print(f"{handler.pc_count}/{handler.node_count} nodes processed")

        pointcache.update_all(handler.postal_code_ranges)

        return handler.postal_code_ranges + cached
    
    return cached

def calculate_boundary(cloud):
        points_array = np.array(cloud.pop('points',[]))
        alpha = 55
        hull = alphashape.alphashape(points_array, alpha)
        while type(hull) is MultiPolygon and alpha > 10:
            alpha = alpha - 2
            hull = alphashape.alphashape(points_array, alpha)
        print(f"Ended with alpha at {alpha}")
        cloud['coordinates'] = [np.array(list(hull.exterior.coords)).tolist()]

        return cloud

def calculate_outer_boundaries(point_clouds):

    if not point_clouds:
        print("No pointclouds need boundary calculations")
        return []
    
    point_clouds = [c for c in point_clouds if 'points' in c]
    point_clouds = [c for c in point_clouds if len(c['points']) > 0]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(calculate_boundary, i) for i in point_clouds]

        results = []

        i = 0
        for future in futures:
            i = i + 1
            result = future.result()
            results.append(result)
            polycache.update(result)
            print(f"Progress: {i} / {len(futures)}")

    return results


def generate_geojson(polygons, geojson_file):
    features = []
    for item in polygons:
        feature = {
            "type": "Feature",
            "properties": {
                "start": item['start'],
                "end": item['end'],
                "tooltip": f"{item['start']} - {item['end']}<br/>{item['name']}<br/>{item['other_therapist']}",
                "colour": item['colour']
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": item['coordinates']
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

    gen_postal_codes()
    with open('data/postal_codes.yaml') as file:
        postal_code_ranges = yaml.load(file, Loader=yaml.FullLoader)['postal_codes']

    xml_file = config['xml_file']
    postal_code_tag = config['postal_code_tag']
    point_clouds_file = "data/point_clouds.json"
    geojson_file = "polygons.geojson"
    web_server_port = 8880

    try:
        if not os.path.isfile(geojson_file):

            cached, uncached = polycache.get_cached(postal_code_ranges)
            print(f"{len(cached)} cached polygons reused, {len(uncached)} uncached")
            for pc in uncached:
                print(polycache.key(pc))

            print(" ## Extracting points")
            point_clouds = extract_points(xml_file, uncached)

            print(" ## Calculating boundaries")
            polygons = calculate_outer_boundaries(point_clouds)

            print(" ## Converting data to geojson format")
            generated = cached + polygons
            generate_geojson(generated, geojson_file)

            print(f" ## GeoJSON file saved as {geojson_file}")

        start_web_server(web_server_port)
    except ValueError as e:
        print(e)

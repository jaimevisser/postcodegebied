import os
import osmium
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image, ImageDraw
from yaml_utils import save_polygons_to_yaml, load_polygons_from_yaml


class PostalCodeHandler(osmium.SimpleHandler):
    def __init__(self, postal_code_ranges):
        super(PostalCodeHandler, self).__init__()
        self.polygons = {}
        self.postal_code_ranges = postal_code_ranges

    def node(self, n):
        if postal_code_tag in n.tags and self._is_valid_postal_code(n.tags[postal_code_tag]):
            postal_code = int(n.tags[postal_code_tag][:4])  # Extract first four digits of postal code
            for (start, end) in self.postal_code_ranges:
                if start <= postal_code <= end:
                    if (start, end) not in self.polygons:
                        self.polygons[(start, end)] = []
                    self.polygons[(start, end)].append((n.location.lon, n.location.lat))
                    break

    def _is_valid_postal_code(self, postal_code):
        code = postal_code[:4]  # Extract first four digits of postal code
        return code.isdigit()


def extract_outer_boundaries(xml_file, postal_code_ranges):
    handler = PostalCodeHandler(postal_code_ranges)
    handler.apply_file(xml_file)
    polygons = {}

    if not handler.polygons:
        raise ValueError("No points found for the given postal code ranges.")

    for (start, end), points in handler.polygons.items():
        points_array = np.array(points)
        hull = ConvexHull(points_array)
        polygons[(start, end)] = points_array[hull.vertices]

    return polygons


def draw_polygon(polygon, file_path):
    canvas_size = (2000, 2000)
    padding = 10

    min_x, min_y = np.min(polygon[:, 0]), np.min(polygon[:, 1])
    max_x, max_y = np.max(polygon[:, 0]), np.max(polygon[:, 1])
    polygon_width = max_x - min_x
    polygon_height = max_y - min_y

    # Calculate the scale factor for both width and height, considering the padding
    scale_factor = min(
        (canvas_size[0] - 2 * padding) / polygon_width,
        (canvas_size[1] - 2 * padding) / polygon_height
    )

    # Apply the scale factor and padding to the polygon
    scaled_polygon = [(int((x - min_x) * scale_factor) + padding, int((y - min_y) * scale_factor) + padding)
                      for x, y in polygon]

    image = Image.new("RGB", canvas_size, color="white")
    draw = ImageDraw.Draw(image)
    draw.polygon(scaled_polygon, outline="black", fill=None)

    image.save(file_path, "PNG")


if __name__ == '__main__':
    import yaml

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    xml_file = config['xml_file']
    postal_code_ranges = [(int(r['start']), int(r['end'])) for r in config['postal_code_ranges']]
    postal_code_tag = config['postal_code_tag']
    output_png_file = "output.png"
    polygons_yaml_file = "polygons.yaml"

    try:
        if not os.path.exists(polygons_yaml_file):
            polygons = extract_outer_boundaries(xml_file, postal_code_ranges)
            save_polygons_to_yaml(polygons, polygons_yaml_file)
        else:
            polygons = load_polygons_from_yaml(polygons_yaml_file)

        first_range = next(iter(polygons))
        draw_polygon(polygons[first_range], output_png_file)
        print(f"Outer boundary polygon saved as {output_png_file}")
    except ValueError as e:
        print(e)

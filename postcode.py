import osmium
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image, ImageDraw
import yaml


class PostalCodeHandler(osmium.SimpleHandler):
    def __init__(self, postal_code_ranges):
        super(PostalCodeHandler, self).__init__()
        self.points = [[] for _ in range(len(postal_code_ranges))]
        self.postal_code_ranges = postal_code_ranges

    def node(self, n):
        if postal_code_tag in n.tags and self._is_valid_postal_code(n.tags[postal_code_tag]):
            postal_code = int(n.tags[postal_code_tag][:4])  # Extract first four digits of postal code
            for i, (start, end) in enumerate(self.postal_code_ranges):
                if start <= postal_code <= end:
                    self.points[i].append((n.location.lon, n.location.lat))
                    break

    def _is_valid_postal_code(self, postal_code):
        code = postal_code[:4]  # Extract first four digits of postal code
        return code.isdigit()


def extract_outer_boundaries(xml_file, postal_code_ranges):
    handler = PostalCodeHandler(postal_code_ranges)
    handler.apply_file(xml_file)
    polygons = []

    if not handler.points[0]:
        raise ValueError("No points found for the given postal code range.")

    for i in handler.points:
        points = np.array(i)
        # Calculate the convex hull to get the outer boundary polygon
        hull = ConvexHull(points)  
        polygons.append(points[hull.vertices])

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
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    xml_file = config['xml_file']
    postal_code_ranges = [(int(r['start']), int(r['end'])) for r in config['postal_code_ranges']]
    postal_code_tag = config['postal_code_tag']
    output_png_file = "output.png"

    try:
        polygons = extract_outer_boundaries(xml_file, postal_code_ranges)
        draw_polygon(polygons[0], output_png_file)
        print(f"Outer boundary polygon saved as {output_png_file}")
    except ValueError as e:
        print(e)

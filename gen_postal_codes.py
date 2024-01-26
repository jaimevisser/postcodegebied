import re
import yaml

def gen_postal_codes():
    with open('data/input.txt', 'r') as file:
        data = file.read()

    color_dict = {
        '1': '#FF0000',  # Red
        '2': '#00FF00',  # Green
        '3': '#0000FF',  # Blue
        '4': '#FFA500',  # Orange
        '5': '#800080',  # Purple
        '6': '#FFFF00',  # Yellow
        '7': '#00FFFF',  # Cyan
        '8': '#FF00FF',  # Magenta
        '9': '#008000',  # Dark Green
        '10': '#800000',  # Maroon
        '11': '#FFD700',  # Gold
        '12': '#8A2BE2',  # Blue Violet
        '13': '#00FF7F',  # Spring Green
        '14': '#FF6347',  # Tomato
        '15': '#40E0D0',   # Turquoise
        '16': '#000080' # Dark blue
    }

    # Remove " i.o" using regex
    data_cleaned = re.sub(r'\si\.o\.?', '', data).replace('\u200b','')

    # Initialize a dictionary to store therapist data
    therapists_dict = {}

    # Define the regex pattern to extract information from each line
    pattern = re.compile(r'(\d+) t/m (\d+) - ([^&]+)(&[^&]+)?')

    # Iterate through each line in the cleaned data
    for line in data_cleaned.strip().split('\n'):
        match = pattern.match(line.strip())
        if match:
            start, end, therapist, other_therapist = match.groups()
            key = therapist.split('&')[0].strip()
            if key not in therapists_dict:
                therapists_dict[key] = {
                    'name': key,
                    'postal_codes': []
                }
                if key in color_dict:
                    therapists_dict[key]['colour'] = color_dict[key]
                else:
                    therapists_dict[key]['colour'] = color_dict.popitem()[1]
            therapists_dict[key]['postal_codes'].append({
                'start': start,
                'end': end,
                'other_therapist': other_therapist[1:].strip() if other_therapist else ''
            })

    # Convert the dictionary values to a list
    therapists_list: list[dict] = list(therapists_dict.values())

    postal_codes = []

    for therapist in therapists_list:
        others = therapist.copy()
        others.pop('postal_codes')

        for pc in therapist['postal_codes']:
            pc.update(others)
            postal_codes.append(pc)

    # Create a dictionary with the therapists data
    result = {'postal_codes': postal_codes}

    # Convert the dictionary to YAML
    yaml_data = yaml.dump(result)

    # Save the YAML data to a file
    with open('data/postal_codes.yaml', 'w') as file:
        file.write(yaml_data)

    print(" ## Postal codes generated")

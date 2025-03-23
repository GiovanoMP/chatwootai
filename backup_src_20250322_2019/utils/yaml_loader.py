import os
import yaml

def load_yaml_config(path):
    config = {}
    for filename in os.listdir(path):
        if filename.endswith(('.yaml', '.yml')):
            with open(os.path.join(path, filename)) as file:
                domain = yaml.safe_load(file)
                config[domain['name']] = domain
    return config

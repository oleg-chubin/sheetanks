import lya
import os

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "config.yaml"
)

yaml_file = os.environ.get('CONFIG', DEFAULT_PATH)

settings = lya.AttrDict.from_yaml(yaml_file)

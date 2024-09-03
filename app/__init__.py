default_app_config = 'app.apps.AppConfig'

from .db_models.node_resolver import custom_install_labels, resolve_node_class

# Run the custom label installation
custom_install_labels()

# Set the node class resolver
from neomodel import config
config.NODE_CLASS_REGISTRY = resolve_node_class

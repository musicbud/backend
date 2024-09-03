from neomodel import StructuredNode, UniqueIdProperty

class CustomStructuredNode(StructuredNode):
    uid = UniqueIdProperty()

    __abstract_node__ = True

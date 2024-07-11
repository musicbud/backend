from neomodel import StructuredNode, StringProperty


class LikedItem(StructuredNode):
    uid = StringProperty(required=True, unique_index=True)

    def serialize(self):
        return {
            'uid': self.uid,
        }


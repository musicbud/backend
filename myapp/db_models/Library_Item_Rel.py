from neomodel import StructuredRel, IntegerProperty

# LibraryItem relationship with playcount and tagcount
class LibraryItemRel(StructuredRel):
    playcount = IntegerProperty()
    tagcount = IntegerProperty()


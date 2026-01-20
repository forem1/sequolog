"""Source model - data source for events"""

class Source:
    def __init__(
        self,
        source_id: str,
        description: str,
        reference: str
        #TODO: implement reference type feature
    ):
        self.source_id = source_id
        self.description = description
        self.reference = reference

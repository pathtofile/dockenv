"""
Mocked classes
"""


# pylint: disable=R0903
class MockedImage():
    """
    Mocked Class of docker.models.images.Image
    """
    tags = None

    def __init__(self, tags):
        self.tags = tags

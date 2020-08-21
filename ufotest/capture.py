"""
A module containing the code related to actually capturing images from the camera.
"""


def get_frame():
    # We are going to do all the file related operations inside the tmp folder and then the return of this function
    # will be the file path of the image. It is then up to the caller of this function to decide where to copy this
    # file to.
    folder = '/tmp'

    # So to get a frame you first need to do a bunch of stuff with the "pci" command...
    pass

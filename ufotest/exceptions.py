"""Custom exception classes for the ufotest project and other exception related utility
"""
from typing import Type


# == UTILITY FUNCTIONS ==

def raise_if(condition: bool, exception: Type[Exception], error_message: str) -> None:
    """Raises the given *exception* with the *error_message*, if and only if the *condition* is True.

    :param condition: The boolean condition which decides whether to raise the error or not
    :param exception: An exception class which will be raised if the condition is True
    :param error_message: The error message, which is passed to the exception's constructor
    """
    if bool(condition):
        raise exception(error_message)


# == CUSTOM EXCEPTION CLASSES ==

class IncompleteBuildError(Exception):
    """When attempting to process an incomplete build context, when you really need a completed build.
    """
    pass


class BuildError(Exception):
    """When something goes wrong during the build process, this is the error that is being passed out.
    """
    pass


class PciError(Exception):
    """When something goes wrong during the PCI communication with the camera.
    """


class FrameDecodingError(Exception):
    """When something goes wrong during the decoding of the frame
    """

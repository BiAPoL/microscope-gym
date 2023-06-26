# I am using the following interface features:
from microscope_gym.interface import Camera, Microscope
from skimage.feature import canny


def canny_edge_detector(microscope: Microscope, *args, **kwargs) -> "numpy.array":
    """Applies Canny Edge Detector to Microscope image

    https://scikit-image.org/docs/stable/auto_examples/edges/plot_canny.html

    Args:
        microscope (Microscope): microscope object from microscope_gym

    Returns:
        numpy.array: results of canny edge detection
    """
    return canny(microscope.acquire_image(), *args, **kwargs)

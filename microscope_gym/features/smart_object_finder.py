'''Smart Object Finder uses the random forest classifier apoc to find objects in a microscope sample.'''

import numpy as np
import pyclesperanto_prototype as cle
import apoc

# I am using the following interface features:
from microscope_gym.interface import Objective, Stage, Camera, Microscope


class SmartObjectFinder:
    '''Smart Object Finder uses the random forest classifier apoc to find objects in a microscope sample.

    methods:
        find_objects_in_image(image: numpy.ndarray) -> list
        scan_for_objects(x_range, y_range) -> list
    '''

    def __init__(self, microscope: Microscope,
                 trained_apoc_segmenter: apoc.ObjectSegmenter, features: str):
        self.microscope = microscope
        self.segmenter = trained_apoc_segmenter
        self.features = features

    def find_objects_in_image(self, overview_image: np.ndarray, object_size_range: tuple = None) -> list:
        '''Finds objects in a given image using the trained apoc segmenter.

        Arguments:
            overview_image {numpy.ndarray} -- Overview image to find objects in.
            size_range {tuple} -- Minimum and maximum size (in number of pixels) of objects to find.

        Returns:
            list -- List of objects found in the image.
        '''
        # Segment the image
        segmentation = self.segmenter.predict(features=self.features, image=overview_image)

        # Post-process the segmentation
        cle.merge_touching_labels(segmentation, labels_destination=segmentation)
        if object_size_range:
            cle.exclude_labels_outside_size_range(
                segmentation,
                destination=segmentation,
                minimum_size=object_size_range[0],
                maximum_size=object_size_range[1])

        return segmentation

    def find_centroids(self, segmentation) -> list:

        # Find centroids of the objects
        centroids = cle.centroids_of_labels(segmentation)
        return np.flip(np.asarray(np.transpose(centroids)), axis=1)

    def find_best_centroid(self, original_image, segmentation, metric='sum_intensity') -> list:
        '''Finds the centroid of the object in a segmentation that maximizes the given metric.

        Arguments:
            original_image {numpy.ndarray} -- Image to find objects in.
            segmentation {numpy.ndarray} -- Segmentation of the image.
            metric {str} -- Metric to sort the objects by. Must be a key in the output of cle.statistics_of_labelled_pixels().

        Returns:
            tuple -- (y, x) coordinates of the centroid.
        '''
        # Find centroids of the objects
        stats = cle.statistics_of_labelled_pixels(original_image, segmentation)
        pixel_x = stats['centroid_x'][np.argmax(stats[metric])]
        pixel_y = stats['centroid_y'][np.argmax(stats[metric])]

        return (pixel_y, pixel_x)

    def image_found_objects(self, imaging_positions: list, imaging_function: callable = None) -> list:
        '''Moves the microscope stage to each (y, x) position in imaging_positions and executes imaging_function (default: Microscope.acquire_image()).

        Arguments:
            imaging_positions {list} -- List of imaging positions.
            imaging_function {callable} -- Function to call to acquire an image at each position.

        Returns:
            list -- List of images acquired at the given positions.
        '''
        if imaging_function is None:
            imaging_function = self.microscope.acquire_image

        # Acquire images at the given positions
        images = []
        for y, x in imaging_positions:
            self.microscope.move_stage_to_nearest_position_in_range(y_position_um=y, x_position_um=x)
            images.append(imaging_function())

        return images

    def find_and_image_objects(self, overview_image: np.ndarray, object_size_range: tuple = None,
                               imaging_function: callable = None) -> list:
        '''Finds objects in an image and moves the microscope stage to each object to acquire an image.

        Arguments:
            overview_image {numpy.ndarray} -- Overview image to find objects in.
            size_range {tuple} -- Minimum and maximum size (in number of pixels) of objects to find.
            imaging_function {callable} -- Function to call to acquire an image at each position.

        Returns:
            list -- List of images acquired at the found positions.
        '''
        # Find objects in the image
        segmentation = self.find_objects_in_image(overview_image, object_size_range)
        positions = self.find_centroids(segmentation)

        # Acquire images at the found positions
        return self.image_found_objects(positions, imaging_function)

    def scan_for_objects(self, num_objects: int, y_range: tuple = None, x_range: tuple = None,
                         imaging_function: callable = None, object_size_range: tuple = None, metric='sum_intensity') -> list:
        '''Scans a given range of x and y positions and finds objects in each image.

        Arguments:
            num_objects: int
                number of objects to find.
            y_range:
                range of y positions to scan (start, end, step) in µm.
            x_range: tuple
                range of x positions to scan (start, end, step) in µm.
            imaging_function: callable (optional)
                Function to call to acquire an image at each position, default is Microscoope.acquire_image().
            object_size_range: tuple (optional)
                Minimum and maximum size (in number of pixels) of objects to find, default is None.
            metric: str (optional)
                Name of the metric to use to choose from multiple objects, default is 'sum_intensity'. Uses metrics from pyclesperanto_prototype.statistics_of_labelled_pixels().

        Returns:
            list -- List of objects found in the scanned images.
        '''
        if y_range is None:
            y_range = self.microscope.stage.y_range + (self.microscope.get_field_of_view_um()[0] * 1.1,)
        if x_range is None:
            x_range = self.microscope.stage.x_range + (self.microscope.get_field_of_view_um()[1] * 1.1,)
        if imaging_function is None:
            imaging_function = self.microscope.acquire_image

        # Scan the range of x and y positions
        images = []
        for y, x in self.microscope.scan_stage_positions(y_range=y_range, x_range=x_range):

            # Acquire image
            search_image = self.microscope.acquire_image()

            # Find objects in the image
            segmentation = self.find_objects_in_image(search_image, object_size_range)

            if segmentation.max() > 0:
                # center the stage on the object found that maximizes sum_intensity
                pixel_coordinates = self.find_best_centroid(search_image, segmentation)
                offset = self.microscope.get_stage_offset_from_pixel_coordinates(pixel_coordinates)
                y_new = y + offset[0]
                x_new = x + offset[1]
                self.microscope.move_stage_to_nearest_position_in_range(y_position_um=y_new, x_position_um=x_new)
                # save the image
                images.append(imaging_function())

            if len(images) >= num_objects:
                break

        return np.asarray(images)

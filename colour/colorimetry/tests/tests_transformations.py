#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines unit tests for :mod:`colour.colorimetry.transformations` module.
"""

from __future__ import division, unicode_literals

import numpy as np
import unittest

from colour.colorimetry import (
    CMFS,
    RGB_10_degree_cmfs_to_LMS_10_degree_cmfs,
    RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs,
    RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs,
    LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs,
    LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs)
from colour.utilities import ignore_numpy_errors

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013 - 2015 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = ['TestRGB_2_degree_cmfs_to_XYZ_2_degree_cmfs',
           'TestRGB_10_degree_cmfs_to_XYZ_10_degree_cmfs',
           'TestRGB_10_degree_cmfs_to_LMS_10_degree_cmfs',
           'TestLMS_2_degree_cmfs_to_XYZ_2_degree_cmfs',
           'TestLMS_10_degree_cmfs_to_XYZ_10_degree_cmfs']


class TestRGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(unittest.TestCase):
    """
    Defines :func:`colour.colorimetry.transformations.\
RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition unit tests methods.
    """

    def test_RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition.
        """

        cmfs = CMFS.get('CIE 1931 2 Degree Standard Observer')
        np.testing.assert_allclose(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(435),
            cmfs.get(435),
            atol=0.0025)

        np.testing.assert_allclose(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(545),
            cmfs.get(545),
            atol=0.0025)

        np.testing.assert_allclose(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(700),
            cmfs.get(700),
            atol=0.0025)

    def test_n_dimensional_RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition n-dimensional arrays
        support.
        """

        wl = 700
        XYZ = np.array([0.01135774, 0.00410200, 0.00000000])
        np.testing.assert_almost_equal(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.tile(wl, 6)
        XYZ = np.tile(XYZ, (6, 1))
        np.testing.assert_almost_equal(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3))
        XYZ = np.reshape(XYZ, (2, 3, 3))
        np.testing.assert_almost_equal(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3, 1))
        XYZ = np.reshape(XYZ, (2, 3, 1, 3))
        np.testing.assert_almost_equal(
            RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

    @ignore_numpy_errors
    def test_nan_RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition nan support.
        """

        RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(
            np.array([-1.0, 0.0, 1.0, -np.inf, np.inf, np.nan]))


class TestRGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(unittest.TestCase):
    """
    Defines :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition unit tests methods.
    """

    def test_RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition.
        """

        cmfs = CMFS.get('CIE 1964 10 Degree Standard Observer')
        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(435),
            cmfs.get(435),
            atol=0.025)

        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(545),
            cmfs.get(545),
            atol=0.025)

        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(700),
            cmfs.get(700),
            atol=0.025)

    def test_n_dimensional_RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition n-dimensional arrays
        support.
        """

        wl = 700
        XYZ = np.array([9.64321500e-03, 3.75263179e-03, -4.10788300e-06])
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.tile(wl, 6)
        XYZ = np.tile(XYZ, (6, 1))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3))
        XYZ = np.reshape(XYZ, (2, 3, 3))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3, 1))
        XYZ = np.reshape(XYZ, (2, 3, 1, 3))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

    @ignore_numpy_errors
    def test_nan_RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition nan support.
        """

        RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(
            np.array([-1.0, 0.0, 1.0, -np.inf, np.inf, np.nan]))


class TestRGB_10_degree_cmfs_to_LMS_10_degree_cmfs(unittest.TestCase):
    """
    Defines :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_LMS_10_degree_cmfs` definition unit tests methods.
    """

    def test_RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_LMS_10_degree_cmfs` definition.
        """

        cmfs = CMFS.get('Stockman & Sharpe 10 Degree Cone Fundamentals')
        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(435),
            cmfs.get(435),
            atol=0.0025)

        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(545),
            cmfs.get(545),
            atol=0.0025)

        np.testing.assert_allclose(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(700),
            cmfs.get(700),
            atol=0.0025)

    def test_n_dimensional_RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_LMS_10_degree_cmfs` definition n-dimensional arrays
        support.
        """

        wl = 700
        LMS = np.array([0.00528607, 0.00032528, 0.00000000])
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(wl),
            LMS)

        wl = np.tile(wl, 6)
        LMS = np.tile(LMS, (6, 1))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(wl),
            LMS)

        wl = np.reshape(wl, (2, 3))
        LMS = np.reshape(LMS, (2, 3, 3))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(wl),
            LMS)

        wl = np.reshape(wl, (2, 3, 1))
        LMS = np.reshape(LMS, (2, 3, 1, 3))
        np.testing.assert_almost_equal(
            RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(wl),
            LMS)

    @ignore_numpy_errors
    def test_nan_RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
RGB_10_degree_cmfs_to_LMS_10_degree_cmfs` definition nan support.
        """

        RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(
            np.array([-1.0, 0.0, 1.0, -np.inf, np.inf, np.nan]))


class TestLMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(unittest.TestCase):
    """
    Defines :func:`colour.colorimetry.transformations.\
LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition unit tests methods.
    """

    def test_LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition.
        """

        cmfs = CMFS.get('CIE 2012 2 Degree Standard Observer')
        np.testing.assert_allclose(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(435),
            cmfs.get(435),
            atol=0.00015)

        np.testing.assert_allclose(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(545),
            cmfs.get(545),
            atol=0.00015)

        np.testing.assert_allclose(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(700),
            cmfs.get(700),
            atol=0.00015)

    def test_n_dimensional_LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition n-dimensional arrays
        support.
        """

        wl = 700
        XYZ = np.array([0.01096778, 0.00419594, 0.00000000])
        np.testing.assert_almost_equal(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.tile(wl, 6)
        XYZ = np.tile(XYZ, (6, 1))
        np.testing.assert_almost_equal(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3))
        XYZ = np.reshape(XYZ, (2, 3, 3))
        np.testing.assert_almost_equal(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3, 1))
        XYZ = np.reshape(XYZ, (2, 3, 1, 3))
        np.testing.assert_almost_equal(
            LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(wl),
            XYZ)

    @ignore_numpy_errors
    def test_nan_LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs` definition nan support.
        """

        LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(
            np.array([-1.0, 0.0, 1.0, -np.inf, np.inf, np.nan]))


class TestLMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(unittest.TestCase):
    """
    Defines :func:`colour.colorimetry.transformations.\
LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition unit tests methods.
    """

    def test_LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition.
        """

        cmfs = CMFS.get('CIE 2012 10 Degree Standard Observer')
        np.testing.assert_allclose(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(435),
            cmfs.get(435),
            atol=0.00015)

        np.testing.assert_allclose(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(545),
            cmfs.get(545),
            atol=0.00015)

        np.testing.assert_allclose(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(700),
            cmfs.get(700),
            atol=0.00015)

    def test_n_dimensional_LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition n-dimensional arrays
        support.
        """

        wl = 700
        XYZ = np.array([0.00981623, 0.00377614, 0.00000000])
        np.testing.assert_almost_equal(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.tile(wl, 6)
        XYZ = np.tile(XYZ, (6, 1))
        np.testing.assert_almost_equal(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3))
        XYZ = np.reshape(XYZ, (2, 3, 3))
        np.testing.assert_almost_equal(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

        wl = np.reshape(wl, (2, 3, 1))
        XYZ = np.reshape(XYZ, (2, 3, 1, 3))
        np.testing.assert_almost_equal(
            LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(wl),
            XYZ)

    @ignore_numpy_errors
    def test_nan_LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(self):
        """
        Tests :func:`colour.colorimetry.transformations.\
LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs` definition nan support.
        """

        LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(
            np.array([-1.0, 0.0, 1.0, -np.inf, np.inf, np.nan]))


if __name__ == '__main__':
    unittest.main()

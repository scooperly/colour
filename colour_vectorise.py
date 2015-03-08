#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NOTE: This is a work in progress and will be injected into the API.

Defines *Colour* vectorised prototype definitions. They are designed to be
compatible with the existing API while accepting arrays with n-dimensions.

Helpers
-------

# (.*)_analysis\(\)$
$1_analysis()

"""

from __future__ import division, with_statement

import numpy as np
import time
from pprint import pprint

from colour.utilities import (
    handle_numpy_errors,
    ignore_numpy_errors,
    is_iterable,
    is_numeric,
    message_box,
    row_as_diagonal,
    warning)


# np.random.seed(64)

DATA_HD1 = np.random.rand(1920 * 1080, 3)
DATA_HD2 = np.random.rand(1920 * 1080, 3)
DATA_HD3 = np.random.rand(1920 * 1080, 3)

DATA_VGA1 = np.random.rand(320 * 200, 3)
DATA_VGA2 = np.random.rand(320 * 200, 3)
DATA_VGA3 = np.random.rand(320 * 200, 3)

DATA1, DATA2, DATA3 = DATA_VGA1, DATA_VGA2, DATA_VGA3


def profile(method):
    iterations = 10

    def wrapper(*args, **kwargs):
        times = []
        for i in range(iterations):
            ts = time.time()
            method(*args, **kwargs)
            te = time.time()

            times.append(te - ts)

        message_box(
            '{0}: {1} seconds'.format(method.__name__, np.average(times)))

        return method(*args, **kwargs)

    return wrapper


def zstack(a):
    # Similar to *dstack* except that operation is always performed on
    # last axis.
    return np.concatenate([x[..., np.newaxis] for x in a], axis=-1)


def zsplit(a):
    # Similar to *dsplit* except that operation is always performed on
    # last axis.
    a = np.asarray(a)
    return [a[..., x] for x in range(a.shape[-1])]

# #############################################################################
# #############################################################################
# ## colour.adaptation.cie1994
# #############################################################################
# #############################################################################
from colour.adaptation import *
from colour.adaptation.cie1994 import *


def chromatic_adaptation_CIE1994_2d(XYZ_1):
    xy_o1 = (0.4476, 0.4074)
    xy_o2 = (0.3127, 0.3290)
    Y_o = 20
    E_o1 = 1000
    E_o2 = 1000

    for i in range(len(XYZ_1)):
        chromatic_adaptation_CIE1994(XYZ_1[i], xy_o1, xy_o2, Y_o, E_o1, E_o2)


def chromatic_adaptation_CIE1994_vectorise(XYZ_1,
                                           xy_o1,
                                           xy_o2,
                                           Y_o,
                                           E_o1,
                                           E_o2,
                                           n=1):
    if np.any(Y_o < 18) or np.any(Y_o > 100):
        warning(('"Y_o" luminance factor must be in [18, 100] domain, '
                 'unpredictable results may occur!'))

    RGB_1 = XYZ_to_RGB_cie1994_vectorise(XYZ_1)

    xez_1 = intermediate_values_vectorise(xy_o1)
    xez_2 = intermediate_values_vectorise(xy_o2)

    RGB_o1 = effective_adapting_responses_vectorise(xez_1, Y_o, E_o1)
    RGB_o2 = effective_adapting_responses_vectorise(xez_2, Y_o, E_o2)

    bRGB_o1 = exponential_factors_vectorise(RGB_o1)
    bRGB_o2 = exponential_factors_vectorise(RGB_o2)

    K = K_coefficient_vectorise(xez_1, xez_2, bRGB_o1, bRGB_o2, Y_o, n)

    RGB_2 = corresponding_colour_vectorise(
        RGB_1, xez_1, xez_2, bRGB_o1, bRGB_o2, Y_o, K, n)
    XYZ_2 = RGB_to_XYZ_cie1994_vectorise(RGB_2)

    return XYZ_2


def XYZ_to_RGB_cie1994_vectorise(XYZ):
    return np.einsum('...ij,...j->...i', CIE1994_XYZ_TO_RGB_MATRIX, XYZ)


def RGB_to_XYZ_cie1994_vectorise(RGB):
    return np.einsum('...ij,...j->...i', CIE1994_RGB_TO_XYZ_MATRIX, RGB)


def intermediate_values_vectorise(xy_o):
    x_o, y_o = zsplit(xy_o)

    # Computing :math:`\xi`, :math:`\eta`, :math:`\zeta` values.
    xi = (0.48105 * x_o + 0.78841 * y_o - 0.08081) / y_o
    eta = (-0.27200 * x_o + 1.11962 * y_o + 0.04570) / y_o
    zeta = (0.91822 * (1 - x_o - y_o)) / y_o

    xez = zstack((xi, eta, zeta))

    return xez


def effective_adapting_responses_vectorise(xez, Y_o, E_o):
    # TODO: Mention *xez* place change.
    xez = np.asarray(xez)
    Y_o = np.asarray(Y_o)
    E_o = np.asarray(E_o)

    RGB_o = ((Y_o * E_o) / (100 * np.pi)) * xez

    return RGB_o


def beta_1_vectorise(x):
    return (6.469 + 6.362 * (x ** 0.4495)) / (6.469 + (x ** 0.4495))


def beta_2_vectorise(x):
    return 0.7844 * (8.414 + 8.091 * (x ** 0.5128)) / (8.414 + (x ** 0.5128))


def exponential_factors_vectorise(RGB_o):
    R_o, G_o, B_o = zsplit(RGB_o)

    bR_o = beta_1_vectorise(R_o)
    bG_o = beta_1_vectorise(G_o)
    bB_o = beta_2_vectorise(B_o)

    bRGB_o = zstack((bR_o, bG_o, bB_o))

    return bRGB_o


def K_coefficient_vectorise(xez_1, xez_2, bRGB_o1, bRGB_o2, Y_o, n=1):
    # TODO: Mention *Y_o* place change.

    xi_1, eta_1, zeta_1 = zsplit(xez_1)
    xi_2, eta_2, zeta_2 = zsplit(xez_2)
    bR_o1, bG_o1, bB_o1 = zsplit(bRGB_o1)
    bR_o2, bG_o2, bB_o2 = zsplit(bRGB_o2)
    Y_o = np.asarray(Y_o)

    K = (((Y_o * xi_1 + n) / (20 * xi_1 + n)) ** ((2 / 3) * bR_o1) /
         ((Y_o * xi_2 + n) / (20 * xi_2 + n)) ** ((2 / 3) * bR_o2))

    K *= (((Y_o * eta_1 + n) / (20 * eta_1 + n)) ** ((1 / 3) * bG_o1) /
          ((Y_o * eta_2 + n) / (20 * eta_2 + n)) ** ((1 / 3) * bG_o2))

    return K


def corresponding_colour_vectorise(
        RGB_1, xez_1, xez_2, bRGB_o1, bRGB_o2, Y_o, K, n=1):
    # TODO: Mention *Y_o* place change.

    R_1, G_1, B_1 = zsplit(RGB_1)
    xi_1, eta_1, zeta_1 = zsplit(xez_1)
    xi_2, eta_2, zeta_2 = zsplit(xez_2)
    bR_o1, bG_o1, bB_o1 = zsplit(bRGB_o1)
    bR_o2, bG_o2, bB_o2 = zsplit(bRGB_o2)
    Y_o = np.asarray(Y_o)
    K = np.asarray(K)

    RGBc = lambda x1, x2, y1, y2, z: (
        (Y_o * x2 + n) * K ** (1 / y2) *
        ((z + n) / (Y_o * x1 + n)) ** (y1 / y2) - n)

    R_2 = RGBc(xi_1, xi_2, bR_o1, bR_o2, R_1)
    G_2 = RGBc(eta_1, eta_2, bG_o1, bG_o2, G_1)
    B_2 = RGBc(zeta_1, zeta_2, bB_o1, bB_o2, B_1)

    RGB_2 = zstack((R_2, G_2, B_2))

    return RGB_2


def chromatic_adaptation_CIE1994_analysis():
    message_box('chromatic_adaptation_CIE1994')

    print('Reference:')
    XYZ_1 = np.array([28.0, 21.26, 5.27])
    xy_o1 = np.array([0.4476, 0.4074])
    xy_o2 = np.array([0.3127, 0.3290])
    Y_o = 20
    E_o1 = 1000
    E_o2 = 1000
    print(chromatic_adaptation_CIE1994(XYZ_1, xy_o1, xy_o2, Y_o, E_o1, E_o2))

    print('\n')

    print('1d array input:')
    print(chromatic_adaptation_CIE1994_vectorise(
        XYZ_1, xy_o1, xy_o2, Y_o, E_o1, E_o2))

    print('\n')

    print('2d array input:')
    XYZ_1 = np.tile(XYZ_1, (6, 1))
    print(chromatic_adaptation_CIE1994_vectorise(
        XYZ_1, xy_o1, xy_o2, Y_o, E_o1, E_o2))

    print('\n')

    print('3d array input:')
    XYZ_1 = np.reshape(XYZ_1, (2, 3, 3))
    print(chromatic_adaptation_CIE1994_vectorise(
        XYZ_1, xy_o1, xy_o2, Y_o, E_o1, E_o2))

    print('\n')


# chromatic_adaptation_CIE1994_analysis()

# #############################################################################
# #############################################################################
# ## colour.adaptation.cmccat2000
# #############################################################################
# #############################################################################
from colour.adaptation.cmccat2000 import *


def CMCCAT2000_forward_vectorise(XYZ,
                                 XYZ_w,
                                 XYZ_wr,
                                 L_A1,
                                 L_A2,
                                 surround=CMCCAT2000_VIEWING_CONDITIONS.get(
                                     'Average')):
    L_A1 = np.asarray(L_A1)
    L_A2 = np.asarray(L_A2)

    RGB = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ)
    RGB_w = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ_w)
    RGB_wr = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ_wr)

    D = (surround.F *
         (0.08 * np.log10(0.5 * (L_A1 + L_A2)) +
          0.76 - 0.45 * (L_A1 - L_A2) / (L_A1 + L_A2)))

    D = np.clip(D, 0, 1)
    a = D * XYZ_w[..., 1] / XYZ_wr[..., 1]

    RGB_c = (RGB *
             (a[..., np.newaxis] * (RGB_wr / RGB_w) + 1 - D[..., np.newaxis]))
    XYZ_c = np.einsum('...ij,...j->...i', CMCCAT2000_INVERSE_CAT, RGB_c)

    return XYZ_c


def CMCCAT2000_forward_analysis():
    message_box('CMCCAT2000_forward')

    print('Reference:')
    XYZ = np.array([22.48, 22.74, 8.54])
    XYZ_w = np.array([111.15, 100.00, 35.20])
    XYZ_wr = np.array([94.81, 100.00, 107.30])
    L_A1 = 200
    L_A2 = 200
    print(CMCCAT2000_forward(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('1d array input:')
    print(CMCCAT2000_forward_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(CMCCAT2000_forward_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(CMCCAT2000_forward_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')


# CMCCAT2000_forward_analysis()


def CMCCAT2000_reverse_vectorise(XYZ_c,
                                 XYZ_w,
                                 XYZ_wr,
                                 L_A1,
                                 L_A2,
                                 surround=CMCCAT2000_VIEWING_CONDITIONS.get(
                                     'Average')):
    L_A1 = np.asarray(L_A1)
    L_A2 = np.asarray(L_A2)

    RGB_c = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ_c)
    RGB_w = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ_w)
    RGB_wr = np.einsum('...ij,...j->...i', CMCCAT2000_CAT, XYZ_wr)

    D = (surround.F *
         (0.08 * np.log10(0.5 * (L_A1 + L_A2)) +
          0.76 - 0.45 * (L_A1 - L_A2) / (L_A1 + L_A2)))

    D = np.clip(D, 0, 1)
    a = D * XYZ_w[..., 1] / XYZ_wr[..., 1]

    RGB = (RGB_c /
           (a[..., np.newaxis] * (RGB_wr / RGB_w) + 1 - D[..., np.newaxis]))
    XYZ = np.einsum('...ij,...j->...i', CMCCAT2000_INVERSE_CAT, RGB)

    return XYZ


def CMCCAT2000_reverse_analysis():
    message_box('CMCCAT2000_reverse')

    print('Reference:')
    XYZ = np.array([22.48, 22.74, 8.54])
    XYZ_w = np.array([111.15, 100.00, 35.20])
    XYZ_wr = np.array([94.81, 100.00, 107.30])
    L_A1 = 200
    L_A2 = 200
    print(CMCCAT2000_reverse(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('1d array input:')
    print(CMCCAT2000_reverse_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(CMCCAT2000_reverse_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(CMCCAT2000_reverse_vectorise(XYZ, XYZ_w, XYZ_wr, L_A1, L_A2))

    print('\n')


# CMCCAT2000_reverse_analysis()

# #############################################################################
# #############################################################################
# ## colour.adaptation.vonkries
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.chromatic_adaptation_matrix_VonKries
# #############################################################################
from colour.adaptation.vonkries import *


def chromatic_adaptation_matrix_VonKries_2d(data1, data2):
    for i in range(len(data1)):
        chromatic_adaptation_matrix_VonKries(data1[i], data2[i])


def chromatic_adaptation_matrix_VonKries_vectorise(XYZ_w,
                                                   XYZ_wr,
                                                   transform='CAT02'):
    M = CHROMATIC_ADAPTATION_TRANSFORMS.get(transform)

    if M is None:
        raise KeyError(
            '"{0}" chromatic adaptation transform is not defined! Supported '
            'methods: "{1}".'.format(transform,
                                     CHROMATIC_ADAPTATION_TRANSFORMS.keys()))

    rgb_w = np.einsum('...i,...ij->...j', XYZ_w, np.transpose(M))
    rgb_wr = np.einsum('...i,...ij->...j', XYZ_wr, np.transpose(M))

    D = rgb_wr / rgb_w

    D = row_as_diagonal(D)

    cat = np.einsum('...ij,...jk->...ik', np.linalg.inv(M), D)
    cat = np.einsum('...ij,...jk->...ik', cat, M)

    return cat


def chromatic_adaptation_matrix_VonKries_analysis():
    message_box('chromatic_adaptation_matrix_VonKries')

    print('Reference:')
    XYZ_w = np.array([1.09846607, 1., 0.3558228])
    XYZ_wr = np.array([0.95042855, 1., 1.08890037])
    print(chromatic_adaptation_matrix_VonKries(XYZ_w, XYZ_wr))

    print('\n')

    print('1d array input:')
    print(chromatic_adaptation_matrix_VonKries_vectorise(XYZ_w, XYZ_wr))

    print('\n')

    print('2d array input:')
    XYZ_w = np.tile(XYZ_w, (6, 1))
    XYZ_wr = np.tile(XYZ_wr, (6, 1))
    print(chromatic_adaptation_matrix_VonKries_vectorise(XYZ_w, XYZ_wr))

    print('\n')

    print('3d array input:')
    XYZ_w = np.reshape(XYZ_w, (2, 3, 3))
    XYZ_wr = np.reshape(XYZ_wr, (2, 3, 3))
    print(chromatic_adaptation_matrix_VonKries_vectorise(XYZ_w, XYZ_wr))

    print('\n')


# chromatic_adaptation_matrix_VonKries_analysis()

# #############################################################################
# # ### colour.chromatic_adaptation_VonKries
# #############################################################################


def chromatic_adaptation_VonKries_2d(data1, data2, data3):
    for i in range(len(data1)):
        chromatic_adaptation_VonKries(data1[i], data2[i], data3[i])


def chromatic_adaptation_VonKries_vectorise(XYZ,
                                            XYZ_w,
                                            XYZ_wr,
                                            transform='CAT02'):
    cat = chromatic_adaptation_matrix_VonKries_vectorise(XYZ_w, XYZ_wr,
                                                         transform)
    XYZ_a = np.einsum('...ij,...j->...i', cat, XYZ)

    return XYZ_a


def chromatic_adaptation_VonKries_analysis():
    message_box('chromatic_adaptation_VonKries')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    XYZ_w = np.array([1.09846607, 1., 0.3558228])
    XYZ_wr = np.array([0.95042855, 1., 1.08890037])
    print(chromatic_adaptation_VonKries(XYZ, XYZ_w, XYZ_wr))

    print('\n')

    print('1d array input:')
    print(chromatic_adaptation_VonKries_vectorise(XYZ, XYZ_w, XYZ_wr))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    XYZ_w = np.tile(XYZ_w, (6, 1))
    XYZ_wr = np.tile(XYZ_wr, (6, 1))
    print(chromatic_adaptation_VonKries_vectorise(XYZ, XYZ_w, XYZ_wr))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    XYZ_w = np.reshape(XYZ_w, (2, 3, 3))
    XYZ_wr = np.reshape(XYZ_wr, (2, 3, 3))
    print(chromatic_adaptation_VonKries_vectorise(XYZ,
                                                  XYZ_w,
                                                  XYZ_wr))

    print('\n')


# chromatic_adaptation_VonKries_analysis()

# #############################################################################
# #############################################################################
# ## colour.algebra.coordinates.transformations
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.cartesian_to_spherical
# #############################################################################
from colour.algebra.coordinates.transformations import *


def cartesian_to_spherical_2d(vectors):
    for vector in vectors:
        cartesian_to_spherical(vector)


def cartesian_to_spherical_vectorise(vector):
    x, y, z = zsplit(vector)

    r = np.linalg.norm(vector, axis=-1)
    theta = np.arctan2(z, np.linalg.norm(zstack((x, y))))
    phi = np.arctan2(y, x)

    rtp = zstack((r, theta, phi))

    return rtp


def cartesian_to_spherical_analysis():
    message_box('cartesian_to_spherical')

    print('Reference:')
    vector = np.array([3, 1, 6])
    print(cartesian_to_spherical(vector))

    print('\n')

    print('1d array input:')
    print(cartesian_to_spherical_vectorise(vector))

    print('\n')

    print('2d array input:')
    vector = np.tile(vector, (6, 1))
    print(cartesian_to_spherical_vectorise(vector))

    print('\n')

    print('3d array input:')
    vector = np.reshape(vector, (2, 3, 3))
    print(cartesian_to_spherical_vectorise(vector))

    print('\n')


# cartesian_to_spherical_analysis()

# #############################################################################
# # ### colour.spherical_to_cartesian
# #############################################################################


def spherical_to_cartesian_2d(vectors):
    for vector in vectors:
        spherical_to_cartesian(vector)


def spherical_to_cartesian_vectorise(vector):
    r, theta, phi = zsplit(vector)

    x = r * np.cos(theta) * np.cos(phi)
    y = r * np.cos(theta) * np.sin(phi)
    z = r * np.sin(theta)

    xyz = zstack((x, y, z))

    return xyz


def spherical_to_cartesian_analysis():
    message_box('spherical_to_cartesian')

    print('Reference:')
    vector = np.array([6.78232998, 1.08574654, 0.32175055])
    print(spherical_to_cartesian(vector))

    print('\n')

    print('1d array input:')
    print(spherical_to_cartesian_vectorise(vector))

    print('\n')

    print('2d array input:')
    vector = np.tile(vector, (6, 1))
    print(spherical_to_cartesian_vectorise(vector))

    print('\n')

    print('3d array input:')
    vector = np.reshape(vector, (2, 3, 3))
    print(spherical_to_cartesian_vectorise(vector))

    print('\n')


# spherical_to_cartesian_analysis()

# #############################################################################
# # ### colour.cartesian_to_cylindrical
# #############################################################################


def cartesian_to_cylindrical_2d(vectors):
    for vector in vectors:
        cartesian_to_cylindrical(vector)


def cartesian_to_cylindrical_vectorise(vector):
    x, y, z = zsplit(vector)

    theta = np.arctan2(y, x)
    rho = np.linalg.norm(zstack((x, y)), axis=-1)

    return zstack((z, theta, rho))


def cartesian_to_cylindrical_analysis():
    message_box('cartesian_to_cylindrical')

    print('Reference:')
    vector = np.array([3, 1, 6])
    print(cartesian_to_cylindrical(vector))

    print('\n')

    print('1d array input:')
    print(cartesian_to_cylindrical_vectorise(vector))

    print('\n')

    print('2d array input:')
    vector = np.tile(vector, (6, 1))
    print(cartesian_to_cylindrical_vectorise(vector))

    print('\n')

    print('3d array input:')
    vector = np.reshape(vector, (2, 3, 3))
    print(cartesian_to_cylindrical_vectorise(vector))

    print('\n')


# cartesian_to_cylindrical_analysis()

# #############################################################################
# # ### colour.cylindrical_to_cartesian
# #############################################################################


def cylindrical_to_cartesian_2d(vectors):
    for vector in vectors:
        cylindrical_to_cartesian(vector)


def cylindrical_to_cartesian_vectorise(vector):
    z, theta, rho = zsplit(vector)

    x = rho * np.cos(theta)
    y = rho * np.sin(theta)

    return zstack((x, y, z))


def cylindrical_to_cartesian_analysis():
    message_box('cylindrical_to_cartesian')

    print('Reference:')
    vector = np.array([6, 0.32175055, 3.16227766])
    print(cylindrical_to_cartesian(vector))

    print('\n')

    print('1d array input:')
    print(cylindrical_to_cartesian_vectorise(vector))

    print('\n')

    print('2d array input:')
    vector = np.tile(vector, (6, 1))
    print(cylindrical_to_cartesian_vectorise(vector))

    print('\n')

    print('3d array input:')
    vector = np.reshape(vector, (2, 3, 3))
    print(cylindrical_to_cartesian_vectorise(vector))

    print('\n')


# cylindrical_to_cartesian_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.lightness
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.lightness_Glasser1958
# #############################################################################
from colour.colorimetry.lightness import *

Y = np.linspace(0, 100, 1000000)


def lightness_Glasser1958_2d(Y):
    for Y_ in Y:
        lightness_Glasser1958(Y_)


def lightness_Glasser1958_vectorise(Y, **kwargs):
    Y = np.asarray(Y)

    L = 25.29 * (Y ** (1 / 3)) - 18.38

    return L


def lightness_Glasser1958_analysis():
    message_box('lightness_Glasser1958')

    print('Reference:')
    print(lightness_Glasser1958(10.08))

    print('\n')

    print('Numeric input:')
    print(lightness_Glasser1958_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(lightness_Glasser1958_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(lightness_Glasser1958_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(np.array(Y), (2, 3))
    print(lightness_Glasser1958_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(np.array(Y), (2, 3, 1))
    print(lightness_Glasser1958_vectorise(Y))

    print('\n')


# lightness_Glasser1958_analysis()

# #############################################################################
# # ### colour.lightness_Wyszecki1963
# #############################################################################
def lightness_Wyszecki1963_2d(Y):
    for Y_ in Y:
        lightness_Wyszecki1963(Y_)


def lightness_Wyszecki1963_vectorise(Y, **kwargs):
    Y = np.asarray(Y)

    if np.any(Y < 1) or np.any(Y > 98):
        warning(('"W*" Lightness computation is only applicable for '
                 '1% < "Y" < 98%, unpredictable results may occur!'))

    W = 25 * (Y ** (1 / 3)) - 17

    return W


def lightness_Wyszecki1963_analysis():
    message_box('lightness_Wyszecki1963')

    print('Reference:')
    print(lightness_Wyszecki1963(10.08))

    print('\n')

    print('Numeric input:')
    print(lightness_Wyszecki1963_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(lightness_Wyszecki1963_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(lightness_Wyszecki1963_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(np.array(Y), (2, 3))
    print(lightness_Wyszecki1963_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(np.array(Y), (2, 3, 1))
    print(lightness_Wyszecki1963_vectorise(Y))

    print('\n')


# lightness_Wyszecki1963_analysis()

# #############################################################################
# # ### colour.lightness_1976
# #############################################################################
def lightness_1976_2d(Y):
    Lstar = []
    for Y_ in Y:
        Lstar.append(lightness_1976(Y_))
    return Lstar


from colour.constants import CIE_E, CIE_K


def lightness_1976_vectorise(Y, Y_n=100):
    Y = np.asarray(Y)
    Y_n = np.asarray(Y_n)

    Lstar = Y / Y_n

    Lstar = np.where(Lstar <= CIE_E,
                     CIE_K * Lstar,
                     116 * Lstar ** (1 / 3) - 16)

    return Lstar


def lightness_1976_analysis():
    message_box('lightness_1976')

    print('Reference:')
    print(lightness_1976(10.08, 100))

    print('\n')

    print('Numeric input:')
    print(lightness_1976_vectorise(10.08, 100))

    print('\n')

    print('0d array input:')
    print(lightness_1976_vectorise(np.array(10.08), np.array(100)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(lightness_1976_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(lightness_1976_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(lightness_1976_vectorise(Y))

    print('\n')

    Y = np.linspace(0, 100, 10000)
    np.testing.assert_almost_equal(lightness_1976_2d(Y),
                                   lightness_1976_vectorise(Y))


# lightness_1976_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.luminance
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.luminance_Newhall1943
# #############################################################################
from colour.colorimetry.luminance import *

L = np.linspace(0, 100, 1000000)


def luminance_Newhall1943_2d(L):
    for L_ in L:
        luminance_Newhall1943(L_)


def luminance_Newhall1943_vectorise(V, **kwargs):
    V = np.asarray(V)

    R_Y = (1.2219 * V - 0.23111 * (V * V) + 0.23951 * (V ** 3) - 0.021009 *
           (V ** 4) + 0.0008404 * (V ** 5))

    return R_Y


def luminance_Newhall1943_analysis():
    message_box('luminance_Newhall1943')

    print('Reference:')
    print(luminance_Newhall1943(3.74629715382))

    print('\n')

    print('Numeric input:')
    print(luminance_Newhall1943_vectorise(3.74629715382))

    print('\n')

    print('0d array input:')
    print(luminance_Newhall1943_vectorise(np.array(3.74629715382)))

    print('\n')

    print('1d array input:')
    V = [3.74629715382] * 6
    print(luminance_Newhall1943_vectorise(V))

    print('\n')

    print('2d array input:')
    V = np.reshape(np.array(V), (2, 3))
    print(luminance_Newhall1943_vectorise(V))

    print('\n')

    print('3d array input:')
    V = np.reshape(np.array(V), (2, 3, 1))
    print(luminance_Newhall1943_vectorise(V))

    print('\n')


# luminance_Newhall1943_analysis()

# #############################################################################
# # ### colour.luminance_ASTMD153508
# #############################################################################


def luminance_ASTMD153508_vectorise(V, **kwargs):
    V = np.asarray(V)

    Y = (1.1914 * V - 0.22533 * (V ** 2) + 0.23352 * (V ** 3) - 0.020484 *
         (V ** 4) + 0.00081939 * (V ** 5))

    return Y


def luminance_ASTMD153508_2d(L):
    for L_ in L:
        luminance_ASTMD153508(L_)


def luminance_ASTMD153508_analysis():
    message_box('luminance_ASTMD153508')

    print('Reference:')
    print(luminance_ASTMD153508(3.74629715382))

    print('\n')

    print('Numeric input:')
    print(luminance_ASTMD153508_vectorise(3.74629715382))

    print('\n')

    print('0d array input:')
    print(luminance_ASTMD153508_vectorise(np.array(3.74629715382)))

    print('\n')

    print('1d array input:')
    V = [3.74629715382] * 6
    print(luminance_ASTMD153508_vectorise(V))

    print('\n')

    print('2d array input:')
    V = np.reshape(np.array(V), (2, 3))
    print(luminance_ASTMD153508_vectorise(V))

    print('\n')

    print('3d array input:')
    V = np.reshape(np.array(V), (2, 3, 1))
    print(luminance_ASTMD153508_vectorise(V))

    print('\n')


# luminance_ASTMD153508_analysis()

# #############################################################################
# # ### colour.luminance_1976
# #############################################################################

def luminance_1976_2d(L):
    Y = []
    for L_ in L:
        Y.append(luminance_1976(L_))
    return Y


def luminance_1976_vectorise(Lstar, Y_n=100):
    Lstar = np.asarray(Lstar)
    Y_n = np.asarray(Y_n)

    Y = np.where(Lstar > CIE_K * CIE_E,
                 Y_n * ((Lstar + 16) / 116) ** 3,
                 Y_n * (Lstar / CIE_K))

    return Y


def luminance_1976_analysis():
    message_box('luminance_1976')

    print('Reference:')
    print(luminance_1976(37.9856290977))

    print('\n')

    print('Numeric input:')
    print(luminance_1976_vectorise(37.9856290977))

    print('\n')

    print('0d array input:')
    print(luminance_1976_vectorise(np.array(37.9856290977)))

    print('\n')

    print('1d array input:')
    Lstar = [37.9856290977] * 6
    print(luminance_1976_vectorise(Lstar))

    print('\n')

    print('2d array input:')
    Lstar = np.reshape(np.array(Lstar), (2, 3))
    print(luminance_1976_vectorise(Lstar))

    print('\n')

    print('3d array input:')
    Lstar = np.reshape(np.array(Lstar), (2, 3, 1))
    print(luminance_1976_vectorise(Lstar))

    print('\n')

    Lstar = np.linspace(0, 100, 10000)
    np.testing.assert_almost_equal(luminance_1976_2d(Lstar),
                                   luminance_1976_vectorise(Lstar))


# luminance_1976_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.spectrum
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.SpectralShape
# #############################################################################
from colour.colorimetry.spectrum import *


def SpectralShape__contains__(self, wavelength):
    return np.all(np.in1d(np.ravel(wavelength), self.range()))


SpectralShape.__contains__ = SpectralShape__contains__


def SpectralShape__contains__analysis():
    message_box('SpectralShape.__contains__')

    print(380 in SpectralShape(360, 830, 1))

    print('\n')

    print((380, 480) in SpectralShape(360, 830, 1))

    print('\n')

    print((380, 480.5) in SpectralShape(360, 830, 1))

    print('\n')


# SpectralShape__contains__analysis()

# #############################################################################
# # ### colour.SpectralPowerDistribution
# #############################################################################

def SpectralPowerDistribution__getitem__(self, wavelength):
    if type(wavelength) is slice:
        return self.values[wavelength]
    else:
        wavelength = np.asarray(wavelength)

        value = [self.data.__getitem__(x) for x in np.ravel(wavelength)]
        value = np.reshape(value, wavelength.shape)

        return value


SpectralPowerDistribution.__getitem__ = SpectralPowerDistribution__getitem__


def SpectralPowerDistribution__getitem__analysis():
    message_box('SpectralPowerDistribution.__getitem___')

    data = {510: 49.67, 520: 69.59, 530: 81.73, 540: 88.19}
    spd = SpectralPowerDistribution('Spd', data)

    print(spd[510])

    print('\n')

    print(spd[np.array(510)])

    print('\n')

    print(spd[np.array([510])])

    print('\n')

    print(spd[[510, 520]])

    print('\n')

    print(spd[np.array([510, 520])])

    print('\n')

    print(spd[np.array([[510], [520]])])

    print('\n')

    print(spd[np.array([[[510, 520]], [[530, 540]]])])

    print('\n')

    print(spd[0:-1])

    print('\n')


# SpectralPowerDistribution__getitem__analysis()


def SpectralPowerDistribution__setitem__(self, wavelength, value):
    # TODO: Mention implicit resize.
    if is_numeric(wavelength) or is_iterable(wavelength):
        wavelengths = np.ravel(wavelength)
    elif type(wavelength) is slice:
        wavelengths = self.wavelengths[wavelength]
    else:
        raise NotImplementedError(
            '"{0}" type is not supported for indexing!'.format(
                type(wavelength)))

    values = np.resize(value, wavelengths.shape)
    for i in range(len(wavelengths)):
        # self.data ===> self.__data
        self.data.__setitem__(wavelengths[i], values[i])


SpectralPowerDistribution.__setitem__ = SpectralPowerDistribution__setitem__


def SpectralPowerDistribution__setitem__analysis():
    message_box('SpectralPowerDistribution.__setitem__')

    spd = SpectralPowerDistribution('Spd', {})

    spd[510] = 49.67
    pprint(list(spd.items))

    print('\n')

    spd[[520, 530]] = (69.59, 81.73)
    pprint(list(spd.items))

    print('\n')

    spd[[540, 550]] = 88.19
    pprint(list(spd.items))

    print('\n')

    spd[:] = 49.67
    pprint(list(spd.items))

    print('\n')

    spd[0:3] = 69.59
    pprint(list(spd.items))

    print('\n')


# SpectralPowerDistribution__setitem__analysis()

def SpectralPowerDistribution_get(self, wavelength, default=None):
    wavelength = np.asarray(wavelength)

    value = [self.data.get(x, default) for x in np.ravel(wavelength)]
    value = np.reshape(value, wavelength.shape)

    return value


SpectralPowerDistribution.get = SpectralPowerDistribution_get


def SpectralPowerDistribution_get_analysis():
    message_box('SpectralPowerDistribution.get')

    data = {510: 49.67, 520: 69.59, 530: 81.73, 540: 88.19}
    spd = SpectralPowerDistribution('Spd', data)

    print(spd.get(510))

    print('\n')

    print(spd.get(np.array(510)))

    print('\n')

    print(spd.get(np.array([510])))

    print('\n')

    print(spd.get([510, 520]))

    print('\n')

    print(spd.get(np.array([510, 520])))

    print('\n')

    print(spd.get(np.array([[510], [520]])))

    print('\n')

    print(spd.get([510, 520, 521]))

    print('\n')


# SpectralPowerDistribution_get_analysis()


def SpectralPowerDistribution__contains__(self, wavelength):
    return np.all(np.in1d(np.ravel(wavelength), self.wavelengths))


SpectralPowerDistribution.__contains__ = SpectralPowerDistribution__contains__


def SpectralPowerDistribution__contains__analysis():
    message_box('SpectralPowerDistribution.__contains__')

    data = {510: 49.67, 520: 69.59, 530: 81.73, 540: 88.19}
    spd = SpectralPowerDistribution('Spd', data)

    print(510 in spd)

    print('\n')

    print([510, 520] in spd)

    print('\n')

    print([510, 520, 521] in spd)

    print('\n')


# SpectralPowerDistribution__contains__analysis()

# #############################################################################
# # ### colour.TriSpectralPowerDistribution
# #############################################################################


def TriSpectralPowerDistribution__getitem__(self, wavelength):
    value = zstack((np.asarray(self.x[wavelength]),
                    np.asarray(self.y[wavelength]),
                    np.asarray(self.z[wavelength])))

    return value


TriSpectralPowerDistribution.__getitem__ = TriSpectralPowerDistribution__getitem__


def TriSpectralPowerDistribution__getitem__analysis():
    message_box('TriSpectralPowerDistribution.__getitem__')

    x_bar = {510: 49.67, 520: 69.59, 530: 81.73, 540: 88.19}
    y_bar = {510: 90.56, 520: 87.34, 530: 45.76, 540: 23.45}
    z_bar = {510: 12.43, 520: 23.15, 530: 67.98, 540: 90.28}
    data = {'x_bar': x_bar, 'y_bar': y_bar, 'z_bar': z_bar}
    mpg = {'x': 'x_bar', 'y': 'y_bar', 'z': 'z_bar'}
    tri_spd = TriSpectralPowerDistribution('Tri Spd', data, mpg)

    print(tri_spd[510])

    print('\n')

    print(tri_spd[np.array(510)])

    print('\n')

    print(tri_spd[[510, 520]])

    print('\n')

    print(tri_spd[np.array([[510, 520]])])

    print('\n')

    print(tri_spd[np.array([[510], [520]])])

    print('\n')

    print(tri_spd[0:-1])

    print('\n')


# TriSpectralPowerDistribution__getitem__analysis()


def TriSpectralPowerDistribution__setitem__(self, wavelength, value):
    # TODO: Mention implicit resize.
    if is_numeric(wavelength) or is_iterable(wavelength):
        wavelengths = np.ravel(wavelength)
    elif type(wavelength) is slice:
        wavelengths = self.wavelengths[wavelength]
    else:
        raise NotImplementedError(
            '"{0}" type is not supported for indexing!'.format(
                type(wavelength)))

    value = np.resize(value, (wavelengths.shape[0], 3))

    self.x.__setitem__(wavelengths, value[..., 0])
    self.y.__setitem__(wavelengths, value[..., 1])
    self.z.__setitem__(wavelengths, value[..., 2])


TriSpectralPowerDistribution.__setitem__ = TriSpectralPowerDistribution__setitem__


def TriSpectralPowerDistribution__setitem__analysis():
    message_box('TriSpectralPowerDistribution.__setitem__')

    data = {'x_bar': {}, 'y_bar': {}, 'z_bar': {}}
    mpg = {'x': 'x_bar', 'y': 'y_bar', 'z': 'z_bar'}
    tri_spd = TriSpectralPowerDistribution('Tri Spd', data, mpg)

    tri_spd[510] = 49.67
    pprint(list(tri_spd.items))

    print('\n')

    tri_spd[[520, 530]] = (69.59, 81.73)
    pprint(list(tri_spd.items))

    print('\n')

    tri_spd[[540, 550]] = ((49.67, 69.59, 81.73), (81.73, 69.59, 49.67))
    pprint(list(tri_spd.items))

    print('\n')

    tri_spd[:] = 49.67
    pprint(list(tri_spd.items))

    print('\n')

    tri_spd[0:3] = ((81.73, 69.59, 49.67), (49.67, 69.59, 81.73))
    pprint(list(tri_spd.items))

    print('\n')


# TriSpectralPowerDistribution__setitem__analysis()


def TriSpectralPowerDistribution_get(self, wavelength, default=None):
    wavelength = np.asarray(wavelength)

    value = np.asarray([(self.x.get(x, default),
                         self.y.get(x, default),
                         self.z.get(x, default))
                        for x in np.ravel(wavelength)])

    value = np.reshape(value, wavelength.shape + (3,))

    return value


TriSpectralPowerDistribution.get = TriSpectralPowerDistribution_get


def TriSpectralPowerDistribution_get_analysis():
    message_box('TriSpectralPowerDistribution.get')

    x_bar = {510: 49.67, 520: 69.59, 530: 81.73, 540: 88.19}
    y_bar = {510: 90.56, 520: 87.34, 530: 45.76, 540: 23.45}
    z_bar = {510: 12.43, 520: 23.15, 530: 67.98, 540: 90.28}
    data = {'x_bar': x_bar, 'y_bar': y_bar, 'z_bar': z_bar}
    mpg = {'x': 'x_bar', 'y': 'y_bar', 'z': 'z_bar'}
    tri_spd = TriSpectralPowerDistribution('Tri Spd', data, mpg)

    print(tri_spd.get(510))

    print('\n')

    print(tri_spd.get(np.array(510)))

    print('\n')

    print(tri_spd.get(np.array([510])))

    print('\n')

    print(tri_spd.get([510, 520]))

    print('\n')

    print(tri_spd.get(np.array([510, 520])))

    print('\n')

    print(tri_spd.get(np.array([[510], [520]])))

    print('\n')

    print(tri_spd.get([510, 520, 521]))

    print('\n')


# TriSpectralPowerDistribution_get_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.transformations
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs
# #############################################################################
from colour import PHOTOPIC_LEFS, RGB_CMFS
from colour.colorimetry.transformations import *


def RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wavelength):
    cmfs = RGB_CMFS.get('Wright & Guild 1931 2 Degree RGB CMFs')

    try:
        rgb_bar = cmfs[wavelength]
    except KeyError as error:
        raise KeyError(('"{0} nm" wavelength not available in "{1}" colour '
                        'matching functions with "{2}" shape!').format(
            error.args[0], cmfs.name, cmfs.shape))

    rgb = rgb_bar / np.sum(rgb_bar)

    M1 = np.array([[0.49000, 0.31000, 0.20000],
                   [0.17697, 0.81240, 0.01063],
                   [0.00000, 0.01000, 0.99000]])

    M2 = np.array([[0.66697, 1.13240, 1.20063],
                   [0.66697, 1.13240, 1.20063],
                   [0.66697, 1.13240, 1.20063]])

    xyz = np.einsum('...ij,...j->...i', M1, rgb)
    xyz /= np.einsum('...ij,...j->...i', M2, rgb)

    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]

    V = PHOTOPIC_LEFS.get('CIE 1924 Photopic Standard Observer').clone()
    V.align(cmfs.shape)
    L = V[wavelength]

    x_bar = x / y * L
    y_bar = L
    z_bar = z / y * L

    xyz_bar = zstack((np.asarray(x_bar),
                      np.asarray(y_bar),
                      np.asarray(z_bar)))

    return xyz_bar


def RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_analysis():
    message_box('RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs')

    print('Reference:')
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs(700))

    print('\n')

    print('Numeric input:')
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(700))

    print('\n')

    print('0d array input:')
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(np.array(700)))

    print('\n')

    print('1d array input:')
    wl = [700] * 6
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3))
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(np.array(wl), (2, 3, 1))
    print(RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')


# RGB_2_degree_cmfs_to_XYZ_2_degree_cmfs_analysis()

# #############################################################################
# # ### colour.RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs
# #############################################################################


def RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wavelength):
    cmfs = RGB_CMFS.get('Stiles & Burch 1959 10 Degree RGB CMFs')

    try:
        rgb_bar = cmfs[wavelength]
    except KeyError as error:
        raise KeyError(('"{0} nm" wavelength not available in "{1}" colour '
                        'matching functions with "{2}" shape!').format(
            error.args[0], cmfs.name, cmfs.shape))

    M = np.array([[0.341080, 0.189145, 0.387529],
                  [0.139058, 0.837460, 0.073316],
                  [0.000000, 0.039553, 2.026200]])

    xyz_bar = np.einsum('...ij,...j->...i', M, rgb_bar)

    return xyz_bar


def RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_analysis():
    message_box('RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs')

    print('Reference:')
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs(700))

    print('\n')

    print('Numeric input:')
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(700))

    print('\n')

    print('0d array input:')
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(np.array(700)))

    print('\n')

    print('1d array input:')
    wl = [700] * 6
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3))
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(np.array(wl), (2, 3, 1))
    print(RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')


# RGB_10_degree_cmfs_to_XYZ_10_degree_cmfs_analysis()

# #############################################################################
# # ### colour.RGB_10_degree_cmfs_to_LMS_10_degree_cmfs
# #############################################################################

def RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(wavelength):
    cmfs = RGB_CMFS.get('Stiles & Burch 1959 10 Degree RGB CMFs')

    try:
        rgb_bar = cmfs[wavelength]
    except KeyError as error:
        raise KeyError(('"{0} nm" wavelength not available in "{1}" colour '
                        'matching functions with "{2}" shape!').format(
            error.args[0], cmfs.name, cmfs.shape))

    M = np.array([[0.1923252690, 0.749548882, 0.0675726702],
                  [0.0192290085, 0.940908496, 0.113830196],
                  [0.0000000000, 0.0105107859, 0.991427669]])

    lms_bar = np.einsum('...ij,...j->...i', M, rgb_bar)
    lms_bar[..., -1][np.asarray(np.asarray(wavelength) > 505)] = 0

    return lms_bar


def RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_analysis():
    message_box('RGB_10_degree_cmfs_to_LMS_10_degree_cmfs')

    print('Reference:')
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs(700))

    print('\n')

    print('Numeric input:')
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(700))

    print('\n')

    print('0d array input:')
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(np.array(700)))

    print('\n')

    print('1d array input:')
    wl = [700] * 6
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3))
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3, 1))
    print(RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_vectorise(wl))

    print('\n')


# RGB_10_degree_cmfs_to_LMS_10_degree_cmfs_analysis()

# #############################################################################
# # ### colour.LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs
# #############################################################################
from colour import LMS_CMFS


def LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wavelength):
    cmfs = LMS_CMFS.get('Stockman & Sharpe 2 Degree Cone Fundamentals')

    try:
        lms_bar = cmfs[wavelength]
    except KeyError as error:
        raise KeyError(('"{0} nm" wavelength not available in "{1}" colour '
                        'matching functions with "{2}" shape!').format(
            error.args[0], cmfs.name, cmfs.shape))

    M = np.array([[1.94735469, -1.41445123, 0.36476327],
                  [0.68990272, 0.34832189, 0.00000000],
                  [0.00000000, 0.00000000, 1.93485343]])

    xyz_bar = np.einsum('...ij,...j->...i', M, lms_bar)

    return xyz_bar


def LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_analysis():
    message_box('LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs')

    print('Reference:')
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs(700))

    print('\n')

    print('Numeric input:')
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(700))

    print('\n')

    print('0d array input:')
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(np.array(700)))

    print('\n')

    print('1d array input:')
    wl = [700] * 6
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3))
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(np.array(wl), (2, 3, 1))
    print(LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_vectorise(wl))

    print('\n')


# LMS_2_degree_cmfs_to_XYZ_2_degree_cmfs_analysis()

# #############################################################################
# # ### colour.LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs
# #############################################################################


def LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wavelength):
    cmfs = LMS_CMFS.get('Stockman & Sharpe 10 Degree Cone Fundamentals')

    try:
        lms_bar = cmfs[wavelength]
    except KeyError as error:
        raise KeyError(('"{0} nm" wavelength not available in "{1}" colour '
                        'matching functions with "{2}" shape!').format(
            error.args[0], cmfs.name, cmfs.shape))

    M = np.array([[1.93986443, -1.34664359, 0.43044935],
                  [0.69283932, 0.34967567, 0.00000000],
                  [0.00000000, 0.00000000, 2.14687945]])

    xyz_bar = np.einsum('...ij,...j->...i', M, lms_bar)

    return xyz_bar


def LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_analysis():
    message_box('LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs')

    print('Reference:')
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs(700))

    print('\n')

    print('Numeric input:')
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(700))

    print('\n')

    print('0d array input:')
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(np.array(700)))

    print('\n')

    print('1d array input:')
    wl = [700] * 6
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(np.array(wl), (2, 3))
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(np.array(wl), (2, 3, 1))
    print(LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_vectorise(wl))

    print('\n')


# LMS_10_degree_cmfs_to_XYZ_10_degree_cmfs_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.tristimulus
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.wavelength_to_XYZ
# #############################################################################
from colour import (
    STANDARD_OBSERVERS_CMFS,
    SpragueInterpolator,
    SplineInterpolator)
from colour.colorimetry.tristimulus import *

WAVELENGTHS = np.linspace(400, 700, 1000)


def wavelength_to_XYZ_2d(wavelengths):
    for wavelength in wavelengths:
        wavelength_to_XYZ(wavelength)


def wavelength_to_XYZ_vectorise(wavelength,
                                cmfs=STANDARD_OBSERVERS_CMFS.get(
                                    'CIE 1931 2 Degree Standard Observer')):
    cmfs_shape = cmfs.shape
    if (np.min(wavelength) < cmfs_shape.start or
                np.max(wavelength) > cmfs_shape.end):
        raise ValueError(
            '"{0} nm" wavelength is not in "[{1}, {2}]" domain!'.format(
                wavelength, cmfs_shape.start, cmfs_shape.end))

    if wavelength not in cmfs:
        wavelengths, values, = cmfs.wavelengths, cmfs.values
        interpolator = (SpragueInterpolator
                        if cmfs.is_uniform() else
                        SplineInterpolator)

        interpolators = [interpolator(wavelengths, values[:, i])
                         for i in range(values.shape[-1])]

        XYZ = np.dstack([interpolator(np.ravel(wavelength))
                         for interpolator in interpolators])
    else:
        XYZ = cmfs.get(wavelength)

    XYZ = np.reshape(XYZ, np.asarray(wavelength).shape + (3,))

    return XYZ


def wavelength_to_XYZ_analysis():
    message_box('wavelength_to_XYZ')

    print('Reference:')
    print(wavelength_to_XYZ(480))

    print('\n')

    print('Numeric input:')
    print(wavelength_to_XYZ_vectorise(480))

    print('\n')

    print('0d array input:')
    print(wavelength_to_XYZ_vectorise(np.array(480)))

    print('\n')

    print('1d array input:')
    print(wavelength_to_XYZ_vectorise([480] * 6))

    print('\n')

    print('1d array input:')
    print(wavelength_to_XYZ_vectorise(np.array([480] * 5 + [480.5])))

    print('\n')

    print('2d array input:')
    print(wavelength_to_XYZ_vectorise(
        np.array([[480] * 3, [480] * 2 + [480.5]])))

    print('\n')

    print('3d array input:')
    print(wavelength_to_XYZ_vectorise(
        np.array([[[480] * 3], [[480] * 2 + [480.5]]])))

    print('\n')


# wavelength_to_XYZ_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.blackbody
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.planck_law
# #############################################################################
from colour.colorimetry.blackbody import *
from colour.colorimetry.spectrum import *

WAVELENGTHS = np.linspace(1, 15000, 100000) * 1e-9


def planck_law_2d(wavelengths):
    for wavelength in wavelengths:
        planck_law(wavelength, 5500)


@handle_numpy_errors(over='ignore')
def planck_law_vectorise(wavelength, temperature, c1=C1, c2=C2, n=N):
    l = np.asarray(wavelength)
    t = np.asarray(temperature)

    p = (((c1 * n ** -2 * l ** -5) / np.pi) *
         (np.exp(c2 / (n * l * t)) - 1) ** -1)

    return p


def planck_law_analysis():
    message_box('planck_law')

    print('Reference:')
    print(planck_law(500 * 1e-9, 5500))

    print('\n')

    print('Numeric input:')
    print(planck_law_vectorise(500 * 1e-9, 5500))

    print('\n')

    print('0d array input:')
    print(planck_law_vectorise(np.array(500 * 1e-9), 5500))

    print('\n')

    print('1d array input:')
    wl = [500 * 1e-9] * 6
    print(planck_law_vectorise(wl, 5500))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(planck_law_vectorise(wl, 5500))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(planck_law_vectorise(wl, 5500))

    print('\n')


# planck_law_analysis()


def blackbody_spd_vectorise(temperature,
                            shape=DEFAULT_SPECTRAL_SHAPE,
                            c1=C1,
                            c2=C2,
                            n=N):
    wavelengths = shape.range()
    return SpectralPowerDistribution(
        name='{0}K Blackbody'.format(temperature),
        data=dict(
            zip(wavelengths,
                planck_law_vectorise(
                    wavelengths * 1e-9, temperature, c1, c2, n))))


def blackbody_spd_analysis():
    message_box('blackbody_spd')

    print(blackbody_spd_vectorise(5000).values)


# blackbody_spd_analysis()

# #############################################################################
# #############################################################################
# ## colour.colorimetry.whiteness
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.whiteness_Berger1959
# #############################################################################
from colour.colorimetry.whiteness import *


def whiteness_Berger1959_2d(XYZ, XYZ_0):
    for i in range(len(XYZ)):
        whiteness_Berger1959(XYZ[i], XYZ_0[i])


def whiteness_Berger1959_vectorise(XYZ, XYZ_0):
    X, Y, Z = zsplit(XYZ)
    X_0, Y_0, Z_0 = zsplit(XYZ_0)

    WI = 0.333 * Y + 125 * (Z / Z_0) - 125 * (X / X_0)

    return WI


def whiteness_Berger1959_analysis():
    message_box('whiteness_Berger1959')

    print('Reference:')
    XYZ = np.array([95., 100., 105.])
    XYZ_0 = np.array([94.80966767, 100., 107.30513595])
    print(whiteness_Berger1959(XYZ, XYZ_0))

    print('\n')

    print('1d array input:')
    print(whiteness_Berger1959_vectorise(XYZ, XYZ_0))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(whiteness_Berger1959_vectorise(XYZ, XYZ_0))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(whiteness_Berger1959_vectorise(XYZ, XYZ_0))

    print('\n')


# whiteness_Berger1959_analysis()

# #############################################################################
# # ### colour.whiteness_Taube1960
# #############################################################################


def whiteness_Taube1960_2d(XYZ, XYZ_0):
    for i in range(len(XYZ)):
        whiteness_Taube1960(XYZ[i], XYZ_0[i])


def whiteness_Taube1960_vectorise(XYZ, XYZ_0):
    X, Y, Z = zsplit(XYZ)
    X_0, Y_0, Z_0 = zsplit(XYZ_0)

    WI = 400 * (Z / Z_0) - 3 * Y

    return WI


def whiteness_Taube1960_analysis():
    message_box('whiteness_Taube1960')

    print('Reference:')
    XYZ = np.array([95., 100., 105.])
    XYZ_0 = np.array([94.80966767, 100., 107.30513595])
    print(whiteness_Taube1960(XYZ, XYZ_0))

    print('\n')

    print('1d array input:')
    print(whiteness_Taube1960_vectorise(XYZ, XYZ_0))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(whiteness_Taube1960_vectorise(XYZ, XYZ_0))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(whiteness_Taube1960_vectorise(XYZ, XYZ_0))

    print('\n')


# whiteness_Taube1960_analysis()

# #############################################################################
# # ### colour.whiteness_Stensby1968
# #############################################################################


def whiteness_Stensby1968_2d(Lab):
    for i in range(len(Lab)):
        whiteness_Stensby1968(Lab[i])


def whiteness_Stensby1968_vectorise(Lab):
    L, a, b = zsplit(Lab)

    WI = L - 3 * b + 3 * a

    return WI


def whiteness_Stensby1968_analysis():
    message_box('whiteness_Stensby1968')

    print('Reference:')
    Lab = np.array([100., -2.46875131, -16.72486654])
    print(whiteness_Stensby1968(Lab))

    print('\n')

    print('1d array input:')
    print(whiteness_Stensby1968_vectorise(Lab))

    print('\n')

    print('2d array input:')
    Lab = np.tile(Lab, (6, 1))
    print(whiteness_Stensby1968_vectorise(Lab))

    print('\n')

    print('3d array input:')
    Lab = np.reshape(Lab, (2, 3, 3))
    print(whiteness_Stensby1968_vectorise(Lab))

    print('\n')


# whiteness_Stensby1968_analysis()

# #############################################################################
# # ### colour.whiteness_ASTM313
# #############################################################################


def whiteness_ASTM313_2d(XYZ):
    for i in range(len(XYZ)):
        whiteness_ASTM313(XYZ[i])


def whiteness_ASTM313_vectorise(XYZ):
    X, Y, Z = zsplit(XYZ)

    WI = 3.388 * Z - 3 * Y

    return WI


def whiteness_ASTM313_analysis():
    message_box('whiteness_ASTM313')

    print('Reference:')
    XYZ = np.array([95., 100., 105.])
    print(whiteness_ASTM313(XYZ))

    print('\n')

    print('1d array input:')
    print(whiteness_ASTM313_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(whiteness_ASTM313_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(whiteness_ASTM313_vectorise(XYZ))

    print('\n')


# whiteness_ASTM313_analysis()

# #############################################################################
# # ### colour.whiteness_Ganz1979
# #############################################################################


def whiteness_Ganz1979_2d(xy, Y):
    for i in range(len(xy)):
        whiteness_Ganz1979(xy[i], Y[i])


def whiteness_Ganz1979_vectorise(xy, Y):
    x, y = zsplit(xy)

    W = Y - 1868.322 * x - 3695.690 * y + 1809.441
    T = -1001.223 * x + 748.366 * y + 68.261

    WT = zstack((W, T))

    return WT


def whiteness_Ganz1979_analysis():
    message_box('whiteness_Ganz1979')

    print('Reference:')
    xy = (0.3167, 0.3334)
    Y = 100.
    print(whiteness_Ganz1979(xy, Y))

    print('\n')

    print('1d array input:')
    print(whiteness_Ganz1979_vectorise(xy, Y))

    print('\n')

    print('2d array input:')
    xy = np.tile(xy, (6, 1))
    print(whiteness_Ganz1979_vectorise(xy, Y))

    print('\n')

    print('3d array input:')
    xy = np.reshape(xy, (2, 3, 2))
    print(whiteness_Ganz1979_vectorise(xy, Y))

    print('\n')


# whiteness_Ganz1979_analysis()

# #############################################################################
# # ### colour.whiteness_CIE2004
# #############################################################################


def whiteness_CIE2004_2d(xy, Y, xy_n):
    for i in range(len(xy)):
        whiteness_CIE2004(xy[i], Y[i], xy_n[i])


def whiteness_CIE2004_vectorise(xy,
                                Y,
                                xy_n,
                                observer='CIE 1931 2 Degree Standard Observer'):
    x, y = zsplit(xy)
    Y = np.asarray(Y)
    x_n, y_n = zsplit(xy_n)

    W = Y + 800 * (x_n - x) + 1700 * (y_n - y)
    T = (1000 if '1931' in observer else 900) * (x_n - x) - 650 * (y_n - y)

    WT = zstack((W, T))

    return WT


def whiteness_CIE2004_analysis():
    message_box('whiteness_CIE2004')

    print('Reference:')
    xy = (0.3167, 0.3334)
    Y = 100.
    xy_n = (0.3139, 0.3311)
    print(whiteness_CIE2004(xy, Y, xy_n))

    print('\n')

    print('1d array input:')
    print(whiteness_CIE2004_vectorise(xy, Y, xy_n))

    print('\n')

    print('2d array input:')
    xy = np.tile(xy, (6, 1))
    xy_n = np.tile(xy_n, (6, 1))
    print(whiteness_CIE2004_vectorise(xy, Y, xy_n))

    print('\n')

    print('3d array input:')
    xy = np.reshape(xy, (2, 3, 2))
    xy_n = np.reshape(xy_n, (2, 3, 2))
    print(whiteness_CIE2004_vectorise(xy, Y, xy_n))

    print('\n')


# whiteness_CIE2004_analysis()

# #############################################################################
# #############################################################################
# ## colour.difference.delta_e
# #############################################################################
# #############################################################################

# #############################################################################
# ## colour.delta_E_CIE1976
# #############################################################################
from colour.difference.delta_e import *


def delta_E_CIE1976_2d(Lab1, Lab2):
    for i in range(len(Lab1)):
        delta_E_CIE1976(Lab1[i], Lab2[i])


def delta_E_CIE1976_vectorise(Lab1, Lab2, **kwargs):
    delta_E = np.linalg.norm(np.asarray(Lab1) - np.asarray(Lab2), axis=-1)

    return delta_E


def delta_E_CIE1976_analysis():
    message_box('delta_E_CIE1976')

    print('Reference:')
    Lab1 = np.array([100, 21.57210357, 272.2281935])
    Lab2 = np.array([100, 426.67945353, 72.39590835])
    print(delta_E_CIE1976(Lab1, Lab2))

    print('\n')

    print('1d array input:')
    print(delta_E_CIE1976_vectorise(Lab1, Lab2))

    print('\n')

    print('2d array input:')
    Lab1 = np.tile(Lab1, (6, 1))
    Lab2 = np.tile(Lab2, (6, 1))
    print(delta_E_CIE1976_vectorise(Lab1, Lab2))

    print('\n')

    print('3d array input:')
    Lab1 = np.reshape(Lab1, (2, 3, 3))
    Lab2 = np.reshape(Lab2, (2, 3, 3))
    print(delta_E_CIE1976_vectorise(Lab1, Lab2))

    print('\n')


# delta_E_CIE1976_analysis()

# #############################################################################
# # ### colour.delta_E_CIE1994
# #############################################################################


def delta_E_CIE1994_2d(Lab1, Lab2):
    for i in range(len(Lab1)):
        delta_E_CIE1994(Lab1[i], Lab2[i])


def delta_E_CIE1994_vectorise(Lab1, Lab2, textiles=True, **kwargs):
    k1 = 0.048 if textiles else 0.045
    k2 = 0.014 if textiles else 0.015
    kL = 2 if textiles else 1
    kC = 1
    kH = 1

    L1, a1, b1 = zsplit(Lab1)
    L2, a2, b2 = zsplit(Lab2)

    C1 = np.sqrt(a1 ** 2 + b1 ** 2)
    C2 = np.sqrt(a2 ** 2 + b2 ** 2)

    sL = 1
    sC = 1 + k1 * C1
    sH = 1 + k2 * C1

    delta_L = L1 - L2
    delta_C = C1 - C2
    delta_A = a1 - a2
    delta_B = b1 - b2

    delta_H = np.sqrt(delta_A ** 2 + delta_B ** 2 - delta_C ** 2)

    L = (delta_L / (kL * sL)) ** 2
    C = (delta_C / (kC * sC)) ** 2
    H = (delta_H / (kH * sH)) ** 2

    delta_E = np.sqrt(L + C + H)

    return delta_E


def delta_E_CIE1994_analysis():
    message_box('delta_E_CIE1994')

    print('Reference:')
    Lab1 = np.array([100, 21.57210357, 272.2281935])
    Lab2 = np.array([100, 426.67945353, 72.39590835])
    print(delta_E_CIE1994(Lab1, Lab2))

    print('\n')

    print('1d array input:')
    print(delta_E_CIE1994_vectorise(Lab1, Lab2))

    print('\n')

    print('2d array input:')
    Lab1 = np.tile(Lab1, (6, 1))
    Lab2 = np.tile(Lab2, (6, 1))
    print(delta_E_CIE1994_vectorise(Lab1, Lab2))

    print('\n')

    print('3d array input:')
    Lab1 = np.reshape(Lab1, (2, 3, 3))
    Lab2 = np.reshape(Lab2, (2, 3, 3))
    print(delta_E_CIE1994_vectorise(Lab1, Lab2))

    print('\n')


# delta_E_CIE1994_analysis()

# #############################################################################
# # ### colour.delta_E_CIE2000
# #############################################################################


def delta_E_CIE2000_2d(Lab1, Lab2):
    delta_E = []
    for i in range(len(Lab1)):
        delta_E.append(delta_E_CIE2000(Lab1[i], Lab2[i]))
    return delta_E


def delta_E_CIE2000_vectorise(Lab1, Lab2, **kwargs):
    kL = 1
    kC = 1
    kH = 1

    L1, a1, b1 = zsplit(Lab1)
    L2, a2, b2 = zsplit(Lab2)

    l_bar_prime = 0.5 * (L1 + L2)

    c1 = np.sqrt(a1 * a1 + b1 * b1)
    c2 = np.sqrt(a2 * a2 + b2 * b2)

    c_bar = 0.5 * (c1 + c2)
    c_bar7 = np.power(c_bar, 7)

    g = 0.5 * (1 - np.sqrt(c_bar7 / (c_bar7 + 25 ** 7)))

    a1_prime = a1 * (1 + g)
    a2_prime = a2 * (1 + g)
    c1_prime = np.sqrt(a1_prime * a1_prime + b1 * b1)
    c2_prime = np.sqrt(a2_prime * a2_prime + b2 * b2)
    c_bar_prime = 0.5 * (c1_prime + c2_prime)

    h1_prime = np.asarray(np.rad2deg(np.arctan2(b1, a1_prime)))
    h1_prime[np.asarray(h1_prime < 0.0)] += 360

    h2_prime = np.asarray(np.rad2deg(np.arctan2(b2, a2_prime)))
    h2_prime[np.asarray(h2_prime < 0.0)] += 360

    h_bar_prime = np.where(np.fabs(h1_prime - h2_prime) <= 180,
                           0.5 * (h1_prime + h2_prime),
                           (0.5 * (h1_prime + h2_prime + 360)))

    t = (1 - 0.17 * np.cos(np.deg2rad(h_bar_prime - 30)) +
         0.24 * np.cos(np.deg2rad(2 * h_bar_prime)) +
         0.32 * np.cos(np.deg2rad(3 * h_bar_prime + 6)) -
         0.20 * np.cos(np.deg2rad(4 * h_bar_prime - 63)))

    h = h2_prime - h1_prime
    delta_h_prime = np.where(h2_prime <= h1_prime, h - 360, h + 360)
    delta_h_prime = np.where(np.fabs(h) <= 180, h, delta_h_prime)

    delta_L_prime = L2 - L1
    delta_C_prime = c2_prime - c1_prime
    delta_H_prime = (2 * np.sqrt(c1_prime * c2_prime) *
                     np.sin(np.deg2rad(0.5 * delta_h_prime)))

    sL = 1 + ((0.015 * (l_bar_prime - 50) * (l_bar_prime - 50)) /
              np.sqrt(20 + (l_bar_prime - 50) * (l_bar_prime - 50)))
    sC = 1 + 0.045 * c_bar_prime
    sH = 1 + 0.015 * c_bar_prime * t

    delta_theta = (30 * np.exp(-((h_bar_prime - 275) / 25) *
                               ((h_bar_prime - 275) / 25)))

    c_bar_prime7 = c_bar_prime ** 7

    rC = np.sqrt(c_bar_prime7 / (c_bar_prime7 + 25 ** 7))
    rT = -2 * rC * np.sin(np.deg2rad(2 * delta_theta))

    delta_E = np.sqrt(
        (delta_L_prime / (kL * sL)) * (delta_L_prime / (kL * sL)) +
        (delta_C_prime / (kC * sC)) * (delta_C_prime / (kC * sC)) +
        (delta_H_prime / (kH * sH)) * (delta_H_prime / (kH * sH)) +
        (delta_C_prime / (kC * sC)) * (delta_H_prime / (kH * sH)) * rT)

    return delta_E


def delta_E_CIE2000_analysis():
    message_box('delta_E_CIE2000')

    print('Reference:')
    Lab1 = np.array([100, 21.57210357, 272.2281935])
    Lab2 = np.array([100, 426.67945353, 72.39590835])
    print(delta_E_CIE2000(Lab1, Lab2))

    print('\n')

    print('1d array input:')
    print(delta_E_CIE2000_vectorise(Lab1, Lab2))

    print('\n')

    print('2d array input:')
    Lab1 = np.tile(Lab1, (6, 1))
    Lab2 = np.tile(Lab2, (6, 1))
    print(delta_E_CIE2000_vectorise(Lab1, Lab2))

    print('\n')

    print('3d array input:')
    Lab1 = np.reshape(Lab1, (2, 3, 3))
    Lab2 = np.reshape(Lab2, (2, 3, 3))
    print(delta_E_CIE2000_vectorise(Lab1, Lab2))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(delta_E_CIE2000_2d(DATA1 * 360, DATA2 * 360)),
        np.ravel(delta_E_CIE2000_vectorise(DATA1 * 360, DATA2 * 360)))


# delta_E_CIE2000_analysis()

# #############################################################################
# # ### colour.delta_E_CMC
# #############################################################################


def delta_E_CMC_2d(Lab1, Lab2):
    delta_E = []
    for i in range(len(Lab1)):
        delta_E.append(delta_E_CMC(Lab1[i], Lab2[i]))
    return delta_E


def delta_E_CMC_vectorise(Lab1, Lab2, l=2, c=1):
    L1, a1, b1 = zsplit(Lab1)
    L2, a2, b2 = zsplit(Lab2)

    c1 = np.sqrt(a1 * a1 + b1 * b1)
    c2 = np.sqrt(a2 * a2 + b2 * b2)
    sl = np.where(L1 < 16, 0.511, (0.040975 * L1) / (1 + 0.01765 * L1))
    sc = 0.0638 * c1 / (1 + 0.0131 * c1) + 0.638
    h1 = np.where(c1 < 0.000001, 0, np.rad2deg(np.arctan2(b1, a1)))

    while np.any(h1 < 0):
        h1[h1 < 0] += 360

    while np.any(h1 >= 360):
        h1[h1 >= 360] -= 360

    t = np.where(np.logical_and(h1 >= 164, h1 <= 345),
                 0.56 + np.fabs(0.2 * np.cos(np.deg2rad(h1 + 168))),
                 0.36 + np.fabs(0.4 * np.cos(np.deg2rad(h1 + 35))))

    c4 = c1 * c1 * c1 * c1
    f = np.sqrt(c4 / (c4 + 1900))
    sh = sc * (f * t + 1 - f)

    delta_L = L1 - L2
    delta_C = c1 - c2
    delta_A = a1 - a2
    delta_B = b1 - b2
    delta_H2 = delta_A * delta_A + delta_B * delta_B - delta_C * delta_C

    v1 = delta_L / (l * sl)
    v2 = delta_C / (c * sc)
    v3 = sh

    delta_E = np.sqrt(v1 * v1 + v2 * v2 + (delta_H2 / (v3 * v3)))

    return delta_E


def delta_E_CMC_analysis():
    message_box('delta_E_CMC')

    print('Reference:')
    Lab1 = np.array([100, 21.57210357, 272.2281935])
    Lab2 = np.array([100, 426.67945353, 72.39590835])
    print(delta_E_CMC(Lab1, Lab2))

    print('\n')

    print('1d array input:')
    print(delta_E_CMC_vectorise(Lab1, Lab2))

    print('\n')

    print('2d array input:')
    Lab1 = np.tile(Lab1, (6, 1))
    Lab2 = np.tile(Lab2, (6, 1))
    print(delta_E_CMC_vectorise(Lab1, Lab2))

    print('\n')

    print('3d array input:')
    Lab1 = np.reshape(Lab1, (2, 3, 3))
    Lab2 = np.reshape(Lab2, (2, 3, 3))
    print(delta_E_CMC_vectorise(Lab1, Lab2))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(delta_E_CMC_2d(DATA1 * 360, DATA2 * 360)),
        np.ravel(delta_E_CMC_vectorise(DATA1 * 360, DATA2 * 360)))


# delta_E_CMC_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.cie_xyy
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.XYZ_to_xyY
# #############################################################################
from colour import ILLUMINANTS
from colour.models.cie_xyy import *


def XYZ_to_xyY_2d(XYZ):
    xyY = []
    for i in range(len(XYZ)):
        xyY.append(XYZ_to_xyY(XYZ[i]))
    return xyY


@handle_numpy_errors(divide='ignore', invalid='ignore')
def XYZ_to_xyY_vectorise(XYZ,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    # TODO: Mention implicit resize.
    XYZ = np.asarray(XYZ)
    X, Y, Z = zsplit(XYZ)
    x_w, y_w = zsplit(illuminant)

    xyY = np.where(
        XYZ == 0,
        zstack((np.resize(x_w, X.shape), np.resize(y_w, Y.shape), Y)),
        zstack((X / (X + Y + Z), Y / (X + Y + Z), Y)))

    return xyY


def XYZ_to_xyY_analysis():
    message_box('XYZ_to_xyY')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_xyY(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_xyY_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_xyY_vectorise(XYZ))

    print('\n')

    XYZ = np.tile((0, 0, 0), (6, 1))
    print(XYZ_to_xyY_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(np.tile([0.07049534, 0.1008, 0.09558313], (6, 1)),
                     (2, 3, 3))
    print(XYZ_to_xyY_vectorise(XYZ))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(XYZ_to_xyY_2d(DATA1)),
        np.ravel(XYZ_to_xyY_vectorise(DATA1)))


# XYZ_to_xyY_analysis()

# #############################################################################
# # ### colour.xyY_to_XYZ
# #############################################################################


def xyY_to_XYZ_2d(xyY):
    XYZ = []
    for i in range(len(xyY)):
        XYZ.append(xyY_to_XYZ(xyY[i]))
    return XYZ


@handle_numpy_errors(divide='ignore')
def xyY_to_XYZ_vectorise(xyY):
    x, y, Y = zsplit(xyY)

    XYZ = np.where((y == 0)[..., np.newaxis],
                   zstack((y, y, y)),
                   zstack((x * Y / y, Y, (1 - x - y) * Y / y)))

    return XYZ


def xyY_to_XYZ_analysis():
    message_box('xyY_to_XYZ')

    print('Reference:')
    xyY = np.array([0.26414772, 0.37770001, 0.1008])
    print(xyY_to_XYZ(xyY))

    print('\n')

    print('1d array input:')
    print(xyY_to_XYZ_vectorise(xyY))

    print('\n')

    print('2d array input:')
    xyY = np.tile(xyY, (6, 1))
    print(xyY_to_XYZ_vectorise(xyY))

    print('\n')

    print('3d array input:')
    xyY = np.reshape(xyY, (2, 3, 3))
    print(xyY_to_XYZ_vectorise(xyY))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(xyY_to_XYZ_2d(DATA1)),
        np.ravel(xyY_to_XYZ_vectorise(DATA1)))


# xyY_to_XYZ_analysis()

# #############################################################################
# # ### colour.xy_to_XYZ
# #############################################################################


def xy_to_XYZ_2d(xy):
    for i in range(len(xy)):
        xy_to_XYZ(xy[i])


def xy_to_XYZ_vectorise(xy):
    x, y = zsplit(xy)

    xyY = zstack((x, y, np.ones(x.shape)))
    XYZ = xyY_to_XYZ_vectorise(xyY)

    return XYZ


def xy_to_XYZ_analysis():
    message_box('xy_to_XYZ')

    print('Reference:')
    xy = (0.26414772236966133, 0.37770000704815188)
    print(xy_to_XYZ(xy))

    print('\n')

    print('1d array input:')
    print(xy_to_XYZ_vectorise(xy))

    print('\n')

    print('2d array input:')
    xy = np.tile(xy, (6, 1))
    print(xy_to_XYZ_vectorise(xy))

    print('\n')

    print('3d array input:')
    xy = np.reshape(xy, (2, 3, 2))
    print(xy_to_XYZ_vectorise(xy))

    print('\n')


# xy_to_XYZ_analysis()

# #############################################################################
# # ### colour.XYZ_to_xy
# #############################################################################


def XYZ_to_xy_2d(XYZ):
    for i in range(len(XYZ)):
        XYZ_to_xy(XYZ[i])


def XYZ_to_xy_vectorise(XYZ,
                        illuminant=ILLUMINANTS.get(
                            'CIE 1931 2 Degree Standard Observer').get('D50')):
    xyY = XYZ_to_xyY_vectorise(XYZ, illuminant)
    xy = xyY[..., 0:2]

    return xy


def XYZ_to_xy_analysis():
    message_box('XYZ_to_xy')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_xy(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_xy_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_xy_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_xy_vectorise(XYZ))

    print('\n')


# XYZ_to_xy_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.cie_lab
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.XYZ_to_Lab
# #############################################################################
from colour.models.cie_lab import *


def XYZ_to_Lab_2d(XYZ):
    Lab = []
    for i in range(len(XYZ)):
        Lab.append(XYZ_to_Lab(XYZ[i]))
    return Lab


def XYZ_to_Lab_vectorise(XYZ,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    XYZ = np.asarray(XYZ)
    XYZ_r = xy_to_XYZ_vectorise(illuminant)

    XYZ_f = XYZ / XYZ_r

    XYZ_f = np.where(XYZ_f > CIE_E,
                     np.power(XYZ_f, 1 / 3),
                     (CIE_K * XYZ_f + 16) / 116)

    X_f, Y_f, Z_f = zsplit(XYZ_f)

    L = 116 * Y_f - 16
    a = 500 * (X_f - Y_f)
    b = 200 * (Y_f - Z_f)

    Lab = zstack((L, a, b))

    return Lab


def XYZ_to_Lab_analysis():
    message_box('XYZ_to_Lab')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_Lab(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_Lab_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_Lab_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_Lab_vectorise(XYZ))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(XYZ_to_Lab_2d(DATA1)),
        np.ravel(XYZ_to_Lab_vectorise(DATA1)))


# XYZ_to_Lab_analysis()

# #############################################################################
# # ### colour.Lab_to_XYZ
# #############################################################################


def Lab_to_XYZ_2d(Lab):
    XYZ = []
    for i in range(len(Lab)):
        XYZ.append(Lab_to_XYZ(Lab[i]))
    return XYZ


def Lab_to_XYZ_vectorise(Lab,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    L, a, b = zsplit(Lab)
    XYZ_r = xy_to_XYZ_vectorise(illuminant)

    f_y = (L + 16) / 116
    f_x = a / 500 + f_y
    f_z = f_y - b / 200

    x_r = np.where(f_x ** 3 > CIE_E, f_x ** 3, (116 * f_x - 16) / CIE_K)
    y_r = np.where(L > CIE_K * CIE_E, ((L + 16) / 116) ** 3, L / CIE_K)
    z_r = np.where(f_z ** 3 > CIE_E, f_z ** 3, (116 * f_z - 16) / CIE_K)

    XYZ = zstack((x_r, y_r, z_r)) * XYZ_r

    return XYZ


def Lab_to_XYZ_analysis():
    message_box('Lab_to_XYZ')

    print('Reference:')
    Lab = np.array([37.9856291, -23.62302887, -4.41417036])
    print(Lab_to_XYZ(Lab))

    print('\n')

    print('1d array input:')
    print(Lab_to_XYZ_vectorise(Lab))

    print('\n')

    print('2d array input:')
    Lab = np.tile(Lab, (6, 1))
    print(Lab_to_XYZ_vectorise(Lab))

    print('\n')

    print('3d array input:')
    Lab = np.reshape(Lab, (2, 3, 3))
    print(Lab_to_XYZ_vectorise(Lab))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(Lab_to_XYZ_2d(DATA1 * 360)),
        np.ravel(Lab_to_XYZ_vectorise(DATA1 * 360)))


# Lab_to_XYZ_analysis()

# #############################################################################
# # ### colour.Lab_to_LCHab
# #############################################################################


def Lab_to_LCHab_2d(Lab):
    for i in range(len(Lab)):
        Lab_to_LCHab(Lab[i])


def Lab_to_LCHab_vectorise(Lab):
    L, a, b = zsplit(Lab)

    H = np.asarray(180 * np.arctan2(b, a) / np.pi)
    H[np.asarray(H < 0)] += 360

    LCHab = zstack((L, np.sqrt(a ** 2 + b ** 2), H))

    return LCHab


def Lab_to_LCHab_analysis():
    message_box('Lab_to_LCHab')

    print('Reference:')
    Lab = np.array([37.9856291, -23.62302887, -4.41417036])
    print(Lab_to_LCHab(Lab))

    print('\n')

    print('1d array input:')
    print(Lab_to_LCHab_vectorise(Lab))

    print('\n')

    print('2d array input:')
    Lab = np.tile(Lab, (6, 1))
    print(Lab_to_LCHab_vectorise(Lab))

    print('\n')

    print('2d array input:')
    Lab = np.reshape(Lab, (2, 3, 3))
    print(Lab_to_LCHab_vectorise(Lab))

    print('\n')


# Lab_to_LCHab_analysis()

# #############################################################################
# # ### colour.LCHab_to_Lab
# #############################################################################


def LCHab_to_Lab_2d(LCHab):
    for i in range(len(LCHab)):
        LCHab_to_Lab(LCHab[i])


def LCHab_to_Lab_vectorise(LCHab):
    L, C, H = zsplit(LCHab)

    return zstack((L,
                   C * np.cos(np.radians(H)),
                   C * np.sin(np.radians(H))))


def LCHab_to_Lab_analysis():
    message_box('LCHab_to_Lab')

    print('Reference:')
    LCHab = np.array([37.9856291, 24.03190365, 190.58415972])
    print(LCHab_to_Lab(LCHab))

    print('\n')

    print('1d array input:')
    print(LCHab_to_Lab_vectorise(LCHab))

    print('\n')

    print('2d array input:')
    LCHab = np.tile(LCHab, (6, 1))
    print(LCHab_to_Lab_vectorise(LCHab))

    print('\n')

    print('3d array input:')
    LCHab = np.reshape(LCHab, (2, 3, 3))
    print(LCHab_to_Lab_vectorise(LCHab))

    print('\n')


# LCHab_to_Lab_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.cie_luv
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.XYZ_to_Luv
# #############################################################################
from colour.models.cie_luv import *


def XYZ_to_Luv_2d(XYZ):
    Luv = []
    for i in range(len(XYZ)):
        Luv.append(XYZ_to_Luv(XYZ[i]))
    return Luv


def XYZ_to_Luv_vectorise(XYZ,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    X, Y, Z = zsplit(XYZ)
    X_r, Y_r, Z_r = zsplit(xy_to_XYZ_vectorise(illuminant))

    y_r = Y / Y_r

    L = np.where(y_r > CIE_E, 116 * y_r ** (1 / 3) - 16, CIE_K * y_r)

    u = (13 * L * ((4 * X / (X + 15 * Y + 3 * Z)) -
                   (4 * X_r / (X_r + 15 * Y_r + 3 * Z_r))))
    v = (13 * L * ((9 * Y / (X + 15 * Y + 3 * Z)) -
                   (9 * Y_r / (X_r + 15 * Y_r + 3 * Z_r))))

    Luv = zstack((L, u, v))

    return Luv


def XYZ_to_Luv_analysis():
    message_box('XYZ_to_Luv')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_Luv(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_Luv_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_Luv_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_Luv_vectorise(XYZ))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(XYZ_to_Luv_2d(DATA1)),
        np.ravel(XYZ_to_Luv_vectorise(DATA1)))


# XYZ_to_Luv_analysis()

# #############################################################################
# # ### colour.Luv_to_XYZ
# #############################################################################


def Luv_to_XYZ_2d(Luv):
    XYZ = []
    for i in range(len(Luv)):
        XYZ.append(Luv_to_XYZ(Luv[i]))
    return XYZ


def Luv_to_XYZ_vectorise(Luv,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    L, u, v = zsplit(Luv)
    X_r, Y_r, Z_r = zsplit(xy_to_XYZ_vectorise(illuminant))

    Y = np.where(L > CIE_E * CIE_K, ((L + 16) / 116) ** 3, L / CIE_K)

    a = 1 / 3 * ((52 * L / (u + 13 * L *
                            (4 * X_r / (X_r + 15 * Y_r + 3 * Z_r)))) - 1)
    b = -5 * Y
    c = -1 / 3.0
    d = Y * (39 * L / (v + 13 * L *
                       (9 * Y_r / (X_r + 15 * Y_r + 3 * Z_r))) - 5)

    X = (d - b) / (a - c)
    Z = X * a + b

    XYZ = zstack((X, Y, Z))

    return XYZ


def Luv_to_XYZ_analysis():
    message_box('Luv_to_XYZ')

    print('Reference:')
    Luv = np.array([37.9856291, -28.79229446, -1.3558195])
    print(Luv_to_XYZ(Luv))

    print('\n')

    print('1d array input:')
    print(Luv_to_XYZ_vectorise(Luv))

    print('\n')

    print('2d array input:')
    Luv = np.tile(Luv, (6, 1))
    print(Luv_to_XYZ_vectorise(Luv))

    print('\n')

    print('3d array input:')
    Luv = np.reshape(Luv, (2, 3, 3))
    print(Luv_to_XYZ_vectorise(Luv))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(Luv_to_XYZ_2d(DATA1)),
        np.ravel(Luv_to_XYZ_vectorise(DATA1)))


# Luv_to_XYZ_analysis()

# #############################################################################
# # ### colour.Luv_to_uv
# #############################################################################


def Luv_to_uv_2d(Luv):
    for i in range(len(Luv)):
        Luv_to_uv(Luv[i])


def Luv_to_uv_vectorise(Luv,
                        illuminant=ILLUMINANTS.get(
                            'CIE 1931 2 Degree Standard Observer').get('D50')):
    X, Y, Z = zsplit(Luv_to_XYZ_vectorise(Luv, illuminant))

    uv = zstack((4 * X / (X + 15 * Y + 3 * Z),
                 9 * Y / (X + 15 * Y + 3 * Z)))

    return uv


def Luv_to_uv_analysis():
    message_box('Luv_to_uv')

    print('Reference:')
    Luv = np.array([37.9856291, -28.79229446, -1.3558195])
    print(Luv_to_uv(Luv))

    print('\n')

    print('1d array input:')
    print(Luv_to_uv_vectorise(Luv))

    print('\n')

    print('2d array input:')
    Luv = np.tile(Luv, (6, 1))
    print(Luv_to_uv_vectorise(Luv))

    print('\n')

    print('3d array input:')
    Luv = np.reshape(Luv, (2, 3, 3))
    print(Luv_to_uv_vectorise(Luv))

    print('\n')


# Luv_to_uv_analysis()

# #############################################################################
# # ### colour.Luv_uv_to_xy
# #############################################################################


def Luv_uv_to_xy_2d(uv):
    for i in range(len(uv)):
        Luv_uv_to_xy(uv[i])


def Luv_uv_to_xy_vectorise(uv):
    u, v = zsplit(uv)

    xy = zstack((9 * u / (6 * u - 16 * v + 12),
                 4 * v / (6 * u - 16 * v + 12)))

    return xy


def Luv_uv_to_xy_analysis():
    message_box('Luv_uv_to_xy')

    print('Reference:')
    uv = np.array([0.15085309882985695, 0.48532970854318019])
    print(Luv_uv_to_xy(uv))

    print('\n')

    print('1d array input:')
    print(Luv_uv_to_xy_vectorise(uv))

    print('\n')

    print('2d array input:')
    uv = np.tile(uv, (6, 1))
    print(Luv_uv_to_xy_vectorise(uv))

    print('\n')

    print('3d array input:')
    uv = np.reshape(uv, (2, 3, 2))
    print(Luv_uv_to_xy_vectorise(uv))

    print('\n')


# Luv_uv_to_xy_analysis()

# #############################################################################
# # ### colour.Luv_to_LCHuv
# #############################################################################


def Luv_to_LCHuv_2d(Luv):
    for i in range(len(Luv)):
        Luv_to_LCHuv(Luv[i])


def Luv_to_LCHuv_vectorise(Luv):
    L, u, v = zsplit(Luv)

    H = np.asarray(180 * np.arctan2(v, u) / np.pi)
    H[np.asarray(H < 0)] += 360

    LCHuv = zstack((L, np.sqrt(u ** 2 + v ** 2), H))

    return LCHuv


def Luv_to_LCHuv_analysis():
    message_box('Luv_to_LCHuv')

    print('Reference:')
    Luv = np.array([37.9856291, -28.79229446, -1.3558195])
    print(Luv_to_LCHuv(Luv))

    print('\n')

    print('1d array input:')
    print(Luv_to_LCHuv_vectorise(Luv))

    print('\n')

    print('2d array input:')
    Luv = np.tile(Luv, (6, 1))
    print(Luv_to_LCHuv_vectorise(Luv))

    print('\n')

    print('3d array input:')
    Luv = np.reshape(Luv, (2, 3, 3))
    print(Luv_to_LCHuv_vectorise(Luv))

    print('\n')


# Luv_to_LCHuv_analysis()

# #############################################################################
# # ### colour.LCHuv_to_Luv
# #############################################################################


def LCHuv_to_Luv_2d(LCHuv):
    for i in range(len(LCHuv)):
        LCHuv_to_Luv(LCHuv[i])


def LCHuv_to_Luv_vectorise(LCHuv):
    L, C, H = zsplit(LCHuv)

    Luv = zstack((L, C * np.cos(np.radians(H)), C * np.sin(np.radians(H))))

    return Luv


def LCHuv_to_Luv_analysis():
    message_box('LCHuv_to_Luv')

    print('Reference:')
    LCHuv = np.array([37.9856291, 28.82419933, 182.69604747])
    print(LCHuv_to_Luv(LCHuv))

    print('\n')

    print('1d array input:')
    print(LCHuv_to_Luv_vectorise(LCHuv))

    print('\n')

    print('2d array input:')
    LCHuv = np.tile(LCHuv, (6, 1))
    print(LCHuv_to_Luv_vectorise(LCHuv))

    print('\n')

    print('3d array input:')
    LCHuv = np.reshape(LCHuv, (2, 3, 3))
    print(LCHuv_to_Luv_vectorise(LCHuv))

    print('\n')


# LCHuv_to_Luv_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.cie_ucs
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.XYZ_to_UCS
# #############################################################################
from colour.models.cie_ucs import *


def XYZ_to_UCS_2d(XYZ):
    for i in range(len(XYZ)):
        XYZ_to_UCS(XYZ[i])


def XYZ_to_UCS_vectorise(XYZ):
    X, Y, Z = zsplit(XYZ)

    UVW = zstack((2 / 3 * X, Y, 1 / 2 * (-X + 3 * Y + Z)))

    return UVW


def XYZ_to_UCS_analysis():
    message_box('XYZ_to_UCS')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_UCS(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_UCS_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_UCS_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_UCS_vectorise(XYZ))

    print('\n')


# XYZ_to_UCS_analysis()

# #############################################################################
# # ### colour.UCS_to_XYZ
# #############################################################################


def UCS_to_XYZ_2d(UVW):
    for i in range(len(UVW)):
        UCS_to_XYZ(UVW[i])


def UCS_to_XYZ_vectorise(UVW):
    U, V, W = zsplit(UVW)

    XYZ = zstack((3 / 2 * U, V, 3 / 2 * U - (3 * V) + (2 * W)))

    return XYZ


def UCS_to_XYZ_analysis():
    message_box('UCS_to_XYZ')

    print('Reference:')
    UVW = np.array([0.04699689, 0.1008, 0.1637439])
    print(UCS_to_XYZ(UVW))

    print('\n')

    print('1d array input:')
    print(UCS_to_XYZ_vectorise(UVW))

    print('\n')

    print('2d array input:')
    UVW = np.tile(UVW, (6, 1))
    print(UCS_to_XYZ_vectorise(UVW))

    print('\n')

    print('3d array input:')
    UVW = np.reshape(UVW, (2, 3, 3))
    print(UCS_to_XYZ_vectorise(UVW))

    print('\n')


# UCS_to_XYZ_analysis()

# #############################################################################
# # ### colour.UCS_to_uv
# #############################################################################


def UCS_to_uv_2d(UVW):
    for i in range(len(UVW)):
        UCS_to_uv(UVW[i])


def UCS_to_uv_vectorise(UVW):
    U, V, W = zsplit(UVW)

    uv = zstack((U / (U + V + W), V / (U + V + W)))

    return uv


def UCS_to_uv_analysis():
    message_box('UCS_to_uv')

    print('Reference:')
    UVW = np.array([0.04699689, 0.1008, 0.1637439])
    print(UCS_to_uv(UVW))

    print('\n')

    print('1d array input:')
    print(UCS_to_uv_vectorise(UVW))

    print('\n')

    print('2d array input:')
    UVW = np.tile(UVW, (6, 1))
    print(UCS_to_uv_vectorise(UVW))

    print('\n')

    print('3d array input:')
    UVW = np.reshape(UVW, (2, 3, 3))
    print(UCS_to_uv_vectorise(UVW))

    print('\n')


# UCS_to_uv_analysis()

# #############################################################################
# # ### colour.UCS_uv_to_xy
# #############################################################################


def UCS_uv_to_xy_2d(uv):
    for i in range(len(uv)):
        UCS_uv_to_xy(uv[i])


def UCS_uv_to_xy_vectorise(uv):
    u, v = zsplit(uv)

    xy = zstack((3 * u / (2 * u - 8 * v + 4), 2 * v / (2 * u - 8 * v + 4)))

    return xy


def UCS_uv_to_xy_analysis():
    message_box('UCS_uv_to_xy')

    print('Reference:')
    uv = np.array([0.15085308732766581, 0.3235531372954405])
    print(UCS_uv_to_xy(uv))

    print('\n')

    print('1d array input:')
    print(UCS_uv_to_xy_vectorise(uv))

    print('\n')

    print('2d array input:')
    uv = np.tile(uv, (6, 1))
    print(UCS_uv_to_xy_vectorise(uv))

    print('\n')

    print('3d array input:')
    uv = np.reshape(uv, (2, 3, 2))
    print(UCS_uv_to_xy_vectorise(uv))

    print('\n')


# UCS_uv_to_xy_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.cie_uvw
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.XYZ_to_UVW
# #############################################################################
from colour.models.cie_uvw import *


def XYZ_to_UVW_2d(XYZ):
    for i in range(len(XYZ)):
        XYZ_to_UVW(XYZ[i])


def XYZ_to_UVW_vectorise(XYZ,
                         illuminant=ILLUMINANTS.get(
                             'CIE 1931 2 Degree Standard Observer').get(
                             'D50')):
    xyY = XYZ_to_xyY_vectorise(XYZ, illuminant)
    x, y, Y = zsplit(xyY)

    u, v = zsplit(UCS_to_uv_vectorise(XYZ_to_UCS_vectorise(XYZ)))
    u_0, v_0 = zsplit(UCS_to_uv_vectorise(XYZ_to_UCS_vectorise(
        xy_to_XYZ_vectorise(illuminant))))

    W = 25 * Y ** (1 / 3) - 17
    U = 13 * W * (u - u_0)
    V = 13 * W * (v - v_0)

    UVW = zstack((U, V, W))

    return UVW


def XYZ_to_UVW_analysis():
    message_box('XYZ_to_UVW')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])
    print(XYZ_to_UVW(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_UVW_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_UVW_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_UVW_vectorise(XYZ))

    print('\n')


# XYZ_to_UVW_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.deprecated
# #############################################################################
# #############################################################################

# #############################################################################
# # ### colour.models.deprecated.RGB_to_HSV
# #############################################################################
from colour.models.deprecated import *


def RGB_to_HSV_2d(RGB):
    HSV = []
    for i in range(len(RGB)):
        HSV.append(RGB_to_HSV(RGB[i]))
    return HSV


@handle_numpy_errors(divide='ignore', invalid='ignore')
def RGB_to_HSV_vectorise(RGB):
    minimum = np.amin(RGB, -1)
    maximum = np.amax(RGB, -1)
    delta = np.ptp(RGB, -1)

    V = maximum

    R, G, B = zsplit(RGB)

    S = np.asarray(delta / maximum)
    S[np.asarray(delta == 0)] = 0

    delta_R = (((maximum - R) / 6) + (delta / 2)) / delta
    delta_G = (((maximum - G) / 6) + (delta / 2)) / delta
    delta_B = (((maximum - B) / 6) + (delta / 2)) / delta

    H = delta_B - delta_G
    H = np.where(G == maximum, (1 / 3) + delta_R - delta_B, H)
    H = np.where(B == maximum, (2 / 3) + delta_G - delta_R, H)
    H[np.asarray(H < 0)] += 1
    H[np.asarray(H > 1)] -= 1
    H[np.asarray(delta == 0)] = 0

    HSV = zstack((H, S, V))

    return HSV


def RGB_to_HSV_analysis():
    message_box('RGB_to_HSV')

    print('Reference:')
    RGB = np.array([0.49019608, 0.98039216, 0.25098039])
    print(RGB_to_HSV(RGB))

    print('\n')

    print('1d array input:')
    print(RGB_to_HSV_vectorise(RGB))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_HSV_vectorise(RGB))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_HSV_vectorise(RGB))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(RGB_to_HSV_2d(DATA1)),
        np.ravel(RGB_to_HSV_vectorise(DATA1)))


# RGB_to_HSV_analysis()

# #############################################################################
# # ### colour.models.deprecated.HSV_to_RGB
# #############################################################################
def HSV_to_RGB_2d(HSV):
    RGB = []
    for i in range(len(HSV)):
        RGB.append(HSV_to_RGB(HSV[i]))
    return RGB


def HSV_to_RGB_vectorise(HSV):
    H, S, V = zsplit(HSV)

    h = np.asarray(H * 6)
    h[np.asarray(h == 6)] = 0

    i = np.floor(h)
    j = V * (1 - S)
    k = V * (1 - S * (h - i))
    l = V * (1 - S * (1 - (h - i)))

    i = zstack((i, i, i)).astype(np.uint8)
    RGB = np.choose(i,
                    (zstack((V, l, j)),
                     zstack((k, V, j)),
                     zstack((j, V, l)),
                     zstack((j, k, V)),
                     zstack((l, j, V)),
                     zstack((V, j, k))))

    return RGB


def RGB_to_HSV_analysis():
    message_box('RGB_to_HSV')

    print('Reference:')
    HSV = np.array([0.27867383, 0.744, 0.98039216])
    print(HSV_to_RGB(HSV))

    print('\n')

    print('1d array input:')
    print(HSV_to_RGB_vectorise(HSV))

    print('\n')

    print('2d array input:')
    HSV = np.tile(HSV, (6, 1))
    print(HSV_to_RGB_vectorise(HSV))

    print('\n')

    print('3d array input:')
    HSV = np.reshape(HSV, (2, 3, 3))
    print(HSV_to_RGB_vectorise(HSV))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(HSV_to_RGB_2d(DATA1)),
        np.ravel(HSV_to_RGB_vectorise(DATA1)))


# RGB_to_HSV_analysis()

# #############################################################################
# # ### colour.models.deprecated.RGB_to_HSL
# #############################################################################


def RGB_to_HSL_2d(RGB):
    HSL = []
    for i in range(len(RGB)):
        HSL.append(RGB_to_HSL(RGB[i]))
    return HSL


@handle_numpy_errors(divide='ignore', invalid='ignore')
def RGB_to_HSL_vectorise(RGB):
    minimum = np.amin(RGB, -1)
    maximum = np.amax(RGB, -1)
    delta = np.ptp(RGB, -1)

    R, G, B = zsplit(RGB)

    L = (maximum + minimum) / 2

    S = np.where(L < 0.5,
                 delta / (maximum + minimum),
                 delta / (2 - maximum - minimum))
    S[np.asarray(delta == 0)] = 0

    delta_R = (((maximum - R) / 6) + (delta / 2)) / delta
    delta_G = (((maximum - G) / 6) + (delta / 2)) / delta
    delta_B = (((maximum - B) / 6) + (delta / 2)) / delta

    H = delta_B - delta_G
    H = np.where(G == maximum, (1 / 3) + delta_R - delta_B, H)
    H = np.where(B == maximum, (2 / 3) + delta_G - delta_R, H)
    H[np.asarray(H < 0)] += 1
    H[np.asarray(H > 1)] -= 1
    H[np.asarray(delta == 0)] = 0

    HSL = zstack((H, S, L))

    return HSL


def RGB_to_HSL_analysis():
    message_box('RGB_to_HSL')

    print('Reference:')
    RGB = np.array([0.49019608, 0.98039216, 0.25098039])
    print(RGB_to_HSL(RGB))

    print('\n')

    print('1d array input:')
    print(RGB_to_HSL_vectorise(RGB))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_HSL_vectorise(RGB))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_HSL_vectorise(RGB))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(RGB_to_HSL_2d(DATA1)),
        np.ravel(RGB_to_HSL_vectorise(DATA1)))


# RGB_to_HSL_analysis()

# #############################################################################
# # ### colour.models.deprecated.HSL_to_RGB
# #############################################################################


def HSL_to_RGB_2d(HSL):
    RGB = []
    for i in range(len(HSL)):
        RGB.append(HSL_to_RGB(HSL[i]))
    return RGB


def HSL_to_RGB_vectorise(HSL):
    H, S, L = zsplit(HSL)

    def H_to_RGB(vi, vj, vH):
        """
        Converts *hue* value to *RGB* colourspace.
        """

        vH = np.asarray(vH)

        vH[np.asarray(vH < 0)] += 1
        vH[np.asarray(vH > 1)] -= 1

        v = np.full(vi.shape, np.nan)

        v = np.where(np.logical_and(6 * vH < 1, np.isnan(v)),
                     vi + (vj - vi) * 6 * vH,
                     v)
        v = np.where(np.logical_and(2 * vH < 1, np.isnan(v)),
                     vj,
                     v)
        v = np.where(np.logical_and(3 * vH < 2, np.isnan(v)),
                     vi + (vj - vi) * ((2 / 3) - vH) * 6,
                     v)
        v = np.where(np.isnan(v), vi, v)

        return v

    j = np.where(L < 0.5, L * (1 + S), (L + S) - (S * L))
    i = 2 * L - j

    R = H_to_RGB(i, j, H + (1 / 3))
    G = H_to_RGB(i, j, H)
    B = H_to_RGB(i, j, H - (1 / 3))

    R = np.where(S == 1, L, R)
    G = np.where(S == 1, L, G)
    B = np.where(S == 1, L, B)

    RGB = zstack((R, G, B))

    return RGB


def HSL_to_RGB_analysis():
    message_box('HSL_to_RGB')

    print('Reference:')
    HSL = np.array([0.27867383, 0.9489796, 0.61568627])
    print(HSL_to_RGB(HSL))

    print('\n')

    print('1d array input:')
    print(HSL_to_RGB_vectorise(HSL))

    print('\n')

    print('2d array input:')
    HSL = np.tile(HSL, (6, 1))
    print(HSL_to_RGB_vectorise(HSL))

    print('\n')

    print('3d array input:')
    HSL = np.reshape(HSL, (2, 3, 3))
    print(HSL_to_RGB_vectorise(HSL))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(HSL_to_RGB_2d(DATA1)),
        np.ravel(HSL_to_RGB_vectorise(DATA1)))


# HSL_to_RGB_analysis()

# #############################################################################
# # ### colour.models.deprecated.RGB_to_CMY
# #############################################################################


def RGB_to_CMY_2d(RGB):
    for i in range(len(RGB)):
        RGB_to_CMY(RGB[i])


def RGB_to_CMY_vectorise(RGB):
    CMY = 1 - np.asarray(RGB)

    return CMY


def RGB_to_CMY_analysis():
    message_box('RGB_to_CMY')

    print('Reference:')
    RGB = np.array([0.49019608, 0.98039216, 0.25098039])
    print(RGB_to_CMY(RGB))

    print('\n')

    print('1d array input:')
    print(RGB_to_CMY_vectorise(RGB))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_CMY_vectorise(RGB))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_CMY_vectorise(RGB))

    print('\n')


# RGB_to_CMY_analysis()

# #############################################################################
# # ### colour.models.deprecated.CMY_to_RGB
# #############################################################################


def CMY_to_RGB_2d(CMY):
    for i in range(len(CMY)):
        CMY_to_RGB(CMY[i])


def CMY_to_RGB_vectorise(CMY):
    RGB = 1 - np.asarray(CMY)

    return RGB


def CMY_to_RGB_analysis():
    message_box('CMY_to_RGB')

    print('Reference:')
    CMY = np.array([0.50980392, 0.01960784, 0.74901961])
    print(CMY_to_RGB(CMY))

    print('\n')

    print('1d array input:')
    print(CMY_to_RGB_vectorise(CMY))

    print('\n')

    print('2d array input:')
    CMY = np.tile(CMY, (6, 1))
    print(CMY_to_RGB_vectorise(CMY))

    print('\n')

    print('3d array input:')
    CMY = np.reshape(CMY, (2, 3, 3))
    print(CMY_to_RGB_vectorise(CMY))

    print('\n')


# CMY_to_RGB_analysis()

# #############################################################################
# # ### colour.models.deprecated.CMY_to_CMYK
# #############################################################################


def CMY_to_CMYK_2d(CMY):
    CMYK = []
    for i in range(len(CMY)):
        CMYK.append(CMY_to_CMYK(CMY[i]))
    return CMYK


def CMY_to_CMYK_vectorise(CMY):
    C, M, Y = zsplit(CMY)

    K = np.ones(C.shape)
    K = np.where(C < K, C, K)
    K = np.where(M < K, M, K)
    K = np.where(Y < K, Y, K)

    C = np.asarray((C - K) / (1 - K))
    M = np.asarray((M - K) / (1 - K))
    Y = np.asarray((Y - K) / (1 - K))

    C[np.asarray(K == 1)] = 0
    M[np.asarray(K == 1)] = 0
    Y[np.asarray(K == 1)] = 0

    CMYK = zstack((C, M, Y, K))

    return CMYK


def CMY_to_CMYK_analysis():
    message_box('CMY_to_CMYK')

    print('Reference:')
    CMY = np.array([0.49019608, 0.98039216, 0.25098039])
    print(CMY_to_CMYK(CMY))

    print('\n')

    print('1d array input:')
    print(CMY_to_CMYK_vectorise(CMY))

    print('\n')

    print('2d array input:')
    CMY = np.tile(CMY, (6, 1))
    print(CMY_to_CMYK_vectorise(CMY))

    print('\n')

    print('3d array input:')
    CMY = np.reshape(CMY, (2, 3, 3))
    print(CMY_to_CMYK_vectorise(CMY))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(CMY_to_CMYK_2d(DATA1)),
        np.ravel(CMY_to_CMYK_vectorise(DATA1)))


# CMY_to_CMYK_analysis()

# #############################################################################
# # ### colour.models.deprecated.CMYK_to_CMY
# #############################################################################


def CMYK_to_CMY_2d(CMYK):
    for i in range(len(CMYK)):
        CMYK_to_CMY(CMYK[i])


def CMYK_to_CMY_vectorise(CMYK):
    C, M, Y, K = zsplit(CMYK)

    CMY = zstack((C * (1 - K) + K,
                  M * (1 - K) + K,
                  Y * (1 - K) + K))

    return CMY


def CMYK_to_CMY_analysis():
    message_box('CMYK_to_CMY')

    print('Reference:')
    CMYK = np.array([0.31937173, 0.97382199, 0., 0.25098039])
    print(CMYK_to_CMY(CMYK))

    print('\n')

    print('1d array input:')
    print(CMYK_to_CMY_vectorise(CMYK))

    print('\n')

    print('2d array input:')
    CMYK = np.tile(CMYK, (6, 1))
    print(CMYK_to_CMY_vectorise(CMYK))

    print('\n')

    print('3d array input:')
    CMYK = np.reshape(CMYK, (2, 3, 4))
    print(CMYK_to_CMY_vectorise(CMYK))

    print('\n')


# CMYK_to_CMY_analysis()

# #############################################################################
# #############################################################################
# ## colour.models.derivation
# #############################################################################
# #############################################################################
# #############################################################################
# # ### colour.normalised_primary_matrix
# #############################################################################
from colour.models.derivation import *


def xy_to_z_vectorise(xy):
    x, y = zsplit(xy)

    z = 1 - x - y

    return z


def normalised_primary_matrix_vectorise(primaries, whitepoint):
    primaries = np.reshape(primaries, (3, 2))

    z = xy_to_z_vectorise(primaries)[..., np.newaxis]
    primaries = np.transpose(np.hstack((primaries, z)))

    whitepoint = xy_to_XYZ(whitepoint)

    coefficients = np.dot(np.linalg.inv(primaries), whitepoint)
    coefficients = np.diagflat(coefficients)

    npm = np.dot(primaries, coefficients)

    return npm


def normalised_primary_matrix_analysis():
    message_box('normalised_primary_matrix')

    print('Reference:')
    P = np.array([0.73470, 0.26530, 0.00000, 1.00000, 0.00010, -0.07700])
    W = (0.32168, 0.33767)
    print(normalised_primary_matrix(P, W))

    print('\n')

    print('Refactor:')
    print(normalised_primary_matrix_vectorise(P, W))

    print('\n')


# normalised_primary_matrix_analysis()

# #############################################################################
# # ### colour.primaries_whitepoint
# #############################################################################
def primaries_whitepoint_vectorise(npm):
    npm = npm.reshape((3, 3))

    primaries = XYZ_to_xy_vectorise(
        np.transpose(np.dot(npm, np.identity(3))))
    whitepoint = XYZ_to_xy_vectorise(
        np.transpose(np.dot(npm, np.ones((3, 1)))))

    # TODO: Should we return a tuple or stack the whitepoint chromaticity
    # coordinates to the primaries.
    return primaries, whitepoint


def primaries_whitepoint_analysis():
    message_box('primaries_whitepoint')

    print('Reference:')
    npm = np.array([[9.52552396e-01, 0.00000000e+00, 9.36786317e-05],
                    [3.43966450e-01, 7.28166097e-01, -7.21325464e-02],
                    [0.00000000e+00, 0.00000000e+00, 1.00882518e+00]])
    print(primaries_whitepoint(npm))

    print('\n')

    print('Refactor:')
    print(primaries_whitepoint_vectorise(npm))

    print('\n')


# primaries_whitepoint_analysis()

# #############################################################################
# # ### colour.RGB_luminance
# #############################################################################


def RGB_luminance_2d(RGB):
    for i in range(len(RGB)):
        RGB_luminance(RGB[i],
                      np.array([0.73470, 0.26530, 0.00000, 1.00000, 0.00010,
                                -0.07700]),
                      (0.32168, 0.33767))


def RGB_luminance_vectorise(RGB, primaries, whitepoint):
    R, G, B = zsplit(RGB)

    X, Y, Z = np.ravel(normalised_primary_matrix_vectorise(primaries,
                                                           whitepoint))[3:6]
    L = X * R + Y * G + Z * B

    return L


def RGB_luminance_analysis():
    message_box('RGB_luminance')

    print('Reference:')
    RGB = np.array([40.6, 4.2, 67.4])
    P = np.array([0.73470, 0.26530, 0.00000, 1.00000, 0.00010, -0.07700])
    W = (0.32168, 0.33767)
    print(RGB_luminance(RGB, P, W))

    print('\n')

    print('1d array input:')
    print(RGB_luminance_vectorise(RGB, P, W))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_luminance_vectorise(RGB, P, W))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_luminance_vectorise(RGB, P, W))

    print('\n')


# RGB_luminance_analysis()

# #############################################################################
# #############################################################################
# ### colour.models.ipt
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.XYZ_to_IPT
# #############################################################################
from colour.models.ipt import *


def XYZ_to_IPT_2d(XYZ):
    for i in range(len(XYZ)):
        XYZ_to_IPT(XYZ[i])


def XYZ_to_IPT_vectorise(XYZ):
    LMS = np.einsum('...ij,...j->...i', IPT_XYZ_TO_LMS_MATRIX, XYZ)
    LMS_prime = np.sign(LMS) * np.abs(LMS) ** 0.43
    IPT = np.einsum('...ij,...j->...i', IPT_LMS_TO_IPT_MATRIX, LMS_prime)

    return IPT


def XYZ_to_IPT_analysis():
    message_box('XYZ_to_IPT')

    print('Reference:')
    XYZ = np.array([0.96907232, 1, 1.12179215])
    print(XYZ_to_IPT(XYZ))

    print('\n')

    print('1d array input:')
    print(XYZ_to_IPT_vectorise(XYZ))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_IPT_vectorise(XYZ))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_IPT_vectorise(XYZ))

    print('\n')


# XYZ_to_IPT_analysis()

# #############################################################################
# #############################################################################
# ### colour.IPT_to_XYZ
# #############################################################################
# #############################################################################


def IPT_to_XYZ_2d(IPT):
    for i in range(len(IPT)):
        IPT_to_XYZ(IPT[i])


def IPT_to_XYZ_vectorise(IPT):
    LMS = np.einsum('...ij,...j->...i', IPT_IPT_TO_LMS_MATRIX, IPT)
    LMS_prime = np.sign(LMS) * np.abs(LMS) ** (1 / 0.43)
    XYZ = np.einsum('...ij,...j->...i', IPT_LMS_TO_XYZ_MATRIX, LMS_prime)

    return XYZ


def IPT_to_XYZ_analysis():
    message_box('IPT_to_XYZ')

    print('Reference:')
    IPT = np.array([1.00300825, 0.01906918, -0.01369292])
    print(IPT_to_XYZ(IPT))

    print('\n')

    print('1d array input:')
    print(IPT_to_XYZ_vectorise(IPT))

    print('\n')

    print('2d array input:')
    IPT = np.tile(IPT, (6, 1))
    print(IPT_to_XYZ_vectorise(IPT))

    print('\n')

    print('3d array input:')
    IPT = np.reshape(IPT, (2, 3, 3))
    print(IPT_to_XYZ_vectorise(IPT))

    print('\n')


# IPT_to_XYZ_analysis()

# #############################################################################
# ### colour.IPT_hue_angle
# #############################################################################


def IPT_hue_angle_2d(IPT):
    for i in range(len(IPT)):
        IPT_hue_angle(IPT[i])


def IPT_hue_angle_vectorise(IPT):
    I, P, T = zsplit(IPT)

    hue = np.arctan2(T, P)

    return hue


def IPT_hue_angle_analysis():
    message_box('IPT_hue_angle')

    print('Reference:')
    IPT = np.array([0.96907232, 1., 1.12179215])
    print(IPT_hue_angle(IPT))

    print('\n')

    print('1d array input:')
    print(IPT_hue_angle_vectorise(IPT))

    print('\n')

    print('2d array input:')
    IPT = np.tile(IPT, (6, 1))
    print(IPT_hue_angle_vectorise(IPT))

    print('\n')

    print('3d array input:')
    IPT = np.reshape(IPT, (2, 3, 3))
    print(IPT_hue_angle_vectorise(IPT))

    print('\n')


# IPT_hue_angle_analysis()

# #############################################################################
# #############################################################################
# ### colour.models.log
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.linear_to_cineon
# #############################################################################
from colour.models.log import *


DATA = np.linspace(0, 1, 1000000)


def linear_to_cineon_2d(value):
    for i in range(len(value)):
        linear_to_cineon(value[i])


def linear_to_cineon_vectorise(value,
                               black_offset=10 ** ((95 - 685) / 300),
                               **kwargs):
    value = np.asarray(value)

    return ((685 + 300 *
             np.log10(value * (1 - black_offset) + black_offset)) / 1023)


def linear_to_cineon_analysis():
    message_box('linear_to_cineon')

    print('Reference:')
    print(linear_to_cineon(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_cineon_vectorise(0.18))

    print('\n')

    print('0d array input:')
    print(linear_to_cineon_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_cineon_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_cineon_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_cineon_vectorise(linear))

    print('\n')


# linear_to_cineon_analysis()

# #############################################################################
# ### colour.cineon_to_linear
# #############################################################################


def cineon_to_linear_2d(value):
    for i in range(len(value)):
        cineon_to_linear(value[i])


def cineon_to_linear_vectorise(value,
                               black_offset=10 ** ((95 - 685) / 300),
                               **kwargs):
    value = np.asarray(value)

    return ((10 ** ((1023 * value - 685) / 300) - black_offset) /
            (1 - black_offset))


def cineon_to_linear_analysis():
    message_box('cineon_to_linear')

    print('Reference:')
    print(cineon_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(cineon_to_linear_vectorise(0.5))

    print('\n')

    print('0d array input:')
    print(cineon_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(cineon_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(cineon_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(cineon_to_linear_vectorise(log))

    print('\n')


# cineon_to_linear_analysis()

# #############################################################################
# ### colour.linear_to_panalog
# #############################################################################


def linear_to_panalog_2d(value):
    for i in range(len(value)):
        linear_to_panalog(value[i])


def linear_to_panalog_vectorise(value,
                                black_offset=10 ** ((64 - 681) / 444),
                                **kwargs):
    value = np.asarray(value)

    return ((681 + 444 *
             np.log10(value * (1 - black_offset) + black_offset)) / 1023)


def linear_to_panalog_analysis():
    message_box('linear_to_panalog')

    print('Reference:')
    print(linear_to_panalog(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_panalog_vectorise(0.18))

    print('\n')

    print('0d array input:')
    print(linear_to_panalog_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_panalog_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_panalog_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_panalog_vectorise(linear))

    print('\n')


# linear_to_panalog_analysis()

# #############################################################################
# ### colour.panalog_to_linear
# #############################################################################


def panalog_to_linear_2d(value):
    for i in range(len(value)):
        panalog_to_linear(value[i])


def panalog_to_linear_vectorise(value,
                                black_offset=10 ** ((64 - 681) / 444),
                                **kwargs):
    value = np.asarray(value)

    return ((10 ** ((1023 * value - 681) / 444) - black_offset) /
            (1 - black_offset))


def panalog_to_linear_analysis():
    message_box('panalog_to_linear')

    print('Reference:')
    print(panalog_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(panalog_to_linear_vectorise(0.5))

    print('\n')

    print('0d array input:')
    print(panalog_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(panalog_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(panalog_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(panalog_to_linear_vectorise(log))

    print('\n')


# panalog_to_linear_analysis()

# #############################################################################
# ### colour.linear_to_red_log
# #############################################################################


def linear_to_red_log_2d(value):
    for i in range(len(value)):
        linear_to_red_log(value[i])


def linear_to_red_log_vectorise(value,
                                black_offset=10 ** ((0 - 1023) / 511),
                                **kwargs):
    value = np.asarray(value)

    return ((1023 +
             511 * np.log10(value * (1 - black_offset) + black_offset)) / 1023)


def linear_to_red_log_analysis():
    message_box('linear_to_red_log')

    print('Reference:')
    print(linear_to_red_log(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_red_log_vectorise(0.18))

    print('\n')

    print('0d array input:')
    print(linear_to_red_log_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_red_log_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_red_log_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_red_log_vectorise(linear))

    print('\n')


# linear_to_red_log_analysis()

# #############################################################################
# ### colour.red_log_to_linear
# #############################################################################


def red_log_to_linear_2d(value):
    for i in range(len(value)):
        red_log_to_linear(value[i])


def red_log_to_linear_vectorise(value,
                                black_offset=10 ** ((0 - 1023) / 511),
                                **kwargs):
    value = np.asarray(value)

    return (((10 **
              ((1023 * value - 1023) / 511)) - black_offset) /
            (1 - black_offset))


def red_log_to_linear_analysis():
    message_box('red_log_to_linear')

    print('Reference:')
    print(red_log_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(red_log_to_linear_vectorise(0.5))

    print('\n')

    print('1d array input:')
    print(red_log_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(red_log_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(red_log_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(red_log_to_linear_vectorise(log))

    print('\n')


# red_log_to_linear_analysis()

# #############################################################################
# ### colour.linear_to_viper_log
# #############################################################################


def linear_to_viper_log_2d(value):
    for i in range(len(value)):
        linear_to_viper_log(value[i])


def linear_to_viper_log_vectorise(value, **kwargs):
    value = np.asarray(value)

    return (1023 + 500 * np.log10(value)) / 1023


def linear_to_viper_log_analysis():
    message_box('linear_to_viper_log')

    print('Reference:')
    print(linear_to_viper_log(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_viper_log_vectorise(0.18))

    print('\n')

    print('1d array input:')
    print(linear_to_viper_log_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_viper_log_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_viper_log_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_viper_log_vectorise(linear))

    print('\n')


# linear_to_viper_log_analysis()

# #############################################################################
# ### colour.viper_log_to_linear
# #############################################################################


def viper_log_to_linear_2d(value):
    for i in range(len(value)):
        viper_log_to_linear(value[i])


def viper_log_to_linear_vectorise(value, **kwargs):
    value = np.asarray(value)

    return 10 ** ((1023 * value - 1023) / 500)


def viper_log_to_linear_analysis():
    message_box('viper_log_to_linear')

    print('Reference:')
    print(viper_log_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(viper_log_to_linear_vectorise(0.5))

    print('\n')

    print('0d array input:')
    print(viper_log_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(viper_log_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(viper_log_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(viper_log_to_linear_vectorise(log))

    print('\n')


# viper_log_to_linear_analysis()

# #############################################################################
# ### colour.linear_to_pivoted_log
# #############################################################################


def linear_to_pivoted_log_2d(value):
    for i in range(len(value)):
        linear_to_pivoted_log(value[i])


def linear_to_pivoted_log_vectorise(value,
                                    log_reference=445,
                                    linear_reference=0.18,
                                    negative_gamma=0.6,
                                    density_per_code_value=0.002):
    value = np.asarray(value)

    return ((log_reference + np.log10(value / linear_reference) /
             (density_per_code_value / negative_gamma)) / 1023)


def linear_to_pivoted_log_analysis():
    message_box('linear_to_pivoted_log')

    print('Reference:')
    print(linear_to_pivoted_log(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_pivoted_log_vectorise(0.18))

    print('\n')

    print('0d array input:')
    print(linear_to_pivoted_log_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_pivoted_log_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_pivoted_log_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_pivoted_log_vectorise(linear))

    print('\n')


# linear_to_pivoted_log_analysis()

# #############################################################################
# ### colour.pivoted_log_to_linear
# #############################################################################


def pivoted_log_to_linear_2d(value):
    for i in range(len(value)):
        pivoted_log_to_linear(value[i])


def pivoted_log_to_linear_vectorise(value,
                                    log_reference=445,
                                    linear_reference=0.18,
                                    negative_gamma=0.6,
                                    density_per_code_value=0.002):
    value = np.asarray(value)

    return (10 ** ((value * 1023 - log_reference) *
                   (density_per_code_value / negative_gamma)) *
            linear_reference)


def pivoted_log_to_linear_analysis():
    message_box('pivoted_log_to_linear')

    print('Reference:')
    print(pivoted_log_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(pivoted_log_to_linear_vectorise(0.5))

    print('\n')

    print('0d array input:')
    print(pivoted_log_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(pivoted_log_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(pivoted_log_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(pivoted_log_to_linear_vectorise(log))

    print('\n')


# pivoted_log_to_linear_analysis()

# #############################################################################
# ### colour.linear_to_c_log
# #############################################################################


def linear_to_c_log_2d(value):
    for i in range(len(value)):
        linear_to_c_log(value[i])


def linear_to_c_log_vectorise(value, **kwargs):
    value = np.asarray(value)

    return 0.529136 * np.log10(10.1596 * value + 1) + 0.0730597


def linear_to_c_log_analysis():
    message_box('linear_to_c_log')

    print('Reference:')
    print(linear_to_c_log(0.18))

    print('\n')

    print('Numeric input:')
    print(linear_to_c_log_vectorise(0.18))

    print('\n')

    print('0d array input:')
    print(linear_to_c_log_vectorise(np.array(0.18)))

    print('\n')

    print('1d array input:')
    linear = [0.18] * 6
    print(linear_to_c_log_vectorise(linear))

    print('\n')

    print('2d array input:')
    linear = np.reshape(linear, (2, 3))
    print(linear_to_c_log_vectorise(linear))

    print('\n')

    print('3d array input:')
    linear = np.reshape(linear, (2, 3, 1))
    print(linear_to_c_log_vectorise(linear))

    print('\n')


# linear_to_c_log_analysis()

# #############################################################################
# ### colour.c_log_to_linear
# #############################################################################


def c_log_to_linear_2d(value):
    for i in range(len(value)):
        c_log_to_linear(value[i])


def c_log_to_linear_vectorise(value, **kwargs):
    value = np.asarray(value)

    return (-0.071622555735168 *
            (1.3742747797867 - np.exp(1) ** (4.3515940948906 * value)))


def c_log_to_linear_analysis():
    message_box('c_log_to_linear')

    print('Reference:')
    print(c_log_to_linear(0.5))

    print('\n')

    print('Numeric input:')
    print(c_log_to_linear_vectorise(0.5))

    print('\n')

    print('0d array input:')
    print(c_log_to_linear_vectorise(np.array(0.5)))

    print('\n')

    print('1d array input:')
    log = [0.5] * 6
    print(c_log_to_linear_vectorise(log))

    print('\n')

    print('2d array input:')
    log = np.reshape(log, (2, 3))
    print(c_log_to_linear_vectorise(log))

    print('\n')

    print('3d array input:')
    log = np.reshape(log, (2, 3, 1))
    print(c_log_to_linear_vectorise(log))

    print('\n')


# c_log_to_linear_analysis()

# #############################################################################
# #############################################################################
# ### colour.models.rgb
# #############################################################################
# #############################################################################

# #############################################################################
# ### OECF / OECF_i
# #############################################################################
from colour.models.dataset.aces import (
    _aces_cc_transfer_function,
    _aces_cc_inverse_transfer_function)
from colour.models.dataset.aces import *


RGB = np.array([0.86969452, 1.00516431, 1.41715848])
RGB_t = np.tile(RGB, (6, 1)).reshape(2, 3, 3)


def _aces_cc_transfer_function_vectorise(value):
    value = np.asarray(value)

    output = np.where(value < 0,
                      (np.log2(2 ** -15 * 0.5) + 9.72) / 17.52,
                      (np.log2(2 ** -16 + value * 0.5) + 9.72) / 17.52)
    output = np.where(value >= 2 ** -15,
                      (np.log2(value) + 9.72) / 17.52,
                      output)

    return output


def _aces_cc_transfer_function_analysis():
    message_box('_aces_cc_transfer_function')

    print(_aces_cc_transfer_function(RGB[0]))

    print(_aces_cc_transfer_function_vectorise(RGB[0]))

    print(_aces_cc_transfer_function_vectorise(RGB))

    print(_aces_cc_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_aces_cc_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_aces_cc_transfer_function_vectorise(DATA1)))


# _aces_cc_transfer_function_analysis()


def _aces_cc_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    output = np.where(value < (9.72 - 15) / 17.52,
                      (2 ** (value * 17.52 - 9.72) - 2 ** -16) * 2,
                      2 ** (value * 17.52 - 9.72))
    output = np.where(value >= (np.log2(65504) + 9.72) / 17.52,
                      65504,
                      output)

    return output


def _aces_cc_inverse_transfer_function_analysis():
    message_box('_aces_cc_inverse_transfer_function')

    print(_aces_cc_inverse_transfer_function(RGB[0]))

    print(_aces_cc_inverse_transfer_function_vectorise(RGB[0]))

    print(_aces_cc_inverse_transfer_function_vectorise(RGB))

    print(_aces_cc_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_aces_cc_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_aces_cc_inverse_transfer_function_vectorise(DATA1)))


# _aces_cc_inverse_transfer_function_analysis()

from colour.models.dataset.aces import (
    _aces_proxy_transfer_function,
    _aces_proxy_inverse_transfer_function)


def _aces_proxy_transfer_function_vectorise(value, bit_depth='10 Bit'):
    value = np.asarray(value)

    constants = ACES_PROXY_CONSTANTS.get(bit_depth)

    CV_min = np.resize(constants.CV_min, value.shape)
    CV_max = np.resize(constants.CV_max, value.shape)

    float_2_cv = lambda x: np.maximum(CV_min, np.minimum(CV_max, np.round(x)))

    output = np.where(value > 2 ** -9.72,
                      float_2_cv((np.log2(value) + constants.mid_log_offset) *
                                 constants.steps_per_stop + constants.mid_CV_offset),
                      np.resize(CV_min, value.shape))
    return output


def _aces_proxy_transfer_function_analysis():
    message_box('_aces_proxy_transfer_function')

    print(_aces_proxy_transfer_function(RGB[0]))

    print(_aces_proxy_transfer_function_vectorise(RGB[0]))

    print(_aces_proxy_transfer_function_vectorise(RGB))

    print(_aces_proxy_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_aces_proxy_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_aces_proxy_transfer_function_vectorise(DATA1)))


# _aces_proxy_transfer_function_analysis()


def _aces_proxy_inverse_transfer_function_vectorise(value, bit_depth='10 Bit'):
    value = np.asarray(value)

    constants = ACES_PROXY_CONSTANTS.get(bit_depth)

    return (2 ** (((value - constants.mid_CV_offset) /
                   constants.steps_per_stop - constants.mid_log_offset)))


def _aces_proxy_inverse_transfer_function_analysis():
    message_box('_aces_proxy_inverse_transfer_function')

    print(_aces_proxy_inverse_transfer_function(RGB[0]))

    print(_aces_proxy_inverse_transfer_function_vectorise(RGB[0]))

    print(_aces_proxy_inverse_transfer_function_vectorise(RGB))

    print(_aces_proxy_inverse_transfer_function_vectorise(RGB_t))

    print('\t')


# _aces_proxy_inverse_transfer_function_analysis()

from colour.models.dataset.adobe_rgb_1998 import (
    _adobe_rgb_1998_transfer_function,
    _adobe_rgb_1998_inverse_transfer_function)
from colour.models.dataset.adobe_rgb_1998 import *


def _adobe_rgb_1998_transfer_function_vectorise(value):
    # Also valid for:
    # _adobe_wide_gamut_rgb_transfer_function
    value = np.asarray(value)

    return value ** (1 / (563 / 256))


def _adobe_rgb_1998_transfer_function_analysis():
    message_box('_adobe_rgb_1998_transfer_function')

    print(_adobe_rgb_1998_transfer_function(RGB[0]))

    print(_adobe_rgb_1998_transfer_function_vectorise(RGB[0]))

    print(_adobe_rgb_1998_transfer_function_vectorise(RGB))

    print(_adobe_rgb_1998_transfer_function_vectorise(RGB_t))

    print('\t')


# _adobe_rgb_1998_transfer_function_analysis()


def _adobe_rgb_1998_inverse_transfer_function_vectorise(value):
    # Also valid for:
    # _adobe_wide_gamut_rgb_inverse_transfer_function
    value = np.asarray(value)

    return value ** (563 / 256)


def _adobe_rgb_1998_inverse_transfer_function_analysis():
    message_box('_adobe_rgb_1998_inverse_transfer_function')

    print(_adobe_rgb_1998_inverse_transfer_function(RGB[0]))

    print(_adobe_rgb_1998_inverse_transfer_function_vectorise(RGB[0]))

    print(_adobe_rgb_1998_inverse_transfer_function_vectorise(RGB))

    print(_adobe_rgb_1998_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _adobe_rgb_1998_inverse_transfer_function_analysis()

from colour.models.dataset.alexa_wide_gamut_rgb import (
    _alexa_wide_gamut_rgb_transfer_function,
    _alexa_wide_gamut_rgb_inverse_transfer_function)
from colour.models.dataset.alexa_wide_gamut_rgb import *


def _alexa_wide_gamut_rgb_transfer_function_vectorise(
        value,
        firmware='SUP 3.x',
        method='Linear Scene Exposure Factor',
        EI=800):
    value = np.asarray(value)

    cut, a, b, c, d, e, f, _ = ALEXA_LOG_C_CURVE_CONVERSION_DATA.get(
        firmware).get(method).get(EI)

    return np.where(value > cut,
                    c * np.log10(a * value + b) + d,
                    e * value + f)


def _alexa_wide_gamut_rgb_transfer_function_analysis():
    message_box('_alexa_wide_gamut_rgb_transfer_function')

    print(_alexa_wide_gamut_rgb_transfer_function(RGB[0]))

    print(_alexa_wide_gamut_rgb_transfer_function_vectorise(RGB[0]))

    print(_alexa_wide_gamut_rgb_transfer_function_vectorise(RGB))

    print(_alexa_wide_gamut_rgb_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_alexa_wide_gamut_rgb_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_alexa_wide_gamut_rgb_transfer_function_vectorise(DATA1)))


# _alexa_wide_gamut_rgb_transfer_function_analysis()


def _alexa_wide_gamut_rgb_inverse_transfer_function_vectorise(
        value,
        firmware='SUP 3.x',
        method='Linear Scene Exposure Factor',
        EI=800):
    value = np.asarray(value)

    cut, a, b, c, d, e, f, _ = (
        ALEXA_LOG_C_CURVE_CONVERSION_DATA.get(firmware).get(method).get(EI))

    return np.where(value > e * cut + f,
                    (np.power(10., (value - d) / c) - b) / a,
                    (value - f) / e)


def _alexa_wide_gamut_rgb_inverse_transfer_function_analysis():
    message_box('_alexa_wide_gamut_rgb_inverse_transfer_function')

    print(_alexa_wide_gamut_rgb_inverse_transfer_function(RGB[0]))

    print(_alexa_wide_gamut_rgb_inverse_transfer_function_vectorise(RGB[0]))

    print(_alexa_wide_gamut_rgb_inverse_transfer_function_vectorise(RGB))

    print(_alexa_wide_gamut_rgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_alexa_wide_gamut_rgb_inverse_transfer_function(x) for x in
         np.ravel(DATA1)],
        np.ravel(
            _alexa_wide_gamut_rgb_inverse_transfer_function_vectorise(DATA1)))


# _alexa_wide_gamut_rgb_inverse_transfer_function_analysis()

from colour.models.dataset.apple_rgb import (
    _apple_rgb_transfer_function,
    _apple_rgb_inverse_transfer_function)
from colour.models.dataset.apple_rgb import *


def _apple_rgb_transfer_function_vectorise(value):
    # Also valid for:
    # _color_match_rgb_transfer_function
    value = np.asarray(value)

    return value ** (1 / 1.8)


def _apple_rgb_transfer_function_function_analysis():
    message_box('_apple_rgb_transfer_function')

    print(_apple_rgb_transfer_function(RGB[0]))

    print(_apple_rgb_transfer_function_vectorise(RGB[0]))

    print(_apple_rgb_transfer_function_vectorise(RGB))

    print(_apple_rgb_transfer_function_vectorise(RGB_t))

    print('\n')


# _apple_rgb_transfer_function_function_analysis()


def _apple_rgb_inverse_transfer_function_vectorise(value):
    # Also valid for:
    # _color_match_rgb_inverse_transfer_function
    value = np.asarray(value)

    return value ** 1.8


def _apple_rgb_inverse_transfer_function_analysis():
    message_box('_apple_rgb_inverse_transfer_function')

    print(_apple_rgb_inverse_transfer_function(RGB[0]))

    print(_apple_rgb_inverse_transfer_function_vectorise(RGB[0]))

    print(_apple_rgb_inverse_transfer_function_vectorise(RGB))

    print(_apple_rgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _apple_rgb_inverse_transfer_function_analysis()

from colour.models.dataset.best_rgb import (
    _best_rgb_transfer_function,
    _best_rgb_inverse_transfer_function)
from colour.models.dataset.best_rgb import *


def _best_rgb_transfer_function_vectorise(value):
    # Also valid for:
    # _beta_rgb_transfer_function
    # _cie_rgb_transfer_function
    # _don_rgb_4_transfer_function
    # _ekta_space_ps_5_transfer_function
    # _max_rgb_transfer_function
    # _ntsc_rgb_transfer_function
    # _russell_rgb_transfer_function
    # _smpte_c_rgb_transfer_function
    # _xtreme_rgb_transfer_function
    value = np.asarray(value)

    return value ** (1 / 2.2)


def _best_rgb_transfer_function_analysis():
    message_box('_best_rgb_transfer_function')

    print(_best_rgb_transfer_function(RGB[0]))

    print(_best_rgb_transfer_function_vectorise(RGB[0]))

    print(_best_rgb_transfer_function_vectorise(RGB))

    print(_best_rgb_transfer_function_vectorise(RGB_t))

    print('\n')


# _best_rgb_transfer_function_analysis()


def _best_rgb_inverse_transfer_function_vectorise(value):
    # Also valid for:
    # _beta_rgb_inverse_transfer_function
    # _cie_rgb_inverse_transfer_function
    # _don_rgb_4_inverse_transfer_function
    # _ekta_space_ps_5_inverse_transfer_function
    # _max_rgb_inverse_transfer_function
    # _ntsc_rgb_inverse_transfer_function
    # _russell_rgb_inverse_transfer_function
    # _smpte_c_rgb_inverse_transfer_function
    # _xtreme_rgb_inverse_transfer_function
    value = np.asarray(value)

    return value ** 2.2


def _best_rgb_inverse_transfer_function_analysis():
    message_box('_best_rgb_inverse_transfer_function')

    print(_best_rgb_inverse_transfer_function(RGB[0]))

    print(_best_rgb_inverse_transfer_function_vectorise(RGB[0]))

    print(_best_rgb_inverse_transfer_function_vectorise(RGB))

    print(_best_rgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _best_rgb_inverse_transfer_function_analysis()

from colour.models.dataset.dci_p3 import (
    _dci_p3_transfer_function,
    _dci_p3_inverse_transfer_function)
from colour.models.dataset.dci_p3 import *


def _dci_p3_transfer_function_vectorise(value):
    value = np.asarray(value)

    return 4095 * (value / 52.37) ** (1 / 2.6)


def _dci_p3_transfer_function_analysis():
    message_box('_dci_p3_transfer_function')

    print(_dci_p3_transfer_function(RGB[0]))

    print(_dci_p3_transfer_function_vectorise(RGB[0]))

    print(_dci_p3_transfer_function_vectorise(RGB))

    print(_dci_p3_transfer_function_vectorise(RGB_t))

    print('\n')


# _dci_p3_transfer_function_analysis()


def _dci_p3_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return 52.37 * (value / 4095) ** 2.6


def _dci_p3_inverse_transfer_function_analysis():
    message_box('_dci_p3_inverse_transfer_function')

    print(_dci_p3_inverse_transfer_function(RGB[0]))

    print(_dci_p3_inverse_transfer_function_vectorise(RGB[0]))

    print(_dci_p3_inverse_transfer_function_vectorise(RGB))

    print(_dci_p3_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _dci_p3_inverse_transfer_function_analysis()

from colour.models.dataset.pal_secam_rgb import (
    _pal_secam_rgb_transfer_function,
    _pal_secam_rgb_inverse_transfer_function)
from colour.models.dataset.pal_secam_rgb import *


def _pal_secam_rgb_transfer_function_vectorise(value):
    value = np.asarray(value)

    return value ** (1 / 2.8)


def _pal_secam_rgb_transfer_function_analysis():
    message_box('_pal_secam_rgb_transfer_function')

    print(_pal_secam_rgb_transfer_function(RGB[0]))

    print(_pal_secam_rgb_transfer_function_vectorise(RGB[0]))

    print(_pal_secam_rgb_transfer_function_vectorise(RGB))

    print(_pal_secam_rgb_transfer_function_vectorise(RGB_t))

    print('\n')


# _pal_secam_rgb_transfer_function_analysis()


def _pal_secam_rgb_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return value ** 2.8


def _pal_secam_rgb_inverse_transfer_function_analysis():
    message_box('_pal_secam_rgb_inverse_transfer_function')

    print(_pal_secam_rgb_inverse_transfer_function(RGB[0]))

    print(_pal_secam_rgb_inverse_transfer_function_vectorise(RGB[0]))

    print(_pal_secam_rgb_inverse_transfer_function_vectorise(RGB))

    print(_pal_secam_rgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _pal_secam_rgb_inverse_transfer_function_analysis()

from colour.models.dataset.prophoto_rgb import (
    _prophoto_rgb_transfer_function,
    _prophoto_rgb_inverse_transfer_function)
from colour.models.dataset.prophoto_rgb import *


def _prophoto_rgb_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value < 0.001953,
                    value * 16,
                    value ** (1 / 1.8))


def _prophoto_rgb_transfer_function_analysis():
    message_box('_prophoto_rgb_transfer_function')

    print(_prophoto_rgb_transfer_function_vectorise(RGB))

    print(_prophoto_rgb_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_prophoto_rgb_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_prophoto_rgb_transfer_function_vectorise(DATA1)))


# _prophoto_rgb_transfer_function_analysis()


def _prophoto_rgb_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(
        value < _prophoto_rgb_transfer_function_vectorise(0.001953),
        value / 16,
        value ** 1.8)


def _prophoto_rgb_inverse_transfer_function_analysis():
    message_box('_prophoto_rgb_inverse_transfer_function')

    print(_prophoto_rgb_inverse_transfer_function_vectorise(RGB))

    print(_prophoto_rgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_prophoto_rgb_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_prophoto_rgb_inverse_transfer_function_vectorise(DATA1)))


# _prophoto_rgb_inverse_transfer_function_analysis()

from colour.models.dataset.rec_709 import (
    _rec_709_transfer_function,
    _rec_709_inverse_transfer_function)
from colour.models.dataset.rec_709 import *


def _rec_709_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value < 0.018,
                    value * 4.5,
                    1.099 * (value ** 0.45) - 0.099)


def _rec_709_transfer_function_analysis():
    message_box('_rec_709_transfer_function')

    print(_rec_709_transfer_function_vectorise(RGB))

    print(_rec_709_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_rec_709_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_rec_709_transfer_function_vectorise(DATA1)))


# _rec_709_transfer_function_analysis()


def _rec_709_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value < _rec_709_transfer_function_vectorise(0.018),
                    value / 4.5,
                    ((value + 0.099) / 1.099) ** (1 / 0.45))


def _rec_709_inverse_transfer_function_analysis():
    message_box('_rec_709_inverse_transfer_function')

    print(_rec_709_inverse_transfer_function_vectorise(RGB))

    print(_rec_709_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_rec_709_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_rec_709_inverse_transfer_function_vectorise(DATA1)))


# _rec_709_inverse_transfer_function_analysis()

from colour.models.dataset.rec_2020 import (
    _rec_2020_transfer_function,
    _rec_2020_inverse_transfer_function)
from colour.models.dataset.rec_2020 import *


def _rec_2020_transfer_function_vectorise(value, is_10_bits_system=True):
    value = np.asarray(value)

    a = REC_2020_CONSTANTS.alpha(is_10_bits_system)
    b = REC_2020_CONSTANTS.beta(is_10_bits_system)
    return np.where(value < b,
                    value * 4.5,
                    a * (value ** 0.45) - (a - 1))


def _rec_2020_transfer_function_analysis():
    message_box('_rec_2020_transfer_function')

    print(_rec_2020_transfer_function_vectorise(RGB))

    print(_rec_2020_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_rec_2020_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_rec_2020_transfer_function_vectorise(DATA1)))


# _rec_2020_transfer_function_analysis()


def _rec_2020_inverse_transfer_function_vectorise(value,
                                                  is_10_bits_system=True):
    value = np.asarray(value)

    a = REC_2020_CONSTANTS.alpha(is_10_bits_system)
    b = REC_2020_CONSTANTS.beta(is_10_bits_system)
    return np.where(value < _rec_2020_transfer_function_vectorise(b),
                    value / 4.5,
                    ((value + (a - 1)) / a) ** (1 / 0.45))


def _rec_2020_inverse_transfer_function_analysis():
    message_box('_rec_2020_inverse_transfer_function')

    print(_rec_2020_inverse_transfer_function_vectorise(RGB))

    print(_rec_2020_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_rec_2020_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_rec_2020_inverse_transfer_function_vectorise(DATA1)))


# _rec_2020_inverse_transfer_function_analysis()

from colour.models.dataset.s_gamut import (
    _s_log_transfer_function,
    _s_log_inverse_transfer_function,
    _s_log2_transfer_function,
    _s_log2_inverse_transfer_function,
    _s_log3_transfer_function,
    _s_log3_inverse_transfer_function)
from colour.models.dataset.s_gamut import *


def _s_log_transfer_function_vectorise(value):
    value = np.asarray(value)

    return (0.432699 * np.log10(value + 0.037584) + 0.616596) + 0.03


def _s_log_transfer_function_analysis():
    message_box('_s_log_transfer_function')

    print(_s_log_transfer_function(RGB[0]))

    print(_s_log_transfer_function_vectorise(RGB[0]))

    print(_s_log_transfer_function_vectorise(RGB))

    print(_s_log_transfer_function_vectorise(RGB_t))

    print('\n')


# _s_log_transfer_function_analysis()


def _s_log_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return 10 ** (((value - 0.616596 - 0.03) / 0.432699)) - 0.037584


def _s_log_inverse_transfer_function_analysis():
    message_box('_s_log_inverse_transfer_function')

    print(_s_log_inverse_transfer_function(RGB[0]))

    print(_s_log_inverse_transfer_function_vectorise(RGB[0]))

    print(_s_log_inverse_transfer_function_vectorise(RGB))

    print(_s_log_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _s_log_inverse_transfer_function_analysis()


def _s_log2_transfer_function_vectorise(value):
    value = np.asarray(value)

    return ((4 * (16 + 219 *
                  (0.616596 + 0.03 + 0.432699 *
                   (np.log10(0.037584 + value / 0.9))))) / 1023)


def _s_log2_transfer_function_analysis():
    message_box('_s_log2_transfer_function')

    print(_s_log2_transfer_function(RGB[0]))

    print(_s_log2_transfer_function_vectorise(RGB[0]))

    print(_s_log2_transfer_function_vectorise(RGB))

    print(_s_log2_transfer_function_vectorise(RGB_t))

    print('\n')


# _s_log2_transfer_function_analysis()


def _s_log2_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return ((10 ** (((((value * 1023 / 4 - 16) / 219) - 0.616596 - 0.03) /
                     0.432699)) - 0.037584) * 0.9)


def _s_log2_inverse_transfer_function_analysis():
    message_box('_s_log2_inverse_transfer_function')

    print(_s_log2_inverse_transfer_function(RGB[0]))

    print(_s_log2_inverse_transfer_function_vectorise(RGB[0]))

    print(_s_log2_inverse_transfer_function_vectorise(RGB))

    print(_s_log2_inverse_transfer_function_vectorise(RGB_t))

    print('\n')


# _s_log2_inverse_transfer_function_analysis()


def _s_log3_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value >= 0.01125000,
                    (420 + np.log10((value + 0.01) /
                                    (0.18 + 0.01)) * 261.5) / 1023,
                    (value * (171.2102946929 - 95) / 0.01125000 + 95) / 1023)


def _s_log3_transfer_function_analysis():
    message_box('_s_log3_transfer_function')

    print(_s_log3_transfer_function(RGB[0]))

    print(_s_log3_transfer_function_vectorise(RGB[0]))

    print(_s_log3_transfer_function_vectorise(RGB))

    print(_s_log3_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_s_log3_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_s_log3_transfer_function_vectorise(DATA1)))


# _s_log3_transfer_function_analysis()


def _s_log3_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value >= 171.2102946929 / 1023,
                    ((10 ** ((value * 1023 - 420) / 261.5)) *
                     (0.18 + 0.01) - 0.01),
                    (value * 1023 - 95) * 0.01125000 / (171.2102946929 - 95))


def _s_log3_inverse_transfer_function_analysis():
    message_box('_s_log3_inverse_transfer_function')

    print(_s_log3_inverse_transfer_function(RGB[0]))

    print(_s_log3_inverse_transfer_function_vectorise(RGB[0]))

    print(_s_log3_inverse_transfer_function_vectorise(RGB))

    print(_s_log3_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_s_log3_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_s_log3_inverse_transfer_function_vectorise(DATA1)))


# _s_log3_inverse_transfer_function_analysis()

from colour.models.dataset.srgb import (
    _srgb_transfer_function,
    _srgb_inverse_transfer_function)
from colour.models.dataset.srgb import *


def _srgb_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value <= 0.0031308,
                    value * 12.92,
                    1.055 * (value ** (1 / 2.4)) - 0.055)


def _srgb_transfer_function_analysis():
    message_box('_srgb_transfer_function')

    print(_srgb_transfer_function_vectorise(RGB))

    print(_srgb_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_srgb_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_srgb_transfer_function_vectorise(DATA1)))


# _srgb_transfer_function_analysis()


def _srgb_inverse_transfer_function_vectorise(value):
    value = np.asarray(value)

    return np.where(value <= _srgb_transfer_function_vectorise(0.0031308),
                    value / 12.92,
                    ((value + 0.055) / 1.055) ** 2.4)


def _srgb_inverse_transfer_function_analysis():
    message_box('_srgb_inverse_transfer_function')

    print(_srgb_inverse_transfer_function_vectorise(RGB))

    print(_srgb_inverse_transfer_function_vectorise(RGB_t))

    print('\n')

    np.testing.assert_almost_equal(
        [_srgb_inverse_transfer_function(x) for x in np.ravel(DATA1)],
        np.ravel(_srgb_inverse_transfer_function_vectorise(DATA1)))


# _srgb_inverse_transfer_function_analysis()

# #############################################################################
# ### colour.XYZ_to_RGB
# #############################################################################
from colour.models.rgb import *

W_R = (0.34567, 0.35850)
W_T = (0.31271, 0.32902)
CAT = 'Bradford'
M = np.array([
    [3.24100326, -1.53739899, -0.49861587],
    [-0.96922426, 1.87592999, 0.04155422],
    [0.05563942, -0.2040112, 1.05714897]])


def XYZ_to_RGB_2d(XYZ):
    for i in range(len(XYZ)):
        XYZ_to_RGB(XYZ[i], W_R, W_T, M, CAT)


def XYZ_to_RGB_vectorise(XYZ,
                         illuminant_XYZ,
                         illuminant_RGB,
                         XYZ_to_RGB_matrix,
                         chromatic_adaptation_transform='CAT02',
                         transfer_function=None):
    M = chromatic_adaptation_matrix_VonKries_vectorise(
        xy_to_XYZ_vectorise(illuminant_XYZ),
        xy_to_XYZ_vectorise(illuminant_RGB),
        transform=chromatic_adaptation_transform)

    XYZ_a = np.einsum('...ij,...j->...i', M, XYZ)

    RGB = np.einsum('...ij,...j->...i', XYZ_to_RGB_matrix, XYZ_a)

    if transfer_function is not None:
        RGB = transfer_function(RGB)

    return RGB


def XYZ_to_RGB_analysis():
    message_box('XYZ_to_RGB')

    print('Reference:')
    XYZ = np.array([0.07049534, 0.1008, 0.09558313])

    print(XYZ_to_RGB(XYZ, W_R, W_T, M, CAT))

    print('\n')

    print('1d array input:')
    print(XYZ_to_RGB_vectorise(XYZ, W_R, W_T, M, CAT))

    print('\n')

    print('2d array input:')
    XYZ = np.tile(XYZ, (6, 1))
    print(XYZ_to_RGB_vectorise(XYZ, W_R, W_T, M, CAT))

    print('\n')

    print('3d array input:')
    XYZ = np.reshape(XYZ, (2, 3, 3))
    print(XYZ_to_RGB_vectorise(XYZ, W_R, W_T, M, CAT))

    print('\n')


# XYZ_to_RGB_analysis()

# #############################################################################
# # ### colour.RGB_to_XYZ
# #############################################################################
W_R = (0.31271, 0.32902)
W_T = (0.34567, 0.35850)
CAT = 'Bradford'
M = np.array([
    [0.41238656, 0.35759149, 0.18045049],
    [0.21263682, 0.71518298, 0.0721802],
    [0.01933062, 0.11919716, 0.95037259]])


def RGB_to_XYZ_2d(RGB):
    for i in range(len(RGB)):
        RGB_to_XYZ(RGB[i], W_R, W_T, M, CAT)


def RGB_to_XYZ_vectorise(RGB,
                         illuminant_RGB,
                         illuminant_XYZ,
                         RGB_to_XYZ_matrix,
                         chromatic_adaptation_transform='CAT02',
                         inverse_transfer_function=None):
    if inverse_transfer_function is not None:
        RGB = inverse_transfer_function(RGB)

    XYZ = np.einsum('...ij,...j->...i', RGB_to_XYZ_matrix, RGB)

    M = chromatic_adaptation_matrix_VonKries_vectorise(
        xy_to_XYZ_vectorise(illuminant_RGB),
        xy_to_XYZ_vectorise(illuminant_XYZ),
        transform=chromatic_adaptation_transform)

    XYZ_a = np.einsum('...ij,...j->...i', M, XYZ)

    return XYZ_a


def RGB_to_XYZ_analysis():
    message_box('RGB_to_XYZ')

    print('Reference:')
    RGB = np.array([0.86969452, 1.00516431, 1.41715848])
    print(RGB_to_XYZ(RGB, W_R, W_T, M, CAT))

    print('\n')

    print('1d array input:')
    print(RGB_to_XYZ_vectorise(RGB, W_R, W_T, M, CAT))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_XYZ_vectorise(RGB, W_R, W_T, M, CAT))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_XYZ_vectorise(RGB, W_R, W_T, M, CAT))

    print('\n')


# RGB_to_XYZ_analysis()

# #############################################################################
# ### colour.RGB_to_RGB
# #############################################################################
from colour import sRGB_COLOURSPACE

C = sRGB_COLOURSPACE
CAT = 'Bradford'


def RGB_to_RGB_2d(RGB):
    for i in range(len(RGB)):
        RGB_to_RGB(RGB[i], C, C, CAT)


def RGB_to_RGB_vectorise(RGB,
                         input_colourspace,
                         output_colourspace,
                         chromatic_adaptation_transform='CAT02'):
    cat = chromatic_adaptation_matrix_VonKries_vectorise(
        xy_to_XYZ_vectorise(input_colourspace.whitepoint),
        xy_to_XYZ_vectorise(output_colourspace.whitepoint),
        chromatic_adaptation_transform)

    M = np.einsum('...ij,...jk->...ik',
                  input_colourspace.RGB_to_XYZ_matrix,
                  cat)
    M = np.einsum('...ij,...jk->...ik',
                  M,
                  output_colourspace.XYZ_to_RGB_matrix)

    RGB = np.einsum('...ij,...j->...i', M, RGB)

    return RGB


def RGB_to_RGB_analysis():
    message_box('RGB_to_RGB')

    print('Reference:')
    RGB = np.array([0.86969452, 1.00516431, 1.41715848])
    print(RGB_to_RGB(RGB, C, C, CAT))

    print('\n')

    print('1d array input:')
    print(RGB_to_RGB_vectorise(RGB, C, C, CAT))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_RGB_vectorise(RGB, C, C, CAT))
    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_RGB_vectorise(RGB, C, C, CAT))

    print('\n')


# RGB_to_RGB_analysis()

# #############################################################################
# #############################################################################
# ### colour.notation.munsell
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.munsell_value_Priest1920
# #############################################################################
from colour.notation.munsell import *

Y = np.linspace(0, 100, 1000000)


def munsell_value_Priest1920_2d(Y):
    for i in range(len(Y)):
        munsell_value_Priest1920(Y[i])


def munsell_value_Priest1920_vectorise(Y):
    Y = np.asarray(Y)

    Y /= 100
    V = 10 * np.sqrt(Y)

    return V


def munsell_value_Priest1920_analysis():
    message_box('munsell_value_Priest1920')

    print('Reference:')
    print(munsell_value_Priest1920(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_Priest1920_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_Priest1920_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_Priest1920_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_Priest1920_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_Priest1920_vectorise(Y))

    print('\n')


# munsell_value_Priest1920_analysis()

# #############################################################################
# ### colour.munsell_value_Munsell1933
# #############################################################################


def munsell_value_Munsell1933_2d(Y):
    for i in range(len(Y)):
        munsell_value_Munsell1933(Y[i])


def munsell_value_Munsell1933_vectorise(Y):
    Y = np.asarray(Y)

    V = np.sqrt(1.4742 * Y - 0.004743 * (Y * Y))

    return V


def munsell_value_Munsell1933_analysis():
    message_box('munsell_value_Munsell1933')

    print('Reference:')
    print(munsell_value_Munsell1933(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_Munsell1933_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_Munsell1933_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_Munsell1933_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_Munsell1933_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_Munsell1933_vectorise(Y))

    print('\n')


# munsell_value_Munsell1933_analysis()

# #############################################################################
# ### colour.munsell_value_Moon1943
# #############################################################################


def munsell_value_Moon1943_2d(Y):
    for i in range(len(Y)):
        munsell_value_Moon1943(Y[i])


def munsell_value_Moon1943_vectorise(Y):
    Y = np.asarray(Y)

    V = 1.4 * Y ** 0.426

    return V


def munsell_value_Moon1943_analysis():
    message_box('munsell_value_Moon1943')

    print('Reference:')
    print(munsell_value_Moon1943(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_Moon1943_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_Moon1943_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_Moon1943_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_Moon1943_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_Moon1943_vectorise(Y))

    print('\n')


# munsell_value_Moon1943_analysis()

# #############################################################################
# ### colour.munsell_value_Saunderson1944
# #############################################################################


def munsell_value_Saunderson1944_2d(Y):
    for i in range(len(Y)):
        munsell_value_Saunderson1944(Y[i])


def munsell_value_Saunderson1944_vectorise(Y):
    Y = np.asarray(Y)

    V = 2.357 * (Y ** 0.343) - 1.52

    return V


def munsell_value_Saunderson1944_analysis():
    message_box('munsell_value_Saunderson1944')

    print('Reference:')
    print(munsell_value_Saunderson1944(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_Saunderson1944_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_Saunderson1944_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_Saunderson1944_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_Saunderson1944_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_Saunderson1944_vectorise(Y))

    print('\n')


# munsell_value_Saunderson1944_analysis()

# #############################################################################
# ### colour.munsell_value_Ladd1955
# #############################################################################


def munsell_value_Ladd1955_2d(Y):
    for i in range(len(Y)):
        munsell_value_Ladd1955(Y[i])


def munsell_value_Ladd1955_vectorise(Y):
    Y = np.asarray(Y)

    V = 2.468 * (Y ** (1 / 3)) - 1.636

    return V


def munsell_value_Ladd1955_analysis():
    message_box('munsell_value_Ladd1955')

    print('Reference:')
    print(munsell_value_Ladd1955(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_Ladd1955_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_Ladd1955_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_Ladd1955_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_Ladd1955_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_Ladd1955_vectorise(Y))

    print('\n')


# munsell_value_Ladd1955_analysis()

# #############################################################################
# ### colour.munsell_value_McCamy1987
# #############################################################################


def munsell_value_McCamy1987_2d(Y):
    V = []
    for i in range(len(Y)):
        V.append(munsell_value_McCamy1987(Y[i]))
    return V


@ignore_numpy_errors
def munsell_value_McCamy1987_vectorise(Y):
    Y = np.asarray(Y)

    V = np.where(Y <= 0.9,
                 0.87445 * (Y ** 0.9967),
                 (2.49268 * (Y ** (1 / 3)) - 1.5614 -
                  (0.985 / (((0.1073 * Y - 3.084) ** 2) + 7.54)) +
                  (0.0133 / (Y ** 2.3)) +
                  0.0084 * np.sin(4.1 * (Y ** (1 / 3)) + 1) +
                  (0.0221 / Y) * np.sin(0.39 * (Y - 2)) -
                  (0.0037 / (0.44 * Y)) * np.sin(1.28 * (Y - 0.53))))

    return V


def munsell_value_McCamy1987_analysis():
    message_box('munsell_value_McCamy1987')

    print('Reference:')
    print(munsell_value_McCamy1987(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_McCamy1987_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_McCamy1987_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_McCamy1987_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_McCamy1987_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_McCamy1987_vectorise(Y))

    print('\n')

    Y = np.linspace(0, 100, 10000)
    np.testing.assert_almost_equal(
        munsell_value_McCamy1987_2d(Y),
        munsell_value_McCamy1987_vectorise(Y))


# munsell_value_McCamy1987_analysis()

# #############################################################################
# ### colour.munsell_value_ASTMD153508
# #############################################################################


def munsell_value_ASTMD153508_2d(Y):
    for i in range(len(Y)):
        munsell_value_ASTMD153508(Y[i])


from colour.algebra import *

_MUNSELL_VALUE_ASTM_D1535_08_INTERPOLATOR_CACHE = None


def _munsell_value_ASTMD153508_interpolator():
    global _MUNSELL_VALUE_ASTM_D1535_08_INTERPOLATOR_CACHE
    munsell_values = np.arange(0, 10, 0.001)
    if _MUNSELL_VALUE_ASTM_D1535_08_INTERPOLATOR_CACHE is None:
        _MUNSELL_VALUE_ASTM_D1535_08_INTERPOLATOR_CACHE = Extrapolator1d(
            LinearInterpolator1d(
                luminance_ASTMD153508_vectorise(munsell_values),
                munsell_values))

    return _MUNSELL_VALUE_ASTM_D1535_08_INTERPOLATOR_CACHE


def munsell_value_ASTMD153508_vectorise(Y):
    Y = np.asarray(Y)

    V = _munsell_value_ASTMD153508_interpolator()(Y)

    return V


def munsell_value_ASTMD153508_analysis():
    message_box('munsell_value_ASTMD153508')

    print('Reference:')
    print(munsell_value_ASTMD153508(10.08))

    print('\n')

    print('Numeric input:')
    print(munsell_value_ASTMD153508_vectorise(10.08))

    print('\n')

    print('0d array input:')
    print(munsell_value_ASTMD153508_vectorise(np.array(10.08)))

    print('\n')

    print('1d array input:')
    Y = [10.08] * 6
    print(munsell_value_ASTMD153508_vectorise(Y))

    print('\n')

    print('2d array input:')
    Y = np.reshape(Y, (2, 3))
    print(munsell_value_ASTMD153508_vectorise(Y))

    print('\n')

    print('3d array input:')
    Y = np.reshape(Y, (2, 3, 1))
    print(munsell_value_ASTMD153508_vectorise(Y))

    print('\n')


# munsell_value_ASTMD153508_analysis()

# #############################################################################
# #############################################################################
# ### colour.notation.triplet
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.notation.triplet.RGB_to_HEX
# #############################################################################
from colour.notation.triplet import *


def RGB_to_HEX_2d(RGB):
    for i in range(len(RGB)):
        RGB_to_HEX(RGB[i])


def RGB_to_HEX_vectorise(RGB):
    to_HEX = np.vectorize('{0:02x}'.format)

    HEX = to_HEX((RGB * 255).astype(np.uint8)).astype(object)
    HEX = np.asarray('#') + HEX[..., 0] + HEX[..., 1] + HEX[..., 2]

    return HEX


def RGB_to_HEX_analysis():
    message_box('RGB_to_HEX')

    print('Reference:')
    RGB = np.array([0.66666667, 0.86666667, 1])
    print(RGB_to_HEX(RGB))

    print('\n')

    print('1d array input:')
    print(RGB_to_HEX_vectorise(RGB))

    print('\n')

    print('2d array input:')
    RGB = np.tile(RGB, (6, 1))
    print(RGB_to_HEX_vectorise(RGB))

    print('\n')

    print('3d array input:')
    RGB = np.reshape(RGB, (2, 3, 3))
    print(RGB_to_HEX_vectorise(RGB))

    print('\n')


# RGB_to_HEX_analysis()

# #############################################################################
# ### colour.notation.triplet.HEX_to_RGB
# #############################################################################
from colour.notation.triplet import *


def HEX_to_RGB_2d(HEX):
    for i in range(len(HEX)):
        HEX_to_RGB(HEX[i])


def HEX_to_RGB_vectorise(HEX):
    HEX = np.core.defchararray.lstrip(HEX, '#')

    def to_RGB(x):
        length = len(x)
        return [int(x[i:i + length // 3], 16)
                for i in range(0, length, length // 3)]

    toRGB = np.vectorize(to_RGB, otypes=[np.ndarray])

    RGB = np.asarray(toRGB(HEX).tolist()) / 255

    return RGB


def HEX_to_RGB_analysis():
    message_box('HEX_to_RGB')

    print('Reference:')
    HEX = '#aaddff'
    print(HEX_to_RGB(HEX))

    print('\n')

    print('Numeric input:')
    print(HEX_to_RGB_vectorise(HEX))

    print('\n')

    print('1d array input:')
    HEX = np.tile(HEX, (6,))
    print(HEX_to_RGB_vectorise(HEX))

    print('\n')

    print('2d array input:')
    HEX = np.reshape(HEX, (2, 3))
    print(HEX_to_RGB_vectorise(HEX))

    # HEX1 = ['#aaddff'] * (1920 * 1080)

    print('\n')


# HEX_to_RGB_analysis()

# #############################################################################
# #############################################################################
# ### colour.phenomenons.rayleigh
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.phenomenons.rayleigh.air_refraction_index_Penndorf1957
# #############################################################################
from colour.phenomenons.rayleigh import *


def air_refraction_index_Penndorf1957_2d(wl):
    for i in range(len(wl)):
        air_refraction_index_Penndorf1957(wl[i])


def air_refraction_index_Penndorf1957_vectorise(wavelength, *args):
    wl = np.asarray(wavelength)

    n = 6432.8 + 2949810 / (146 - wl ** (-2)) + 25540 / (41 - wl ** (-2))
    n = n / 1.0e8 + 1

    return n


def air_refraction_index_Penndorf1957_analysis():
    message_box('air_refraction_index_Penndorf1957')

    print('Reference:')
    print(air_refraction_index_Penndorf1957(0.555))

    print('\n')

    print('Numeric input:')
    print(air_refraction_index_Penndorf1957_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(air_refraction_index_Penndorf1957_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(air_refraction_index_Penndorf1957_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(air_refraction_index_Penndorf1957_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(air_refraction_index_Penndorf1957_vectorise(wl))

    print('\n')


# air_refraction_index_Penndorf1957_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.air_refraction_index_Edlen1966
# #############################################################################


def air_refraction_index_Edlen1966_2d(wl):
    for i in range(len(wl)):
        air_refraction_index_Edlen1966(wl[i])


def air_refraction_index_Edlen1966_vectorise(wavelength, *args):
    wl = np.asarray(wavelength)

    n = 8342.13 + 2406030 / (130 - wl ** (-2)) + 15997 / (38.9 - wl ** (-2))
    n = n / 1.0e8 + 1

    return n


def air_refraction_index_Edlen1966_analysis():
    message_box('air_refraction_index_Edlen1966')

    print('Reference:')
    print(air_refraction_index_Edlen1966(0.555))

    print('\n')

    print('Numeric input:')
    print(air_refraction_index_Edlen1966_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(air_refraction_index_Edlen1966_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(air_refraction_index_Edlen1966_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(air_refraction_index_Edlen1966_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(air_refraction_index_Edlen1966_vectorise(wl))

    print('\n')


# air_refraction_index_Edlen1966_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.air_refraction_index_Peck1972
# #############################################################################


def air_refraction_index_Peck1972_2d(wl):
    for i in range(len(wl)):
        air_refraction_index_Peck1972(wl[i])


def air_refraction_index_Peck1972_vectorise(wavelength, *args):
    wl = np.asarray(wavelength)

    n = (8060.51 + 2480990 / (132.274 - wl ** (-2)) + 17455.7 /
         (39.32957 - wl ** (-2)))
    n = n / 1.0e8 + 1

    return n


def air_refraction_index_Peck1972_analysis():
    message_box('air_refraction_index_Peck1972')

    print('Reference:')
    print(air_refraction_index_Peck1972(0.555))

    print('\n')

    print('Numeric input:')
    print(air_refraction_index_Peck1972_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(air_refraction_index_Peck1972_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(air_refraction_index_Peck1972_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(air_refraction_index_Peck1972_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(air_refraction_index_Peck1972_vectorise(wl))

    print('\n')


# air_refraction_index_Peck1972_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.air_refraction_index_Bodhaine1999
# #############################################################################


def air_refraction_index_Bodhaine1999_2d(wl):
    for i in range(len(wl)):
        air_refraction_index_Bodhaine1999(wl[i])


def air_refraction_index_Bodhaine1999_vectorise(
        wavelength,
        CO2_concentration=STANDARD_CO2_CONCENTRATION):
    wl = np.asarray(wavelength)
    CO2_c = np.asarray(CO2_concentration)

    n = ((1 + 0.54 * ((CO2_c * 1e-6) - 300e-6)) *
         (air_refraction_index_Peck1972(wl) - 1) + 1)

    return n


def air_refraction_index_Bodhaine1999_analysis():
    message_box('air_refraction_index_Bodhaine1999')

    print('Reference:')
    print(air_refraction_index_Bodhaine1999(0.555))

    print('\n')

    print('Numeric input:')
    print(air_refraction_index_Bodhaine1999_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(air_refraction_index_Bodhaine1999_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(air_refraction_index_Bodhaine1999_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(air_refraction_index_Bodhaine1999_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(air_refraction_index_Bodhaine1999_vectorise(wl))

    print('\n')


# air_refraction_index_Bodhaine1999_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.N2_depolarisation
# #############################################################################


def N2_depolarisation_2d(wl):
    for i in range(len(wl)):
        N2_depolarisation(wl[i])


def N2_depolarisation_vectorise(wavelength):
    wl = np.asarray(wavelength)

    N2 = 1.034 + 3.17 * 1.0e-4 * (1 / wl ** 2)

    return N2


def N2_depolarisation_analysis():
    message_box('N2_depolarisation')

    print('Reference:')
    print(N2_depolarisation(0.555))

    print('\n')

    print('Numeric input:')
    print(N2_depolarisation_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(N2_depolarisation_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(N2_depolarisation_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(N2_depolarisation_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(N2_depolarisation_vectorise(wl))

    print('\n')


# N2_depolarisation_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.O2_depolarisation
# #############################################################################


def O2_depolarisation_2d(wl):
    for i in range(len(wl)):
        O2_depolarisation(wl[i])


def O2_depolarisation_vectorise(wavelength):
    wl = np.asarray(wavelength)

    O2 = (1.096 + 1.385 * 1.0e-3 * (1 / wl ** 2) + 1.448 * 1.0e-4 *
          (1 / wl ** 4))

    return O2


def O2_depolarisation_analysis():
    message_box('O2_depolarisation')

    print('Reference:')
    print(O2_depolarisation(0.555))

    print('\n')

    print('Numeric input:')
    print(O2_depolarisation_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(O2_depolarisation_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(O2_depolarisation_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(O2_depolarisation_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(O2_depolarisation_vectorise(wl))

    print('\n')


# O2_depolarisation_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.F_air_Penndorf1957
# #############################################################################


def F_air_Penndorf1957_vectorise(wavelength, *args):
    wl = np.asarray(wavelength)

    return np.resize(np.array([1.0608]), wl.shape)


def F_air_Penndorf1957_analysis():
    message_box('F_air_Penndorf1957')

    print('Reference:')
    print(F_air_Penndorf1957(0.555))

    print('\n')

    print('Numeric input:')
    print(F_air_Penndorf1957_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(F_air_Penndorf1957_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(F_air_Penndorf1957_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(F_air_Penndorf1957_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(F_air_Penndorf1957_vectorise(wl))


# F_air_Penndorf1957_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.F_air_Young1981
# #############################################################################


def F_air_Young1981_vectorise(wavelength, *args):
    wl = np.asarray(wavelength)

    return np.resize(np.array([1.0480]), wl.shape)


def F_air_Young1981_analysis():
    message_box('F_air_Young1981')

    print('Reference:')
    print(F_air_Young1981(0.555))

    print('\n')

    print('Numeric input:')
    print(F_air_Young1981_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(F_air_Young1981_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(F_air_Young1981_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(F_air_Young1981_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(F_air_Young1981_vectorise(wl))


# F_air_Young1981_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.F_air_Bates1984
# #############################################################################


def F_air_Bates1984_2d(wl):
    for i in range(len(wl)):
        F_air_Bates1984(wl[i])


def F_air_Bates1984_vectorise(wavelength, *args):
    O2 = O2_depolarisation_vectorise(wavelength)
    N2 = N2_depolarisation_vectorise(wavelength)
    Ar = 1.00
    CO2 = 1.15

    F_air = ((78.084 * N2 + 20.946 * O2 + CO2 + Ar) /
             (78.084 + 20.946 + Ar + CO2))

    return F_air


def F_air_Bates1984_analysis():
    message_box('F_air_Bates1984')

    print('Reference:')
    print(F_air_Bates1984(0.555))

    print('\n')

    print('Numeric input:')
    print(F_air_Bates1984_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(F_air_Bates1984_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(F_air_Bates1984_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(F_air_Bates1984_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(F_air_Bates1984_vectorise(wl))

    print('\n')


# F_air_Bates1984_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.F_air_Bodhaine1999
# #############################################################################


def F_air_Bodhaine1999_2d(wl):
    for i in range(len(wl)):
        F_air_Bodhaine1999(wl[i])


def F_air_Bodhaine1999_vectorise(wavelength,
                                 CO2_concentration=STANDARD_CO2_CONCENTRATION):
    O2 = O2_depolarisation_vectorise(wavelength)
    N2 = N2_depolarisation_vectorise(wavelength)
    CO2_c = np.asarray(CO2_concentration)

    F_air = ((78.084 * N2 + 20.946 * O2 + 0.934 * 1 + CO2_c * 1.15) /
             (78.084 + 20.946 + 0.934 + CO2_c))

    return F_air


def F_air_Bodhaine1999_analysis():
    message_box('F_air_Bodhaine1999')

    print('Reference:')
    print(F_air_Bodhaine1999(0.555))

    print('\n')

    print('Numeric input:')
    print(F_air_Bodhaine1999_vectorise(0.555))

    print('\n')

    print('0d array input:')
    print(F_air_Bodhaine1999_vectorise(np.array(0.555)))

    print('\n')

    print('1d array input:')
    wl = [0.555] * 6
    print(F_air_Bodhaine1999_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(F_air_Bodhaine1999_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(F_air_Bodhaine1999_vectorise(wl))

    print('\n')


# F_air_Bodhaine1999_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.molecular_density
# #############################################################################
from colour.constants import AVOGADRO_CONSTANT


def molecular_density_2d(temperature):
    for i in range(len(temperature)):
        molecular_density(temperature[i])


def molecular_density_vectorise(temperature=STANDARD_AIR_TEMPERATURE,
                                avogadro_constant=AVOGADRO_CONSTANT):
    # Review doctests to use coherent temperature values.
    T = np.asarray(temperature)

    N_s = (avogadro_constant / 22.4141) * (273.15 / T) * (1 / 1000)

    return N_s


def molecular_density_analysis():
    message_box('molecular_density')

    print('Reference:')
    print(molecular_density(15))

    print('\n')

    print('Numeric input:')
    print(molecular_density_vectorise(15))

    print('\n')

    print('0d array input:')
    print(molecular_density_vectorise(np.array(15)))

    print('\n')

    print('1d array input:')
    t = [15] * 6
    print(molecular_density_vectorise(t))

    print('\n')

    print('2d array input:')
    t = np.reshape(t, (2, 3))
    print(molecular_density_vectorise(t))

    print('\n')

    print('3d array input:')
    t = np.reshape(t, (2, 3, 1))
    print(molecular_density_vectorise(t))

    print('\n')


# molecular_density_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.mean_molecular_weights
# #############################################################################


def mean_molecular_weights_2d(C):
    for i in range(len(C)):
        mean_molecular_weights(C[i])


def mean_molecular_weights_vectorise(
        CO2_concentration=STANDARD_CO2_CONCENTRATION):
    CO2_c = np.asarray(CO2_concentration) * 1.0e-6

    m_a = 15.0556 * CO2_c + 28.9595

    return m_a


def mean_molecular_weights_analysis():
    message_box('mean_molecular_weights')

    print('Reference:')
    print(mean_molecular_weights(300))

    print('\n')

    print('Numeric input:')
    print(mean_molecular_weights_vectorise(300))

    print('\n')

    print('0d array input:')
    print(mean_molecular_weights_vectorise(np.array(300)))

    print('\n')

    print('1d array input:')
    c = [300] * 6
    print(mean_molecular_weights_vectorise(c))

    print('\n')

    print('2d array input:')
    c = np.reshape(c, (2, 3))
    print(mean_molecular_weights_vectorise(c))

    print('\n')

    print('3d array input:')
    c = np.reshape(c, (2, 3, 1))
    print(mean_molecular_weights_vectorise(c))

    print('\n')


# mean_molecular_weights_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.gravity_List1968
# #############################################################################


def gravity_List1968_2d(C):
    for i in range(len(C)):
        gravity_List1968(C[i])


def gravity_List1968_vectorise(latitude=DEFAULT_LATITUDE,
                               altitude=DEFAULT_ALTITUDE):
    latitude = np.asarray(latitude)
    altitude = np.asarray(altitude)

    cos2phi = np.cos(2 * np.radians(latitude))

    # Sea level acceleration of gravity.
    g0 = 980.6160 * (1 - 0.0026373 * cos2phi + 0.0000059 * cos2phi ** 2)

    g = (g0 - (3.085462e-4 + 2.27e-7 * cos2phi) * altitude +
         (7.254e-11 + 1.0e-13 * cos2phi) * altitude ** 2 -
         (1.517e-17 + 6e-20 * cos2phi) * altitude ** 3)

    return g


def gravity_List1968_analysis():
    message_box('gravity_List1968')

    print('Reference:')
    print(gravity_List1968(0, 0))

    print('\n')

    print('Numeric input:')
    print(gravity_List1968_vectorise(0, 0))

    print('\n')

    print('1d array input:')
    print(gravity_List1968_vectorise([0] * 6, [0]))

    print('\n')

    print('2d array input:')
    l = np.reshape([0] * 6, (2, 3))
    print(gravity_List1968_vectorise(l, [0]))

    print('\n')

    print('2d array input:')
    l = np.reshape([0] * 6, (2, 3, 1))
    print(gravity_List1968_vectorise(l, [0]))

    print('\n')


# gravity_List1968_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.scattering_cross_section
# #############################################################################


def scattering_cross_section_2d(wl):
    for i in range(len(wl)):
        scattering_cross_section(wl[i])


def scattering_cross_section_vectorise(wavelength,
                                       CO2_concentration=STANDARD_CO2_CONCENTRATION,
                                       temperature=STANDARD_AIR_TEMPERATURE,
                                       avogadro_constant=AVOGADRO_CONSTANT,
                                       n_s=air_refraction_index_Bodhaine1999,
                                       F_air=F_air_Bodhaine1999):
    wl = np.asarray(wavelength)
    CO2_c = np.asarray(CO2_concentration)
    temperature = np.asarray(temperature)

    wl_micrometers = wl * 10e3

    n_s = n_s(wl_micrometers)
    N_s = molecular_density(temperature, avogadro_constant)
    F_air = F_air(wl_micrometers, CO2_c)

    sigma = (24 * np.pi ** 3 * (n_s ** 2 - 1) ** 2 /
             (wl ** 4 * N_s ** 2 * (n_s ** 2 + 2) ** 2))
    sigma *= F_air

    return sigma


def scattering_cross_section_analysis():
    message_box('scattering_cross_section')

    print('Reference:')
    print(scattering_cross_section(555 * 10e-8))

    print('\n')

    print('Numeric input:')
    print(scattering_cross_section_vectorise(555 * 10e-8))

    print('\n')

    print('0d array input:')
    print(scattering_cross_section_vectorise(np.array(555 * 10e-8)))

    print('\n')

    print('1d array input:')
    wl = [555 * 10e-8] * 6
    print(scattering_cross_section_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(scattering_cross_section_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(scattering_cross_section_vectorise(wl))

    print('\n')


# scattering_cross_section_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.rayleigh_optical_depth
# #############################################################################


def rayleigh_optical_depth_2d(wl):
    for i in range(len(wl)):
        rayleigh_optical_depth(wl[i])


def rayleigh_optical_depth_vectorise(wavelength,
                                     CO2_concentration=STANDARD_CO2_CONCENTRATION,
                                     temperature=STANDARD_AIR_TEMPERATURE,
                                     pressure=AVERAGE_PRESSURE_MEAN_SEA_LEVEL,
                                     latitude=DEFAULT_LATITUDE,
                                     altitude=DEFAULT_ALTITUDE,
                                     avogadro_constant=AVOGADRO_CONSTANT,
                                     n_s=air_refraction_index_Bodhaine1999,
                                     F_air=F_air_Bodhaine1999):
    wavelength = np.asarray(wavelength)
    CO2_c = np.asarray(CO2_concentration)
    latitude = np.asarray(latitude)
    altitude = np.asarray(altitude)
    # Conversion from pascal to dyne/cm2.
    P = np.asarray(pressure * 10)

    sigma = scattering_cross_section(wavelength,
                                     CO2_c,
                                     temperature,
                                     avogadro_constant,
                                     n_s,
                                     F_air)

    m_a = mean_molecular_weights(CO2_c)
    g = gravity_List1968(latitude, altitude)

    T_R = sigma * (P * avogadro_constant) / (m_a * g)

    return T_R


def rayleigh_optical_depth_analysis():
    message_box('rayleigh_optical_depth')

    print('Reference:')
    print(rayleigh_optical_depth(555 * 10e-8))

    print('\n')

    print('Numeric input:')
    print(rayleigh_optical_depth_vectorise(555 * 10e-8))

    print('\n')

    print('0d array input:')
    print(rayleigh_optical_depth_vectorise(np.array(555 * 10e-8)))

    print('\n')

    print('1d array input:')
    wl = [555 * 10e-8] * 6
    print(rayleigh_optical_depth_vectorise(wl))

    print('\n')

    print('2d array input:')
    wl = np.reshape(wl, (2, 3))
    print(rayleigh_optical_depth_vectorise(wl))

    print('\n')

    print('3d array input:')
    wl = np.reshape(wl, (2, 3, 1))
    print(rayleigh_optical_depth_vectorise(wl))

    print('\n')


# rayleigh_optical_depth_analysis()

# #############################################################################
# ### colour.phenomenons.rayleigh.rayleigh_scattering_spd
# #############################################################################


def rayleigh_scattering_spd_vectorise(shape=DEFAULT_SPECTRAL_SHAPE,
                                      CO2_concentration=STANDARD_CO2_CONCENTRATION,
                                      temperature=STANDARD_AIR_TEMPERATURE,
                                      pressure=AVERAGE_PRESSURE_MEAN_SEA_LEVEL,
                                      latitude=DEFAULT_LATITUDE,
                                      altitude=DEFAULT_ALTITUDE,
                                      avogadro_constant=AVOGADRO_CONSTANT,
                                      n_s=air_refraction_index_Bodhaine1999,
                                      F_air=F_air_Bodhaine1999):
    wavelengths = shape.range()
    return SpectralPowerDistribution(
        name=('Rayleigh Scattering - {0} ppm, {1} K, {2} Pa, {3} Degrees, '
              '{4} m').format(CO2_concentration,
                              temperature,
                              pressure,
                              latitude,
                              altitude),
        data=dict(zip(wavelengths,
                      rayleigh_optical_depth_vectorise(wavelengths * 10e-8,
                                                       CO2_concentration,
                                                       temperature,
                                                       pressure,
                                                       latitude,
                                                       altitude,
                                                       avogadro_constant,
                                                       n_s,
                                                       F_air))))


def rayleigh_scattering_spd_analysis():
    message_box('rayleigh_scattering_spd')

    print(rayleigh_scattering_spd_vectorise().values)

    print('\n')


# rayleigh_scattering_spd_analysis()

# #############################################################################
# #############################################################################
# ### colour.quality.cqs
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.quality.cqs.gamut_area
# #############################################################################
from colour.quality.cqs import *


def gamut_area_vectorise(Lab):
    Lab = np.asarray(Lab)
    Lab_s = np.roll(np.copy(Lab), -3)

    L, a, b = zsplit(Lab)
    L_s, a_s, b_s = zsplit(Lab_s)

    A = np.linalg.norm(Lab[..., 1:3], axis=-1)
    B = np.linalg.norm(Lab_s[..., 1:3], axis=-1)
    C = np.linalg.norm(np.dstack((a_s - a, b_s - b)), axis=-1)
    t = (A + B + C) / 2
    S = np.sqrt(t * (t - A) * (t - B) * (t - C))

    return np.sum(S)


def gamut_area_vectorise_analysis():
    message_box('gamut_area_vectorise')

    Lab = [np.array([39.94996006, 34.59018231, -19.86046321]),
           np.array([38.88395498, 21.44348519, -34.87805301]),
           np.array([36.60576301, 7.06742454, -43.21461177]),
           np.array([46.60142558, -15.90481586, -34.64616865]),
           np.array([56.50196523, -29.5465555, -20.50177194]),
           np.array([55.73912101, -43.39520959, -5.08956953]),
           np.array([56.2077687, -53.68997662, 20.2113441]),
           np.array([66.16683122, -38.64600327, 42.77396631]),
           np.array([76.7295211, -23.9214821, 61.04740432]),
           np.array([82.85370708, -3.98679065, 75.43320144]),
           np.array([69.26458861, 13.11066359, 68.83858372]),
           np.array([69.63154351, 28.24532497, 59.45609803]),
           np.array([61.26281449, 40.87950839, 44.97606172]),
           np.array([41.62567821, 57.34129516, 27.4671817]),
           np.array([40.52565174, 48.87449192, 3.4512168])]

    print(gamut_area(Lab))

    print(gamut_area_vectorise(Lab))

    print('\n')


# gamut_area_vectorise_analysis()

# #############################################################################
# #############################################################################
# ### colour.temperature.cct
# #############################################################################
# #############################################################################

# #############################################################################
# ### colour.xy_to_CCT_McCamy1992
# #############################################################################
from colour.temperature.cct import *


def xy_to_CCT_McCamy1992_2d(xy):
    for i in range(len(xy)):
        xy_to_CCT_McCamy1992(xy[i])


def xy_to_CCT_McCamy1992_vectorise(xy):
    x, y = zsplit(xy)

    n = (x - 0.3320) / (y - 0.1858)
    CCT = -449 * n ** 3 + 3525 * n ** 2 - 6823.3 * n + 5520.33

    return CCT


def xy_to_CCT_McCamy1992_analysis():
    message_box('xy_to_CCT_McCamy1992')

    print('Reference:')
    xy = np.array([0.31271, 0.32902])
    print(xy_to_CCT_McCamy1992(xy))

    print('\n')

    print('1d array input:')
    print(xy_to_CCT_McCamy1992_vectorise(xy))

    print('\n')

    print('2d array input:')
    xy = np.tile(xy, (6, 1))
    print(xy_to_CCT_McCamy1992_vectorise(xy))

    print('\n')

    print('3d array input:')
    xy = np.reshape(xy, (2, 3, 2))
    print(xy_to_CCT_McCamy1992_vectorise(xy))

    print('\n')


# xy_to_CCT_McCamy1992_analysis()

# #############################################################################
# ### colour.xy_to_CCT_Hernandez1999
# #############################################################################


def xy_to_CCT_Hernandez1999_2d(xy):
    CCT = []
    for i in range(len(xy)):
        CCT.append(xy_to_CCT_Hernandez1999(xy[i]))
    return CCT


def xy_to_CCT_Hernandez1999_vectorise(xy):
    x, y = zsplit(xy)

    n = (x - 0.3366) / (y - 0.1735)
    CCT = (-949.86315 +
           6253.80338 * np.exp(-n / 0.92159) +
           28.70599 * np.exp(-n / 0.20039) +
           0.00004 * np.exp(-n / 0.07125))

    n = np.where(CCT > 50000,
                 (x - 0.3356) / (y - 0.1691),
                 n)

    CCT = np.where(CCT > 50000,
                   36284.48953 + 0.00228 * np.exp(-n / 0.07861) +
                   5.4535e-36 * np.exp(-n / 0.01543),
                   CCT)

    return CCT


def xy_to_CCT_Hernandez1999_analysis():
    message_box('xy_to_CCT_Hernandez1999')

    print('Reference:')
    xy = np.array([0.31271, 0.32902])
    print(xy_to_CCT_Hernandez1999(xy))

    print('\n')

    print('1d array input:')
    print(xy_to_CCT_Hernandez1999_vectorise(xy))

    print('\n')

    print('2d array input:')
    xy = np.tile(xy, (6, 1))
    print(xy_to_CCT_Hernandez1999_vectorise(xy))

    print('\n')

    print('3d array input:')
    xy = np.reshape(xy, (2, 3, 2))
    print(xy_to_CCT_Hernandez1999_vectorise(xy))

    print('\n')

    np.testing.assert_almost_equal(
        np.ravel(xy_to_CCT_Hernandez1999_2d(DATA1[:, 0:2])),
        np.ravel(xy_to_CCT_Hernandez1999_vectorise(DATA1[:, 0:2])))


# xy_to_CCT_Hernandez1999_analysis()

# #############################################################################
# ### colour.CCT_to_xy_Kang2002
# #############################################################################
CCT = np.linspace(4000, 20000, 1000000)


def CCT_to_xy_Kang2002_2d(CCT):
    xy = []
    for i in range(len(CCT)):
        xy.append(CCT_to_xy_Kang2002(CCT[i]))
    return xy


def CCT_to_xy_Kang2002_vectorise(CCT):
    CCT = np.asarray(CCT)

    if np.any(CCT[np.asarray(np.logical_or(CCT < 1667, CCT > 25000))]):
        warning(('Correlated colour temperature must be in domain '
                 '[1667, 25000], unpredictable results may occur!'))

    x = np.where(CCT <= 4000,
                 -0.2661239 * 10 ** 9 / CCT ** 3 -
                 0.2343589 * 10 ** 6 / CCT ** 2 +
                 0.8776956 * 10 ** 3 / CCT +
                 0.179910,
                 -3.0258469 * 10 ** 9 / CCT ** 3 +
                 2.1070379 * 10 ** 6 / CCT ** 2 +
                 0.2226347 * 10 ** 3 / CCT +
                 0.24039)

    y = np.select([CCT <= 2222,
                   np.logical_and(CCT > 2222, CCT <= 4000),
                   CCT > 4000],
                  [-1.1063814 * x ** 3 -
                   1.34811020 * x ** 2 +
                   2.18555832 * x -
                   0.20219683,
                   -0.9549476 * x ** 3 -
                   1.37418593 * x ** 2 +
                   2.09137015 * x -
                   0.16748867,
                   3.0817580 * x ** 3 -
                   5.8733867 * x ** 2 +
                   3.75112997 * x -
                   0.37001483])

    xy = zstack((x, y))

    return xy


def CCT_to_xy_Kang2002_analysis():
    message_box('CCT_to_xy_Kang2002')

    print('Reference:')
    print(CCT_to_xy_Kang2002(6504.38938305))

    print('\n')

    print('Numeric input:')
    print(CCT_to_xy_Kang2002_vectorise(6504.38938305))

    print('\n')

    print('0d array input:')
    print(CCT_to_xy_Kang2002_vectorise(np.array(6504.38938305)))

    print('\n')

    print('1d array input:')
    CCT = [6504.38938305] * 6
    print(CCT_to_xy_Kang2002_vectorise(CCT))

    print('\n')

    print('2d array input:')
    CCT = np.reshape(CCT, (2, 3))
    print(CCT_to_xy_Kang2002_vectorise(CCT))

    print('\n')

    print('3d array input:')
    CCT = np.reshape(CCT, (2, 3, 1))
    print(CCT_to_xy_Kang2002_vectorise(CCT))

    print('\n')

    CCT = np.linspace(1667, 25000, 10000)
    np.testing.assert_almost_equal(
        np.ravel(CCT_to_xy_Kang2002_2d(CCT)),
        np.ravel(CCT_to_xy_Kang2002_vectorise(CCT)))


# CCT_to_xy_Kang2002_analysis()

# #############################################################################
# ### colour.CCT_to_xy_CIE_D
# #############################################################################


def CCT_to_xy_CIE_D_2d(CCT):
    xy = []
    for i in range(len(CCT)):
        xy.append(CCT_to_xy_CIE_D(CCT[i]))
    return xy


def CCT_to_xy_CIE_D_vectorise(CCT):
    CCT = np.asarray(CCT)

    if np.any(CCT[np.asarray(np.logical_or(CCT < 4000, CCT > 25000))]):
        warning(('Correlated colour temperature must be in domain '
                 '[4000, 25000], unpredictable results may occur!'))

    x = np.where(CCT <= 7000,
                 -4.607 * 10 ** 9 / CCT ** 3 +
                 2.9678 * 10 ** 6 / CCT ** 2 +
                 0.09911 * 10 ** 3 / CCT +
                 0.244063,
                 -2.0064 * 10 ** 9 / CCT ** 3 +
                 1.9018 * 10 ** 6 / CCT ** 2 +
                 0.24748 * 10 ** 3 / CCT +
                 0.23704)

    y = -3 * x ** 2 + 2.87 * x - 0.275

    xy = zstack((x, y))

    return xy


def CCT_to_xy_CIE_D_analysis():
    message_box('CCT_to_xy_CIE_D')

    print('Reference:')
    print(CCT_to_xy_CIE_D(6504.38938305))

    print('\n')

    print('Numeric input:')
    print(CCT_to_xy_CIE_D_vectorise(6504.38938305))

    print('\n')

    print('0d array input:')
    print(CCT_to_xy_CIE_D_vectorise(np.array(6504.38938305)))

    print('\n')

    print('1d array input:')
    CCT = [6504.38938305] * 6
    print(CCT_to_xy_CIE_D_vectorise(CCT))

    print('\n')

    print('2d array input:')
    CCT = np.reshape(CCT, (2, 3))
    print(CCT_to_xy_CIE_D_vectorise(CCT))

    print('\n')

    print('3d array input:')
    CCT = np.reshape(CCT, (2, 3, 1))
    print(CCT_to_xy_CIE_D_vectorise(CCT))

    print('\n')

    CCT = np.linspace(4000, 25000, 10000)
    np.testing.assert_almost_equal(
        np.ravel(CCT_to_xy_CIE_D_2d(CCT)),
        np.ravel(CCT_to_xy_CIE_D_vectorise(CCT)))


    # CCT_to_xy_CIE_D_analysis()

    # #############################################################################
    # #############################################################################
    # ### Ramblings
    # #############################################################################
    # #############################################################################

    # #############################################################################
    # ### Image Operations
    # #############################################################################

    # import pylab
    # from OpenImageIO import FLOAT, ImageInput
    #
    # import colour
    # from colour.plotting import *
    #
    #
    # def read_image_as_array(path, bit_depth=FLOAT):
    # image = ImageInput.open(path)
    # specification = image.spec()
    #
    # return np.array(image.read_image(bit_depth)).reshape((specification.height,
    # specification.width,
    # specification.nchannels))
    #
    #
    # colour.sRGB_COLOURSPACE.transfer_function = _srgb_transfer_function
    #
    #
    # def image_plot(image,
    # transfer_function=colour.sRGB_COLOURSPACE.transfer_function):
    # image = np.clip(transfer_function(Lab_to_XYZ_vectorise(image)), 0, 1)
    # pylab.imshow(image)
    #
    # settings = {'no_ticks': True,
    # 'bounding_box': [0, 1, 0, 1],
    # 'bbox_inches': 'tight',
    # 'pad_inches': 0}
    #
    # canvas(**{'figure_size': (16, 16)})
    # decorate(**settings)
    # display(**settings)
    #
    #
    # marcie = read_image_as_array(
    # '/colour-science/colour-ramblings/resources/images/Digital_LAD_2048x1556.exr')
    #
    # image_plot(marcie)
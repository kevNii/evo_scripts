import itertools as it

from bisect import bisect_left
from typing import List

import numpy as np
import pandas as pd
import scipy.stats as sp

from pandas import Categorical

import pandas as pd

from numpy import mean, std # version >= 1.7.1 && <= 1.9.1
from math import sqrt, isnan

# From http://stackoverflow.com/questions/21532471/how-to-calculate-cohens-d-in-python
def cohen_d(x,y):
  return (mean(x) - mean(y)) / sqrt((std(x, ddof=1) ** 2 + std(y, ddof=1) ** 2) / 2.0)


def VD_A(treatment: List[float], control: List[float]):
    """
    Computes Vargha and Delaney A index
    A. Vargha and H. D. Delaney.
    A critique and improvement of the CL common language
    effect size statistics of McGraw and Wong.
    Journal of Educational and Behavioral Statistics, 25(2):101-132, 2000

    The formula to compute A has been transformed to minimize accuracy errors
    See: http://mtorchiano.wordpress.com/2014/05/19/effect-size-of-r-precision/

    :param treatment: a numeric list
    :param control: another numeric list

    :returns the value estimate and the magnitude
    """
    m = len(treatment)
    n = len(control)

    if m != n:
        raise ValueError("Data d and f must have the same length")

    r = sp.rankdata(treatment + control)
    r1 = sum(r[0:m])

    # Compute the measure
    # A = (r1/m - (m+1)/2)/n # formula (14) in Vargha and Delaney, 2000
    A = (2 * r1 - m * (m + 1)) / (2 * n * m)  # equivalent formula to avoid accuracy errors

    levels = [0.147, 0.33, 0.474]  # effect sizes from Hess and Kromrey, 2004
    magnitude = ["negligible", "small", "medium", "large"]
    scaled_A = (A - 0.5) * 2

    magnitude = magnitude[bisect_left(levels, abs(scaled_A))]
    estimate = A

    return estimate, magnitude


def VD_A_DF(data, val_col: str = None, group_col: str = None, sort=True):
    """

    :param data: pandas DataFrame object
        An array, any object exposing the array interface or a pandas DataFrame.
        Array must be two-dimensional. Second dimension may vary,
        i.e. groups may have different lengths.
    :param val_col: str, optional
        Must be specified if `a` is a pandas DataFrame object.
        Name of the column that contains values.
    :param group_col: str, optional
        Must be specified if `a` is a pandas DataFrame object.
        Name of the column that contains group names.
    :param sort : bool, optional
        Specifies whether to sort DataFrame by group_col or not. Recommended
        unless you sort your data manually.

    :return: stats : pandas DataFrame of effect sizes

    Stats summary ::
    'A' : Name of first measurement
    'B' : Name of second measurement
    'estimate' : effect sizes
    'magnitude' : magnitude

    """

    x = data.copy()
    if sort:
        x[group_col] = Categorical(x[group_col], categories=x[group_col].unique(), ordered=True)
        x.sort_values(by=[group_col, val_col], ascending=True, inplace=True)

    groups = x[group_col].unique()

    # Pairwise combinations
    g2, g1 = np.array(list(it.combinations(np.arange(groups.size), 2))).T

    # Compute effect size for each combination
    ef = np.array([VD_A(list(x[val_col][x[group_col] == groups[i]].values),
                        list(x[val_col][x[group_col] == groups[j]].values)) for i, j in zip(g1, g2)])

    return pd.DataFrame({
        'A': np.unique(data[group_col])[g1],
        'B': np.unique(data[group_col])[g2],
        'estimate': ef[:, 0],
        'magnitude': ef[:, 1]
    })


if __name__ == '__main__':
    df = pd.read_csv('evosuite-report/statistics.csv')
    data_points = ["Total_Time", "Coverage"]
    # data_point = "Total_Time"

    data_point_fn = {
        "Total_Time": lambda x: x / 1000,
        "Coverage": lambda x: x * 100
    }

    data_point_format = {
        "Total_Time": "{:.1f}",
        "Coverage": "{:.2f}"
    }

    for data_point in data_points:
        seen = {}

        higher = 0
        lower = 0
        same = 0
        total = 0
        count = 0

        significant_diff = {
            "higher": [],
            "lower": []
        }
        result = pd.DataFrame(columns=("Class", "DynaMOSA_" + data_point, "PVADynaMOSA_" + data_point, "A", "Magnitude", "p"))
        for target in df["TARGET_CLASS"]:
            if target in seen:
                continue
            else:
                seen[target] = True

            target_df = df[df["TARGET_CLASS"]==target]
            dyna_df = target_df[target_df["configuration_id"]=="DynaMOSA"]
            pva_df  = target_df[target_df["configuration_id"]=="PVADynaMOSA"]

            # print(target)
            try:
                vd = VD_A_DF(target_df, data_point, "configuration_id")
                cd = cohen_d(pva_df[data_point], dyna_df[data_point])
                wlcx_p = 1
                wlcx_s = 0
                if cd != 0 and not isnan(cd):
                    wlcx = sp.wilcoxon(pva_df[data_point], dyna_df[data_point])
                    wlcx_p = wlcx.pvalue
                    wlcx_s = wlcx.statistic
            except Exception as e:
                print(str(e))

            # print(vd)
            # print("Cohen_d: %.2f (s:%f ,p:%f)" % (cd, wlcx_s, wlcx_p))

            dyna_mean = target_df[target_df["configuration_id"]=="DynaMOSA"][data_point].mean()
            pva_mean = target_df[target_df["configuration_id"]=="PVADynaMOSA"][data_point].mean()
            # print("{}: {}".format("DynaMOSA", dyna_mean))
            # print("{}: {}".format("PVADynaMOSA", pva_mean))

            # print("\n---------------------------\n")

            estimate = float(vd["estimate"][0])
            magnitude = vd["magnitude"][0]

            result.loc[count] = [target, data_point_format[data_point].format(data_point_fn[data_point](dyna_mean)), data_point_format[data_point].format(data_point_fn[data_point](pva_mean)), "{:.2f}".format(estimate), magnitude, "{:.3f}".format(wlcx_p)]

            if estimate > 0.5:
                higher += 1
                if wlcx_p <= 0.05:
                    significant_diff["higher"].append(target)
            elif estimate < 0.5:
                lower += 1
                if wlcx_p <= 0.05:
                    significant_diff["lower"].append(target)
            else:
                same += 1

            total += estimate
            count += 1

        result.index += 1
        result.to_csv("evaluated_results_{}.csv".format(data_point))
        print("---------{}---------".format(data_point))
        print("higher: {}, lower: {}, same: {}".format(higher, lower, same))
        print(" avg: {}".format(total/count))

        print("significant_diff:")
        print(significant_diff)
        print("----------------------------")

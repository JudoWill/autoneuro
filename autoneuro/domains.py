# AUTOGENERATED! DO NOT EDIT! File to edit: 03_domains.ipynb (unless otherwise specified).

__all__ = ['AbstractDomain', 'MemoryDomain', 'ExecutiveFunctionDomain']

# Cell
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sbn

from .calculators import TestCalculator


# Cell
from bokeh.transform import factor_cmap, factor_mark
from bokeh.models import BooleanFilter, CDSView, BoxAnnotation, Band, IndexFilter, BooleanFilter, FactorRange
from bokeh.models import Legend, LegendItem

from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from bokeh.layouts import gridplot, layout
from bokeh.io import show

# Cell

import os
from itertools import chain

class AbstractDomain(object):

    source = None
    data = None
    ranges = {}
    tools = "pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"

    def __init__(self, calculator):
        """

        Parameters
        ----------
        calculator : TestCalculator
        """

        self.calculator = calculator

    def _load_data(self):
        pass

    def load_data(self, data, mapping=None):
        self.data = self.calculator.process_dataframe(data, mapping=mapping)
        self._load_data()
        self.source = ColumnDataSource(self.data)

    def build_scatter_fig(self, x = None, y = None,
                          fig = None, scatter_kwargs = None):

        x_range = self.ranges.get(x, Range1d(-10, 10))
        y_range = self.ranges.get(y, Range1d(-10, 10))
        default = {'x_range': x_range, 'y_range': y_range, 'tools': self.tools}
        if fig is None:
            fig = figure(**default)
        elif type(fig) == dict:
            fig = figure(**fig, **default)

        scatter_kwargs = {} if scatter_kwargs is None else scatter_kwargs
        fig.scatter(x = x, y = y, source = self.source,
                    **scatter_kwargs)
        fig.xaxis.axis_label = x
        fig.yaxis.axis_label = y

        self.ranges[x] = fig.x_range
        self.ranges[y] = fig.y_range

        return fig



class MemoryDomain(AbstractDomain):


    @staticmethod
    def from_defaults(root_data = 'data/'):

        bvmt_test_definition = os.path.join(root_data, 'test_calculators/BVMT.yaml')
        bvmt_calc = TestCalculator.from_config(yaml.full_load(open(bvmt_test_definition)))

        heaton_norm_definition = os.path.join(root_data, 'norms/from_kate/heaton_bvmt.yaml')
        heaton_bvmt_calc = TestCalculator.from_config(yaml.full_load(open(heaton_norm_definition)))

        norman_regression_definition = os.path.join(root_data, 'norms/norman/norman_bvmt_regnorm.yaml')
        reg_calc = TestCalculator.from_config(yaml.full_load(open(norman_regression_definition)))

        full_bvmt_calc = bvmt_calc + heaton_bvmt_calc + reg_calc

        return MemoryDomain(full_bvmt_calc)

# Cell

class ExecutiveFunctionDomain(AbstractDomain):


    @staticmethod
    def from_defaults(root_data = 'data/'):

        norman_regression_definition = os.path.join(root_data, 'norms/norman/norman_stroop_regnorm.yaml')
        reg_calc = TestCalculator.from_config(yaml.full_load(open(norman_regression_definition)))

        full_exec_calc = reg_calc

        return ExecutiveFunctionDomain(full_exec_calc)
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
from sklearn.decomposition import TruncatedSVD

class AbstractDomain(object):

    source = None
    data = None
    ranges = {}
    _weights = 1
    tools = "pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"

    def __init__(self, calculator, final_fields, agg_method = 'SVD'):
        """

        Parameters
        ----------
        calculator : TestCalculator
        final_fields : list[str]
        aggmethod : str
        """

        self.calculator = calculator
        self.final_fields = final_fields
        self.agg_method = agg_method

    def _load_data(self):
        pass

    def load_data(self, data, mapping=None):
        self.data = self.calculator.process_dataframe(data, mapping=mapping)
        self._load_data()
        self.aggregate_scores()
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

    def aggregate_scores(self):

        if self.agg_method == 'SVD':
            ndata = self.data[self.final_fields].dropna()
            svd = TruncatedSVD(n_components=1, random_state=12)
            svd.fit(ndata)
            weights = np.abs(svd.components_[0, :]) # Deal with sign
            weights = weights / np.sum(weights) # Deal with scale
            self._weights = pd.Series(weights, index = self.final_fields)

            res = (weights*self.data[self.final_fields].values).sum(axis=1)
        elif self.agg_method == 'mean':
            res = self.data[self.final_fields].mean(axis=1)
        else:
            raise ValueError('Did not understand aggmethod: ' + self.agg_method)

        self.data['aggregated_score'] = res

    def build_aggscore_figures(self, fig = None, scatter_kwargs = None):

        if 'aggregated_score' not in self.data.columns:
            self.aggregate_scores()

        figs = []
        for col in self.final_fields:
            figs.append(self.build_scatter_fig(x = col, y = 'aggregated_score',
                                               scatter_kwargs=scatter_kwargs,
                                               fig=fig))

        return figs



# Cell


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

        final_fields = ['heaton_immediate', 'heaton_delay', 'heaton_recognition', 'heaton_retention',
                        'norman_immediate', 'norman_delay']

        return MemoryDomain(full_bvmt_calc, final_fields)

# Cell

class ExecutiveFunctionDomain(AbstractDomain):


    @staticmethod
    def from_defaults(root_data = 'data/'):

        norman_stroop = os.path.join(root_data, 'norms/norman/norman_stroop_regnorm.yaml')
        stroop_reg_calc = TestCalculator.from_config(yaml.full_load(open(norman_stroop)))

        norman_stroop = os.path.join(root_data, 'norms/norman/norman_stroop_regnorm.yaml')
        stroop_reg_calc = TestCalculator.from_config(yaml.full_load(open(norman_stroop)))


        full_exec_calc = stroop_reg_calc
        final_fields = ['norman_stroop_color', 'norman_stroop_word', 'norman_stroop_color_word']

        return ExecutiveFunctionDomain(full_exec_calc, final_fields)
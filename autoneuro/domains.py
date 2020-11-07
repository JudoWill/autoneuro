# AUTOGENERATED! DO NOT EDIT! File to edit: 03_domains.ipynb (unless otherwise specified).

__all__ = ['LoadRawAndNormMixin', 'AbstractTest', 'AbstractDomain', 'MemoryDomain']

# Cell
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sbn

from autoneuro import core
from .core import build_from_yaml


# Cell

from sklearn.base import BaseEstimator

class LoadRawAndNormMixin(object):

    raw = None
    norm = None
    fields = None
    transforms = []


    def _extract_raw(self, data, mapping = None):
        """

        Parameters
        ----------
        data : pd.DataFrame
        mapping : dict
          Renaming mapping

        Returns
        -------
        None
        """

        if mapping is not None:
            ndata = data.rename(columns=mapping)
            self.raw = ndata[self.fields].copy()
        else:
            self.raw = data.reindex(self.fields, axis=1).copy()


    def _normalize_data(self):

        norm = {}
        for transform in self.transforms:
            res = transform.transform(self.raw)
            if type(res) == pd.DataFrame:
                for col in res.columns:
                    norm[col] = res[col]
            else:
                norm[transform.name] = res

        self.norm = pd.DataFrame(norm)


    #def load_data(self, data, mapping=None):

        #self._extract_raw(data, mapping=mapping)
        #self._normalize_data()

    def _normalize_data(self):

        norm = {}
        for transform in self.transforms:
            res = transform.transform(self.raw)
            if type(res) == pd.DataFrame:
                for col in res.columns:
                    norm[col] = res[col]
            else:
                norm[transform.name] = res

        self.norm = pd.DataFrame(norm)


    def load_data(self, data, mapping=None, missing='raise'):

        if set(self.fields).issubset(set(data.columns) | set(mapping.values())) | (missing == 'ignore'):

            self._extract_raw(data, mapping=mapping)
            self._normalize_data()
        else:
            missing = sorted(set(self.fields) - set(data.columns))
            raise KeyError(f'Missing {missing} fields.')


class AbstractTest(LoadRawAndNormMixin):



    def __init__(self, transforms):
        """

        Parameters
        ----------
        fields : list[str]
        transforms : list
        """

        self.transforms = list(transforms)
        self.fields = sum((tf.needed_cols for tf in self.transforms), [])
        self.fields = sorted(set(self.fields))

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

class AbstractDomain(LoadRawAndNormMixin):

    source = None
    data = None
    ranges = {}
    tools = "pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"

    def __init__(self, tests):
        """

        Parameters
        ----------
        tests : list[AbstractTest]
        """

        self.tests = tests

        self.fields = sum((test.fields for test in self.tests), [])
        self.fields = sorted(set(self.fields))

    @property
    def transforms(self):
        return chain.from_iterable(test.transforms for test in self.tests)


    def check_reasonableness(self, drop=True):

        extreme = (self.norm.abs() > 8).any(axis=1)
        if extreme.any():
            print('EXTREME OUTLIERS FOUND!')
            #print(self.raw.loc[extreme])
            #print(self.norm.loc[extreme])
            if drop:
                print('Dropping')
                self.raw.drop(extreme[extreme].index, inplace=True)
                self.norm.drop(extreme[extreme].index, inplace=True)

    def _prep_figs(self):
        pass

    def prep_figs(self):

        self._prep_figs()
        self.source = ColumnDataSource(self.norm)


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

        kate_tests =  list(build_from_yaml(os.path.join(root_data,
                                                   'norms/from_kate/BVMTR/description.yaml')))
        kate_tests += list(build_from_yaml(os.path.join(root_data,
                                                   'norms/from_kate/HVLTR/description.yaml')))

        heaton_transform = core.EncodingTransform(replacements = {'Sex': {1: 0,
                                                              2: 1},
                                                      'Race': {2: 'AA',
                                                               1: 'White'}},
                                      renames = {'Sex': 'heaton_gender',
                                                 'Race': 'RaceCat',
                                                 'BVMTimmed': 'BVMTtotalrecal',
                                                 'HVLT.total': 'HVLTtotalrecal'
                                                  })

        heaton_normer = core.ScaledRegressionTransform.from_yaml(['data/norms/heaton/heaton_AA_BVMTdelay.yaml',
                                                                  'data/norms/heaton/heaton_AA_BVMTtotalrecall.yaml',
                                                                  'data/norms/heaton/heaton_White_BVMTdelay.yaml',
                                                                  'data/norms/heaton/heaton_White_BVMTtotalrecall.yaml',
                                                             ], transform=heaton_transform)
        #AbstractTest([heaton_normer])
        return MemoryDomain([AbstractTest(kate_tests)])

    def build_delay_fig(self, fig_kwargs = None):
        kwargs = {'title': 'Correlated metrics?'}
        fig_kwargs = {} if fig_kwargs is None else fig_kwargs
        kwargs.update(fig_kwargs)

        return self.build_scatter_fig(x = 'BVMTdelay', y = 'HVLTdelay',
                                      fig = kwargs, scatter_kwargs = None)

    def build_delay_immed_fig(self, fig_kwargs = None):
        kwargs = {'title': 'BVMT Immed vs delay'}
        fig_kwargs = {} if fig_kwargs is None else fig_kwargs
        kwargs.update(fig_kwargs)

        return self.build_scatter_fig(x = 'BVMTimmed', y = 'BVMTdelay',
                                      fig = kwargs, scatter_kwargs = None)

    def build_immed_recog_fig(self, fig_kwargs = None):
        kwargs = {'title': 'BVMT Immed vs recog'}
        fig_kwargs = {} if fig_kwargs is None else fig_kwargs
        kwargs.update(fig_kwargs)

        return self.build_scatter_fig(x = 'BVMTimmed', y = 'BVMTrecog',
                                      fig = kwargs, scatter_kwargs = None)


    def build_figs(self, fig_kwargs=None):

        self.prep_figs()

        delay_fig = self.build_delay_fig(fig_kwargs=fig_kwargs)
        delay_immed_fig = self.build_delay_immed_fig(fig_kwargs=fig_kwargs)
        immed_recog_fig = self.build_immed_recog_fig(fig_kwargs=fig_kwargs)

        return delay_fig, delay_immed_fig, immed_recog_fig
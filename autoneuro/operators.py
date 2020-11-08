# AUTOGENERATED! DO NOT EDIT! File to edit: 01_operators.ipynb (unless otherwise specified).

__all__ = ['AbstractOperation', 'EquationOp', 'AggregationOp', 'ClipOp', 'NormativeLookupOp', 'BinnedScalingOp',
           'CategoricalOp', 'RegressionNormOp']

# Cell
#export
import pandas as pd
import numpy as np
import numexpr as ne

# Cell
#export
class AbstractOperation(object):

    fields = []
    result_fields = []

    @staticmethod
    def from_config(config):
        op_classes = [EquationOp,
                      AggregationOp,
                      ClipOp,
                      NormativeLookupOp,
                      CategoricalOp,
                      BinnedScalingOp,
                      RegressionNormOp]

        for op_class in op_classes:
            op = op_class.from_config(config)
            if op is not None:
                return op
        raise NotImplementedError(f'Did not understand type: {config["type"]}')
        #return None

    def process_single(self, row):
        raise NotImplementedError

    def explain(self, row):
        raise NotImplementedError


    def to_series(self, row):

        series = pd.Series(dict((field, row.get(field)) for field in self.fields))
        return series

    def __call__(self, row):

        res = self.process_single(row)
        yield self.result_fields[0], res

# Cell
class EquationOp(AbstractOperation):
    "Manipulate values with 1numexpr1 equations."

    def __init__(self, out_field, equation, fields):
        """

        Parameters
        ----------
        out_field : str
        equation : str
        fields : list[str]
        """

        self.fields = fields
        self.equation = equation
        self.result_fields = [out_field]

    @staticmethod
    def from_config(config):
        """

        Expecting yaml of the format:
          type: equation
          equation: "hits-false_pos"
          fields: ['hits', 'false_pos']
          out_field: 'recognition'

        Parameters
        ----------
        config : dict

        Returns
        -------
        EquationOp
        """
        if config['type'] == 'equation':
            return EquationOp(config['out_field'],
                              config['equation'],
                              config['fields'])
        return None

    def explain(self, row):
        """

        Parameters
        ----------
        row : dict,pd.Series

        Returns
        -------
        str
        """

        res = self.process_single(row)
        return f'Used Equation: {self.equation} = {res} = {self.result_fields[0]}'

    def process_single(self, row):
        """ Apply the equation to the row

        Parameters
        ----------
        row : mapping

        Returns
        -------
        float

        """

        data = self.to_series(row)
        #print(data)
        if data.notnull().all():
            res = pd.eval(self.equation, local_dict=data.to_dict())
        else:
            res = np.nan
        return res

# Cell

class AggregationOp(AbstractOperation):

    def __init__(self, out_field, aggregation, fields):
        """

        Parameters
        ----------
        out_field : str
        aggregation : str
        fields : list[str]
        """

        self.fields = fields
        self.aggregation = aggregation
        self.result_fields = [out_field]

    @staticmethod
    def from_config(config):
        """
        Load from config. Expects:
            type: agg
            method: 'max'
            fields: ['trial2', 'trial3']
            out_field: retention_denom

        Parameters
        ----------
        config : dict

        Returns
        -------
        AggregationOp
        """
        if config['type'] == 'agg':
            return AggregationOp(config['out_field'],
                                 config['method'],
                                 config['fields'])
        return None

    def explain(self, row):
        res = self.process_single(row)
        return f'Aggregation: {self.aggregation} [{", ".join(self.fields)}]  = {res}'

    def process_single(self, row):
        data = self.to_series(row)
        return data.agg(self.aggregation)

# Cell
class ClipOp(AbstractOperation):

    def __init__(self, field, lower = 0, upper=1):
        """

        Parameters
        ----------
        field : str
        lower : float
        upper : float
        """

        self.fields = [field]
        self.lower = lower
        self.upper = upper
        self.result_fields = [field]

    @staticmethod
    def from_config(config):
        """
        Load from config. Expects:
            type: clip
            field: retention
            lower: 0
            upper: 1
        Parameters
        ----------
        config

        Returns
        -------
        ClipOp

        """
        if config['type'] == 'clip':
            return ClipOp(config['field'],
                          lower = config['lower'],
                          upper = config['upper'])
        return None

    def explain(self, row):
        return f'Clipped {self.fields[0]} to [{self.lower}, {self.upper}]'

    def process_single(self, row):

        data = self.to_series(row)
        clipped = data.clip(lower=self.lower, upper=self.upper)
        return clipped[self.result_fields[0]]

# Cell

class NormativeLookupOp(AbstractOperation):
    """Lookup table with normalized scores."""

    def __init__(self, lookup_table, filter_cols, measure_col, out_name):

        self.lookup_table = lookup_table
        self.filter_cols = filter_cols
        self.fields = filter_cols + [measure_col]
        self.result_fields = [out_name]
        self.measure_col = measure_col

    @staticmethod
    def from_config(config):

        if config['type'] == 'normative_lookup':

            return NormativeLookupOp(config['table'],
                                     config['filter_cols'],
                                     config['measure_col'],
                                     config['out_name'])
        return None

    def lookup_norm(self, row):

        data = self.to_series(row)
        for filt in self.lookup_table:
            if ne.evaluate(filt['filter'], local_dict=data):
                return filt['filter'], filt['mean'], filt['std']

        return None, None, None

    def explain(self, row):

        flt, mean, std = self.lookup_norm(row)

        if flt is None:
            data = self.to_series(row)
            return f'Could not find matching filter for {data[self.filter_cols]}'
        else:
            return f'Matched {flt}, Expecting {mean} +- {std}'

    def process_single(self, row):

        data = self.to_series(row)
        _, mean, std = self.lookup_norm(data)
        if mean is None:
            return np.nan
        return (data[self.measure_col] - mean)/std

# Cell

class BinnedScalingOp(AbstractOperation):
    def __init__(self, bins, measure_col, out_field = None):


        self.fields = [measure_col]
        if out_field is None:
            self.result_fields = [measure_col+'_scaled']
        else:
            self.result_fields = [out_field]
        self.bins = sorted(bins, key = lambda x: x['min'],
                           reverse=True)

    @staticmethod
    def from_config(config):
        """
        Build from config, Expecting yaml like:
          type: binned_scaling
          measure_col: delay
          bins:
            - scaled: 14
              min: 12
            - scaled: 11
              min: 11
            - scaled: 9
              min: 10

        Parameters
        ----------
        config

        Returns
        -------
        BinnedScalingOp

        """

        if config['type'] == 'binned_scaling':
            return BinnedScalingOp(config['bins'],
                                   config['measure_col'])
        return None

    def lookup_bin(self, row):

        data = self.to_series(row)
        val = data[self.fields[0]]
        if val == val:
            for bin in self.bins:
                if val >= bin['min']:
                    return bin['min'], bin['scaled']
            return np.nan, np.nan
        else:
            return np.nan, np.nan

    def explain(self, row):

        edge, scaled = self.lookup_bin(row)

        if edge != edge:
            data = self.to_series(row)
            return f'Could not find matching bin for {data[self.fields[0]]}'
        else:
            return f'{self.fields[0]} matched {edge}, scaled to {scaled}'

    def process_single(self, row):
        _, res = self.lookup_bin(row)
        return res

# Cell

class CategoricalOp(AbstractOperation):

    def __init__(self, measure_col, mapping, out_col):

        self.result_fields = [out_col]
        self.mapping = mapping
        self.fields = [measure_col]

    @staticmethod
    def from_config(config):
        """
        Build from config. Expects yaml like:
          type: categorical
          in_field: gender
          out_field: norman_gender
          mapping:
            male: 0
            female: 1

        Parameters
        ----------
        config : dict

        Returns
        -------

        """

        if config['type'] == 'categorical':
            return CategoricalOp(config['in_field'],
                                 config['mapping'],
                                 config['out_field'])
        return None

    def lookup(self, row):

        data = self.to_series(row)
        return self.mapping.get(data[self.fields[0]])

    def process_single(self, row):

        return self.lookup(row)

    def explain(self, row):

        res = self.lookup(row)
        if res is not None:
            return f'{self.fields[0]}:{row[self.fields[0]]} -> {self.result_fields[0]}:{res}'
        else:
            return f'Could not match {self.fields[0]}:{row[self.fields[0]]}'

# Cell
class RegressionNormOp(AbstractOperation):

    def __init__(self, fields, regressions, out_field, result_type = 'zscale'):

        self.regressions = regressions
        self.fields = fields
        self.result_fields = [out_field]
        self.result_type = result_type

    @staticmethod
    def from_config(config):
        if config['type'] == 'regression_norm':
            return RegressionNormOp(config['fields'],
                                    config['regressions'],
                                    config['out_field'],
                                    result_type = config['result_type'])

        return None

    def search_filters(self, row):

        data = self.to_series(row)
        check_func = lambda reg: pd.eval(reg['filter'], local_dict=data.to_dict())
        return [reg for reg in self.regressions if check_func(reg)]

    def scale_data(self, row):

        data = self.to_series(row)
        hits = self.search_filters(row)
        if hits: #Currently only implementing "first"
            reg = hits[0]
            val = pd.eval(reg['norm'], local_dict=data.to_dict())
            return reg, val
        return None, None


    def explain(self, row):

        data = self.to_series(row)
        reg, val = self.scale_data(row)

        if reg is None:
            return 'Could not find a match for regression normalization.'
        else:
            return f'Matched {reg["filter"]}, applied {reg["norm"]} = {float(val)}'


    def process_single(self, row):

        _, val = self.scale_data(row)
        return val
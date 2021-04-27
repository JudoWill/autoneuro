# AUTOGENERATED! DO NOT EDIT! File to edit: 01_operators.ipynb (unless otherwise specified).

__all__ = ['AbstractOperation', 'EquationOp', 'AggregationOp', 'ClipOp', 'AbstractNormative', 'MeanStdNormative',
           'NormativeLookupOp', 'LookupNormative', 'BinnedScalingOp', 'CategoricalOp', 'EquationFilterOp',
           'MultiLookupOp', 'HEATON_MAPPINGS', 'ReverseLookupOp']

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

    origin = 'autoneuro_calculation'
    section = None
    internal_field = None
    calculation = None
    field_type = None

    @staticmethod
    def from_config(config):
        op_classes = [EquationOp,
                      AggregationOp,
                      ClipOp,
                      NormativeLookupOp,
                      CategoricalOp,
                      BinnedScalingOp,
                      EquationFilterOp]

        for op_class in op_classes:
            op = op_class.from_config(config)
            if op is not None:
                op.parse_info(config.get('info', {}))
                return op
        raise NotImplementedError(f'Did not understand type: {config["type"]}')
        #return None

    def process_single(self, row):
        raise NotImplementedError

    def explain(self, row):
        raise NotImplementedError

    def to_config(self):
        raise NotImplementedError

    def parse_info(self, info):

        fields = ['internal_field', 'calculation',
                  'origin', 'section']
        for f in fields:
            if f in info:
                setattr(self, f, info[f])


    def to_field_mapping(self):

        info = {'internal_field': self.internal_field,
                'calculation': self.calculation,
                'origin': self.origin,
                'section': self.section}


        return pd.Series(info)


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

        self.internal_field = out_field
        self.calculation = equation

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

    def to_config(self):

        return {'type': 'equation',
                'out_field': self.result_fields[0],
                'equation': self.equation,
                'fields': self.fields}



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
            res = pd.eval(self.equation, local_dict=data.to_dict(), truediv=True)
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

        self.internal_field = out_field
        self.calculation = f'{aggregation} of {fields}'


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

    def to_config(self):

        return {'type': 'agg',
                'out_field': self.result_fields[0],
                'method': self.aggregation,
                'fields': self.fields}


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

        self.internal_field = field
        self.calculation = f'clipping {field} to [{lower}, {upper}]'


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

    def to_config(self):

        return {'type': 'clip',
                'lower': self.lower,
                'upper': self.aggregation,
                'field': self.fields[0]}

    def explain(self, row):
        return f'Clipped {self.fields[0]} to [{self.lower}, {self.upper}]'

    def process_single(self, row):

        data = self.to_series(row)
        clipped = data.clip(lower=self.lower, upper=self.upper)
        return clipped[self.result_fields[0]]

# Cell
# hide


class AbstractNormative(object):

    flt = None

    def to_config(self):
        raise NotImplementedError

    @staticmethod
    def from_config(config):
        for cl in [MeanStdNormative, LookupNormative]:
            obj = cl.from_config(config)
            if obj is not None:
                return obj
        raise ValueError(f'Could not understand config: {config}')


    def explain(self, value): raise NotImplementedError

    def scale(self, data): raise NotImplementedError


    def is_valid(self, data):
        return ne.evaluate(self.flt, local_dict=data)



# Cell

class MeanStdNormative(AbstractNormative):
    """Deal with mean/std scaled -> percentile lookup tables"""

    def __init__(self, flt, mean, std):
        self.flt = flt
        self.mean, self.std = mean, std


    @staticmethod
    def from_config(config):
        if ('mean' in config) and ('std' in config):
            return MeanStdNormative(config['filter'],
                                    config['mean'],
                                    config['std'])
        return None

    def to_config(self):

        return {'type': 'mean_std',
                'filter': self.filter,
                'mean': self.mean, 'std': self.std}

    def scale(self, value):
        return (value-self.mean)/self.std

    def explain(self, value):

        scaled = self.scale(value)
        matched = f'Matched: {self.flt}'
        calculated = f'Expected {self.mean}+/-{self.std} but observed {value}'
        result = f'Scaled to: z={scaled}'
        return '\n'.join([matched, calculated, result])

# Cell

class NormativeLookupOp(AbstractOperation):
    """Lookup table with normalized scores."""

    def __init__(self, lookup_table, filter_cols, measure_col, out_name):

        self.lookup_table = lookup_table
        self.filter_cols = filter_cols
        self.fields = filter_cols + [measure_col]
        self.result_fields = [out_name]
        self.measure_col = measure_col

        self.internal_field = out_name
        self.calculation = f'Normative table lookup of {measure_col} using {filter_cols}'


    @staticmethod
    def from_config(config):

        if config['type'] == 'normative_lookup':

            return NormativeLookupOp([AbstractNormative.from_config(row) for row in config['table']],
                                     config['filter_cols'],
                                     config['measure_col'],
                                     config['out_name'])
        return None

    def to_config(self):

        return {'type': 'normative_lookup',
                'table': [norm.to_config() for norm in self.lookup_table],
                'filter_cols': self.filter_cols,
                'measure_col': self.measure_col,
                'out_name': self.result_fields[0]}

    def lookup_norm(self, row):

        data = self.to_series(row)
        for norm in self.lookup_table:
            if norm.is_valid(data):
                return norm

        return None

    def explain(self, row):

        norm = self.lookup_norm(row)
        data = self.to_series(row)

        if norm is None:
            return f'{self.result_fields[0]}: Could not find matching filter for {data[self.filter_cols]}'
        else:
            return norm.explain(data[self.measure_col])

    def process_single(self, row):

        data = self.to_series(row)
        norm = self.lookup_norm(data)
        if norm is None:
            return np.nan
        r = norm.scale(data[self.measure_col])
        return r

# Cell
import scipy.stats as st

class LookupNormative(AbstractNormative):
    """Deal with scaled -> percentile lookup tables"""

    def __init__(self, flt, mapping, post = None):
        self.flt = flt
        self.mapping = mapping # A dict {'raw': 'scaled', 'raw': 'scaled'}
        self.post = post

    @staticmethod
    def from_config(config):
        if ('mapping' in config):
            return LookupNormative(config['filter'],
                                   config['mapping'],
                                   post = config.get('post', None))
        return None

    def to_config(self):

        return {'type': 'lookup',
                'filter': self.filter,
                'mapping': self.mapping,
                'post': self.post}

    def scale(self, value):
        try:
            scaled = self.mapping[value]
        except KeyError:
            return np.nan

        if self.post == 'leave':
            pass
        elif self.post == 'ss2z':
            # standard (50/10) to Z (0/1)
            scaled = (scaled - 50)/10
        elif self.post == 'percentile2z':
            scaled = st.norm.ppf(scaled/100)
        elif self.post == 'scaled2z':
            # sscaled (10/3) to Z (0/1)
            scaled = (scaled-10)/3

        return scaled

    def explain(self, value):

        try:
            mapped = self.mapping[value]
        except KeyError:
            mapped = 'missing'
        scaled = self.scale(value)

        matched = f'Matched: {self.flt}'
        calculated = f'Mapped to: {mapped}'
        if (self.post is None) or (self.post == 'leave'):
            result = ''
        else: result = f'Scaled to: z={scaled}'

        return '\n'.join([matched, calculated, result])

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

        self.internal_field = self.result_fields[0]
        self.calculation = f'Table based scaling lookup of {measure_col}.'



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

    def to_config(self):

        return {'type': 'binned_scaling',
                'bins': self.bins,
                'measure_col': self.measure_col}

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

        self.internal_field = out_col
        self.calculation = f'Categorical mapping of {measure_col} to {out_col}.'

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

    def to_config(self):

        return {'type': 'categorical',
                'in_field': self.fields[0],
                'mapping': self.mapping,
                'out_field': self.result_fields[0]}

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
class EquationFilterOp(AbstractOperation):

    def __init__(self, fields, regressions, out_field, result_type = 'zscale'):

        self.regressions = regressions
        self.fields = fields
        self.result_fields = [out_field]
        self.result_type = result_type

        self.internal_field = out_field
        self.calculation = f'Regression based normalization using {self.fields} to create {out_field}.'

    @staticmethod
    def from_config(config):
        if config['type'] == 'equation_filter':
            return EquationFilterOp(config['fields'],
                                    config['equations'],
                                    config['out_field'],
                                    result_type = config['result_type'])

        return None

    def to_config(self):

        return {'type': 'equation_filter',
                'fields': self.fields,
                'equations': self.regressions,
                'result_type': self.result_type,
                'out_field': self.result_fields[0]}

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

            if (self.result_type == 'standard_score') | (self.result_type == 'tscore'):
                val = (val - 50)/10
            elif (self.result_type  == 'zscore') | (self.result_type  == 'zscale'):
                pass
            elif self.result_type == 'other':
                pass
            else:
                raise ValueError(f'Did not understand result_type: {self.result_type}')

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

# Cell

class MultiLookupOp(NormativeLookupOp):

    def __init__(self, lookup_table, filter_cols, measure_col, out_name):

        self.lookup_table = lookup_table
        self.filter_cols = filter_cols
        self.fields = filter_cols + [measure_col]
        self.result_fields = [out_name]
        self.measure_col = measure_col

        self.internal_field = out_name
        self.calculation = f'Table based normative lookup of {measure_col} using {self.fields}.'


    def incoperate(self, other):

        self.lookup_table += other.lookup_table


    @staticmethod
    def from_sheet_format(path, filter_mappings, filter_cols,
                          measure_col, out_name, post = 'ss2z', extra_filter = None):

        data = pd.read_csv(path)
        scale_cols = [col for col in data.columns if col not in filter_mappings]

        lookup_table = []

        for _, row in data.iterrows():
            flt = []
            for col, mapping in filter_mappings.items():
                flt.append(mapping[row[col]])
            flt = ' & '.join(f'({fl})' for fl in flt)

            if extra_filter is not None:
                flt = f'({extra_filter}) & ({flt})'

            lookup_table.append(LookupNormative(flt,
                                                dict((int(sc), row[sc]) for sc in scale_cols),
                                                post = post))

        return MultiLookupOp(lookup_table, filter_cols,
                             measure_col, out_name)



# Cell
# hide

HEATON_MAPPINGS = {'Age':{1: '(0 < age) & (age < 35)',
                          2: '(35 <= age) & (age < 40)',
                          3: '(40 <= age) & (age < 45)',
                          4: '(45 <= age) & (age < 50)',
                          5: 'age >= 50'},
                   'Education':{1: '(0 < education) & (education <= 9)',
                                2: '(9 < education) & (education <= 12)',
                                3: '(12 < education) & (education <= 13)',
                                4: '(13 < education) & (education <= 16)',
                                5: '(16 < education) & (education <= 18)',
                                6: '(education > 18)',
                               },
                   'Gender': {1: 'heaton_gender == 1',
                              2: 'heaton_gender == 2'}}

# Cell

class ReverseLookupOp(MultiLookupOp):


    @staticmethod
    def from_sheet_format(path, measure_col, out_name,
                          filter_col = 'age',
                          post = 'scaled2z'):


        lookup_table = []

        with open(path) as handle:

            r1, r2 = next(handle).strip(), next(handle).strip()
            r1, r2 = r1.split(','), r2.split(',')

            df = pd.read_csv(handle, low_memory=False)
            val_cols = df.columns[1:]
            scaled_col = df.columns[0]

            for lower, upper, val_col in zip(r1[1:], r2[1:], val_cols):
                flt = f'({lower} <= {filter_col}) & ({filter_col} < {upper})'
                mapping = {}
                items = df[[scaled_col, val_col]].dropna()
                for _, row in items.iterrows():
                    mapping[row[val_col]] = row[scaled_col]

                lookup_table.append(LookupNormative(flt,
                                                    dict(mapping.items()),
                                                    post = post))


        return ReverseLookupOp(lookup_table, [filter_col],
                             measure_col, out_name)

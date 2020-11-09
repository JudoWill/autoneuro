# AUTOGENERATED! DO NOT EDIT! File to edit: 00_calculators.ipynb (unless otherwise specified).

__all__ = ['AbstractCalculator', 'TestCalculator']

# Cell
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sbn
import numexpr as ne

from autoneuro import operators


# Cell
class AbstractCalculator(object):
    fields = []
    operations = []
    inferred_cols = []

    def __init__(self, name, operations):
        """

        Parameters
        ----------
        name : list[str]
        operations : list[AbstractOperation]
        """

        self.name = name
        self.operations = operations

        fields = sum((op.fields for op in operations), start = [])
        fields = set(fields)

        inferred = sum((op.result_fields for op in operations), start = [])
        inferred = set(inferred)

        self.fields = sorted(fields-inferred)
        self.inferred_cols = sorted(inferred)

    def to_series(self, row):

        series = pd.Series(dict((field, row.get(field)) for field in self.fields))
        return series

    def explain(self, row):

        ins = [f'{f}:{row[f]}' for f in self.fields]
        print('Taking:', ', '.join(ins))

        res = self.process_single(row, explain=True)
        outs = [f'{f}:{res[f]}' for f in self.inferred_cols]
        print('Resulting in:', ', '.join(outs))

    def __add__(self, other):

        return AbstractCalculator(self.name, self.operations+other.operations)

    def process_single(self, row, explain=False):
        """

        Parameters
        ----------
        row : pd.Series,dict
        explain : bool

        Returns
        -------

        """

        data = self.to_series(row)
        if self.operations:
            for operation in self.operations:
                for field, val in operation(data):
                    data[field] = val
                if explain:
                    print(operation.explain(data))

            #print(data)
        return pd.Series(data)


    def process_dataframe(self, df, mapping = None):
        """

        Parameters
        ----------
        df : pd.DataFrame
        mapping : dict
        Returns
        -------
        pd.DataFrame

        """

        if mapping is not None:
            clean_data = df.rename(columns=mapping)
        else:
            clean_data = df

        #print(clean_data[self.fields])

        res = clean_data.apply(self.process_single, axis=1)
        return res

# Cell

class TestCalculator(AbstractCalculator):

    def __init__(self, name, operations):
        super().__init__(name, operations)

    @staticmethod
    def from_config(config):
        name = config['short_name']
        ops = [operators.AbstractOperation.from_config(c) for c in config['operations']]
        return TestCalculator(name, ops)
import pandas as pd
import matplotlib.pyplot as plot

class History:
    def __init__(self):
        self.file = './data/history.csv'
        self.delimiter = '\t'

    def read(self):
        df = pd.read_csv(self.file, sep=self.delimiter, index_col='Date')  
        return df

    def add_date(self, date, below, above, total):
        df = self.read()
        df.loc[date] = [below, above, total]
        df.to_csv(self.file, sep=self.delimiter, encoding='utf-8', header='true')

    def show_plot(self):
        df = self.read()
        df.plot.area(stacked=False)
        plot.show()

    def save_plot(self, output_file):
        df = self.read()
        df.plot.area(stacked=False)
        plot.savefig(output_file)
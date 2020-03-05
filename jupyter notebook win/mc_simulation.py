# script to import for running 'psa_cashflow_projection' multiprocessing on Windows

import numpy as np
import numpy_financial as npf
import pandas as pd

class PSAFinModel(object):
    """An object for calculating and modeling of financial data
    and cash flow of production sharing agreement
    """
    
    def __init__(self, prod_cap_op_cost, parameters_dict):
        """Input data:
        """
        self.prod_cap_op_cost = prod_cap_op_cost
        self.p = parameters_dict
    
        # cash-flow projection DataFrame
        self.df = pd.DataFrame(np.zeros((19,23)), index=[*range(1,20)])
        self.df.columns = [
            'Production (1,000 bbl)', 'Oil Price ($/bbl)', 'Gross Revenue ($m)',
            'Royalty ($m)', 'Net Revenue ($m)', 'Capital Costs ($m)',
            'Depreciation ($m)', 'Operating Cost ($/1000 bbl)',
            'Operating Expense ($m)', 'Total Expenses ($m)',
            'Cost Recovery Limit ($m)', 'C/R C/F ($m)', 'Cost Recovery ($m)',
            'Total Profit Oil ($m)', 'State Profit Oil Share ($m)',
            'IOC Profit Oil Share ($m)', 'Signature Bonus ($m)',
            'Taxable Income ($m)', 'Income Tax ($m)', 'IOC Net Cash Flow ($m)',
            'IOC DCF @ 12% (half-year)', 'State Net Cash Flow ($m)',
            'State DCF @ 12% (half-year)']
        self.df.index.name = 'Year'
        
        # project kpi DataFrame
        self.kpi = pd.DataFrame(np.zeros((6,3)),
                                columns=['IOC', 'State', 'Project'],
                                index=['CCF ($m)', 'NPV ($m)', 'IRR (%)',
                                       'PP (y)', 'DPP (y)', 'PI'])
        
        
    def get_ncf(self):
        """Step by step calculation of net cash flow of IOC and State
        """
        
        # Set input data
        self.df[['Production (1,000 bbl)', 'Capital Costs ($m)',
                 'Operating Cost ($/1000 bbl)']] = self.prod_cap_op_cost.values
        
        # Revenue
        # Set a price USD per bbl. for each year
        self.df['Oil Price ($/bbl)'] = self.p['Oil Price ($/bbl)']
        # Calculate Gross Revenue, in thousand USD
        self.df['Gross Revenue ($m)'] = self.df[['Production (1,000 bbl)',
                                                 'Oil Price ($/bbl)']].\
                                                 prod(axis=1) # $m
        # Calculate Royalty and net Revenue
        self.df['Royalty ($m)'] = self.df['Gross Revenue ($m)'].\
                                  multiply(self.p['Royalty Rate'])
        self.df['Net Revenue ($m)'] = self.df['Gross Revenue ($m)'] - \
                                      self.df['Royalty ($m)']
        
        # Capital Costs and Depreciation
        # Find first of operation year (lets play algo)
        prod_gt0 = (self.df['Production (1,000 bbl)'] > 0)
        first_year_of_operation = self.df.index[prod_gt0][0]
        # Calculate depreciation, starting no earlier than 1st year of operation
        depr_schedule = pd.DataFrame(0., index=self.df.index,
                         columns=self.df.index[self.df['Capital Costs ($m)']>0])
        # Assign yearly depreciation values
        depr_schedule.loc[1:self.p['Depreciation Term'],:] = \
                        self.df['Capital Costs ($m)'].\
                        where(self.df['Capital Costs ($m)']>0) / \
                        self.p['Depreciation Term']
        # Shift depreciation to proper years
        depr_schedule = depr_schedule.apply(lambda x: 
                                            x.shift(max(first_year_of_operation,
                                                        x.name) - 1,
                                                    fill_value=0), axis=0)
        # Finally, sum all depreciation schedule into net Depreciation
        self.df['Depreciation ($m)'] = depr_schedule.sum(axis=1)
 
        # Operating Costs
        # Calculate Operating Expense 
        self.df['Operating Expense ($m)'] = self.df[['Production (1,000 bbl)', 
                                   'Operating Cost ($/1000 bbl)']].prod(axis=1)
        # Total Expense
        self.df['Total Expenses ($m)'] = self.df[['Operating Expense ($m)',
                                              'Depreciation ($m)']].sum(axis=1)

        # Cost Recovery
        self.df['Cost Recovery Limit ($m)'] = self.df['Gross Revenue ($m)'] * \
                                              self.p['Cost Recovery Limit']
        # Cost Recovery Carry Forward
        self.df['C/R C/F ($m)'] = (self.df['Total Expenses ($m)'] - 
                                   self.df['Cost Recovery Limit ($m)']).\
                                   cumsum().clip(lower=0)

        self.df['Cost Recovery ($m)'] = np.minimum(
                                          self.df['Total Expenses ($m)'] + 
                                          self.df['C/R C/F ($m)'].\
                                                shift(1, fill_value=0),
                                          self.df['Cost Recovery Limit ($m)'])  
        
        # Profit Oil
        # Calculate Profit Oil
        self.df['Total Profit Oil ($m)'] = self.df['Net Revenue ($m)'] - \
                                           self.df['Cost Recovery ($m)']
        # Calculate split of profit oil between IOC and State
        self.df['State Profit Oil Share ($m)'] = \
                                            self.df['Total Profit Oil ($m)'] * \
                                            (1 - self.p['IOC Profit Oil Split'])
        self.df['IOC Profit Oil Share ($m)'] = \
                                            self.df['Total Profit Oil ($m)'] * \
                                            self.p['IOC Profit Oil Split']

        # Bonuses and Taxes of IOC
        # Signature bonus in case a PSA is signed
        self.df.at[1,'Signature Bonus ($m)'] = self.p['Signature Bonus']
        # Calculate operating income
        operating_income = (self.df[['Cost Recovery ($m)',
                                     'IOC Profit Oil Share ($m)']]\
                                                .sum(axis=1) -\
                            self.df[['Total Expenses ($m)',
                                     'Signature Bonus ($m)']].sum(axis=1))

        # Create function and calculate loss carry forward (no term limits)
        loss_carry_forward = np.frompyfunc(lambda a,b: a+b if a < 0
                                           else b, 2, 1)
        self.df['Taxable Income ($m)'] = loss_carry_forward.accumulate(
                                      operating_income.values, dtype=np.object)

        # Calculate Income Tax of IOC
        self.df['Income Tax ($m)'] = self.df['Taxable Income ($m)']\
                                  .multiply(self.p['Income Tax']).clip(lower=0)
            
        # IOC Free Cash Flow
        self.df['IOC Net Cash Flow ($m)'] = (self.df[['Cost Recovery ($m)',
                                    'IOC Profit Oil Share ($m)']].sum(axis=1) -\
                                             self.df[['Capital Costs ($m)',
                                                      'Operating Expense ($m)',
                                                      'Signature Bonus ($m)',
                                                      'Income Tax ($m)']]\
                                                  .sum(axis=1))
        self.df['IOC DCF @ 12% (half-year)'] = \
                            self.df['IOC Net Cash Flow ($m)'] / \
                            (1 + self.p['Discount Rate'])**(self.df.index - 0.5)

        # State Free Cash Flow
        self.df['State Net Cash Flow ($m)'] = \
          self.df[['Signature Bonus ($m)', 'Royalty ($m)',
                   'State Profit Oil Share ($m)','Income Tax ($m)']].sum(axis=1)
        self.df['State DCF @ 12% (half-year)'] = \
                             self.df['State Net Cash Flow ($m)'] / \
                            (1 + self.p['Discount Rate'])**(self.df.index - 0.5)
            
        return self.df[['IOC Net Cash Flow ($m)',
                        'IOC DCF @ 12% (half-year)',
                        'State Net Cash Flow ($m)',
                        'State DCF @ 12% (half-year)']]

    
    def get_kpi(self):
        """Module to calculate investment project indicators:
        Cumulative Cash Flow, Net Present Value, Internal Rate of Return,
        Payback Period, Discounted Payback Period, Profitability Index
        for investment decision making.
        """

        def payback_period(ts):
            """Function to calculate PP with for input time-series
            """
            if not (ts[ts.cumsum() > 0].empty | ts[ts.cumsum() < 0].empty):
                final_full_year = ts[ts.cumsum() < 0].index.values.max()
                fractional_yr = - ts.cumsum()[final_full_year] / \
                                  ts[final_full_year + 1]
                pp = (final_full_year + fractional_yr)
                pp = round(pp, 1)
            elif ts[ts.cumsum() < 0].empty:
                pp = 0
            else:
                pp = np.nan
            return pp
        
        profitability_index = lambda ts:round(((ts>0)*(1-ts.cumsum()
                     / ts.cumsum().min())).max(), 1) if ts.min() < 0 else np.inf
        
        irr = lambda dcf: round(npf.irr(dcf)*100, 1) \
                                            if not np.isnan(npf.irr(dcf)) else 0

        # a loop to get kpi values
        for i, (cf, dcf) in enumerate([(self.df['IOC Net Cash Flow ($m)'],
                                        self.df['IOC DCF @ 12% (half-year)']),
                                    (self.df['State Net Cash Flow ($m)'],
                                     self.df['State DCF @ 12% (half-year)']),
                        (self.df[['IOC Net Cash Flow ($m)',
                                  'State Net Cash Flow ($m)']].sum(axis=1),
                         self.df[['IOC DCF @ 12% (half-year)',
                                  'State DCF @ 12% (half-year)']].sum(axis=1))
                                    ]):
            self.kpi.iloc[:,i] = [round(cf.sum(), 1),
                                  round(dcf.sum(), 1),
                                  irr(cf),
                                  payback_period(cf),
                                  payback_period(dcf),
                                  profitability_index(dcf)]
        self.kpi.index.name = 'Parameter'
       
        return self.kpi


# Set input parameters
# Dictionary with major inputs
psa_parameters_dict = {
    'Oil Price ($/bbl)': 20,     # Oil price $20/bbl for the model estimation
    'Royalty Rate': 0.1,         # Royalty rate 10%
    'Cost Recovery Limit': 0.5,  # Up to 50% of Gross Revenue
    'IOC Profit Oil Split': 0.4, # IOC 40%/ State 60%
    'Income Tax': 0.3,           # CIT 30%
    'Signature Bonus': 1e7/1e3,  # Signature Bonus $10M
    'Depreciation Method': 'SL', # Straight Line depreciation of capital assets
    'Depreciation Term': 5,      # 5 years
    'Discount Rate': .12         # 12% discount rate
}

# DataFrame with input time-series
input_estimates = pd.DataFrame(
    {'Production (1,000 bbl)': [0, 0, 578, 6100, 9420, 12400, 10850, 9494, 8307,
                                7269,6360, 5565, 4869, 4261, 3728, 3262, 2854,
                                2498, 2185],
     'Capital Costs ($m)': [30000, 40000, 100000, 60000, 70000] + [0]*14,
     'Operating Cost ($/1000 bbl)': [0, 0, 5.5, 2.6, 2.4, 2.3, 2.36, 2.4, 2.46,
                                     2.54, 2.64, 2.72, 2.82, 2.94, 3.08, 3.24,
                                     3.4, 3.6, 3.4]
    },    
    index=[*range(1,20)]
                              )


def get_npv_irr(mcc, input_estimates=input_estimates,
                psa_parameters_dict=psa_parameters_dict):
    """Function to get NPV and IRR for each Monte Carlo path
    """

    # getting the previously set input parameters
    # global input_estimates, psa_parameters_dict
    res = []
    # make a copy for further adjustment
    for mc in mcc:
        psa_parameters_dict_mc = psa_parameters_dict.copy()
        input_estimates_mc = input_estimates.copy()

        # set the MC path values according to input 2D array
        psa_parameters_dict_mc['Oil Price ($/bbl)'] *= mc[0, 0]
        input_estimates_mc *= mc[:, :3]

        psa = PSAFinModel(prod_cap_op_cost=input_estimates_mc,
                          parameters_dict=psa_parameters_dict_mc)
        psa.get_ncf()
        res.append([psa.df['IOC DCF @ 12% (half-year)'].sum(),
            npf.irr(psa.df['IOC Net Cash Flow ($m)'])*100])
    return res
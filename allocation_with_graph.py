import pandas as pd
import numpy as np
import datetime as dt
import xlrd

fred = pd.read_csv('fredgraph.csv')
spxtr = pd.read_csv('SP500TR.csv')
rut = pd.read_csv('RUT.csv')
wilshire = pd.read_csv('W5000.csv')
damo = pd.read_excel('damo.xls')
damo2 = pd.read_excel('damo2.ods')

now = dt.datetime.now()
now_str = now.strftime('%Y-%m')
now_year = int(now_str[:4])
now_month = int(now_str[5:])
end_year = int(fred['DATE'].iloc[0][:4])

now = dt.datetime.now()
num_years_held = 10
start_year = now_year
#print('start_year:', start_year)
#print('end_year:', end_year)
start_month = now_month
range_length = start_year - end_year

fred_dict = {}
spxtr_dict = {}
rut_dict = {}
wilshire_dict = {}
yahoo_triples = [
    [spxtr, 'S&P500', spxtr_dict],
    [rut, 'RUT', rut_dict],
    [wilshire, 'W5000', wilshire_dict],
]
damo_spx = {}
damo_bond3 = {}
damo_bond5 = {}
damo_cbond = {}
damo_tuples = [
    ['S&P 500 (includes dividends)3', damo_spx],
    ['3-month T.Bill4', damo_bond3],
    ['US T. Bond5', damo_bond5],
    ['Baa Corporate Bond6', damo_cbond],
]
for year_delta in range(range_length):
    year = start_year - year_delta
    for i in range(12):
        month = 12-i
        if month < 10:
            month = f'0{month}'

        date = f'{year}-{month}-01'
        years_ago_date = f'{year - num_years_held}-{month}-01'

        fred_datum = fred.loc[fred['DATE'] == date]['NCBEILQ027S_BCNSDODNS_CMDEBT_FGSDODNS_SLGSDODNS_FBCELLQ027S_DODFFSWCMI']
        if i == 11: #set all data to january
            if not fred_datum.empty:
                if fred_datum.iloc[0].startswith('0'):
                    fred_datum = float(fred_datum.iloc[0])
                    fred_dict[date] = fred_datum

        if i == 11:
            # yahoo data
            for y_df, y_str, y_dict in yahoo_triples:
                dates = [date, f'{year}-{month}-02', f'{year}-{month}-03']
                y_datum = None
                for i_date in dates:
                    if y_datum is None:
                        y_datum = y_df.loc[y_df['Date'] == i_date]['Adj Close']
                        x_date = i_date
                    elif y_datum.empty:
                        y_datum = y_df.loc[y_df['Date'] == i_date]['Adj Close']
                        x_date = i_date
                if not y_datum.empty:
                    y_datum = y_datum.iloc[0]

                    years_ago_dates = [years_ago_date, years_ago_date[:-3] + '-02', years_ago_date[:-3] + '-03']
                    old_y_datum = None
                    for io_date in years_ago_dates:
                        if old_y_datum is None:
                            old_y_datum = y_df.loc[y_df['Date'] == io_date]['Adj Close']
                            o_date = i_date
                        elif old_y_datum.empty:
                            old_y_datum = y_df.loc[y_df['Date'] == io_date]['Adj Close']
                            o_date = i_date
                    if not old_y_datum.empty:
                        old_y_datum = old_y_datum.iloc[0]
                        y_delta = y_datum - old_y_datum
                        y_return = y_delta / old_y_datum
                        y_return = ((1 + y_return)**(1/num_years_held) - 1)
                        if y_return < 0:
                            result_str = f'{years_ago_date[:4]}-{month}: {(y_return *100).round(2)}%'
                        else:
                            result_str = f'{years_ago_date[:4]}-{month}:  {(y_return *100).round(2)}%'
                        y_dict[years_ago_date] = y_return

        if i == 11: #set all data to january
            for damo_str, damo_dict in damo_tuples:
                #print(damo_str)
                damo_datum = damo2.loc[damo2['Year'] == year - 1][damo_str]
                if not damo_datum.empty:
                    damo_datum = damo_datum.iloc[0]
                    old_damo_datum = damo2.loc[damo2['Year'] == year - 1 - num_years_held][damo_str]
                    if not old_damo_datum.empty:
                        old_damo_datum = old_damo_datum.iloc[0]
                        damo_datum = float(damo_datum)
                        old_damo_datum = float(old_damo_datum)
                        damo_delta = damo_datum - old_damo_datum
                        damo_return = damo_delta / old_damo_datum
                        damo_return = ((1 + damo_return)**(1/num_years_held) - 1)
                        #print(year-1, damo_return)
                        damo_dict[years_ago_date] = damo_return


# In[163]:


data_list = []
for key in reversed(fred_dict.keys()):
    fred_datum = fred_dict.get(key)
    datum_list = [key, fred_datum]

    for y_df, y_str, y_dict in yahoo_triples:
        y_datum = y_dict.get(key)
        if y_datum:
            datum_list.append(y_datum)
        else:
            datum_list.append(np.nan)
        data_list.append(datum_list)

    for damo_str, damo_dict in damo_tuples:
        damo_datum = damo_dict.get(key)
        if damo_datum:
            datum_list.append(damo_datum)
        else:
            datum_list.append(np.nan)

        data_list.append(datum_list)


# In[164]:


cols = ['Date', 'Allocation', 'S&P500', 'RUT', 'W5000']
for damo_str, damo_dict in damo_tuples:
    cols.append(damo_str)
#print(cols)
df = pd.DataFrame(data_list, columns=cols)
damo_df = pd.DataFrame(damo_dict.items(), columns=['Date', 'Damo'])
print(df.head())



# In[181]:


import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
get_ipython().run_line_magic('matplotlib', 'inline')

x = [x[2:4] for x in df['Date']]
y1 = df['Allocation']

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax2.invert_yaxis()


curve1 = ax1.plot(x, y1, label='average investor portfolio allocation', color='r')

yahoo_color_tuples = [
    ['S&P500', '#0015FF'],
    ['RUT',    '#5E6BFF'],
    ['W5000',  '#000C94'],
]
for y_str, color in yahoo_color_tuples:
    y_x = df[y_str]
    curve_y = ax2.plot(x, y_x, label=y_str, color=color)

damo_color_tuples = [
    ['S&P 500 (includes dividends)3', 'c'],
    ['3-month T.Bill4',               'm'],
    ['US T. Bond5',                   'y'],
    ['Baa Corporate Bond6',           'k'],
]
for damo_str, color in damo_color_tuples:
    y_x = df[damo_str]
    curve2 = ax2.plot(x, y_x, label=damo_str, color=color)

ax1.set_xticks(np.arange(0, len(x)+1, 3))
plt.plot()
plt.show()


import sys
import zipfile
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None   ### Inhibit some warnings

### Command-line argument --pm=N
### - number of data points in either direction to use for slope calculations
plusminus = list(map(int,[6]+[arg[5:] for arg in sys.argv if arg.startswith('--pm=')])).pop()

### Rename columns from CSV
r = lambda k:dict(O='Output_pct',S='ScaledInput_degC')[k[0]]
### Extract data from CSV
df=pd.read_csv(zipfile.ZipFile('PID-heating.zip').open('PID-heating.csv'),index_col='time(ms)').rename(columns=r)
### Round PVs to the nearest 0.1degC
df=df.round(dict(ScaledInput_degC=1))

### Convert index from ms in CSV file to minutes
df.index /= 6e4
df.index.name = 'time_min'

### Concatenate a slope column; use time index as initial values ...
s=pd.Series(df.index.to_numpy(),index=df.index,name='degC_per_h')
df=pd.concat((df,s,),axis=1)

### ... and use it to remove suspect values with duplicate time values
df.drop_duplicates(['degC_per_h'],keep=False,inplace=True)

### Prep for slope calculations
### X and Y comprise time and PV data, respectively
X,Y = df.index.to_numpy().reshape((-1,1,)),df.ScaledInput_degC.to_numpy()

### Calculate slope at each row
for i in range(len(df)):
  ilo,ihi = max([0,i-plusminus]),i+plusminus
  A,y = X[ilo:ihi].copy(),Y[ilo:ihi].copy()
  ### offset to mean values so y-intercept will be 0
  y -= y.mean()
  A -= A.mean()
  ### Scale slope, degC/minute, to degC/h, insert into degC_per_h column
  df.degC_per_h[df.index[i]] = np.linalg.lstsq(A,y,rcond=None)[0][0] * 60

### Cumulative sum of sqrt(CV) values
deltax=np.hstack(([0.0],(X[1:] - X[:-1]).flatten(),))
cumsum = (np.sqrt(df.Output_pct.to_numpy().flatten()) * deltax).cumsum()
### - Scale cumulative sum to starting and ending PV temperature values
cumsum *= (Y[-1]-Y[0]) / cumsum[-1]
cumsum += Y[0]
### - Concatenate as another column
s=pd.Series(cumsum,index=df.index,name='CumulOut_degC')
df=pd.concat((df,s,),axis=1)

### Print data, write data to CSV file
print(df)
df.to_csv('PID_heating_with_agitation_reactants.csv')

### Plot data if matplotlib is available
try:
  import matplotlib.pyplot as plt
  plt.plot(df.index,df.Output_pct,label='CV, %')
  plt.plot(df.index,df.ScaledInput_degC,label='PV, \u00B0C')
  plt.plot(df.index,df.CumulOut_degC,label='${\int}_0^T\sqrt{CV}dt$, \u00B0C (scaled)')
  ### Difference between PV and cumul. sqrt(CV) data scaled to PV range
  ### will have similar character to slope data for integrating system
  plt.plot(df.index,3.0*(df.CumulOut_degC-df.ScaledInput_degC),label='${\int}_0^T\sqrt{CV}dt-PV$, (scaled)')
  plt.plot(df.index,df.degC_per_h,label='dPV/dt, \u00B0C/h')

  ### Annotate plot
  plt.legend(loc='best')
  plt.ylabel('CV, PV, dPV/dt, etc.')
  plt.xlabel('time, minutes')
  plt.show()

### Fail gracefully if plotting is not possible e.g. no X-Windows server
except: pass

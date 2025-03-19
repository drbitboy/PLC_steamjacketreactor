import os
import sys
import numpy
from pid import PID

class MODEL:
  """
Model a batch reactor being heated by a steam jacket as a FOPDT
integrating system.  It is integrating becuase it is well insulated and
heat loss to the ambient environment is small or insiginificant.

"""
  def __init__(self
              ,deadcount=None   ### deadtime / deltat
              ,dCVdt=None
              ,k=None
              ,T0=None
              ,deltat=None
              ,PV0=None
              ,sumCV0=None
              ,**kwargs
              ):
    (self.deadtime,self.deadcount,self.dCVdt,self.k,self.T0,self.deltat
    ,) = deadcount*deltat,deadcount,dCVdt,k,T0,deltat
    self.PVs = [PV0] * deadcount
    self.SPs = [PV0]
    self.Ts = [T0 + (i*deltat) for i in range(deadcount)]
    self.sumCVs = [sumCV0]
    self.CVs = [0.0]

  def implicit_euler(self,CVpercent,SParg=None):

    self.SPs.append(self.SPs[-1] if None is SParg else SParg)
    self.CVs.append(CVpercent)
    self.Ts.append(self.Ts[-1] + self.deltat)
    sumCV = self.sumCVs[-1] + (self.dCVdt*self.deltat* CVpercent / 100.0)
    kdeltat = self.k * self.deltat
    newPV = (self.PVs[-1] + (kdeltat*sumCV)) / (1.0 + kdeltat)
    self.PVs.append(newPV)
    self.sumCVs.append(sumCV)


  ########################################################################
  def plot_model(self):

    try: import matplotlib.pyplot as plt
    except: return
    cvcount = len(self.sumCVs)
    fig,(axpv,axcv,) = plt.subplots(2,sharex=True)
    axpv.plot(self.Ts[-cvcount:],self.sumCVs, linestyle='dotted', label='sumCVShifted')
    axpv.plot(self.Ts[:cvcount],self.sumCVs, label='sumCV')
    axpv.plot(self.Ts,self.PVs, label='PV')
    axpv.plot(self.Ts[:cvcount],self.SPs, linestyle='dotted', label='SP')
    axpv.legend(loc='lower right')
    axpv.set_ylabel('Temperature, degC')
    axpv.set_title('https://www.plctalk.net/threads/pid-tuning-for-high-order-lag-system.145422/')

    axcv.plot(self.Ts[:len(self.CVs)],self.CVs, label='CV, %')
    axcv.legend(loc='upper right')
    axcv.set_ylabel('CV')
    axcv.set_xlabel('time, minutes')

    plt.show()


########################################################################
TESTDATA = dict(deadcount=148    ### deadtime / deltat
               ,dCVdt=5.8*39.0/102.0
               ,k=5.8*39.0/(102.0*0.73961)
               ,T0=7.6
               ,deltat=1.0/60.0  
               ,PV0=54.7
               ,sumCV0=54.7
               )
def init_model():
  modeldict = dict()
  model = MODEL(**TESTDATA)
  modeldict.update(vars(model))
  modeldict['SPs'] = model.SPs[:2] + ['...'] + model.SPs[-2:]
  modeldict['PVs'] = model.PVs[:2] + ['...'] + model.PVs[-2:]
  modeldict['Ts'] = model.Ts[:2] + ['...'] + model.Ts[-2:]
  print(modeldict)
  return model


########################################################################
def pid_control_model(SPbump=10.3,**kwargs):

  model_steps_per_pid = 8
  model = init_model()
  modelpid = PID(PV_lo=0.0,PV_hi=100.0
                ,CV_lo=0.0,CV_hi=100.0
                ###,Ki=0.0
                ###,Kd=0.0
                ,deltaT=model.deltat * model_steps_per_pid
                ###,Deadband=0.0
                ###,Bias_pct=0.0
                ,Error_calc='SP-PV'
                ,SP=model.PVs[-1]    ### "Bumpless"
                ,**kwargs
                )
  print(modelpid)

  SP0 = modelpid.SP
  SPnew = SP0 + float(SPbump)
  iPV = 0
  modelrange = range(model_steps_per_pid)
  for pidstep in range(900):
    pidcv = modelpid.update(model.PVs[iPV])
    for modelstep in modelrange:
      model.implicit_euler(pidcv,SParg=modelpid.SP)
      iPV += 1
    modelpid.set_SP(SPnew)

  model.plot_model()


########################################################################
def test_model():

  model = init_model()

  for i in range(int(round(((20.0-model.T0)/model.deltat) - model.deadcount))):
    model.implicit_euler(i<440 and 100.0 or 0.0)

  model.plot_model()


########################################################################
if "__main__" == __name__:
  d = dict()
  for arg in sys.argv[1:]:
    if arg.startswith('--'):
      toks = arg[2:].split('=')
      key = toks.pop(0)
      if toks: d[key] = '='.join(toks)
      else   : d[key] = True
  pid_control_model(**d)
  if 'showtest' in d: test_model()

import os
import sys
import numpy

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
    self.Ts = [T0 + (i*deltat) for i in range(deadcount)]
    self.sumCVs = [sumCV0]
    self.CVs = [0.0]

  def implicit_euler(self,CVpercent):
    self.CVs.append(CVpercent)
    self.Ts.append(self.Ts[-1] + self.deltat)
    sumCV = self.sumCVs[-1] + (self.dCVdt*self.deltat* CVpercent / 100.0)
    kdeltat = self.k * self.deltat
    newPV = (self.PVs[-1] + (kdeltat*sumCV)) / (1.0 + kdeltat)
    self.PVs.append(newPV)
    self.sumCVs.append(sumCV)

def test_model():
  TESTDATA = dict(deadcount=148    ### deadtime / deltat
                 ,dCVdt=5.8*39.0/102.0
                 ,k=5.8*39.0/(102.0*0.73961)
                 ,T0=7.6
                 ,deltat=1.0/60.0  
                 ,PV0=54.7
                 ,sumCV0=54.7
                 )
  modeldict = dict()
  model = MODEL(**TESTDATA)
  modeldict.update(vars(model))
  modeldict['PVs'] = model.PVs[:2] + ['...'] + model.PVs[-2:]
  modeldict['Ts'] = model.Ts[:2] + ['...'] + model.Ts[-2:]
  print(modeldict)
  for i in range(int(round(((20.0-model.T0)/model.deltat) - model.deadcount))):
    model.implicit_euler(i<440 and 100.0 or 0.0)

  try: import matplotlib.pyplot as plt
  except: return
  fig,(axpv,axcv,) = plt.subplots(2,sharex=True)
  axpv.plot(model.Ts[-len(model.sumCVs):],model.sumCVs, linestyle='dotted', label='sumCVShifted')
  axpv.plot(model.Ts[:len(model.sumCVs)],model.sumCVs, label='sumCV')
  axpv.plot(model.Ts,model.PVs, label='PV')
  axpv.legend(loc='lower right')
  axpv.set_ylabel('Temperature, degC')
  axpv.set_title('https://www.plctalk.net/threads/pid-tuning-for-high-order-lag-system.145422/')

  axcv.plot(model.Ts[:len(model.CVs)],model.CVs, label='CV, %')
  axcv.legend(loc='upper right')
  axcv.set_ylabel('CV')
  axcv.set_xlabel('time, minutes')

  plt.show()

if "__main__" == __name__:
  test_model()

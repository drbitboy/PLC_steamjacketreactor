"""
PID class

"""
import os

do_debug = 'DEBUG' in os.environ

class PID:
  """
PID instruction
- with independent gains
- with PV limits
- Bias
- Implemented via incremental ("velocity") model
  - with CV limits => anti-windup reset
- With deadband
"""
  def __init__(self
              ,PV_lo,PV_hi
              ,CV_lo,CV_hi
              ,Kp=0.0,Ki=0.0,Kd=0.0
              ,deltaT=1.0
              ,Deadband=0.0
              ,Bias_pct=0.0
              ,Error_calc='PV-SP'
              ,SP=None
              ,**kwargs
              ):
    """
Initialize PID class
- PV_lo,PV_hi           PV range limits corresponding to 0% and 100% PV%
- CV_lo,CV_hi           CV range limits corresponding to 0% and 100% CV%
- SP=None               Initial Setpoint
- Kp=0.0,Ki=0.0,Kd=0.0  Tuning parameters, unitless (%/%)
- deltaT=1.0            Loop update time, s
- Deadband=0.0          Deadband around SP; input PV units
- Bias_pct=0.0          Initial bias to be added to CV, CV% units
- Error_calc='PV-SP'    Control action:  'PV-SP' => direct; else reverse
- **kwargs              Overide keyword arguments above
"""
    (self.PV_lo,self.PV_hi,self.CV_lo,self.CV_hi,self.Kp,self.Ki,self.Kd
    ,self.Bias_pct,self.deltaT
    ,) = map(float,(PV_lo,PV_hi,CV_lo,CV_hi,Kp,Ki,Kd,Bias_pct,deltaT,))

    if Error_calc.upper()=='PV-SP': self.raw_error = PID.PV_minus_SP
    else                          : self.raw_error = PID.SP_minus_PV

    floatdb = float(Deadband)

    assert self.PV_hi > self.PV_lo
    assert self.CV_hi > self.CV_lo
    assert self.Bias_pct >= 0.0 and self.Bias_pct <= 100.0
    assert floatdb >= 0.0
    assert self.deltaT > 0.0

    self.PV_range = (self.PV_hi - self.PV_lo) / 100.0
    self.Deadband_pct = floatdb / self.PV_range
    self.set_SP(SP)

    self.CV_range = (self.CV_hi - self.CV_lo) / 100.0
    self.CV_pct = self.Bias_pct

    self.last_error_pct = self.last_Perr_pct = 0.0

    if do_debug: print(vars(self))

  def update(self,PV):
    """PID equation:  incremental (a.k.a. "velocity") form"""

    ### - Error portions of P, I and D terms, in percent units
    Ierr = self.calc_Error_pct(PV)       ### Error; E(n); PV-SP or SP-PV
    Perr = Ierr - self.last_error_pct    ### delE(n) = E(n) - E(n-1)
    Derr = Perr - self.last_Perr_pct     ### delDelE=delE(n) - delE(n-1)

    ### - Apply PID equation, clamp result, percent units
    self.CV_pct = self.CV_pct_clamp(self.CV_pct              ### CV(n-1)
                                   +(self.Kp * Perr)                # +P
                                   +(self.Ki * Ierr * self.deltaT)  # +I
                                   +(self.Kd * Derr / self.deltaT)  # +D
                                   )

    ### - Save error terms for next update
    self.last_Perr_pct = Perr        ### Will be next update's delE(n-1)
    self.last_error_pct = Ierr       ### Will be next update's E(n-1)

    return self.calc_CV()            ### Scale CV_pct to output range

  def calc_Error_pct(self,PV):
    """Calculate percent error of PV input argument w.r.t. SP"""

    ### Clamp and convert PV and SP to percentages
    PV_pct = self.calc_PV_pct(PV)
    SP_pct = self.calc_PV_pct(self.SP)

    ### Calculate error; raw_error is either PV%-SP% or SP%-PV%, as
    ### defined in __init__
    error_pct = self.raw_error(PV_pct,SP_pct)

    ### Only return error if it is outside the deadband
    if error_pct >   self.Deadband_pct : return error_pct
    if error_pct < (-self.Deadband_pct): return error_pct

    ### Error within deadband is ignored; N.B. no zero-crossing check
    return 0.0

  def calc_CV(self,CV_pct=None):
    """Convert CV% to output CV range"""
    if None is CV_pct: return self.calc_CV(self.CV_pct)
    return self.CV_lo + (self.CV_pct_clamp(CV_pct) * self.CV_range)

  def calc_PV_pct(self,PV):
    """Clamp PV and convert to PV%"""
    return (self.PV_clamp(PV) - self.PV_lo) / self.PV_range

  def set_SP(self,newSP):
    """Assign setpoint; use PV range midpoint if newSP arg is None"""
    if None is newSP:
      self.set_SP((self.PV_lo + self.PV_hi) / 2.0)
      return
    self.SP = self.PV_clamp(newSP)

  def PV_clamp(self,valarg):
    """Clamp PV to PV range"""
    return PID.clamp(valarg,self.PV_lo,self.PV_hi)

  def CV_pct_clamp(self,valarg):
    """Clamp CV% to CV% range (0-100%)"""
    return PID.clamp(valarg,0.0,100.0)

  @staticmethod
  def clamp(valarg,lo,hi):
    """Generic clamp method"""
    val = float(valarg)
    if val < lo: return lo
    if val > hi: return hi
    return val

  ### Generic error calculation methods:  direct PV-SP; reverse SP-PV
  @staticmethod
  def PV_minus_SP(PV,SP): return PV-SP

  @staticmethod
  def SP_minus_PV(PV,SP): return SP-PV

  def __repr__(self):
    Error_calc = self.raw_error == PID.PV_minus_SP and 'PV-SP' or 'SP-PV'
    return f"<Kp={self.Kp:.3f},Ki={self.Ki:.3f},Kd={self.Kd:.3f},{Error_calc}>"

########################################################################

if "__main__" == __name__:
  True

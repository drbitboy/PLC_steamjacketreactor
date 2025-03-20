import numpy
import PIL.Image
import pandas as pd

### Read PNG image, convert to numpy array; add 1 to remove 0s
arr=numpy.array(PIL.Image.open('zzImages/53C-73C_0450s-1650c.png'),dtype=numpy.float64)+1.0
arr[:,:,1] /= (arr[:,:,0]+arr[:,:,2])  ### divide green channel by red+blue sum
arr[:,:,0] = arr[:,:,1].min()          ### Zero out red channel
arr[:,:,2] = arr[:,:,0]                ### Zero out blue channel
arr -= arr.min()                       ### Shift negative values to 0
arr *= 255/arr.max()                   ### Scale to 0-255

iw=numpy.where(arr>4)                  ### Pixel where scaled green/(red+blue) ratio is greater than 3.8

### Write green pixels

arrout=numpy.array(arr,dtype=numpy.uint8)
arrout[iw]=255
PIL.Image.fromarray(arrout).save('zzImages/green.png')

a=list(zip(iw[1],arr.shape[0]-iw[0]))  ### (column,offset from top,) pairs of green pixels
a.sort()                               ### sort by column

sums=numpy.zeros(arr.shape[1],dtype=numpy.float64)         ### Sums of green pixels' rows, by column
counts=sums+0.0                                            ### Count of green pixels, by column
for col,row in a:
  sums[col] +=row
  counts[col] += 1

means=sums/counts                                          ### Means of grean pixels' rows, by column

temps=means*20./arr.shape[0]+53.0                          ### Scale row means to temperature, by column
times=7.5+(20.*numpy.arange(arr.shape[1])/arr.shape[1])    ### Scale columns to time 
timess=times*60.0

### CV is 100% from between offsets 8 through 279, inclusive, else 0%

CVs = [i>=8 and i<=279 and 100.0 or 0.0 for i in range(arr.shape[1])]

### Write CSV data

pd.DataFrame({'minutes':times
             ,'seconds':timess
             ,'CV%':[i>=8 and i<=279 and 100.0 or 0.0 for i in range(arr.shape[1])]
             ,'degC':temps}
            ).to_csv('zzImages/steamjacketreactor_green.csv',index=False)

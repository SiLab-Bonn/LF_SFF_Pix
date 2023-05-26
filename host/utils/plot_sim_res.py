import numpy as np
import matplotlib.pyplot as plt
import plot_fit as pltfit
from scipy import optimize
from scipy import odr

data=np.genfromtxt('../output/sim/DC_Sweep/data/DC_Sweep_result.txt', delimiter='\t')[1:]
x = data[0:,0]
y = data[0:,1]
pltfit.beauty_plot(figsize=[10,10], ylabel='$V_{OUT}$ / mV', xlabel='$V_{IN}$ / V', xlim=[0,np.max(x)], ylim=[0, max(y)+0.2], fontsize=20)


end_of_dynamic_area_pos_default = 5
end_of_dynamic_area = 0
end_of_dynamic_area_pos = 0

g_ref = (y[1]-y[0])/(x[1]-x[0])
for i in range(1,len(y)-2):
    current_gain = (y[i+1]-y[i])/(x[i+1]-x[i])
    if current_gain/g_ref <=0.7:
        end_of_dynamic_area_pos = i
        end_of_dynamic_area = x[i]
        break
plt.fill_between([-10, end_of_dynamic_area], -1000,1000,alpha=0.2, color='gray')   
plt.vlines(end_of_dynamic_area,-1000,1000, color='black', linestyle='--')
plt.text(end_of_dynamic_area+0.01, np.min(y[0]), 'end of dynamic area: '+str(np.round(end_of_dynamic_area*1000,1))+'mV',rotation = 90)
plt.vlines(end_of_dynamic_area/2,-1000,1000, color='black', linestyle='--')
plt.text(end_of_dynamic_area/2+0.01, np.min(y[0]), 'DC offset: '+str(np.round(end_of_dynamic_area/2*1000,1))+'mV',rotation = 90)

plt.scatter(x,y, label='Simulated data with IBP=-10uA, IBN=100uA')

def func_lin(p,x):
    a,b=p
    return a*x+b

model = odr.Model(func_lin)
data = odr.RealData(x[0:end_of_dynamic_area_pos], y[0:end_of_dynamic_area_pos])
out = odr.ODR(data, model, beta0=[500,1]).run()
popt = out.beta
perr = out.sd_beta

x_fit = np.array([0, end_of_dynamic_area+0.1])
y_fit = popt[0]*x_fit+popt[1]
plt.plot(x_fit, y_fit, color='black', label='$V_{OUT}(V_{IN})=(%.3f\\pm %.3f)\\cdot V_{IN}mV+(%.3f\\pm %.3f)mV$'%(popt[0]/1000, perr[0]/1000, popt[1]/1000, perr[1]/1000))
plt.legend()
plt.savefig('../output/sim/DC_Sweep/DC_Sweep_sim.pdf',bbox_inches='tight')
plt.close()

gain = []
for i in range(0, len(x)-1):
    gain.append((y[i+1]-y[i])/(x[i+1]-x[i])/1000)

pltfit.beauty_plot(figsize=[10,10], xlabel='$V_{IN}$ / V', ylabel='Gain $G$', fontsize=20)
plt.scatter([(x[i+1]+x[i])/2 for i in range(0, len(x)-1)], gain)
plt.savefig('../output/sim/DC_Sweep/DC_Sweep_Gain_sim.pdf',bbox_inches='tight')
plt.close()
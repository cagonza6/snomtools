__author__ = 'hartelt'
'''
This file is meant as a collection of physical constants, that can be used for calculations.
All constants should be given in SI!
'''
import numpy

#pi: the mathematical constant pi. from numpy. only for convenience
pi = numpy.pi

#c: the speed of light in m/s
c = 299792458.0

#mu_0: the magentic constant / permeability of the vacuum in Vs/Am
mu_0 = 4e-7*numpy.pi

#epsilon_0: the dielectric constant / permittivity of the vacuum in As/Vm
epsilon_0 = 1.0/(mu_0*c*c)

#e: the elementary charge in C
e = 1.60217733e-19

#m_e: the electron mass in kg
m_e = 9.1093897e-31

#For testing:
if __name__ == "__main__":
	print pi
	print c
	print(mu_0)
	print(epsilon_0)
	print(e)
	print(m_e)
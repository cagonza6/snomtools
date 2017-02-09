# coding=utf-8
__author__ = 'hartelt'
"""
This scripts imports tiff files, as generated for example by Terra and the PEEM Camera Software. The methods defined
here will read those files and return the data as a DataSet instances. 3D tiff stacks shall be supported.
"""

import snomtools.data.datasets
import os
import numpy
import tifffile
import re
import snomtools.calcs.units as u


def is_tif(filename):
	"""
	Checks if a filename is a tifffile.

	:param filename: string: The filename.

	:return: Boolean.
	"""
	return os.path.splitext(filename)[1] in [".tiff", ".tif"]


def search_tag(tif, tag_id):
	"""
	Searches for a tag in all pages of a tiff file and returns the first match as

	:param tif: An open TiffFile. See tifffile.TiffFile.

	:param tag_id: String: The ID of the tag to search for.

	:return: The tag, object, instance of tifffile.TiffTag.
	"""
	for page in tif:
		for tag in page.tags.values():
			if tag.name == tag_id:
				return tag
	print("WARNING: Tiff tag not found.")
	return None


def peem_dld_read(filepath, mode="terra"):
	"""
	Reads a time-resolved dld dataset. Shadows the different readin functions for the different measurement programs
	and returns the generated DataSets.

	:param filepath: String: The (absolute or relative) path of the input file or folder.

	:param mode: String: The readin mode. Valid options are "terra" for a tiff generated with Terra (default),
	"pne" for a folder of tiffs generated with the Focus ProNanoESCA Software.

	:return: The generated DataSet.
	"""
	if mode == "terra":
		return peem_dld_read_terra(filepath)
	elif mode == "pne":
		raise NotImplementedError("ProNanoESCA DLD tiff readin not yet implemented.")
		# TODO: Implement Focus ProNanoESCA readin.
	elif mode == "dldgui":
		raise NotImplementedError("dldgui tiff readin not yet implemented.")
		# TODO: Implement dldgui readin.
	else:
		raise ValueError("Unrecognized readin mode given to peem_dld_read")


def peem_dld_read_terra(filepath):
	"""
	Reads a tif file as generated by Terra when using the DLD. Therefore, the 3D tif dimensions are interpreted as
	time-channel, x and y, with the first two time channels being the sum and the error image, which will be ignored.

	:param filepath: String: The (absolute or relative) path of input file.

	:return: The dataset instance generated from the tif file.
	"""
	# Translate input path to absolute path:
	filepath = os.path.abspath(filepath)
	filebase = os.path.basename(filepath)

	# Read tif file to numpy array. Axes will be (timechannel, x, y):
	infile = tifffile.TiffFile(filepath)
	indata = infile.asarray()

	# Read time binning metadata from tags:
	roi_and_bin_id = "41010"  # as defined by Christian Schneider #define TIFFTAG_ROI_AND_BIN 41010
	tag = search_tag(infile, roi_and_bin_id)
	# roi_and_bin_list = tag.value
	T, St, Tbin = int(tag.value[2]), int(tag.value[5]), int(tag.value[8])
	infile.close()

	# Remove sum and error image:
	realdata = numpy.delete(indata, [0, 1], axis=0)

	# Initialize data for dataset:
	dataarray = snomtools.data.datasets.DataArray(realdata, unit='count', label='counts', plotlabel='Counts')
	if tag:
		# The following commented lines won't work because of Terras irreproducible channel assignment and saving...
		# assert (realdata.shape[0] == round(St / float(Tbin))), \
		# 	"ERROR: Tifffile metadata time binning does not fit to data size."
		# uplim = T+(round(St/float(Tbin)))*Tbin # upper limit calculation
		# So just take the data dimensions... and pray the channels start at the set T value:
		taxis = snomtools.data.datasets.Axis([T + i * Tbin for i in range(realdata.shape[0])], label='channel',
											 plotlabel='Time Channel')
	else:
		taxis = snomtools.data.datasets.Axis(numpy.arange(0, realdata.shape[0]), label='channel',
											 plotlabel='Time Channel')
	# Careful about orientation! This is like a matrix:
	# rows go first and are numbered in vertical direction -> Y
	# columns go last and are numbered in horizontal direction -> X
	xaxis = snomtools.data.datasets.Axis(numpy.arange(0, realdata.shape[1]), unit='pixel', label='y', plotlabel='y')
	yaxis = snomtools.data.datasets.Axis(numpy.arange(0, realdata.shape[2]), unit='pixel', label='x', plotlabel='x')

	# Return dataset:
	return snomtools.data.datasets.DataSet(label=filebase, datafields=[dataarray], axes=[taxis, xaxis, yaxis])


def peem_camera_read(filepath, mode="camware"):
	"""
	Reads a PEEM image dataset aquired with the camera. Shadows the different readin functions for the different
	measurement programs and returns the generated DataSets.

	:param filepath: String: The (absolute or relative) path of the input file.

	:param mode: String: The readin mode. Valid options are "terra" for a tiff generated with Terra,
	"camware" for a tiff generated with the PCO CamWare Software (default) or "pne" for a tiff generated with the
	Focus ProNanoESCA Software.

	:return: The generated DataSet.
	"""
	if mode == "camware":
		return peem_camera_read_camware(filepath)
	if mode == "terra":
		return (filepath)
	elif mode == "pne":
		raise NotImplementedError("ProNanoESCA DLD tiff readin not yet implemented.")
		# TODO: Implement Focus ProNanoESCA readin.
	else:
		raise ValueError("Unrecognized readin mode given to peem_dld_read")


def peem_camera_read_camware(filepath):
	"""
	Reads a tif file as generated by the Camera Software (PCO Camware) when using the Camera. Therefore, the 2D tif
	dimensions are interpreted as x and y.

	:param filepath: String: The (absolute or relative) path of input file.

	:return: The dataset instance generated from the tif file.
	"""
	# Translate input path to absolute path:
	filepath = os.path.abspath(filepath)
	filebase = os.path.basename(filepath)

	# Read tif file to numpy array. Axes will be (timechannel, x, y):
	infile = tifffile.TiffFile(filepath)
	indata = infile.asarray()

	# Initialize data for dataset:
	dataarray = snomtools.data.datasets.DataArray(indata, unit='count', label='counts', plotlabel='Counts')

	# Careful about orientation! This is like a matrix:
	# rows go first and are numbered in vertical direction -> Y
	# columns go last and are numbered in horizontal direction -> X
	xaxis = snomtools.data.datasets.Axis(numpy.arange(0, indata.shape[0]), unit='pixel', label='y', plotlabel='y')
	yaxis = snomtools.data.datasets.Axis(numpy.arange(0, indata.shape[1]), unit='pixel', label='x', plotlabel='x')

	# Return dataset:
	return snomtools.data.datasets.DataSet(label=filebase, datafields=[dataarray], axes=[xaxis, yaxis])


def peem_camera_read_terra(filepath):
	"""
	Reads a PEEM image aquired with the Camera and saved with Terra. For now, this just shadows the
	powerlaw_folder_peem_camera function, because they work the same way, this can be changed in the future,
	maybe to read addidional metadata generated by Terra.

	:param filepath: String: The (absolute or relative) path of the input file.

	:return: The generated DataSet.
	"""
	return peem_camera_read_camware(filepath)


def powerlaw_folder_peem_camera(folderpath, pattern="mW", powerunit=None, powerunitlabel=None):
	"""

	:param folderpath: The (relative or absolute) path of the folders containing the powerlaw measurement series.

	:param pattern: string: A pattern the powers in the filenames are named with. For example in the default case
	"mW", the filename containing '50,2mW' or '50.2mW' or '50.2 mW' would accord to a power of 50.2 milliwatts. The
	power units for the axis quantities are also cast from this pattern if not explicitly given with powerunit.

	:param powerunit: A valid unit string that will be cast as the unit for the power axis values. If not given,
	the pattern parameter will be cast as unit.

	:param powerunitlabel: string: Will be used as the unit for the power axis plotlabel. Can be for example a LaTeX
	siunitx command. If not given, the powerunit parameter will be used.

	:return: The dataset containing the images stacked along a power axis.
	"""
	if powerunit is None:
		powerunit = pattern
	if powerunitlabel is None:
		powerunitlabel = powerunit
	pat = re.compile('(\d*[,|.]?\d+)\s?' + pattern)

	# Translate input path to absolute path:
	folderpath = os.path.abspath(folderpath)

	# Inspect the given folder for the tif files of the powerlaw:
	powerfiles = {}
	for filename in filter(is_tif, os.listdir(folderpath)):
		found = re.search(pat, filename)
		if found:
			power = float(found.group(1).replace(',', '.'))
			powerfiles[power] = filename

	axlist = []
	datastack = []
	for power in iter(sorted(powerfiles.iterkeys())):
		datastack.append(peem_camera_read(os.path.join(folderpath, powerfiles[power])))
		axlist.append(power)
	powers = u.to_ureg(axlist, powerunit)

	pl = 'Power / ' + powerunitlabel  # Plot label for power axis.
	poweraxis = snomtools.data.datasets.Axis(powers, label='power', plotlabel=pl)

	return snomtools.data.datasets.stack_DataSets(datastack, poweraxis, axis=-1, label="Powerlaw " + folderpath)


def powerlaw_folder_peem_dld(folderpath, pattern="mW", powerunit=None, powerunitlabel=None):
	"""

	:param folderpath: The (relative or absolute) path of the folders containing the powerlaw measurement series.

	:param pattern: string: A pattern the powers in the filenames are named with. For example in the default case
	"mW", the filename containing '50,2mW' or '50.2mW' or '50.2 mW' would accord to a power of 50.2 milliwatts. The
	power units for the axis quantities are also cast from this pattern if not explicitly given with powerunit.

	:param powerunit: A valid unit string that will be cast as the unit for the power axis values. If not given,
	the pattern parameter will be cast as unit.

	:param powerunitlabel: string: Will be used as the unit for the power axis plotlabel. Can be for example a LaTeX
	siunitx command. If not given, the powerunit parameter will be used.

	:return: The dataset containing the images stacked along a power axis.
	"""
	if powerunit is None:
		powerunit = pattern
	if powerunitlabel is None:
		powerunitlabel = powerunit
	pat = re.compile('(\d*[,|.]?\d+)\s?' + pattern)

	# Translate input path to absolute path:
	folderpath = os.path.abspath(folderpath)

	# Inspect the given folder for the tif files of the powerlaw:
	powerfiles = {}
	for filename in filter(is_tif, os.listdir(folderpath)):
		found = re.search(pat, filename)
		if found:
			power = float(found.group(1).replace(',', '.'))
			powerfiles[power] = filename

	axlist = []
	datastack = []
	for power in iter(sorted(powerfiles.iterkeys())):
		datastack.append(peem_dld_read_terra(os.path.join(folderpath, powerfiles[power])))
		axlist.append(power)
	powers = u.to_ureg(axlist, powerunit)

	pl = 'Power / ' + powerunitlabel  # Plot label for power axis.
	poweraxis = snomtools.data.datasets.Axis(powers, label='power', plotlabel=pl)

	return snomtools.data.datasets.stack_DataSets(datastack, poweraxis, axis=-1, label="Powerlaw " + folderpath)


def tr_folder_peem_camera_terra(folderpath, pattern="D", delayunit="um", delayunitlabel=None):
	"""

	:param folderpath:
	:param pattern:
	:param delayunit:
	:param delayunitlabel:
	:return:
	"""
	if delayunitlabel is None:
		delayunitlabel = delayunit
	pat = re.compile(pattern + "(-?\d*).tif")

	# Translate input path to absolute path:
	folderpath = os.path.abspath(folderpath)

	# Inspect the given folder for time step files:
	timefiles = {}
	for filename in filter(is_tif, os.listdir(folderpath)):
		found = re.search(pat, filename)
		if found:
			timestep = float(found.group(1))
			timefiles[timestep] = filename

	axlist = []
	datastack = []
	for timestep in iter(sorted(timefiles.iterkeys())):
		datastack.append(peem_camera_read_terra(os.path.join(folderpath, timefiles[timestep])))
		axlist.append(timestep)
	delays = u.to_ureg(axlist, delayunit)

	pl = 'Pulse Delay / ' + delayunitlabel  # Plot label for power axis.
	delayaxis = snomtools.data.datasets.Axis(delays, label='delay', plotlabel=pl)

	return snomtools.data.datasets.stack_DataSets(datastack, delayaxis, axis=0, label="TR " + folderpath)


def tr_folder_peem_dld_terra(folderpath, pattern="D", delayunit="um", delayunitlabel=None):
	"""

	:param folderpath:
	:param pattern:
	:param delayunit:
	:param delayunitlabel:
	:return:
	"""
	if delayunitlabel is None:
		delayunitlabel = delayunit
	pat = re.compile(pattern + "(-?\d*).tif")

	# Translate input path to absolute path:
	folderpath = os.path.abspath(folderpath)

	# Inspect the given folder for time step files:
	timefiles = {}
	for filename in filter(is_tif, os.listdir(folderpath)):
		found = re.search(pat, filename)
		if found:
			timestep = float(found.group(1))
			timefiles[timestep] = filename

	axlist = []
	datastack = []
	for timestep in iter(sorted(timefiles.iterkeys())):
		datastack.append(peem_dld_read_terra(os.path.join(folderpath, timefiles[timestep])))
		axlist.append(timestep)
	delays = u.to_ureg(axlist, delayunit)

	pl = 'Pulse Delay / ' + delayunitlabel  # Plot label for power axis.
	delayaxis = snomtools.data.datasets.Axis(delays, label='delay', plotlabel=pl)

	return snomtools.data.datasets.stack_DataSets(datastack, delayaxis, axis=0, label="TR " + folderpath)


# if True:  # Just for testing...
if __name__ == "__main__":
	testdata = None

	test_camera_read = False
	if test_camera_read:
		testfilename = "14_800nm_Micha_crosspol_ppol320_t-80fs_50µm.tif"
		testdata = peem_camera_read(testfilename)
		outname = testfilename.replace('.tif', '.hdf5')
		testdata.saveh5(outname)

	test_plot = False
	if test_plot and testdata:
		import snomtools.plots.setupmatplotlib as plt
		import snomtools.plots.datasets

		fig = plt.figure((12, 12), 1200)
		ax = fig.add_subplot(111)
		ax.cla()
		vert = 'y'
		hori = 'x'
		ax.autoscale(tight=True)
		ax.set_aspect('equal')
		snomtools.plots.datasets.project_2d(testdata, ax, axis_vert=vert, axis_hori=hori, data_id='counts')
		plt.savefig(filename="test.png", figures_path=os.getcwd(), transparent=False)

	test_powerlaw = False
	if test_powerlaw:
		plfolder = "Powerlaw"
		pldata = powerlaw_folder_peem_camera(plfolder, powerunitlabel='\\SI{\\milli\\watt}')

	test_timeresolved = True
	if test_timeresolved:
		# trfolder = "02-800nm-FoV50um-exp10s-sq30um_xpol_sp_scan0to120fs/1. Durchlauf"
		# trdata = tr_folder_peem_camera_terra(trfolder, delayunit="as")
		# trdata.saveh5(trfolder+'.hdf5')
		trfolder = "06-800nm-DLD-xpol_sp-scan-10fsto120fs-EK/SUM"
		trdata = tr_folder_peem_dld_terra(trfolder, delayunit="as")
		trdata.saveh5(trfolder+'.hdf5')

	print('done.')

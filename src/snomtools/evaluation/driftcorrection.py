__author__ = 'frisch'
''' 
This file provides driftkorrection for any array stack. 
'''

import cv2 as cv
import numpy as np
import snomtools.data.datasets


class Drift:
	def __init__(self, data=None, template=None, stackAxisID=None, xAxisID=None, yAxisID=None,
				 subpixel=True, method='cv.TM_CCOEFF_NORMED'):

		# Methods: 'cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR', 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'

		# read axis
		if data:
			if stackAxisID is None:
				dstackAxisID = data.get_axis_index('delay')
			else:
				dstackAxisID = data.get_axis_index(stackAxisID)
			if xAxisID is None:
				dxAxisID = data.get_axis_index('x')
			else:
				dxAxisID = data.get_axis_index(xAxisID)
			if yAxisID is None:
				dyAxisID = data.get_axis_index('y')
			else:
				dyAxisID = data.get_axis_index(yAxisID)

			# process data towards 3d array
			self.data = self.extract_3Ddata(data, dstackAxisID, dxAxisID, dyAxisID)

			# read or guess template
			if template:
				if xAxisID is None:
					txAxisID = template.get_axis_index('x')
				else:
					txAxisID = template.get_axis_index(xAxisID)
				if yAxisID is None:
					tyAxisID = template.get_axis_index('y')
				else:
					tyAxisID = template.get_axis_index(yAxisID)
				self.template = self.extract_templatedata(template, txAxisID, tyAxisID)
			else:
				self.template = self.guess_templatedata(data, dxAxisID, dyAxisID)

		# for layers along stackAxisID find drift:
		self.drift = self.template_matching_stack(self.data.get_datafield(0), self.template, stackAxisID)

	@classmethod
	def template_matching_stack(cls, data, template, stackAxisID, method='cv.TM_CCOEFF_NORMED', subpixel=True):
		driftlist = []
		for i in range(data.shape[stackAxisID]):
			slicebase = [np.s_[:], np.s_[:]]
			slicebase.insert(stackAxisID, i)
			slice_ = tuple(slicebase)
			driftlist.append(cls.template_matching((data.data[slice_]), template, method, subpixel))
		return driftlist


	@staticmethod
	def template_matching(array, template, method='cv.TM_CCOEFF_NORMED', subpixel=True):
		# Methods: 'cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR', 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'

		method = eval(method)


		array = np.float32(array)
		template = np.float32(template)
		w, h = template.shape[::-1]

		res = cv.matchTemplate(array, template, method)
		min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

		if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
			if subpixel:
				top_left = Drift.subpixel_peak(min_loc, res)
			else:
				top_left = min_loc
		else:
			if subpixel:
				top_left = Drift.subpixel_peak(max_loc, res)
			else:
				top_left = max_loc

		return top_left


	@staticmethod
	def subpixel_peak(max_var, results):
		x = max_var[0]
		y = max_var[1]
		coord = []

		x_sub = x \
				+ (np.log(results[x - 1, y]) - np.log(results[x + 1, y])) \
				  / \
				  (2 * np.log(results[x - 1, y]) + 2 * np.log(results[x + 1, y]) - 4 * np.log(results[x, y]))
		y_sub = y + \
				(np.log(results[x, y - 1]) - np.log(results[x, y + 1])) \
				/ \
				(2 * np.log(results[x, y - 1]) - 4 * np.log(results[x, y]) + 2 * np.log(results[x, y + 1]))
		return (x_sub, y_sub)


	@staticmethod
	def extract_3Ddata(data, stackAxisID, xAxisID, yAxisID):
		assert isinstance(data, snomtools.data.datasets.DataSet), \
			"ERROR: No dataset or ROI instance given to extract_3Ddata."
		return data.project_nd(stackAxisID, xAxisID, yAxisID)


	@staticmethod
	def extract_templatedata(data, xAxisID, yAxisID):
		assert isinstance(data, snomtools.data.datasets.DataSet) or isinstance(data, snomtools.data.datasets.ROI), \
			"ERROR: No dataset or ROI instance given to extract_templatedata."

		xAxisID = data.get_axis_index(xAxisID)
		yAxisID = data.get_axis_index(yAxisID)
		return data.project_nd(xAxisID, yAxisID).get_datafield(0)


	@staticmethod
	def guess_templatedata(data, xAxisID, yAxisID):
		assert isinstance(data, snomtools.data.datasets.DataSet) or isinstance(data, snomtools.data.datasets.ROI), \
			"ERROR: No dataset or ROI instance given to guess_template."

		xAxisID = data.get_axis_index(xAxisID)
		yAxisID = data.get_axis_index(yAxisID)
		fieldshape = (data.shape[xAxisID], data.shape[yAxisID])
		xl, xr, yl, yr = fieldshape[0] * 2 / 5, fieldshape[0] * 3 / 5, fieldshape[1] * 2 / 5, fieldshape[1] * 3 / 5
		limitlist = {xAxisID: (xl, xr), yAxisID: (yl, yr)}
		roi = snomtools.data.datasets.ROI(data, limitlist, by_index=True)
		return roi.project_nd(xAxisID, yAxisID).get_datafield(0)

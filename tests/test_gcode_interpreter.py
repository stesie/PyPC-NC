import math
import unittest
from Converters import GCode

class TestBlockSplitting(unittest.TestCase):
	def test_splitBlockSelf(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.splitBlock('M30'), [ [ 'M30' ] ])

	def test_splitBlockGroupParams(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.splitBlock('G0 X0'), [ [ 'G0', 'X0' ] ])

	def test_splitBlockGroupInsns(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.splitBlock('M0 M1'), [ [ 'M0' ], [ 'M1' ] ])

	def test_splitBlockM3takesS(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.splitBlock('M3 S3000'), [ [ 'M3', 'S3000' ] ])

	def test_splitBlockComplex(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.splitBlock('G17 G20 G90 G64 P0.003 M3 S3000 M7 F1'), [
			[ 'G17' ],
			[ 'G20' ],
			[ 'G90' ],
			[ 'G64', 'P0.003' ],
			[ 'M3', 'S3000' ],
			[ 'M7' ],
			[ 'F1' ] ])

class TestInterpreterBasics(unittest.TestCase):
	def test_G20(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G20' ])
		self.assertEqual(i.stretch, 25.4)

	def test_G21(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G21' ])
		self.assertEqual(i.stretch, 1)

	def test_G90(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G90' ])
		self.assertEqual(i.absDistanceMode, True)

	def test_G91(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G91' ])
		self.assertEqual(i.absDistanceMode, False)

	def test_M30(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'M30' ])
		self.assertEqual(i.end, True)

	def test_M2(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'M2' ])
		self.assertEqual(i.end, True)

	def test_G17(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G17' ])
		self.assertEqual(i.plane, 'XY')

	def test_G18(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G18' ])
		self.assertEqual(i.plane, 'XZ')

	def test_G19(self):
		i = GCode.GCodeInterpreter()
		i.process([ 'G19' ])
		self.assertEqual(i.plane, 'YZ')

	def test_F1(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'F1' ])
		self.assertEqual(i.buffer, [ 'E', 'G21,1000', 'G20,1000' ])

	def test_F3(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'F3' ])
		self.assertEqual(i.buffer, [ 'E', 'G21,3000', 'G20,3000' ])

class TestInterpreterCoolantControl(unittest.TestCase):
	def test_M7(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M7' ])
		self.assertEqual(i.buffer, [ 'E', 'A53' ])

	def test_M7repeat(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M7' ])
		i.process([ 'M7' ])
		i.process([ 'M7' ])
		self.assertEqual(i.buffer, [ 'E', 'A53', 'E', 'E' ])

	def test_M8(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M8' ])
		self.assertEqual(i.buffer, [ 'E', 'A53' ])

	def test_M8repeat(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M8' ])
		i.process([ 'M8' ])
		i.process([ 'M8' ])
		self.assertEqual(i.buffer, [ 'E', 'A53', 'E', 'E' ])

	def test_M9(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.coolantEnable = True
		i.process([ 'M9' ])
		self.assertEqual(i.buffer, [ 'E', 'A51' ])

	def test_M9repeat(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.coolantEnable = True
		i.process([ 'M9' ])
		i.process([ 'M9' ])
		i.process([ 'M9' ])
		self.assertEqual(i.buffer, [ 'E', 'A51', 'E', 'E' ])

	def test_M9_initiallyOff(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M9' ])
		self.assertEqual(i.buffer, [ 'E' ])

	def test_M8M9_with_CCW_spindle(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M4', 'S3000' ])
		i.process([ 'M8' ])
		i.process([ 'M9' ])

		self.assertEqual(i.buffer, [
			'E', 'AD1', 'E', 'W100', 'E', 'D42', 'W100',
			'E', 'AD3',
			'E', 'AD1'
		])

class TestInterpreterSpindleCoolantCombinations(unittest.TestCase):
	def test_spindleControl_with_CCW_spindle(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M4', 'S3000' ])
		i.process([ 'M8' ])
		i.process([ 'M5' ])
		i.process([ 'M4', 'S4000' ])
		i.process([ 'M9' ])

		self.assertEqual(i.buffer, [
			'E', 'AD1', 'E', 'W100', 'E', 'D42', 'W100',
			'E', 'AD3',						# M8
			'E', 'AD2', 'E',					# M5
			'E', 'AD3',      'W100', 'E', 'D56', 'W100',		# M4 S4000
			'E', 'AD1'
		])

	def test_spindleControl_with_CCW_spindle(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S3000' ])
		i.process([ 'M8' ])
		i.process([ 'M5' ])
		i.process([ 'M3', 'S4000' ])
		i.process([ 'M9' ])

		self.assertEqual(i.buffer, [
			'E',        'E', 'W100', 'E', 'D42', 'W100',
			'E', 'A53',						# M8
			'E', 'A52', 'E',					# M5
			'E', 'A53',      'W100', 'E', 'D56', 'W100',		# M3 S4000
			'E', 'A51'
		])


class TestInterpreterSpindleSpeed(unittest.TestCase):
	def test_M3(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S3000' ])
		self.assertEqual(i.buffer, [ 'E', 'E', 'W100', 'E', 'D42', 'W100' ])

	def test_M3_multi(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S0' ])
		i.process([ 'M3', 'S1000' ])
		i.process([ 'M3', 'S2000' ])
		i.process([ 'M3', 'S3000' ])
		i.process([ 'M3', 'S4000' ])
		i.process([ 'M3', 'S5000' ])
		i.process([ 'M3', 'S10000' ])
		i.process([ 'M3', 'S15000' ])
		i.process([ 'M3', 'S20000' ])
		i.process([ 'M3', 'S30000' ])
		i.process([ 'M3', 'S40000' ])

		self.assertEqual(i.buffer, [
			'E', 'E', 'W100',
			'E', 'E', 'W100', 'E', 'D14', 'W100',  # S1000
			'E', 'E', 'W100', 'E', 'D28', 'W100',  # S2000
			'E', 'E', 'W100', 'E', 'D42', 'W100',  # S3000
			'E', 'E', 'W100', 'E', 'D56', 'W100',  # S4000
			'E', 'E', 'W100', 'E', 'D71', 'W100',  # S5000; WinPC-NC uses D70
			'E', 'E', 'W100', 'E', 'D141', 'W100', # S10000
			'E', 'E', 'W100', 'E', 'D212', 'W100', # S15000
			'E', 'E', 'W100', 'E', 'D255', 'W100', # S20000
			'E', 'E', 'W100', 'E',                 # S30000
			'E', 'E', 'W100', 'E',                 # S40000
		])

	def test_M4(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S8000' ])
		i.process([ 'M4', 'S5000' ])
		i.process([ 'M3', 'S6000' ])
		i.process([ 'M4', 'S7000' ])

		self.assertEqual(i.buffer, [
			'E',        'E', 'W100', 'E', 'D113', 'W100',
			'E', 'AD1', 'E', 'W100', 'E', 'D71',  'W100',   # WinPC-NC uses D70
			'E', 'A51', 'E', 'W100', 'E', 'D85',  'W100',
			'E', 'AD1', 'E', 'W100', 'E', 'D99',  'W100',
		])

	def test_M5ccw(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S8000' ])
		i.process([ 'M4', 'S5000' ])
		i.process([ 'M5' ])
		i.process([ 'M4', 'S7000' ])

		self.assertEqual(i.buffer, [
			'E',        'E', 'W100', 'E', 'D113', 'W100',
			'E', 'AD1', 'E', 'W100', 'E', 'D71',  'W100',   # WinPC-NC uses D70
			'E', 'AD0', 'E',
			'E', 'AD1',      'W100', 'E', 'D99',  'W100',
		])


	def test_M5cw(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.process([ 'M3', 'S8000' ])
		i.process([ 'M5' ])
		i.process([ 'M3', 'S7000' ])

		self.assertEqual(i.buffer, [
			'E',        'E', 'W100', 'E', 'D113', 'W100',
			'E', 'A50', 'E',
			'E', 'A51',      'W100', 'E', 'D99',  'W100',
		])


	def test_M3_W100_behaviour_G0(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.position = [ 0, 0, 0 ]
		i.offsets = [ 30, 30, 10 ]
		i.process([ 'G0', 'X0', 'Y0' ])
		i.process([ 'M3', 'S5000' ])
		i.process([ 'G0', 'X1' ])
		i.process([ 'G1', 'X2' ])
		i.process([ 'G0', 'X3' ])

		self.assertEqual(i.buffer, [
			'E', 'V1,X30000,Y30000',
			'E', 'E', 'W100', 'E', 'D71', 'W100',  # WinPC-NC uses D70
			'E', 'V1,X31000',
			'E', 'E', 'C08', 'W10', 'V21,X32000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X33000',
		])

	def test_M3_W100_behaviour_G1G0G1G0(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.position = [ 0, 0, 0 ]
		i.offsets = [ 30, 30, 10 ]
		i.process([ 'G1', 'X0', 'Y0' ])
		i.process([ 'M3', 'S5000' ])
		i.process([ 'G0', 'X1' ])
		i.process([ 'G1', 'X2' ])
		i.process([ 'G0', 'X3' ])

		self.assertEqual(i.buffer, [
			'E', 'C08', 'W10', 'V21,X30000,Y30000',
			'E', 'E', 'W100', 'E', 'D71', 'W100',  # WinPC-NC uses D70
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X31000',
			'E', 'E', 'C08', 'W10', 'V21,X32000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X33000',
		])

	def test_M3_W100_behaviour_G0G1G1G0G1(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.position = [ 0, 0, 0 ]
		i.offsets = [ 30, 30, 10 ]
		i.process([ 'G0', 'X0', 'Y0' ])
		i.process([ 'M3', 'S5000' ])
		i.process([ 'G1', 'X1' ])
		i.process([ 'G1', 'Y1' ])
		i.process([ 'G0', 'X2' ])
		i.process([ 'G1', 'X3' ])

		self.assertEqual(i.buffer, [
			'E', 'V1,X30000,Y30000',
			'E', 'E', 'W100', 'E', 'D71', 'W100',  # WinPC-NC uses D70
			'E', 'E', 'C08', 'W10', 'V21,X31000',
			'E', 'V21,Y31000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X32000',
			'E', 'E', 'C08', 'W10', 'V21,X33000',
		])


	def test_M3_W100_behaviour_G0G1M3G1G0G1(self):
		i = GCode.GCodeInterpreter()
		i.buffer = []
		i.position = [ 0, 0, 0 ]
		i.offsets = [ 30, 30, 10 ]
		i.process([ 'G0', 'X0', 'Y0' ])
		i.process([ 'M3', 'S5000' ])
		i.process([ 'G1', 'X1' ])
		i.process([ 'M3', 'S7000' ])
		i.process([ 'G1', 'Y1' ])
		i.process([ 'G0', 'X2' ])
		i.process([ 'G1', 'X3' ])

		self.assertEqual(i.buffer, [
			'E', 'V1,X30000,Y30000',
			'E', 'E', 'W100', 'E', 'D71', 'W100',  # WinPC-NC uses D70
			'E', 'E', 'C08', 'W10', 'V21,X31000',
			'E', 'E', 'W100', 'E', 'D99', 'W100',
			'E', 'V21,Y31000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X32000',
			'E', 'E', 'C08', 'W10', 'V21,X33000',
		])




class TestRapidMotionG0(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 5.000, 0.0, 2.000 ]

	def test_G0_simpleX0(self):
		self.i.process([ 'G0', 'X0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X10000' ])

	def test_G0_simpleX10(self):
		self.i.process([ 'G0', 'X10' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X20000' ])

	def test_G0_simpleX10X20(self):
		self.i.process([ 'G0', 'X10' ])
		self.i.process([ 'G0', 'X20' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X20000', 'E', 'V1,X30000' ])

	def test_G0_simpleY10(self):
		self.i.process([ 'G0', 'Y10' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V2,Y20000' ])

	def test_G0_simpleY10Y20(self):
		self.i.process([ 'G0', 'Y10' ])
		self.i.process([ 'G0', 'Y20' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V2,Y20000', 'E', 'V2,Y30000' ])

	def test_G0_simpleXY0(self):
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V2,X10000,Y10000' ])

	def test_G0_simpleXY0(self):
		self.i.position = [ 5.000, 9.500, 2.000 ]
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X10000,Y10000' ])

	def test_G0_simpleX0_repeat(self):
		self.i.process([ 'G0', 'X0' ])
		self.i.process([ 'G0', 'X0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X10000' ])

	def test_G0_simpleY10_repeat(self):
		self.i.process([ 'G0', 'Y10' ])
		self.i.process([ 'G0', 'Y10' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V2,Y20000' ])

	def test_G0_simpleXY0_repeat(self):
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V2,X10000,Y10000' ])

	def test_G0_simpleZ0(self):
		self.i.process([ 'G0', 'Z0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V3,Z10000' ])

	def test_G0_simpleZ0Z10(self):
		self.i.process([ 'G0', 'Z0' ])
		self.i.process([ 'G0', 'Z10' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V3,Z10000', 'E', 'V3,Z20000' ])

	def test_G0_incrXXX(self):
		self.i.process([ 'G0', 'X0' ])
		self.i.process([ 'G91' ])
		self.i.process([ 'G0', 'X5' ])
		self.i.process([ 'G0', 'X5' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X10000', 'E', 'V1,X15000', 'E', 'V1,X20000' ])


class WriteZOnFirstMove(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 9.000, 9.000, 0.000 ]

	def test_firstMove(self):
		self.i.process([ 'G91' ])
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V3,X10000,Y10000,Z10000' ])

	def test_secondMove(self):
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.i.process([ 'G91' ])
		self.i.process([ 'G0', 'X1', 'Y1' ])
		self.assertEqual(self.i.buffer, [ 'E', 'V1,X10000,Y10000', 'E', 'V1,X11000,Y11000' ])



class TestCoordinatedMotionG1(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 5.000, 0.0, 2.000 ]

	def test_G1_simpleX0(self):
		self.i.process([ 'G1', 'X0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'C08', 'W10', 'V21,X10000' ])

	def test_G1_simpleZ0(self):
		self.i.process([ 'G1', 'Z0' ])
		self.assertEqual(self.i.buffer, [ 'E', 'C08', 'W10', 'V21,Z10000' ])

	def test_G1_simpleXYZ1(self):
		self.i.process([ 'G1', 'X1' ])
		self.i.process([ 'G1', 'Y1' ])
		self.i.process([ 'G1', 'Z1' ])
		self.assertEqual(self.i.buffer, [ 'E', 'C08', 'W10', 'V21,X11000', 'E', 'V21,Y11000', 'E', 'V21,Z11000' ])

	def test_G1_simpleXYZ1_G91(self):
		self.i.process([ 'G91' ])
		self.i.process([ 'G1', 'X1' ])
		self.i.process([ 'G1', 'Y1' ])
		self.i.process([ 'G1', 'Z1' ])
		self.assertEqual(self.i.buffer, [ 'E', 'C08', 'W10', 'V21,X11000,Y10000,Z10000', 'E', 'V21,Y11000', 'E', 'V21,Z11000' ])

class TestG0G1Switching(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 9.000, 9.000, 0.000 ]

	def test_G0G1G0(self):
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.i.process([ 'G1', 'X5', 'Y5' ])
		self.i.process([ 'G0', 'X0', 'Y0' ])
		self.assertEqual(self.i.buffer, [
			'E', 'V1,X10000,Y10000',
			'E', 'E', 'C08', 'W10', 'V21,X15000,Y15000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X10000,Y10000'
		])

	def test_G1G0G1G0(self):
		self.i.process([ 'G1', 'X0', 'Y0' ])
		self.i.process([ 'G1', 'X1', 'Y0' ])
		self.i.process([ 'G0', 'X1', 'Y2' ])
		self.i.process([ 'G0', 'X3', 'Y3' ])
		self.i.process([ 'G1', 'X4', 'Y5' ])
		self.i.process([ 'G1', 'X6', 'Y6' ])
		self.i.process([ 'G0', 'X1', 'Y1' ])
		self.i.process([ 'G0', 'X0', 'Y0' ])

		self.assertEqual(self.i.buffer, [
			'E', 'C08', 'W10', 'V21,X10000,Y10000',
			'E', 'V21,X11000',
			'E', 'C10', 'W10',
			'E', 'C10', 'W10', 'V2,Y12000',
			'E', 'V1,X13000,Y13000',
			'E', 'E', 'C08', 'W10', 'V21,X14000,Y15000',
			'E', 'V21,X16000,Y16000',
			'E', 'C10', 'W10', 'E', 'C10', 'W10', 'V1,X11000,Y11000',
			'E', 'V1,X10000,Y10000',
		])

class TestCirclesCW(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 9.000, 9.000, 0.000 ]

	def test_basicQuarterCircle(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-10', 'Y-5', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p-1570796'
		])

	def test_basicHalfCircle(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-30', 'Y15', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p-3141592'
		])

	def test_basicQuarterCircle2(self):
		self.i.process([ 'G0', 'X-10', 'Y-5' ])
		self.i.process([ 'G2', 'X-30', 'Y15', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X0,Y5000',
			'E', 'E', 'C08', 'W10', 'K21,x0,y20000,p-1570796'
		])

	def test_basicQuarterCircle(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-10', 'Y-5', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p-1570796'
		])

	def test_basicArcWith20Degrees(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X8.79385241572', 'Y21.8404028665', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x18794,y6840,p-349044'
		])

	def test_oneMoreStrangeArc(self):
		self.i.process([ 'G0', 'X5', 'Y5' ])
		self.i.process([ 'G2', 'X0', 'Y5', 'R10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X15000,Y15000',
			# WinPC-NC calculates K21,x-2500,y9682,p-505383 here
			# I can't figure out where they round one of the values
			# to get 505383 instead of 505360; using the latter
			# which is just 0.004% off
			'E', 'E', 'C08', 'W10', 'K21,x-2500,y9682,p-505360'
		])

	def test_basicQuarterCircleCenterFormat(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-10', 'Y-5', 'I-20', 'J0' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p-1570796'
		])

	def test_basicQuarterCircleCenterFormatJustI(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-10', 'Y-5', 'I-20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p-1570796'
		])


	def test_basicThreeQuarterCircle1(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G2', 'X-10', 'Y-5', 'J-20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x0,y-20000,p-4712388'
		])

	def test_basicThreeQuarterCircle2(self):
		self.i.process([ 'G0', 'X10', 'Y0' ])
		self.i.process([ 'G2', 'X0', 'Y10', 'I-10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X20000,Y10000',
			'E', 'E', 'C08', 'W10', 'K21,x-10000,y0,p-4712388'
		])

	def test_basicThreeQuarterCircle3(self):
		self.i.process([ 'G0', 'X0', 'Y-10' ])
		self.i.process([ 'G2', 'X10', 'Y0', 'J10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X10000,Y0',
			'E', 'E', 'C08', 'W10', 'K21,x0,y10000,p-4712388'
		])

	def test_basicThreeQuarterCircle4(self):
		self.i.process([ 'G0', 'X-10', 'Y0' ])
		self.i.process([ 'G2', 'X0', 'Y-10', 'I10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X0,Y10000',
			'E', 'E', 'C08', 'W10', 'K21,x10000,y0,p-4712388'
		])


class TestAngleCalcCW(unittest.TestCase):
	def test_angleCalcCW_0(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCW(1, 0), 0)

	def test_angleCalcCW_4thPI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCW(math.cos(-math.pi / 4), math.sin(-math.pi / 4)), 3), round(math.pi / 4, 3))

	def test_angleCalcCW_HalfPI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCW(math.cos(-math.pi / 2), math.sin(-math.pi / 2)), math.pi / 2)

	def test_angleCalcCW_4thPI3(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCW(math.cos(math.pi / 4 * 5), math.sin(math.pi / 4 * 5)), 3), round(math.pi / 4 * 3, 3))

	def test_angleCalcCW_PI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCW(math.cos(math.pi), math.sin(math.pi)), 3), round(math.pi, 3))

	def test_angleCalcCW_4thPI5(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCW(math.cos(math.pi / 4 * 3), math.sin(math.pi / 4 * 3)), 3), round(math.pi / 4 * 5, 3))

	def test_angleCalcCW_HalfPI3(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCW(math.cos(math.pi / 2), math.sin(math.pi / 2)), math.pi / 2 * 3)

	def test_angleCalcCW_4thPI7(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCW(math.cos(math.pi / 4), math.sin(math.pi / 4)), 3), round(math.pi / 4 * 7, 3))

class TestAngleCalcCCW(unittest.TestCase):
	def test_angleCalcCCW_0(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCCW(1, 0), 0)

	def test_angleCalcCCW_4thPI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCCW(math.cos(math.pi / 4), math.sin(math.pi / 4)), 3), round(math.pi / 4, 3))

	def test_angleCalcCCW_HalfPI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCCW(math.cos(math.pi / 2), math.sin(math.pi / 2)), math.pi / 2)

	def test_angleCalcCCW_4thPI3(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCCW(math.cos(math.pi / 4 * 3), math.sin(math.pi / 4 * 3)), 3), round(math.pi / 4 * 3, 3))

	def test_angleCalcCCW_PI(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCCW(math.cos(math.pi), math.sin(math.pi)), 3), round(math.pi, 3))

	def test_angleCalcCCW_4thPI5(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCCW(math.cos(math.pi / 4 * 5), math.sin(math.pi / 4 * 5)), 3), round(math.pi / 4 * 5, 3))

	def test_angleCalcCCW_HalfPI3(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(i.angleCalcCCW(math.cos(math.pi / 2 * 3), math.sin(math.pi / 2 * 3)), math.pi / 2 * 3)

	def test_angleCalcCCW_4thPI7(self):
		i = GCode.GCodeInterpreter()
		self.assertEqual(round(i.angleCalcCCW(math.cos(math.pi / 4 * 7), math.sin(math.pi / 4 * 7)), 3), round(math.pi / 4 * 7, 3))


class TestCirclesCCW(unittest.TestCase):
	def setUp(self):
		self.i = GCode.GCodeInterpreter()
		self.i.buffer = []
		self.i.position = [ 9.000, 9.000, 0.000 ]

	def test_basicQuarterCircle(self):
		self.i.process([ 'G0', 'X-10', 'Y0' ])
		self.i.process([ 'G3', 'X0', 'Y-10', 'I10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X0,Y10000',
			'E', 'E', 'C08', 'W10', 'K21,x10000,y0,p1570797'
		])

	def test_basicHalfCircle(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G3', 'X-30', 'Y15', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p3141593'
		])

	def test_basicArcWith20Degrees(self):
		self.i.process([ 'G0', 'X10', 'Y15' ])
		self.i.process([ 'G3', 'X8.79385241572', 'Y21.8404028665', 'R20' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V2,X20000,Y25000',
			'E', 'E', 'C08', 'W10', 'K21,x-20000,y0,p349045'
		])

	def test_basicThreeQuarterCircle(self):
		self.i.process([ 'G0', 'X10', 'Y0' ])
		self.i.process([ 'G3', 'X0', 'Y-10', 'I-10' ])

		self.assertEqual(self.i.buffer, [
			'E', 'V1,X20000,Y10000',
			'E', 'E', 'C08', 'W10', 'K21,x-10000,y0,p4712389'
		])


class TestParameterizedProgramming(unittest.TestCase):
	def test_readParametersReturnFalseOnNonParam(self):
		i = GCode.GCodeInterpreter()
		r = i.readParameters('M30')
		self.assertEqual(r, False)

	def test_parameterParsing(self):
		i = GCode.GCodeInterpreter()
		i.readParameters('#100=0.002000')
		self.assertEqual(i.parameters[100], 0.002)

	def test_parameterSubstitution(self):
		i = GCode.GCodeInterpreter()
		i.parameters[100] = 0.002
		r = i.substituteParameters('G0 Z#100')
		self.assertEqual(r, 'G0 Z0.002000')

	def test_parameterSubstitutionMulti(self):
		i = GCode.GCodeInterpreter()
		i.parameters[100] = 10
		i.parameters[101] = 5
		r = i.substituteParameters('G0 X#100 Y#100 Z#101')
		self.assertEqual(r, 'G0 X10 Y10 Z5')

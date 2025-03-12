from _layout import Layout

class Booter(Layout):

	def __init__(self,*args,**kwargs):

		super().__init__(*args,**kwargs)

	def get(self,axis,index):
		
		axin = axis.inset_axes(super().get(index))

		axin.yaxis.set_inverted(True)

		axin.xaxis.set_label_position('top')
		axin.xaxis.set_ticks_position('top')

		return axin

	def set(self,axin):

		axin.set_zorder(-1)
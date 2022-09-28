import dirsetup

import core
import textio

names = ["john","timothy","sabrina"]
lasts = ["harkins","bob","elizabeth"]
ages = [32,25,1]

frame = core.frame(names=names,lasts=lasts,ages=ages)

header = textio.header(
    heads=['names','lasts','ages'],
    units=[None,None,None],
    infos=[' ',' ',' '])

file = textio.utxt(frame)

file.write("sample.txt",comment="")

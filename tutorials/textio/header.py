import dirsetup

from core import frame

from textio import header

names = ["john","timothy","sabrina"]
lasts = ["harkins","bob","elizabeth"]
ages = [32,25,1]

# frame = frame(names=names,lasts=lasts,ages=ages)

header = header(
    heads=['names','lasts','ages'],
    units=[None,None,None],
    infos=[' ',' ',' '])

print(header)

header.extend(["gender",None," "])

print(header)

print(header.heads)

print(header["lasts"])

# file = textio.utxt(frame)

# file.write("sample.txt",comment="")

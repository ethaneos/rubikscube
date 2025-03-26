from vpython import *
sizeOfPart = 1
colour = {
    "white": vec(1,1,1),
    "red": vec(1,0,0),
    "green": vec(0,1,0),
    "blue": vec(0,0,1),
    "cyan": vec(0,1,1),
    "magenta": vec(1,0,1),
    "yellow": vec(1,1,0),
    "orange": vec(1,0.6,0),
    "purple": vec(0.4,0.2,0.6),
    "black": vec(0,0,0)
}
def createPart(location, colours):
    dispCalc = lambda lst, size: (lst+lst*0.02*size)
    displacement = list(map(dispCalc, location, [sizeOfPart]*len(location)))
    side5 = box(pos=vec(displacement[0], displacement[1], displacement[2]+sizeOfPart/2), length=sizeOfPart, height=sizeOfPart, width=sizeOfPart/50, color=colour[colours["f"]])
    side6 = box(pos=vec(displacement[0], displacement[1], displacement[2]-sizeOfPart/2), length=sizeOfPart, height=sizeOfPart, width=sizeOfPart/50, color=colour[colours["o"]])
    side1 = box(pos=vec(displacement[0]+sizeOfPart/2, displacement[1], displacement[2]), length=sizeOfPart/50, height=sizeOfPart, width=sizeOfPart, color=colour[colours["r"]])
    side2 = box(pos=vec(displacement[0]-sizeOfPart/2, displacement[1], displacement[2]), length=sizeOfPart/50, height=sizeOfPart, width=sizeOfPart, color=colour[colours["l"]])
    side3 = box(pos=vec(displacement[0], displacement[1]+sizeOfPart/2, displacement[2]), length=sizeOfPart, height=sizeOfPart/50, width=sizeOfPart, color=colour[colours["t"]])
    side4 = box(pos=vec(displacement[0], displacement[1]-sizeOfPart/2, displacement[2]), length=sizeOfPart, height=sizeOfPart/50, width=sizeOfPart, color=colour[colours["b"]])
    return [side1, side2, side3, side4, side5, side6]

right = compound(createPart(
    [1,0,0],
    {
    "f": "black",
    "o": "black",
    "r": "orange",
    "l": "black",
    "t": "black",
    "b": "black"
}))
left = compound(createPart(
    [-1,0,0],
    {
    "f": "white",
    "o": "red",
    "r": "blue",
    "l": "green",
    "t": "cyan",
    "b": "magenta"
}))
topleftfront = compound(createPart(
    [-1,1,1],
    {
    "f": "white",
    "o": "red",
    "r": "blue",
    "l": "green",
    "t": "cyan",
    "b": "magenta"
}))
frontright = compound(createPart(
    [1,0,1],
    {
    "f": "white",
    "o": "red",
    "r": "blue",
    "l": "green",
    "t": "cyan",
    "b": "magenta"
}))
input("enter something to close")
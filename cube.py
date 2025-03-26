from vpython import *
sizeOfPart = 1
colours = {
    "blue": vec(0,0,1),
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
def createPart(data):
    side1 = box(pos=vec(sizeOfPart/2, 0, 0), length=sizeOfPart/50, height=sizeOfPart, width=sizeOfPart, color=colours[colour])
    side2 = box(pos=vec(-sizeOfPart/2, 0, 0), length=sizeOfPart/50, height=sizeOfPart, width=sizeOfPart, color=colours[colour])
    side3 = box(pos=vec(0, sizeOfPart/2, 0), length=sizeOfPart, height=sizeOfPart/50, width=sizeOfPart, color=colours[colour])
    side4 = box(pos=vec(0, -sizeOfPart/2, 0), length=sizeOfPart, height=sizeOfPart/50, width=sizeOfPart, color=colours[colour])
    side5 = box(pos=vec(0, 0, sizeOfPart/2), length=sizeOfPart, height=sizeOfPart, width=sizeOfPart/50, color=colours[colour])
    side6 = box(pos=vec(0, 0, -sizeOfPart/2), length=sizeOfPart, height=sizeOfPart, width=sizeOfPart/50, color=colours[colour])
    return [side1, side2, side3, side4, side5, side6]

part1 = compound(createPart("blue"))
input("enter something to close")
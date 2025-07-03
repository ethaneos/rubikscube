from vpython import *

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

class Part:
    __sizeOfPart = 0.9
    parts = {}
    def __init__(self, location: list):
        self.init_loc = location
        self.part = self.initialisePart(location)
        self.location = vec(location[0], location[1], location[2])
        Part.parts[location] = self

    def createSide(self, partLoc, sideLoc, colour_of_side):
        size = Part.__sizeOfPart
        return box(pos=vec(partLoc[0]+size*sideLoc[0]/2, partLoc[1]+size*sideLoc[1]/2, partLoc[2]+size*sideLoc[2]/2), 
                length=size-size*49/50*abs(sideLoc[0]), height=size-size*49/50*abs(sideLoc[1]), width=size-size*49/50*abs(sideLoc[2]), 
                color=colour[colour_of_side])

    def initialisePart(self, location):
        part = []
        for axis in range(3):
            for side in [-1,1]:
                sideLoc = [0,0,0]
                sideLoc[axis] = side
                try:
                    colourOfSide = cube[tuple(sideLoc)][location]
                except KeyError:
                    colourOfSide = "black"
                part.append(self.createSide(location, sideLoc, colourOfSide))
        return part

    @classmethod
    def movesTranslate(cls, moves: str):
        moveList = moves.split(" ")
        for move in moveList:
            cls.moveTranslate(move)

    @classmethod
    def moveTranslate(cls, move: str):
        moveParts = list(move)
        match moveParts[0]:
            case "U":
                face = [0,1,0]
            case "D":
                face = [0,-1,0]
            case "R":
                face = [1,0,0]
            case "L":
                face = [-1,0,0]
            case "F":
                face = [0,0,1]
            case "B":
                face = [0,0,-1]
        
        rotation = 1
        if len(moveParts) > 1:
            match moveParts[1]:
                case "2":
                    rotation = 2
                case "'":
                    rotation = -1
        
        cls.rotateSide(face, rotation)


    @classmethod
    def rotateSide(cls, face: list, rotation: int):
        for i in range(len(face)):
            if face[i] != 0:
                faceInfo = {"axis": i, "face": face[i]}
                break
        forRoteParts = []
        newPartDict = {}
        for location in cls.parts.keys():
            if location[faceInfo["axis"]] == faceInfo["face"]:
                for i in range(len(cls.parts[location].part)):
                    forRoteParts.append(cls.parts[location].part[i].clone())
                    cls.parts[location].part[i].visible = False
                    cls.parts[location].part[i].rotate(axis = vec(face[0], face[1], face[2]), angle = -1 * (pi / 2) * rotation, origin = vec(0,0,0))
                cls.parts[location].location = rotate(cls.parts[location].location, axis = vec(face[0], face[1], face[2]), angle = -1 * (pi / 2) * rotation)
                newLocation = []
                for i in range(0,3):
                    axis = []
                    for j in range(0,3):
                        if i == j:
                            axis.append(1)
                        else:
                            axis.append(0)
                    axisVec = vec(axis[0], axis[1], axis[2])
                    newLocation.append(int(round(dot(cls.parts[location].location, axisVec), 0)))
                cls.parts[location].location = vec(newLocation[0], newLocation[1], newLocation[2])
                newPartDict[tuple(newLocation)] = cls.parts[location]
        
        forRoteComp = compound(forRoteParts)
        Part.animateRotate(forRoteComp, vec(face[0], face[1], face[2]), -1 * (pi / 2) * rotation, 20)
        
        for location in cls.parts.keys():
            if location[faceInfo["axis"]] == faceInfo["face"]:
                for i in range(len(cls.parts[location].part)):
                    cls.parts[location].part[i].visible = True

        forRoteComp.visible = False
        cls.parts.update(newPartDict)
    
    @staticmethod
    def animateRotate(obj, axis, angle, ticks):
        for i in range(0,ticks):    
            obj.rotate(axis=axis, angle=angle/ticks, origin=vec(0, 0, 0))
            rate(60)
    
        

if __name__ == "__main__":
    cubeTop = {
        (-1,1,-1):"yellow", (0,1,-1):"yellow", (1,1,-1):"yellow",
        (-1,1,0): "yellow", (0,1,0): "yellow", (1,1,0): "yellow",
        (-1,1,1): "yellow", (0,1,1): "yellow", (1,1,1): "yellow"
    }
    cubeLeft = {
        (-1,1,-1): "red", (-1,1,0): "red", (-1,1,1): "red",
        (-1,0,-1): "red", (-1,0,0): "red", (-1,0,1): "red",
        (-1,-1,-1):"red", (-1,-1,0):"red", (-1,-1,1):"red"
    }
    cubeFront = {
        (-1,1,1): "green", (0,1,1): "green", (1,1,1): "green",
        (-1,0,1): "green", (0,0,1): "green", (1,0,1): "green",
        (-1,-1,1):"green", (0,-1,1):"green", (1,-1,1):"green"
    }
    cubeRight = {
        (1,1,1): "orange", (1,1,0): "orange", (1,1,-1): "orange",
        (1,0,1): "orange", (1,0,0): "orange", (1,0,-1): "orange",
        (1,-1,1):"orange", (1,-1,0):"orange", (1,-1,-1):"orange"
    }
    cubeOpposite = {
        (1,1,-1): "blue", (0,1,-1): "blue", (-1,1,-1): "blue",
        (1,0,-1): "blue", (0,0,-1): "blue", (-1,0,-1): "blue",
        (1,-1,-1):"blue", (0,-1,-1):"blue", (-1,-1,-1):"blue"
    }
    cubeBottom = {
        (-1,-1,1): "white", (0,-1,1): "white", (1,-1,1): "white",
        (-1,-1,0): "white", (0,-1,0): "white", (1,-1,0): "white",
        (-1,-1,-1):"white", (0,-1,-1):"white", (1,-1,-1):"white"
    }
    cube = {
                            (0,1,0): cubeTop,
        (-1,0,0): cubeLeft, (0,0,1): cubeFront, (1,0,0): cubeRight, (0,0,-1): cubeOpposite,
                            (0,-1,0): cubeBottom
    }

    new_scene = canvas(background = color.white)
    for x in range(-1,2):
        for y in range(-1,2):
            for z in range(-1,2):
                location = (x,y,z)
                if location == (0,0,0):
                    continue
                else:
                    part = Part(location)
    
    Part.movesTranslate("R U R' U R U2 R'")
    
    input("enter something to close")
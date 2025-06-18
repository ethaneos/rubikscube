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

class Part:
    parts = {}
    def __init__(self, location: list):
        self.init_loc = location
        self.part = self.initialisePart(location)
        Part.parts[location] = self

    def createSide(self, partLoc, sideLoc, colour_of_side):
        return box(pos=vec(partLoc[0]*1.1+sizeOfPart*sideLoc[0]/2, partLoc[1]*1.1+sizeOfPart*sideLoc[1]/2, partLoc[2]*1.1+sizeOfPart*sideLoc[2]/2), 
                length=sizeOfPart-sizeOfPart*49/50*abs(sideLoc[0]), height=sizeOfPart-sizeOfPart*49/50*abs(sideLoc[1]), width=sizeOfPart-sizeOfPart*49/50*abs(sideLoc[2]), 
                color=colour[colour_of_side])

    def initialisePart(self, location):
        part = []
        for axis in range(3):
            for side in [-1,1]:
                sideLoc = [0,0,0]
                sideLoc[axis] = side
                try:
                    colour_of_side = cube[tuple(sideLoc)][location]
                except KeyError:
                    colour_of_side = "black"
                part.append(self.createSide(location, sideLoc, colour_of_side))
        return compound(part)

    @classmethod
    def rotateSide(cls, face: list, rotation: int):
        for i in range(len(face)):
            if face[i] != 0:
                face_info = {"axis": i, "face": face[i]}
                break
        for location in cls.parts.keys():
            if location[face_info["axis"]] == face_info["face"]:
                pass

if __name__ == "__main__":
    cubeTop = {
        (-1,1,-1):"yellow", (0,1,-1):"yellow", (1,1,-1):"yellow",
        (-1,1,0): "yellow", (0,1,0): "yellow", (1,1,0): "yellow",
        (-1,1,1): "yellow", (0,1,1): "yellow", (1,1,1): "yellow"
    }
    cubeLeft = {
        (-1,1,-1): "orange", (-1,1,0): "orange", (-1,1,1): "orange",
        (-1,0,-1): "orange", (-1,0,0): "orange", (-1,0,1): "orange",
        (-1,-1,-1):"orange", (-1,-1,0):"orange", (-1,-1,1):"orange"
    }
    cubeFront = {
        (-1,1,1): "green", (0,1,1): "green", (1,1,1): "green",
        (-1,0,1): "green", (0,0,1): "green", (1,0,1): "green",
        (-1,-1,1):"green", (0,-1,1):"green", (1,-1,1):"green"
    }
    cubeRight = {
        (1,1,1): "red", (1,1,0): "red", (1,1,-1): "red",
        (1,0,1): "red", (1,0,0): "red", (1,0,-1): "red",
        (1,-1,1):"red", (1,-1,0):"red", (1,-1,-1):"red"
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
    
    input("enter something to close")
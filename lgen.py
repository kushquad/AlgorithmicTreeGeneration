import pymel.core as pm
import maya.cmds as cmds
import math
import random

### Fractal tree plant L-system parameters ###

# The initial seed for the Lsystem
startstring = "X"

# Rules are repeatedly applied to the startstring to generate newer strings
# Dictionary is structured as, 'symbol to replace' : 'symbols to replace with', probability of application
# Probability of application makes sense only when stochastic is set to True
rules = {"X":("F-[[X]+X]+F[+FX]-X",0.75),"F":("FF",0.25)}

# The initial bend from the XZ plane, used for the first stroke
initangle = 25

# The angle to turn by for successive strokes
turnangle = 25

# Number of iterations to repeat rule application before rendering (do not recommend exceeding 7/8)
iterations = 5

# The length of each forward stroke
distance = 0.25

# How much to extrude the curve along the Y-axis
thickness = 0.1

# Whether randomness should be used for generation
stochastic = True

# Converting curve group to a renderable poly/NURBS group
# using extrude tool
convertTo3D = True

# Control conversion into polygons or NURBS
convertToPoly = False

##################### L-SYSTEM CODE #####################
# Apply rule transformations on currentstring
# The rules are applied one after the other
def applyRules(currentstring):
    newstring = []
    for ch in currentstring:
        if ch in rules.keys():
            # Apply probability of application if stochastic
            # is enabled
            if stochastic==True:
                if random.random()<=rules[ch][1]:
                    newstring.append(rules[ch][0])
                else:
                    newstring.append(ch)
            else:
                newstring.append(rules[ch][0])
        else:
            newstring.append(ch)
    return "".join(newstring)

##################### DRAWING CODE #####################
# Move a unit 'distance' along a given angle from a given position
# Vector math
def forwardPosition(pos, angle):
    return (pos[0]+distance*math.cos(angle), pos[1], pos[2]+distance*math.sin(angle))
   
# Draw a line segment using a degree 1 EV curve
# Knot vector must be the same size of number of endpoints i.e 2
def drawSegment(curpos, newpos, segments):
    segment = pm.curve(d=1,p=[curpos,newpos],k=[0,1])
    segments.append(segment)
    
# Since this LSystem requires store and load of data,
# we implement it with a stack instead of recursion
def renderString(currentstring):
    stack = []
    segments = []
    curpos = (0,0,0)
    curangle = initangle
    
    for ch in currentstring:

        # Move forward by 1 unit 
        #    - calculate new position
        #    - draw segment, update position
        if ch=='F':
            newpos = forwardPosition(curpos, curangle)
            drawSegment(curpos, newpos, segments)
            curpos = newpos

        # Move left by turnangle
        if ch=='-':
            curangle -= turnangle

        # Move right by turnangle
        if ch=='+':
            curangle += turnangle

        # Store contents in stack
        if ch=='[':
            stack.append((curpos, curangle))
        
        # Pop top of stack, assign to curpos, curangle
        if ch==']':
            curpos, curangle = stack[-1]
            stack.pop()

        # 'X' is a dummy variable, just controls the growth indirectly

    # Group all the curves, center the pivot and return
    curvegroup = pm.group(segments, n='leaf')
    pm.xform(curvegroup, cp=True)
    return (segments,curvegroup)

##################### 3D CONVERSION CODE #####################
# Use extrude tool to increase curve thickness along Y-axis
def convertToNurbsPoly(curves):
    extrudes = []
    for curve in curves:
        extrude = pm.extrude(curve, ch=True, rn=False, po=convertToPoly, et=0, upn=False, d=(0,1,0), l=thickness, ro=0, sc=1, dl=1)
        extrudes.append(extrude)
    
    # Group extrudes, center pivot and return
    extrudegroup = pm.group(extrudes, n='leaf3d')
    pm.xform(extrudegroup, cp=True)
    return extrudes,extrudegroup

##################### MAIN DRIVER #####################
def executeGen():    
    currentstring = startstring
    for i in xrange(0,iterations):
        currentstring = applyRules(currentstring)
    curves,curvegroup = renderString(currentstring)
    pm.rotate(curvegroup, [0,0,90])
    if convertTo3D:
        extrudes, extrudegroup = convertToNurbsPoly(curves)
        pm.delete(curvegroup)
        
##################### UI CODE #####################        
def showInterface():
    window = cmds.window(title="LGen")
    cmds.columnLayout()
    ia = cmds.textFieldGrp(label='Initial Angle', text=initangle)
    ta = cmds.textFieldGrp(label='Turn Angle', text=turnangle)
    iter = cmds.textFieldGrp(label='Iterations', text=iterations)
    dd = cmds.textFieldGrp(label='Draw distance', text=distance)
    thick = cmds.textFieldGrp(label='Thickness', text=thickness)
    stoch = cmds.checkBox(label='Stochastic', value=stochastic)
    c3d = cmds.checkBox(label='Convert to 3D', value=convertTo3D)
    cp = cmds.checkBox(label='Convert to Polygons (else Nurbs)', value=convertToPoly)
    
    # Get value of settings, assign to global settings defined above
    def assignAndLaunch(args):
        global initangle, turnangle, iterations, drawdistance
        global thickness, stochastic, convertTo3D, converToPoly
        
        initangle = float(cmds.textFieldGrp(ia, query=True, text=True))
        turnangle = float(cmds.textFieldGrp(ta, query=True, text=True))
        iterations = int(cmds.textFieldGrp(iter, query=True, text=True))
        drawdistance = float(cmds.textFieldGrp(dd, query=True, text=True))
        thickness = float(cmds.textFieldGrp(thick, query=True, text=True))
        stochastic = cmds.checkBox(stoch, query=True, value=True)
        convertTo3D = cmds.checkBox(c3d, query=True, value=True)
        convertToPoly = cmds.checkBox(cp, query=True, value=True)
        executeGen()
        
    cmds.button(label="Generate",command = assignAndLaunch)
    cmds.showWindow()

# Launch UI    
showInterface()

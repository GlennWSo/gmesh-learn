# This script takes an STL triangulation and creates a brep with a plane surface
# for each triangle

import gmsh
import sys
import numpy as np
import pyvista as pv

def get_poly_data() -> pv.PolyData:
    """extract points and facas from gmsh and
     cosntructs a pyvista.PolyData instance"""

    mesh = gmsh.model.mesh
    typ = 2 # 3-node triangles

    elementTags, _ = gmsh.model.mesh.getElementsByType(typ)
    node_dict = {val: index for (index, val) in enumerate(mesh.getNodes()[0])}

    faces = np.array([[node_dict[key] for key in mesh.getElement(tag)[1]] for tag in elementTags])
    faces = np.pad(faces, pad_width=((0,0), (1,0)), constant_values=3)
    points = np.array([mesh.getNode(index)[0] for index in mesh.getNodes()[0]])
    
    return pv.PolyData(points, faces) 

def mesh2brep():
    """
    constructs a brep in gmsh from gmsh.model.mesh
    the brep is then stored in memory in gmsh.model.occ

    """

    typ = 2 # 3-node triangles
    elementTags, elementNodes = gmsh.model.mesh.getElementsByType(typ)
    nodeTags, nodeCoord, derp = gmsh.model.mesh.getNodesByElementType(typ)
    edgeNodes = gmsh.model.mesh.getElementEdgeNodes(typ)



    # create a new model to store the BREP
    gmsh.model.add('my brep')

    # create a geometrical point for each mesh node
    nodes = dict(zip(nodeTags, np.reshape(nodeCoord, (len(nodeTags), 3))))
    for n in nodes.items():
        gmsh.model.occ.addPoint(n[1][0], n[1][1], n[1][2], tag=n[0])

    # create a geometrical plane surface for each (triangular) element
    allsurfaces = []
    allcurves = {}
    elements = dict(zip(elementTags, np.reshape(edgeNodes, (len(elementTags), 3, 2))))
    for e in elements.items():
        curves = []
        for edge in e[1]:
            ed = tuple(np.sort(edge))
            if ed not in allcurves:
                t = gmsh.model.occ.addLine(edge[0], edge[1])
                allcurves[ed] = t
            else:
                t = allcurves[ed]
            curves.append(t)
        cl = gmsh.model.occ.addCurveLoop(curves)
        allsurfaces.append(gmsh.model.occ.addPlaneSurface([cl]))

    # create a volume bounded by all the surfaces
    sl = gmsh.model.occ.addSurfaceLoop(allsurfaces)
    gmsh.model.occ.addVolume([sl])

    gmsh.model.occ.synchronize()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: {} file.stl'.format(sys.argv[0]))
        # exit(0)
        input_mesh = "sphere.stl"
    else:
        input_mesh = sys.argv[1]

    gmsh.initialize()

    # load the STL mesh and retrieve the element, node and edge data
    gmsh.open(input_mesh)

    poly = get_poly_data()
    poly.plot()

    mesh2brep()    
    
    


    gmsh.write("test.step")

    gmsh.fltk.run()

    gmsh.finalize()

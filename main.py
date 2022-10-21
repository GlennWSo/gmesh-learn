import numpy as np
import warnings
warnings.filterwarnings("ignore")

import gmsh
gmsh.initialize()

gmsh.model.add("dfg 3D")
l = 2.5
b = 0.41
h = 0.41
r = 0.05

channel = gmsh.model.occ.addBox(0,0,0, l, b, h)
cylinder = gmsh.model.occ.addCylinder(0.5, 0, 0.2, 0, b, 0, r)

fluid = gmsh.model.occ.cut([(3, channel)], [(3, cylinder)])
gmsh.model.occ.synchronize()
volumes = gmsh.model.getEntities(dim=3)
assert(volumes == fluid[0])

fluid_marker = 11
gmsh.model.addPhysicalGroup(volumes[0][0], [volumes[0][1]], fluid_marker)
gmsh.model.setPhysicalName(volumes[0][0], fluid_marker, "Fluid_volume")
print("works so far..")

surfaces = gmsh.model.occ.getEntities(dim=2)
inlet_marker, outlet_marker, wall_marker, obstacle_marker = 1, 3, 5, 7
walls = []
obstacles = []
for surface in surfaces:
    com = gmsh.model.occ.getCenterOfMass(surface[0], surface[1])
    if np.allclose(com, [0, b/2, h/2]):
        gmsh.model.addPhysicalGroup(surface[0], [surface[1]], inlet_marker)
        inlet = surface[1]
        gmsh.model.setPhysicalName(surface[0], inlet_marker, "Fluid inlet")
    elif np.allclose(com, [l, b/2, h/2]):
        gmsh.model.addPhysicalGroup(surface[0], [surface[1]], outlet_marker)
        gmsh.model.setPhysicalName(surface[0], outlet_marker, "Fluid outlet")
    elif np.isclose(com[2], 0) or np.isclose(com[1], b) or np.isclose(com[2], h) or np.isclose(com[1],0):
        walls.append(surface[1])
    else:
        obstacles.append(surface[1])

gmsh.model.addPhysicalGroup(2, walls, wall_marker)
gmsh.model.setPhysicalName(2, wall_marker, "Walls")
gmsh.model.addPhysicalGroup(2, obstacles, obstacle_marker)
gmsh.model.setPhysicalName(2, obstacle_marker, "Obstacle")

distance = gmsh.model.mesh.field.add("Distance")
gmsh.model.mesh.field.setNumbers(distance, "FacesList", obstacles)

resolution = r/10
threshold = gmsh.model.mesh.field.add("Threshold")
gmsh.model.mesh.field.setNumber(threshold, "IField", distance)
gmsh.model.mesh.field.setNumber(threshold, "LcMin", resolution)
gmsh.model.mesh.field.setNumber(threshold, "LcMax", 20*resolution)
gmsh.model.mesh.field.setNumber(threshold, "DistMin", 0.5*r)
gmsh.model.mesh.field.setNumber(threshold, "DistMax", r)

def set_threshold(dist_tags, lc_min=.01, lc_max=0.1, d_min=0.1, d_max=1):
    distance_field = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", dist_tags)
    threshold_field = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(threshold_field, "IField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "LcMin", lc_min)
    gmsh.model.mesh.field.setNumber(threshold_field, "LcMax", lc_max)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", d_min)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", d_max)
    return threshold_field


inlet_thre = set_threshold([inlet])

minimum = gmsh.model.mesh.field.add("Min")
gmsh.model.mesh.field.setNumbers(minimum, "FieldsList", [threshold, inlet_thre])
gmsh.model.mesh.field.setAsBackgroundMesh(inlet_thre)

gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

output_name = "mesh3d.msh"
gmsh.fltk.run()
gmsh.write(output_name)

print(f"saved mesh to file: {output_name}")

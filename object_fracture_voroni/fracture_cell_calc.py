# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# Script copyright (C) Blender Foundation 2012


def points_as_bmesh_cells(verts, points, margin=0.01):
    import mathutils
    from mathutils import Vector

    cells = []

    sortedVoronoiPoints = [p for p in points]
    plane_indices = []
    vertices = []

    # there are many ways we could get planes - convex hull for eg
    # but it ends up fastest if we just use bounding box
    if 1:
        xa = [v[0] for v in verts]
        ya = [v[1] for v in verts]
        za = [v[2] for v in verts]
        
        xmin, xmax = min(xa) - margin, max(xa) + margin
        ymin, ymax = min(ya) - margin, max(ya) + margin
        zmin, zmax = min(za) - margin, max(za) + margin
        convexPlanes = [
            Vector((+1.0, 0.0, 0.0, -abs(xmax))),
            Vector((-1.0, 0.0, 0.0, -abs(xmin))),
            Vector((0.0, +1.0, 0.0, -abs(ymax))),
            Vector((0.0, -1.0, 0.0, -abs(ymin))),
            Vector((0.0, 0.0, +1.0, -abs(zmax))),
            Vector((0.0, 0.0, -1.0, -abs(zmin))),
            ]

    for i, curVoronoiPoint in enumerate(points):
        planes = [None] * len(convexPlanes)
        for j in range(len(convexPlanes)):
            planes[j] = convexPlanes[j].copy()
            planes[j][3] += planes[j].xyz.dot(curVoronoiPoint)
        maxDistance = 10000000000.0  # a big value!

        sortedVoronoiPoints.sort(key=lambda p: (p - curVoronoiPoint).length_squared)

        for j in range(1, len(points)):
            normal = sortedVoronoiPoints[j] - curVoronoiPoint
            nlength = normal.length
            if nlength > maxDistance:
                break

            plane = normal.normalized()
            plane.resize_4d()
            plane[3] = -nlength / 2.0
            planes.append(plane)
            
            vertices[:], plane_indices[:] = mathutils.geometry.points_in_planes(planes)
            if len(vertices) == 0:
                break

            if len(plane_indices) != len(planes):
                planes[:] = [planes[k] for k in plane_indices]

            maxDistance = vertices[0].length
            for k in range(1, len(vertices)):
                distance = vertices[k].length
                if maxDistance < distance:
                    maxDistance = distance
            maxDistance *= 2.0

        if len(vertices) == 0:
            continue

        cells.append((curVoronoiPoint, vertices[:]))
        vertices[:] = []

    return cells

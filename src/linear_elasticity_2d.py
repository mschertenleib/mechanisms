import os.path
import webbrowser

import numpy as np
from netgen.geom2d import SplineGeometry
from ngsolve import *
from ngsolve.webgui import Draw


def stress(strain, mu, lam):
    return 2.0 * mu * strain + lam * Trace(strain) * Id(strain.shape[0])


def strain(displacement):
    return Sym(Grad(displacement))


def main() -> None:
    # NOTE: All values in standard units: m, N, Pa
    length = 0.2
    height = 0.02
    width = 0.03
    force = -100.0
    E = 70e9  # Young's modulus
    nu = 0.35  # Poisson's ratio

    geo = SplineGeometry()

    p1, p2, p3, p4 = [
        geo.AppendPoint(x, y) for x, y in [(0, 0), (length, 0), (length, height), (0, height)]
    ]
    geo.Append(["line", p1, p2])
    geo.Append(["line", p2, p3], bc="force")
    geo.Append(["line", p3, p4])
    geo.Append(["line", p4, p1], bc="fix")
    mesh = Mesh(geo.GenerateMesh(maxh=height / 5.0))

    # Lamé parameters
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))

    fes = VectorH1(mesh, order=2, dirichlet="fix")
    u = fes.TrialFunction()
    v = fes.TestFunction()
    gfu = GridFunction(fes)

    a = BilinearForm(InnerProduct(stress(strain(u), mu=mu, lam=lam), strain(v)) * dx)
    a.Assemble()

    f = LinearForm(CoefficientFunction((0, force / (width * height))) * v * ds("force"))
    f.Assemble()

    inv = a.mat.Inverse(freedofs=fes.FreeDofs(), inverse="sparsecholesky")
    gfu.vec.data = inv * f.vec

    Draw(gfu, filename="out.html")
    webbrowser.open("file://" + os.path.abspath("out.html"))

    coords = np.asarray([node.point for node in mesh.vertices])
    disp = gfu(mesh(x=coords[:, 0], y=coords[:, 1]))
    numerical_deflection = np.mean(disp[coords[:, 0] == length, 1])
    print(f"Numerical Y deflection:  {numerical_deflection:.9f} m")


if __name__ == "__main__":
    main()

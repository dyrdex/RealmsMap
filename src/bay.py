"""The small bay at Ocean Keep: one smooth rounded bowl (an ellipse), so it has no square corners.
The town sits at its south end, and the bay opens out to the north-east. Used by the forest fill (which stops at the bay) and by the shore cut."""
import numpy as np

CX, CY, A, B = 51.5, -38.9, 3.5, 3.0            # centre and half-widths: it reaches west only to x = 48.0, just beyond the town's west edge (49.3)


def bay_mask(x, y):
    """True inside the bay. The edge has a very slight natural wobble."""
    wob = 1 + 0.035 * np.sin(2.6 * x + 0.8) + 0.03 * np.sin(3.3 * y + 0.4)
    return (((x - CX) / (A * wob)) ** 2 + ((y - CY) / (B * wob)) ** 2) < 1

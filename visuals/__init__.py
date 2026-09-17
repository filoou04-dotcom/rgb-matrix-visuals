from .plasma import FluidPlasma
from .metaballs import LiquidMetaballs
from .color_waves import FluidWaves

EFFECTS = {
    "plasma": FluidPlasma,
    "metaballs": LiquidMetaballs,
    "waves": FluidWaves,
}

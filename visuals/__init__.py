from .plasma import FluidPlasma
from .metaballs import LiquidMetaballs
from .color_waves import FluidWaves

EFFECTS = {
    "1": FluidPlasma,
    "2": LiquidMetaballs,
    "3": FluidWaves,
    "plasma": FluidPlasma,
    "metaballs": LiquidMetaballs,
    "waves": FluidWaves,
}

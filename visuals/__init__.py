from .plasma import FluidPlasma
from .metaballs import LiquidMetaballs
from .color_waves import FluidWaves
from .minimal_art import MinimalArtSuite

EFFECTS = {
    "minimal": MinimalArtSuite,
    "plasma": FluidPlasma,
    "metaballs": LiquidMetaballs,
    "waves": FluidWaves,
}

from .plasma import FluidPlasma
from .metaballs import LiquidMetaballs
from .color_waves import FluidWaves
from .silhouette_walker import SilhouetteWalker
from .neon_eye import NeonEye
from .mainz_livecam import MainzLiveCam
from .star_chaos import StarChaos
from .lava_lamp import LavaLamp

EFFECTS = {
    "1": FluidPlasma,
    "2": LiquidMetaballs,
    "3": FluidWaves,
    "4": SilhouetteWalker,
    "5": NeonEye,
    "6": MainzLiveCam,
    "7": StarChaos,
    "8": LavaLamp,
    "plasma": FluidPlasma,
    "metaballs": LiquidMetaballs,
    "waves": FluidWaves,
    "walker": SilhouetteWalker,
    "eye": NeonEye,
    "neon_eye": NeonEye,
    "livecam": MainzLiveCam,
    "mainz": MainzLiveCam,
    "star": StarChaos,
    "star_chaos": StarChaos,
    "lavalamp": LavaLamp,
    "lava": LavaLamp,
}

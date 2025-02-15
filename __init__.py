from .nodes.free_gpu import FreeGPUMemory

NODE_CLASS_MAPPINGS = {
    "FreeGPUMemory": FreeGPUMemory
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreeGPUMemory": "Free GPU Memory"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 
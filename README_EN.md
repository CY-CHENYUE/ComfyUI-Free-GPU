# ComfyUI-Free-GPU

English | [简体中文](README.md)

## Introduction

`ComfyUI-Free-GPU` provides a node for releasing RAM and VRAM in ComfyUI.
When your workflow requires loading multiple models and memory becomes tight, this node can help free up used memory to make space for subsequent workflow operations.

## Example
![alt text](img/Snipaste_2025-02-16_21-20-00.png)


## Installation

### 1. Manual Installation

1. Locate your ComfyUI custom nodes directory, typically at `<ComfyUI Installation Path>/custom_nodes/`.
2. Open a terminal, navigate to this directory, and clone the project using:
   ```
   git clone https://github.com/CY-CHENYUE/ComfyUI-Free-GPU.git
   ```
3. Restart ComfyUI, and the new node will be automatically loaded.

### 2. Install via ComfyUI Manager

1. Launch ComfyUI and open the Manager.
2. Search for **ComfyUI-Free-GPU**.
3. Click the install button, and the system will automatically download and configure the node.

## Usage

- When the system encounters insufficient memory or models need to be reloaded, you can use this node to actively release RAM and VRAM, unload loaded models, and clear caches.
- During execution, the node will sequentially call memory cleaning, model unloading, and cache reset operations, and automatically notify the system to refresh model loading status.

## Note
The node calls the /free interface to notify the system to reset model status. This may require workflows to reload nodes when running again.


---

## Contact Me

- X (Twitter): [@cychenyue](https://x.com/cychenyue)
- TikTok: [@cychenyue](https://www.tiktok.com/@cychenyue)
- YouTube: [@CY-CHENYUE](https://www.youtube.com/@CY-CHENYUE)
- BiliBili: [@CY-CHENYUE](https://space.bilibili.com/402808950)
- XiaoHongShu: [@CY-CHENYUE](https://www.xiaohongshu.com/user/profile/6360e61f000000001f01bda0) 
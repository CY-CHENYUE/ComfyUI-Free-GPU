# ComfyUI-Free-GPU

[English](README_EN.md) | 简体中文

## 项目简介

`ComfyUI-Free-GPU` 提供了用于释放内存(RAM)和显存(VRAM)的节点。
当工作流中需要加载大量模型导致显存紧张，可以释放已经使用的占用，为后续工作流留出运行空间。

## 示例
![alt text](img/Snipaste_2025-02-16_21-20-00.png)


## 安装方式

### 1. 手动安装

1. 找到你本地 ComfyUI 的节点目录，通常位于 `<ComfyUI 安装目录>/custom_nodes/`。
2. 打开命令行终端，进入该目录，然后通过下面的命令将本项目克隆到节点目录：
   ```
   git clone https://github.com/CY-CHENYUE/ComfyUI-Free-GPU.git
   ```
3. 重启 ComfyUI，新的节点将会自动加载。

### 2. 通过 ComfyUI 节点管理器安装

1. 启动 ComfyUI 并打开节点管理器。
2. 在节点管理器中搜索 **ComfyUI-Free-GPU**。
3. 点击安装按钮，系统将自动下载并配置该节点。

## 使用说明

- 当系统遇到内存不足或模型需要重新加载时，可通过该节点主动释放内存(RAM)和显存(VRAM)、卸载已加载模型以及清理缓存。
- 该节点在执行过程中，会依次调用内存清理、模型卸载以及缓存重置操作，并自动通知系统刷新模型加载状态。

## 其他
调用 /free 接口，通知系统重置模型状态。可能会让工作流再次运行需要重新加载运行节点。


---

## Contact Me

- X (Twitter): [@cychenyue](https://x.com/cychenyue)
- TikTok: [@cychenyue](https://www.tiktok.com/@cychenyue)
- YouTube: [@CY-CHENYUE](https://www.youtube.com/@CY-CHENYUE)
- BiliBili: [@CY-CHENYUE](https://space.bilibili.com/402808950)
- 小红书: [@CY-CHENYUE](https://www.xiaohongshu.com/user/profile/6360e61f000000001f01bda0)
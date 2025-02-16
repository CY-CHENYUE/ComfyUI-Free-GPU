import gc
import torch
import psutil
import comfy.model_management
import time
import sys
import os

# 添加ComfyUI根目录到Python路径
COMFY_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if COMFY_PATH not in sys.path:
    sys.path.insert(0, COMFY_PATH)

try:
    import cuda_malloc
except ImportError:
    print("[Memory Release] 警告: 无法导入cuda_malloc")
    cuda_malloc = None

class FreeGPUMemory:
    """GPU内存释放节点 - 用于释放GPU/CPU内存、卸载已加载模型以及清理各种缓存，以便在内存紧张时重置系统状态."""
    
    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("status", )
    FUNCTION = "release_memory"
    CATEGORY = "Free-Gpu"
    OUTPUT_NODE = True
    DESCRIPTION = "释放GPU和CPU内存、卸载模型以及清理缓存。该节点专门用于在GPU资源紧张时释放内存"
    # 添加这个属性来标记节点会影响全局状态
    GLOBAL_STATE_CHANGE = True
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "anything": ("STRING,IMAGE,LATENT,MODEL,VAE,CLIP,CONDITIONING", {}),
                "clear_cache": ("BOOLEAN", {"default": True}),
                "clear_models": ("BOOLEAN", {"default": True}),
                "protocol": (["http", "https"], {"default": "http"}),
                "api_host": ("STRING", {"default": "127.0.0.1"}),
                "api_port": ("INT", {"default": 8188, "min": 1, "max": 65535}),
            }
        }

    def get_memory_info(self):
        """获取当前内存使用情况"""
        process = psutil.Process()
        cpu_memory = process.memory_info().rss / 1024 / 1024
        
        info_str = []
        if torch.cuda.is_available():
            gpu_allocated = torch.cuda.memory_allocated() / 1024 / 1024
            gpu_reserved = torch.cuda.memory_reserved() / 1024 / 1024
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            
            info_str.append(f"\n[Memory Release] 当前内存使用情况:")
            info_str.append(f"- CPU 内存: {cpu_memory:.2f}MB")
            info_str.append(f"- GPU 内存:")
            info_str.append(f"  已分配: {gpu_allocated:.2f}MB")
            info_str.append(f"  已预留: {gpu_reserved:.2f}MB")
            info_str.append(f"  总容量: {total_memory:.2f}MB")
            info_str.append(f"  使用率: {(gpu_allocated/total_memory*100):.1f}%")
        
        return (
            cpu_memory, 
            gpu_allocated if 'gpu_allocated' in locals() else 0, 
            gpu_reserved if 'gpu_reserved' in locals() else 0,
            "\n".join(info_str)
        )

    def release_memory(self, anything, clear_cache=True, clear_models=True, protocol="http", api_host="127.0.0.1", api_port=8188):
        """执行内存释放操作"""
        try:
            # 定义日志列表，并重载 print，在本函数内捕获所有打印信息
            logs = []
            def print(*args, **kwargs):
                s = " ".join(str(arg) for arg in args)
                logs.append(s)
            
            print("\n[Memory Release] === 开始执行内存释放 ===")
            
            # 获取初始内存状态
            cpu_before, gpu_allocated_before, gpu_reserved_before, info_str = self.get_memory_info()
            logs.append(info_str)
            
            # 1. 使用cuda_malloc的功能
            if cuda_malloc is not None:
                if hasattr(cuda_malloc, 'get_cached_memory'):
                    print("\n[Memory Release] 清理CUDA缓存内存...")
                    cached = cuda_malloc.get_cached_memory()
                    if cached > 0:
                        cuda_malloc.free_cached_memory()
                
                if hasattr(cuda_malloc, 'get_memory_info'):
                    print("[Memory Release] 获取CUDA内存信息...")
                    total, free, used = cuda_malloc.get_memory_info()
                    if used > 0:
                        print(f"- 已使用: {used/1024/1024:.2f}MB")
            
            # 2. 卸载模型
            if clear_models:
                print("\n[Memory Release] 卸载模型...")
                # [提示] 本处不保存当前加载的模型信息，直接清空，以保证下次工作流模型节点能够重新加载
                if hasattr(comfy.model_management, 'unload_all_models'):
                    comfy.model_management.unload_all_models()
                
                for obj in gc.get_objects():
                    try:
                        if torch.is_tensor(obj):
                            obj.storage().resize_(0)
                            del obj
                        elif hasattr(obj, 'data') and torch.is_tensor(obj.data):
                            obj.data.storage().resize_(0)
                            del obj.data
                    except:
                        pass

                if hasattr(comfy.model_management, 'current_loaded_models'):
                    comfy.model_management.current_loaded_models.clear()
                    comfy.model_management.models_need_reload = True

                if hasattr(comfy.model_management, 'vram_state'):
                    comfy.model_management.vram_state = None

                if hasattr(comfy.model_management, 'model_cache'):
                    comfy.model_management.model_cache.clear()

                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

                time.sleep(0.5)
            
            # 3. 清理缓存
            if clear_cache:
                print("[Memory Release] 清理缓存...")
                model_manager = comfy.model_management
                for cache_name in ['model_cache', 'vae_cache', 'clip_cache']:
                    cache = getattr(model_manager, cache_name, None)
                    if cache is not None and isinstance(cache, dict):
                        cache.clear()
                
                if hasattr(model_manager, 'soft_empty_cache'):
                    model_manager.soft_empty_cache(force=True)
                
                gc.collect()
                
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.reset_max_memory_allocated()
                
                if hasattr(model_manager, 'models_need_reload'):
                    model_manager.models_need_reload = True
            
            time.sleep(1)
            
            cpu_after, gpu_allocated_after, gpu_reserved_after, info_str = self.get_memory_info()
            logs.append(info_str)
            
            cpu_freed = cpu_before - cpu_after
            gpu_allocated_freed = gpu_allocated_before - gpu_allocated_after
            gpu_reserved_freed = gpu_reserved_before - gpu_reserved_after
            
            logs.append(f"\n[Memory Release] 释放效果:")
            logs.append(f"- CPU 释放: {cpu_freed:.2f}MB")
            logs.append(f"- GPU 已分配内存释放: {gpu_allocated_freed:.2f}MB")
            logs.append(f"- GPU 预留内存释放: {gpu_reserved_freed:.2f}MB")
            
            if gpu_allocated_freed > 0 or gpu_reserved_freed > 0:
                logs.append("\n[Memory Release] 释放成功!")
            else:
                logs.append("\n[Memory Release] 提示:")
                logs.append("1. 如果正在生成图片，建议等待完成后再释放")
                logs.append("2. 如果释放效果不理想，可以尝试重启 ComfyUI")

            # 主动调用 /free 接口，通知系统刷新模型加载状态
            if clear_models:
                try:
                    import requests
                    api_url = f"{protocol}://{api_host}:{api_port}/free"
                    requests.post(api_url, json={"free_memory": True, "unload_models": True})
                    logs.append("[Memory Release] 成功调用 /free 接口，通知系统重置模型状态")
                except Exception as e:
                    logs.append(f"[Memory Release] 调用 /free 接口失败 ({protocol}://{api_host}:{api_port}): {e}")

            result_str = "\n".join(logs)
            return (result_str, )
            
        except Exception as e:
            err_str = f"\n[Memory Release] 错误: {str(e)}\n错误类型: {type(e)}\n错误位置: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}"
            logs.append(err_str)
            return ("Memory release failed: " + err_str, ) 
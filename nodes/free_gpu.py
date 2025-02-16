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
    """GPU内存释放节点"""
    
    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("status", )
    FUNCTION = "release_memory"
    CATEGORY = "Free-Gpu"
    OUTPUT_NODE = True
    # 添加这个属性来标记节点会影响全局状态
    GLOBAL_STATE_CHANGE = True
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "anything": ("STRING,IMAGE,LATENT,MODEL,VAE,CLIP,CONDITIONING", {}),
                "purge_cache": ("BOOLEAN", {"default": True}),
                "purge_models": ("BOOLEAN", {"default": True}),
            }
        }

    def get_memory_info(self):
        """获取当前内存使用情况"""
        process = psutil.Process()
        cpu_memory = process.memory_info().rss / 1024 / 1024
        
        if torch.cuda.is_available():
            gpu_allocated = torch.cuda.memory_allocated() / 1024 / 1024
            gpu_reserved = torch.cuda.memory_reserved() / 1024 / 1024
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            
            print(f"\n[Memory Release] 当前内存使用情况:")
            print(f"- CPU 内存: {cpu_memory:.2f}MB")
            print(f"- GPU 内存:")
            print(f"  已分配: {gpu_allocated:.2f}MB")
            print(f"  已预留: {gpu_reserved:.2f}MB")
            print(f"  总容量: {total_memory:.2f}MB")
            print(f"  使用率: {(gpu_allocated/total_memory*100):.1f}%")
        
        return cpu_memory, gpu_allocated if 'gpu_allocated' in locals() else 0, gpu_reserved if 'gpu_reserved' in locals() else 0

    def release_memory(self, anything, purge_cache=True, purge_models=True):
        """执行内存释放操作"""
        try:
            print("\n[Memory Release] === 开始执行内存释放 ===")
            
            # 获取初始内存状态
            cpu_before, gpu_allocated_before, gpu_reserved_before = self.get_memory_info()
            
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
            if purge_models:
                print("\n[Memory Release] 卸载模型...")

                # Save current model info so that auto load works later.
                saved_models = {}
                if hasattr(comfy.model_management, 'current_loaded_models'):
                    saved_models = dict(comfy.model_management.current_loaded_models)

                # 先卸载所有模型
                if hasattr(comfy.model_management, 'unload_all_models'):
                    comfy.model_management.unload_all_models()

                # 强制清理所有模型相关的内存
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

                # 清空已加载模型的注册表，确保下次运行工作流时模型节点可以重新加载模型。
                if hasattr(comfy.model_management, 'current_loaded_models'):
                    comfy.model_management.current_loaded_models.clear()
                    # 设置标识，通知后续节点必须重新加载模型
                    comfy.model_management.models_need_reload = True

                if hasattr(comfy.model_management, 'vram_state'):
                    comfy.model_management.vram_state = None

                # 清理模型缓存
                if hasattr(comfy.model_management, 'model_cache'):
                    comfy.model_management.model_cache.clear()

                # 强制执行垃圾回收
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

                time.sleep(0.5)
            
            # 3. 清理缓存
            if purge_cache:
                print("[Memory Release] 清理缓存...")
                # 清理各种缓存
                model_manager = comfy.model_management
                for cache_name in ['model_cache', 'vae_cache', 'clip_cache']:
                    cache = getattr(model_manager, cache_name, None)
                    if cache is not None and isinstance(cache, dict):
                        cache.clear()
                
                # 使用ComfyUI的缓存清理
                if hasattr(model_manager, 'soft_empty_cache'):
                    model_manager.soft_empty_cache(force=True)
                
                # Python垃圾回收
                gc.collect()
                
                if torch.cuda.is_available():
                    # 同步GPU操作
                    torch.cuda.synchronize()
                    
                    # 清理CUDA缓存
                    torch.cuda.empty_cache()
                    
                    # 重置峰值统计
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.reset_max_memory_allocated()
                
                # 同时设置标识，确保其他节点捕捉到模型需要重新加载
                if hasattr(model_manager, 'models_need_reload'):
                    model_manager.models_need_reload = True
            
            # 等待清理完成
            time.sleep(1)
            
            # 获取释放后的内存状态
            cpu_after, gpu_allocated_after, gpu_reserved_after = self.get_memory_info()
            
            # 计算释放量
            cpu_freed = cpu_before - cpu_after
            gpu_allocated_freed = gpu_allocated_before - gpu_allocated_after
            gpu_reserved_freed = gpu_reserved_before - gpu_reserved_after
            
            print(f"\n[Memory Release] 释放效果:")
            print(f"- CPU 释放: {cpu_freed:.2f}MB")
            print(f"- GPU 已分配内存释放: {gpu_allocated_freed:.2f}MB")
            print(f"- GPU 预留内存释放: {gpu_reserved_freed:.2f}MB")
            
            if gpu_allocated_freed > 0 or gpu_reserved_freed > 0:
                print("\n[Memory Release] 释放成功!")
            else:
                print("\n[Memory Release] 提示:")
                print("1. 如果正在生成图片，建议等待完成后再释放")
                print("2. 如果释放效果不理想，可以尝试重启 ComfyUI")

            # 主动调用 /free 接口，通知系统刷新模型加载状态
            try:
                import requests
                # 根据你的 ComfyUI 配置修改端口号，此处示例为8188
                requests.post("http://127.0.0.1:8188/free", json={"free_memory": True, "unload_models": True})
                print("[Memory Release] 成功调用 /free 接口，通知系统重置模型状态")
            except Exception as e:
                print(f"[Memory Release] 调用 /free 接口失败: {e}")

            return (f"Memory released successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}!", )
            
        except Exception as e:
            print(f"\n[Memory Release] 错误: {str(e)}")
            print(f"错误类型: {type(e)}")
            print(f"错误位置: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            return ("Memory release failed!", ) 
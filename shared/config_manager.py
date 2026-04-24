import json
import os

try:
    from filelock import FileLock, Timeout
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

class ConfigManager:
    """
    Gestor centralizado para la lectura y escritura segura de archivos JSON.
    Implementa D.R.Y (Don't Repeat Yourself) y bloqueos de proceso (FileLock) 
    para evitar corrupciones cuando el Launcher y el Bot acceden al mismo archivo.
    """
    @staticmethod
    def load_json(path, use_lock=False):
        if not os.path.exists(path):
            return {}
        
        try:
            if use_lock and HAS_FILELOCK:
                lock = FileLock(f"{path}.lock", timeout=1.0)
                with lock:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
            else:
                if use_lock and not HAS_FILELOCK:
                    print(f"[ConfigManager] ADVERTENCIA: 'filelock' no está instalado. Leyendo {path} sin protección.")
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[ConfigManager] Error leyendo {path}: {e}")
            return {}

    @staticmethod
    def save_json(path, data, use_lock=False):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            if use_lock and HAS_FILELOCK:
                lock = FileLock(f"{path}.lock", timeout=1.0)
                with lock:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Error guardando {path}: {e}")
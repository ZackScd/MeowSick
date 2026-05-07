import os
import sys
import asyncio
import re

class TTSManager:
    """
    Gestor abstracto para la generación de Texto-a-Voz (TTS).
    Soporta múltiples motores (Edge-TTS, Piper) e inyección de filtros como RVC.
    """
    def __init__(self):
        if getattr(sys, 'frozen', False): 
            self.base_dir = os.path.dirname(sys.executable)
        else: 
            self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.downloads_dir = os.path.join(self.base_dir, "downloads")
        os.makedirs(self.downloads_dir, exist_ok=True)

    async def generate_tts(self, text, guild_id, config, lang):
        try: import edge_tts
        except ImportError: edge_tts = None
            
        if not edge_tts:
            print(lang.get("sys_ai_core_tts_no_lib"))
            return None

        # Limpiar texto de emojis, URLs y formato markdown para que la IA suene natural
        clean_text = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>', '', text) 
        clean_text = re.sub(r'http\S+', '', clean_text)
        clean_text = clean_text.replace('*', '').replace('`', '').replace('_', '').replace('~', '')
        clean_text = clean_text[:800].strip()
        if not clean_text: return None
        
        tts_engine = config.get("tts_engine", "nube_edge")
        
        if config.get("tts_rvc", False):
            print(lang.get("sys_ai_core_rvc_on"))
            # En el futuro, aquí se pasaría el 'tts_file' a través del modelo PyTorch local.

        if tts_engine == "local_piper":
            tts_file = os.path.join(self.downloads_dir, f"tts_ia_{guild_id}.wav")
            piper_exe = os.path.join(self.base_dir, "res", "piper", "piper.exe")
            voice_model = config.get("tts_voice", "es_MX-dalia-medium.onnx")
            model_path = os.path.join(self.base_dir, "res", "piper", "voices", voice_model)
            
            print(lang.get("sys_ai_core_tts_loc_gen").format(model=voice_model))
            try:
                if not os.path.exists(piper_exe) or not os.path.exists(model_path):
                    raise Exception("Binario de Piper o Modelo ONNX no encontrados.")
                process = await asyncio.create_subprocess_shell(
                    f'"{piper_exe}" -m "{model_path}" -f "{tts_file}"',
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await process.communicate(input=clean_text.encode('utf-8'))
                return tts_file
            except Exception as e:
                print(lang.get("sys_ai_core_tts_loc_err").format(e=e))
                tts_engine = "nube_edge" # Fallback automático a la nube
                
        if tts_engine == "nube_edge":
            tts_file = os.path.join(self.downloads_dir, f"tts_ia_{guild_id}.mp3")
            voice_model = config.get("tts_voice", "es-MX-DaliaNeural")
            print(lang.get("sys_ai_core_tts_cld_gen").format(model=voice_model))
            try:
                communicate = edge_tts.Communicate(clean_text, voice_model)
                await communicate.save(tts_file)
                return tts_file
            except Exception as e:
                print(lang.get("sys_ai_core_tts_cld_err").format(e=e))
                return None
        
        return None

tts_manager = TTSManager()
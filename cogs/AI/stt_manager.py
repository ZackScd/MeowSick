import base64

class STTManager:
    """
    Gestor abstracto para el Reconocimiento de Voz a Texto (STT).
    Soporta transcripción local (Whisper) o enrutamiento en Base64 para modelos en la nube.
    """
    async def transcribe(self, audio_path, audio_bytes, engine, lang, loop):
        transcript = None
        media_data = None
        
        if engine == "local":
            try: from faster_whisper import WhisperModel
            except ImportError: WhisperModel = None
            
            if not WhisperModel: raise Exception("Librería faster-whisper no instalada.")
            print(lang.get("sys_ai_core_stt_loc"))
            
            def run_transcribe():
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segs, _ = model.transcribe(audio_path, beam_size=5)
                return " ".join([s.text for s in segs])
                
            transcript = await loop.run_in_executor(None, run_transcribe)
        else:
            b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            media_data = ("audio/wav", b64_audio)
            
        return transcript, media_data

stt_manager = STTManager()
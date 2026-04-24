import os
from .config_manager import ConfigManager

class LanguageManager:
    """
    Gestor de Idiomas (i18n).
    Carga cadenas de texto desde archivos JSON en settings/locales/
    para permitir traducciones dinámicas de la interfaz.
    """
    def __init__(self, locales_dir, default_lang="es"):
        self.locales_dir = locales_dir
        self.strings = {}
        self.load_language(default_lang)

    def load_language(self, lang_code):
        """Carga el archivo de idioma especificado."""
        file_path = os.path.join(self.locales_dir, f"{lang_code}.json")
        
        if not os.path.exists(file_path):
            print(f"🌍 ⚠️ Idioma '{lang_code}' no encontrado. Usando 'es' por defecto.")
            file_path = os.path.join(self.locales_dir, "es.json")
        
        loaded_strings = ConfigManager.load_json(file_path, use_lock=False)
        if loaded_strings is not None:
            self.strings = loaded_strings
            print(f"🌍 Idioma '{lang_code}' cargado exitosamente.")
        else:
            self.strings = {}

    def get(self, key, default=None):
        """Obtiene un texto. Si no existe, muestra [clave] para evidenciar la falta de traducción."""
        return self.strings.get(key, default if default is not None else f"[{key}]")
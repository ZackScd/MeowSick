import os
from .config_manager import ConfigManager

class ThemeManager:
    """
    Gestor de Temas Visuales.
    Carga paletas de colores desde archivos JSON para permitir un theming dinámico.
    """
    def __init__(self, themes_dir, theme_name="dark"):
        self.themes_dir = themes_dir
        self.colors = {}
        self.load_theme(theme_name)

    def load_theme(self, theme_name):
        """Carga un archivo de tema JSON desde el directorio de temas."""
        theme_path = os.path.join(self.themes_dir, f"{theme_name}.json")
        
        loaded_colors = ConfigManager.load_json(theme_path)
        
        if loaded_colors:
            self.colors = loaded_colors
            print(f"🎨 Tema '{theme_name}' cargado exitosamente.")
        else:
            print(f"🎨 ⚠️ No se pudo cargar el tema '{theme_name}'. Usando diccionario vacío.")
            self.colors = {}

    def get(self, key, default=None):
        """Obtiene un valor de color por su clave."""
        return self.colors.get(key, default)
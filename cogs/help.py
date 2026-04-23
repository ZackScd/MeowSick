import discord
from discord.ext import commands
from discord.ui import View, Button

# --- 1. VISTAS INTERACTIVAS (UI VIEWS) ---

class ModuleView(View):
    """
    Vista secundaria de la interfaz de ayuda.
    Contiene únicamente un botón de 'Inicio' destinado a revertir la navegación
    de vuelta al menú principal de categorías.
    """
    def __init__(self, bot, ctx):
        # Invoca al constructor base definiendo un tiempo de vida (timeout) de 60 segundos.
        super().__init__(timeout=60)
        self.bot = bot # Mantiene la referencia a la instancia principal del bot.
        self.ctx = ctx # Mantiene el contexto original para la validación de eventos.

    async def interaction_check(self, interaction: discord.Interaction):
        """
        Gancho (hook) de seguridad invocado antes de procesar el callback de cualquier botón.
        Garantiza que la interacción proviene del mismo usuario que invocó el comando original.
        """
        if interaction.user != self.ctx.author:
            # Rechaza la interacción enviando un mensaje efímero (visible solo para el infractor).
            await interaction.response.send_message("No puedes usar este menú.", ephemeral=True)
            return False
        return True # Autoriza el flujo hacia el callback del botón.

    # Decorador que inyecta y renderiza un botón interactivo en los componentes del mensaje.
    @discord.ui.button(emoji="🏠", label="Inicio", style=discord.ButtonStyle.primary)
    async def home_button(self, interaction: discord.Interaction, button: Button):
        """Callback asíncrono ejecutado al presionar el botón 'Inicio'."""
        # Reconstruye el Embed raíz (Main Menu).
        embed = discord.Embed(
            title=f"🐱 MeowSick: {self.bot.user.display_name} - Ayuda",
            description="Selecciona un módulo para ver sus comandos:",
            color=0xbb9af7
        )
        embed.add_field(name="Módulos", value="🎵 Música\n🧠 Inteligencia Artificial", inline=False)
        
        # Instancia la vista principal (HelpView) para reemplazar la navegación actual.
        view = HelpView(self.bot, self.ctx)
        # Responde a la interacción editando el mensaje original para inyectar el nuevo estado.
        await interaction.response.edit_message(embed=embed, view=view)

class HelpView(View):
    """
    Vista principal (Root View) del sistema de ayuda.
    Alberga los botones que enrutan hacia los menús específicos de cada módulo.
    """
    def __init__(self, bot, ctx):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        """Validación de autoría delegada (idéntica a ModuleView)."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("No puedes usar este menú.", ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="🎵", label="Música", style=discord.ButtonStyle.secondary)
    async def music_button(self, interaction: discord.Interaction, button: Button):
        """Callback de enrutamiento hacia la documentación dinámica del módulo de Música."""
        # Intenta recuperar la instancia registrada del Cog de Música.
        cog = self.bot.get_cog("Music")
        if not cog:
            # Si el módulo fue deshabilitado desde configuración, alerta de su indisponibilidad.
            return await interaction.response.send_message("El módulo de música no está activo.", ephemeral=True)
            
        commands_list = []
        # Itera sobre el registro interno de comandos alojados dentro de la instancia del Cog.
        for command in cog.get_commands():
            # Filtra heurísticamente comandos definidos como invisibles (hidden=True).
            if not command.hidden:
                # Extrae la primera línea del atributo help (docstring) para listados concisos.
                desc = (command.help or "Sin descripción.").split("\n")[0]
                commands_list.append(f"`{command.name}`: {desc}")

        # Ensambla la salida uniendo las cadenas procesadas con saltos de línea.
        embed = discord.Embed(
            title="🎵 Música - Comandos",
            description="\n".join(commands_list),
            color=0xbb9af7
        )
        embed.set_footer(text="MeowSick Bot v3.0")
        # Refleja el cambio adjuntando ModuleView, lo que permite al usuario retornar al menú raíz.
        await interaction.response.edit_message(embed=embed, view=ModuleView(self.bot, self.ctx))

    @discord.ui.button(emoji="🧠", label="IA", style=discord.ButtonStyle.secondary)
    async def ai_button(self, interaction: discord.Interaction, button: Button):
        """Callback de enrutamiento estático hacia la documentación formativa del módulo IA."""
        # Dado que el módulo IA opera de forma pasiva mediante listeners y no comandos puros,
        # se inyecta un Embed con texto informativo harcodeado.
        embed = discord.Embed(
            title="🧠 Inteligencia Artificial",
            description="MeowSick cuenta con un sistema avanzado de IA que le permite interactuar de forma natural, aprender de ti y tener sus propias emociones.\n\n"
                        "**🗣️ ¿Cómo hablar con ella?**\n"
                        f"No necesitas comandos especiales. Solo tienes que **mencionarla** (`@{self.bot.user.display_name}`) o **responder a uno de sus mensajes**. Ella leerá los mensajes recientes automáticamente para entender el contexto.\n\n"
                        "**📚 Memoria y Aprendizaje**\n"
                        "El bot presta atención a los detalles importantes. Si le cuentas cosas sobre ti (tus gustos, de dónde eres, qué haces), ella lo recordará para futuras conversaciones.\n\n"
                        "**❤️ Afinidad y Relaciones**\n"
                        "MeowSick forma sus propias opiniones sobre cada usuario en secreto. Si eres amable, te tratará con más cariño; pero si la insultas o la molestas, se volverá fría o agresiva contigo.\n\n"
                        "**🎭 Sistema de Emociones**\n"
                        "Su humor no es un código fijo. Puede sentirse feliz, curiosa, triste o irritable dependiendo de lo que esté ocurriendo en el chat en ese momento.\n\n"
                        "**🎙️ Comandos de Voz y Módulos**\n"
                        "• `!voice`: Activa o desactiva la lectura en voz alta (TTS) de las respuestas de la IA.\n"
                        "• `!talk`: Activa o desactiva el panel interactivo para hablarle por micrófono.\n"
                        "• `!ask [pregunta]`: Busca información en internet en tiempo real y te responde.\n"
                        "• `!reloadai`: Recarga los módulos y la memoria de la IA en caliente (Solo Admin).\n\n",
            color=0xbb9af7
        )
        embed.set_footer(text="MeowSick Bot v3.0")
        # Edita el mensaje encolando el retroceso (ModuleView).
        await interaction.response.edit_message(embed=embed, view=ModuleView(self.bot, self.ctx))


# --- 2. MÓDULO PRINCIPAL DE AYUDA (COG) ---

class Help(commands.Cog):
    """
    Sustituye la ayuda nativa basada en texto de discord.py
    implementando una interfaz manejable a base de botones (Views).
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Captura el evento de carga del módulo sin emitir logs, preservando el flujo estándar."""
        pass # Mensaje silenciado para mantener la consola más limpia.

    # Definición pública del comando de ayuda usando sus alias respectivos.
    @commands.command(name="help")
    async def help_command(self, ctx):
        """Muestra el menú de ayuda interactivo."""
        # Construcción del marco visual raíz.
        embed = discord.Embed(
            title=f"🐱 MeowSick: {self.bot.user.display_name} - Ayuda",
            description="Selecciona un módulo para ver sus comandos:",
            color=0xbb9af7
        )
        embed.add_field(name="Módulos", value="🎵 Música\n🧠 Inteligencia Artificial", inline=False)
        # Instanciación y acoplamiento del controlador de eventos de interfaz (HelpView).
        view = HelpView(self.bot, ctx)
        await ctx.send(embed=embed, view=view)

# Punto de inyección asíncrona estándar para extensiones de discord.py
async def setup(bot):
    await bot.add_cog(Help(bot))
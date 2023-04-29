import discord
from discord import app_commands
from discord.ext import commands

from AI.openai_api import chatgpt_response, image_generator
from utils.logger_conf import DiscordBotLogger
from utils.utils import COMMAND_DESCRIPTIONS, DEFAULT_DM_MESSAGE

logger = DiscordBotLogger().get_logger()


class OpenAI(commands.Cog):
    def __init__(self, bot, ai):
        self.bot = bot
        self.ai = ai

    def log_command_execution(self, interaction: discord.Interaction):
        logger.command(f"Command '{interaction.data['name']}' executed by {str(interaction.user)}")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{__name__}: Initializing...")
        await self.bot.tree.sync()
        self.bot.loaded_cogs_count += 1
        logger.info(f"{__name__}: Initialized")

    @app_commands.command(name="chatgpt", description=COMMAND_DESCRIPTIONS["chatgpt"])
    async def chatgpt(self, interaction: discord.Interaction, message: str = None):
        """
        A function that sends a chatGPT response to the user's input message.

        Args:
            interaction (discord.Interaction): The interaction object representing the user command.
            message (str, optional): The message provided by the user. Defaults to None.
        """
        self.log_command_execution(interaction)
        if message is None:
            # If no message is provided by the user

            logger.warning("No message provided!")
            await interaction.response.send_message("Please provide a message to discuss with ChatGPT.", ephemeral=True)
        else:
            # If a message is provided by the user
            logger.command(f"{str(interaction.user)} >> {self.bot.user}: {message}")
            bot_response = await chatgpt_response(prompt=message)
            await interaction.response.send_message(f"{interaction.user.mention}: {bot_response}")
            logger.command(f"{self.bot.user} >> {str(interaction.user)}: {bot_response}")

    @app_commands.command(name="dm", description=COMMAND_DESCRIPTIONS["dm"])
    async def dm(self, interaction: discord.Interaction, message: str = None):
        self.log_command_execution(interaction)

        if message is None:
            message = "This is the default message when the user doesn't provide one."

        bot_response = DEFAULT_DM_MESSAGE
        await self.ai.handle_dm(interaction, message, bot_response, self.bot.user, str(interaction.user))
        await interaction.response.send_message("I have sent you a DM", ephemeral=True)

    @app_commands.command(name="image", description=COMMAND_DESCRIPTIONS["image"])
    async def image(
        self,
        interaction: discord.Interaction,
        message: str = None,
        size: str = None,
        num_of_pictures: int = None,
    ):
        self.log_command_execution(interaction)

        if message is None:
            await interaction.response.send_message(
                "You have to provide what you want the AI to generate.", ephemeral=True
            )
            return

        if size is None:
            size = "256x256"
        if num_of_pictures is None:
            num_of_pictures = 1

        # Acknowledge the interaction without sending a message
        await interaction.response.defer(ephemeral=True)

        generated_images = await image_generator(message, size, num_of_pictures)
        logger.info(generated_images)

        # Send each image URL as a separate embed in a follow-up message
        for image_url in generated_images:
            embed = discord.Embed()
            embed.set_image(url=image_url)
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot, ai):
    await bot.add_cog(OpenAI(bot, ai))

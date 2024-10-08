from discord.ext import commands
from captcha.image import ImageCaptcha
import discord, asyncio, os, dotenv, random, string, json

dotenv.load_dotenv()

client = commands.Bot(command_prefix="!", intents=discord.Intents.default())
client.remove_command("help")

with open("./dados.json", "r") as r:
    dados = json.load(r)

ROLE_CAPTCHA_REALIZADO = dados['captcha_realizado_role']
ROLE_CAPTCHA_BLOCKLISTED = dados['captcha_blocklisted_role']

def generate_captcha():
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    image = ImageCaptcha()
    image.write(text, f"{text}.png") 

    return text

@client.event
async def on_ready():
    await client.tree.sync()
    print("Iniciado!")

@client.event
async def on_interaction(interaction: discord.Interaction):
    try:    
        try:
            interaction.data['custom_id']
        except:
            return   
        if interaction.data['custom_id'] == "MENSAGEM_CAPTCHA":
            await interaction.response.defer(ephemeral=True)
            mensagem = await interaction.followup.send("Aguarde, gerando seu captcha.", ephemeral=True)
            for role in interaction.user.roles:
                if role.id == ROLE_CAPTCHA_BLOCKLISTED:
                    await mensagem.edit(content="Você está bloqueado de realizar captchas. Fale com a administração.")
                    return
                elif role.id == ROLE_CAPTCHA_REALIZADO:
                    await mensagem.edit(content="Você já realizou esse captcha.")
                    return

            captcha = generate_captcha()
            op1 = ''.join(random.sample(captcha, len(captcha)))
            op2 = ''.join(random.sample(captcha, len(captcha)))
            op3 = ''.join(random.sample(captcha, len(captcha)))
            while op1 == captcha:
                op1 = ''.join(random.sample(captcha, len(captcha)))
            while op2 == captcha or op2 == op1:
                op2 = ''.join(random.sample(captcha, len(captcha)))
            while op3 == captcha or op3 == op2:
                op3 = ''.join(random.sample(captcha, len(captcha)))

            lista_opcoes = [op1, op2, op3, captcha]
            random.shuffle(lista_opcoes)
            
            view = discord.ui.View()
            select = discord.ui.Select(
                placeholder="Escolha uma opção...",
                options=[]
            )
            for option in lista_opcoes:
                select.add_option(label=option, value=option)

            async def select_callback(interaction: discord.Interaction):
                if select.values[0] == captcha:
                    role = interaction.guild.get_role(ROLE_CAPTCHA_REALIZADO)
                    if role:
                        await interaction.user.add_roles(role)
                    await mensagem.edit(content="Captcha realizado!", embed=None, view=None, attachments=[])
                else:
                    with open("./dados.json", "r") as r:
                        dados = json.load(r)
                    if str(interaction.user.id) not in dados['tried_members']:
                        dados['tried_members'][str(interaction.user.id)] = 0

                    dados['tried_members'][str(interaction.user.id)] += 1

                    with open("./dados.json", "w") as w:
                        json.dump(dados, w, indent=4)

                    await mensagem.edit(content=f"Captcha incorreto. ({dados['tried_members'][str(interaction.user.id)]}/3)", embed=None, view=None, attachments=[])
                    
                    if dados['tried_members'][str(interaction.user.id)] >= 3:
                        role = interaction.guild.get_role(ROLE_CAPTCHA_BLOCKLISTED)
                        if role:
                            await interaction.user.add_roles(role)

            select.callback = select_callback

            view.add_item(select)

            embed = discord.Embed(title="Selecione a opção correta, de acordo com a imagem abaixo", color=0xFF3012)
            with open(f"./{captcha}.png", "rb") as f:
                picture = discord.File(f)
                embed.set_image(url=f"attachment://{captcha}.png") 

                await mensagem.edit(content="", embed=embed, attachments=[picture], view=view)

            os.remove(f"./{captcha}.png")

    except Exception as e:
        print(e)

@client.tree.command()
async def enviarmenucaptcha(inter: discord.Interaction, canal: discord.TextChannel):
    try:
        view = discord.ui.View()
        button = discord.ui.Button(label="Realizar Captcha", style=discord.ButtonStyle.primary, custom_id="MENSAGEM_CAPTCHA")
        view.add_item(button)

        embed = discord.Embed(title="Captcha", description="Prove que você não é um robô respondendo a imagem abaixo.", color=0xFF3012)

        await canal.send(embed=embed, view=view)
        await inter.response.send_message(f"Menu captcha enviado para {canal.mention}!", ephemeral=True)
    except Exception as e:
        print(e)

async def main():
    await client.start(os.getenv("BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
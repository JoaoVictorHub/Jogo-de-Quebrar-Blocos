import pygame
import random
import math
import array

# Configurações Iniciais e Janela
pygame.init()
pygame.mixer.init(frequency=22050,size=-16,channels=1,buffer=512)

tamanhoTela = (800,800)
tela = pygame.display.set_mode(tamanhoTela)
pygame.display.set_caption('Jogo de Quebrar Blocos (Breakout)')

# Controla a velocidade do loop do jogo (FPS)
relogio = pygame.time.Clock()

# Paleta de cores RGB para a interface
cores = {
    'branco':(255,255,255),
    'preto':(0, 0, 0),
    'amarelo':(255,255,0),
    'azul':(0,120,255),
    'verde':(0,255,0),
    'vermelho':(255,50,50),
    'roxo':(180,50,255),
    'laranja':(255,140,0)
}

# Efeitos Sonoros
def gerarSom(frequencia,duracao,tipo="sine"):
    # Gera um Sound do Pygame sintetizado via software
    amostras = int(22050 * duracao)
    buf = array.array('h',[0] * amostras)
    amplitude = 4000
    for i in range(amostras):
        t = i / 22050.0
        if tipo == "sine":
            val = math.sin(2 * math.pi * frequencia * t)
        elif tipo == "noise":
            val = random.uniform(-1,1)
        buf[i] = int(val * amplitude * (1 - i / amostras))
    return pygame.mixer.Sound(buf)

somRebate = gerarSom(440,0.05,"sine")
somBloco = gerarSom(880,0.08,"sine")
somVitoria = gerarSom(523,0.4,"sine")
somDerrota = gerarSom(150,0.5,"noise")

# Sistema de Partículas
particulas = []

def criarExplosao(pos_x,pos_y,cor):
    # Cria partículas que se espalham ao destruir um bloco.
    for _ in range(15):
        vel_x = random.uniform(-4,4)
        vel_y = random.uniform(-4,4)
        tamanho = random.randint(3,6)
        particulas.append({
            'x':pos_x,
            'y':pos_y,
            'vx':vel_x,
            'vy':vel_y,
            'tamanho':tamanho,
            'cor':cor,
            'vida':25 # Quadros antes de sumir
        })

def atualizarDesenhoParticulas():
    for p in particulas[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += 0.1 # Gravidade suave
        p['vida'] -= 1
        
        if p['vida'] <= 0:
            particulas.remove(p)
        else:
            pygame.draw.circle(tela, p['cor'], (int(p['x']), int(p['y'])), p['tamanho'])

# Estado Global do Jogo
estadoJogo = 'MENU' # Modos:'MENU','JOGANDO','GAME_OVER','VITORIA'
vidas = 3
pontuacao = 0

tamanhoJogadorPadrao = 100
jogador = pygame.Rect(350,750,tamanhoJogadorPadrao,15)

tamanhoBola = 15
bolas = []
powerups = []

def resetarBola():
    # Reseta a bola principal no centro acima da raquete
    global bolas
    bolaInicial = pygame.Rect(jogador.centerx - tamanhoBola // 2,500,tamanhoBola,tamanhoBola)
    bolas = [[bolaInicial,[4,-6]]]

# Estrutura dos Blocos com Resistência
quantidadeBlocosLinha = 8
quantidadeBlocosColuna = 5

def criarBlocos():
    distanciaEntreLinhas = 5
    larguraBloco = tamanhoTela[0] / quantidadeBlocosLinha - distanciaEntreLinhas
    alturaBloco = 20
    distanciaEntreColunas = alturaBloco + 10

    blocos = []
    for j in range(quantidadeBlocosColuna):
        for i in range(quantidadeBlocosLinha):
            vidaBloco = 3 if j == 0 else (2 if j in (1, 2) else 1)
            rect = pygame.Rect(
                i * (larguraBloco + distanciaEntreLinhas),
                60 + j * distanciaEntreColunas,
                larguraBloco,
                alturaBloco
            )
            blocos.append({'rect':rect,'vida':vidaBloco})
    return blocos

def iniciarNovoJogo():
    global vidas,pontuacao,blocos,jogador,estadoJogo,powerups,particulas
    vidas = 3
    pontuacao = 0
    powerups = []
    particulas = []
    jogador.width = tamanhoJogadorPadrao
    jogador.x = 350
    blocos = criarBlocos()
    resetarBola()
    estadoJogo = 'JOGANDO'

blocos = criarBlocos()

# Funções de Lógica e Jogabilidade
def movimentarJogador():
    teclas = pygame.key.get_pressed()
    # Move para a direita até a borda da tela
    if teclas[pygame.K_RIGHT] and (jogador.x + jogador.width) < tamanhoTela[0]:
        jogador.x += 8
    # Move para a esquerda até a borda da tela
    if teclas[pygame.K_LEFT] and jogador.x > 0:
        jogador.x -= 8

def gerarPowerUp(pos_x, pos_y):
    # Gera um item de power-up aleatório na posição do bloco destruído
    if random.random() < 0.35: # 35% de chance de soltar item
        tipos = ['aumentarRaquete','multiBolas','maisVelocidade']
        tipo = random.choice(tipos)
        rect = pygame.Rect(pos_x,pos_y,20,20)
        powerups.append({'rect':rect,'tipo':tipo})

def atualizarPowerUps():
    for p in powerups[:]:
        p['rect'].y += 4
        if jogador.colliderect(p['rect']):
            if p['tipo'] == 'aumentarRaquete':
                jogador.width = min(200,jogador.width + 30)
            elif p['tipo'] == 'multiBolas':
                novaBola = pygame.Rect(jogador.centerx,jogador.y - 20,tamanhoBola,tamanhoBola)
                bolas.append([novaBola,[-random.choice([4,5]),-6]])
            powerups.remove(p)
            somRebate.play()
        elif p['rect'].y > tamanhoTela[1]:
            powerups.remove(p)

def atualizarBolas():
    global vidas,pontuacao,estadoJogo

    for itemBola in bolas[:]:
        bola,vel = itemBola[0],itemBola[1]
        bola.x += vel[0]
        bola.y += vel[1]

        # Colisão Parede
        if bola.x <= 0 or bola.x + tamanhoBola >= tamanhoTela[0]:
            vel[0] = -vel[0]
            somRebate.play()

        # Colisão Teto
        if bola.y <= 0:
            vel[1] = -vel[1]
            somRebate.play()

        # Colisão Raquete
        if jogador.colliderect(bola) and vel[1] > 0:
            pontoRelativo = (bola.centerx - jogador.centerx) / (jogador.width / 2)
            vel[0] = pontoRelativo * 8
            vel[1] = -abs(vel[1])
            somRebate.play()
        
        # Colisão Blocos
        for bloco in blocos[:]:
            if bloco['rect'].colliderect(bola):
                bloco['vida'] -= 1
                vel[1] = -vel[1]
                cor_bloco = cores['verde'] if bloco['vida'] == 0 else cores['amarelo']
                criarExplosao(bloco['rect'].centerx, bloco['rect'].centery, cor_bloco)

                if bloco['vida'] <= 0:
                    pontuacao += 10
                    gerarPowerUp(bloco['rect'].centerx,bloco['rect'].centery)
                    blocos.remove(bloco)
                    somBloco.play()
                else:
                    somRebate.play()
                break

        # Bola caiu
        if bola.y + tamanhoBola >= tamanhoTela[1]:
            bolas.remove(itemBola)

    if len(bolas) == 0:
        vidas -= 1
        if vidas > 0:
            jogador.width = tamanhoJogadorPadrao
            jogador.x = 350
            resetarBola()
            pygame.time.delay(500)
        else:
            estadoJogo = 'GAME_OVER'
            somDerrota.play()

# Interface e Renders por Estado
def desenharTextoCentral(textoPrincipal,subtexto,cor):
    fonteGrande = pygame.font.Font(None,60)
    fontePequena = pygame.font.Font(None,30)

    surfP = fonteGrande.render(textoPrincipal,True,cor)
    rectP = surfP.get_rect(center=(tamanhoTela[0] // 2, tamanhoTela[1] // 2 - 20))

    surfS = fontePequena.render(subtexto,True,cores['branco'])
    rectS = surfS.get_rect(center=(tamanhoTela[0] // 2, tamanhoTela[1] // 2 + 30))

    tela.blit(surfP,rectP)
    tela.blit(surfS,rectS)

def desenharJogo():
    tela.fill(cores['preto'])

    if estadoJogo == 'MENU':
        desenharTextoCentral("BREAKOUT","Pressione ESPAÇO para Começar",cores['amarelo'])
    
    elif estadoJogo == 'JOGANDO':
        pygame.draw.rect(tela,cores['azul'],jogador)
        for b in bolas:
            pygame.draw.rect(tela,cores['branco'],b[0])

        for b in blocos:
            cor = cores['verde'] if b['vida'] == 1 else (cores['amarelo'] if b['vida'] == 2 else cores['vermelho'])
            pygame.draw.rect(tela,cor,b['rect'])

        for p in powerups:
            pygame.draw.ellipse(tela,cores['laranja'],p['rect'])

        atualizarDesenhoParticulas()

        # Placar
        fonte = pygame.font.Font(None,30)
        tela.blit(fonte.render(f'Pontos: {pontuacao}',True,cores['amarelo']),(10,770))
        tela.blit(fonte.render(f'Vidas: {vidas}',True,cores['vermelho']),(700,770))

    elif estadoJogo == 'GAME_OVER':
        desenharTextoCentral("GAME OVER","Pressione 'R' para Reiniciar",cores['vermelho'])

    elif estadoJogo == 'VITORIA':
        desenharTextoCentral("VOCÊ VENCEU!","Pressione 'R' para Reiniciar",cores['verde'])

# Game Loop Principal
rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN:
            if estadoJogo == 'MENU' and evento.key == pygame.K_SPACE:
                iniciarNovoJogo()
            elif estadoJogo in ('GAME_OVER','VITORIA') and evento.key == pygame.K_r:
                iniciarNovoJogo()

    if estadoJogo == 'JOGANDO':
        movimentarJogador()
        atualizarBolas()
        atualizarPowerUps()

        if len(blocos) == 0:
            estadoJogo = 'VITORIA'
            somVitoria.play()

    desenharJogo()
    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
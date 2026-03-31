#!/usr/bin/env pybricks-micropython
"""TARS Puppy: controle de comportamento para um robô EV3.

Comandos por sensor de cor e toque, estados de humor (idle, hurt, angry, sleeping),
e movimentos físicos com motores.
"""
# Imports
import urandom # type: ignore

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor, TouchSensor
from pybricks.parameters import Port, Button, Color, Direction
from pybricks.media.ev3dev import Image, ImageFile, SoundFile
from pybricks.tools import wait, StopWatch

class Puppy:
    # Constantes de ângulo para as pernas
    HALF_UP_ANGLE = 25
    STAND_UP_ANGLE = 65
    STRETCH_ANGLE = 150

    # Constantes para a cabeça
    HEAD_UP_ANGLE = 0
    HEAD_DOWN_ANGLE = -40

    def __init__(self):
        self.ev3 = EV3Brick()

        # Configuração dos Motores das Pernas
        self.left_leg_motor = Motor(Port.D, Direction.COUNTERCLOCKWISE)
        self.right_leg_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)

        # Configuração do Motor da Cabeça com relação de engrenagens (Gears)
        self.head_motor = Motor(Port.C, Direction.COUNTERCLOCKWISE,
                                gears=[[1, 24], [12, 36]])
        
        # Configuração dos Sensores
        self.color_sensor = ColorSensor(Port.S4)
        self.touch_sensor = TouchSensor(Port.S1)

        # Timers para comportamento
        self.pet_count_timer = StopWatch()
        self.feed_count_timer = StopWatch()
        self.count_changed_timer = StopWatch()
        self.playful_timer = StopWatch()
        
        # Controle para não sobrecarregar o alerta da bateria
        self.battery_warning_active = False
        
        # Variáveis de estado
        self.reset()

    def adjust_head(self):
        """Ajuste manual da cabeça no início (calibração)."""
        # Mostra um ícone para indicar que estamos no modo de ajuste
        self.ev3.screen.load_image(ImageFile.EV3_ICON)
        self.ev3.light.on(Color.ORANGE)
        print("Ajuste a cabeça com as setas e aperte o Centro.")

        while True:
            # Lê os botões para mover a cabeça para cima ou para baixo
            buttons = self.ev3.buttons.pressed()
            if Button.CENTER in buttons:
                break
            elif Button.UP in buttons:
                self.head_motor.run(25)
            elif Button.DOWN in buttons:
                self.head_motor.run(-25)
            else:
                self.head_motor.stop()
            wait(50)
            
        # Para garantir que a cabeça pare exatamente onde o usuário deixou
        self.head_motor.stop()
        self.head_motor.reset_angle(0)
        self.ev3.light.on(Color.GREEN)

    def move_head(self, target):
        # Velocidade reduzida para movimentos mais suaves
        self.head_motor.run_target(40, target)

    def reset(self):
        """Reinicia os estados de humor do Puppy."""
        # Gera alvos aleatórios para petting e alimentação para criar variação
        self.pet_target = urandom.randint(3, 6)
        self.feed_target = urandom.randint(2, 4)
        self.pet_count, self.feed_count = 1, 1
        
        # Reseta os timers para o estado inicial
        self.pet_count_timer.reset()
        self.feed_count_timer.reset()
        self.count_changed_timer.reset()
        self.playful_timer.reset()
        
        # Começa no comportamento de idle
        self._behavior = self.idle
        self._behavior_changed = True
        self.prev_petted = False
        self.prev_color = None

    # --- Comportamentos ---
    
    def idle(self):
        # O comportamento padrão, onde o Puppy fica feliz e alerta
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.NEUTRAL)
            self.stand_up()
            self.move_head(self.HEAD_UP_ANGLE)
        
        self.update_behavior()
        self.update_pet_count()

    def go_to_sleep(self):
        # O comportamento de sono, onde o Puppy fica cansado e dorme
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.TIRED_MIDDLE)
            self.sit_down()
            self.move_head(self.HEAD_DOWN_ANGLE)
            self.ev3.screen.load_image(ImageFile.SLEEPING)
            self.ev3.speaker.play_file(SoundFile.SNORING)
        
        # Acorda se apertar o botão central ou fizer carinho longo
        if self.touch_sensor.pressed() or Button.CENTER in self.ev3.buttons.pressed():
            self.count_changed_timer.reset()
            self.behavior = self.wake_up

    def wake_up(self):
        # O comportamento de despertar, onde o Puppy acorda lentamente
        self.ev3.screen.load_image(ImageFile.TIRED_MIDDLE)
        self.ev3.speaker.play_file(SoundFile.DOG_WHINE)
        self.move_head(self.HEAD_UP_ANGLE)
        self.stretch()
        self.behavior = self.idle

    def act_hurt(self):
        """Comportamento de tristeza e fome."""
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.NEUTRAL)
            self.feed_count_timer.reset()
            
        # O Puppy fica triste e chora se ficar muito tempo sem comida
        if self.feed_count_timer.time() > 5000:
            self.ev3.speaker.play_file(SoundFile.DOG_WHINE)
            self.feed_count_timer.reset()
            
        # O resgate! Se ganhar comida, ele sai da tristeza e volta pro idle
        if self.feed_count > 0:
            self.behavior = self.idle

    def act_angry(self):
        # Comportamento de raiva, onde o Puppy fica irritado se for maltratado
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.ANGRY)
            self.ev3.speaker.play_file(SoundFile.DOG_GROWL)
            self.stand_up()
            wait(1000)
            self.ev3.speaker.play_file(SoundFile.DOG_BARK_1)
            self.pet_count = max(0, self.pet_count - 1)
            self.behavior = self.idle

    def go_to_bathroom(self):
        # Comportamento de "ir ao banheiro"
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.CRAZY_2)
            self.stand_up()
            
            # Levanta a perna e aguarda
            self.right_leg_motor.run_target(100, self.STRETCH_ANGLE)
            wait(500)
            self.ev3.speaker.play_file(SoundFile.HORN_1) # "Pum"
            wait(1000)
            
            # Volta a perna para a posição em pé
            self.right_leg_motor.run_target(100, self.STAND_UP_ANGLE)
            
            # "Esvazia o estômago" depois de ir ao banheiro
            if self.feed_count > 4:
                self.feed_count = 2
            else:
                self.feed_count = max(0, self.feed_count - 1)
                
            self.behavior = self.idle

    # --- Movimentos Físicos ---

    def sit_down(self):
        # Para sentar, os motores das pernas vão até o limite de torque para garantir que ele sente completamente
        self.left_leg_motor.run_until_stalled(-60)
        self.right_leg_motor.run_until_stalled(-60)
        self.left_leg_motor.reset_angle(0)
        self.right_leg_motor.reset_angle(0)

    def stand_up(self):
        # Velocidade reduzida para 50 para movimentos mais suaves
        self.left_leg_motor.run_target(50, self.STAND_UP_ANGLE, wait=False)
        self.right_leg_motor.run_target(50, self.STAND_UP_ANGLE)

    def stretch(self):
        # Para alongar, os motores das pernas vão até o ângulo de alongamento
        self.left_leg_motor.run_target(50, self.STRETCH_ANGLE, wait=False)
        self.right_leg_motor.run_target(50, self.STRETCH_ANGLE)
        wait(500)
        self.stand_up()

    def hop(self):
        """Faz o puppy dar um pequeno pulo."""
        self.left_leg_motor.run(500)
        self.right_leg_motor.run(500)
        wait(250)
        self.left_leg_motor.run(-200)
        self.right_leg_motor.run(-200)
        wait(250)
        self.stand_up()

    # --- Sistema de Lógica Interna ---

    # Propriedade para o comportamento atual, com flag para detectar mudanças
    @property
    def behavior(self):
        return self._behavior

    # Setter que marca quando o comportamento muda para que possamos reagir a isso
    @behavior.setter
    def behavior(self, value):
        if self._behavior != value:
            self._behavior = value
            self._behavior_changed = True

    # Propriedade para detectar se o comportamento mudou desde a última vez
    @property
    def did_behavior_change(self):
        if self._behavior_changed:
            self._behavior_changed = False
            return True
        return False

    def update_behavior(self):
        # O robô só fica triste se a barriga zerar de verdade
        if self.feed_count == 0 and self.behavior != self.act_hurt:
            self.behavior = self.act_hurt
            
        # Vai ao banheiro se for alimentado muitas vezes
        if self.feed_count > 4 and self.behavior != self.go_to_bathroom:
            self.behavior = self.go_to_bathroom

    def update_pet_count(self):
        # Verifica se o sensor de toque foi pressionado para contar como carinho
        petted = self.touch_sensor.pressed()
        if petted and not self.prev_petted:
            self.pet_count += 1
            self.ev3.speaker.play_file(SoundFile.DOG_SNIFF)
            self.count_changed_timer.reset()
        self.prev_petted = petted

    def check_commands(self):
        """Lê o sensor de cor e executa comandos imediatos."""
        color = self.color_sensor.color()
        if color is None or color == Color.BLACK:
            self.prev_color = None
            return

        self.count_changed_timer.reset()

        if self.behavior == self.go_to_sleep:
            self.behavior = self.wake_up

        if color != self.prev_color:
            print("O TARS está vendo a cor:", color)
            
            # 2. ACORDA SE ESTIVER DORMINDO: 
            if self.behavior == self.go_to_sleep:
                self.behavior = self.wake_up
            
            # Comandos por cor
            if color == Color.GREEN:
                print("Comando: Sentar")
                self.sit_down()
                self.ev3.speaker.play_file(SoundFile.CONFIRM)
                # Removido o self.reset() daqui. Ele vai sentar e ficar sentado!
            
            elif color == Color.BLUE:
                print("Comando: Alongar")
                self.move_head(self.HEAD_UP_ANGLE)
                self.stretch()
                self.behavior = self.idle # 3. Volta a ficar em pé depois de terminar
            
            elif color == Color.YELLOW:
                print("Comando: Pular")
                self.ev3.speaker.play_file(SoundFile.DOG_BARK_1)
                self.move_head(self.HEAD_UP_ANGLE)
                self.hop()
                self.behavior = self.idle # Volta a ficar em pé
            
            elif color == Color.RED:
                print("Comando: Alimentar")
                self.feed_count += 1
                self.ev3.speaker.play_file(SoundFile.CRUNCHING)
                self.behavior = self.idle # Fica feliz e alerta (em pé)
                
            elif color == Color.WHITE:
                print("Comando: Ficar Feliz e Levantar")
                # Enche as barrinhas para ele não ficar triste/com fome
                self.feed_count = self.feed_target
                self.pet_count = self.pet_target
                
                # Muda a carinha, faz som alegre e levanta
                self.ev3.screen.load_image(ImageFile.AWAKE)
                self.ev3.speaker.play_file(SoundFile.DOG_BARK_2)
                self.stand_up()
                
                # Garante que ele volte ao estado normal (sem choro)
                self.behavior = self.idle
                
            elif color == Color.BROWN:
                print("Comando: Ir ao Banheiro")
                self.behavior = self.go_to_bathroom
                
            else:
                print("Cor desconhecida, ignorando...")

            self.prev_color = color

    def monitor_counts(self):
        # Usa um timer separado para não atrapalhar o sono
        if self.playful_timer.time() > 10000:
            self.feed_count = max(0, self.feed_count - 1)
            self.pet_count = max(0, self.pet_count - 1)
            self.playful_timer.reset()
        
        # O robô cai no sono depois de 30 segundos sem ninguém interagir
        if self.count_changed_timer.time() > 60000:
            self.behavior = self.go_to_sleep

    def monitor_battery(self):
        # Se a bateria estiver abaixo de 7V, acende a luz vermelha sem ficar "spammando" o comando
        if self.ev3.battery.voltage() < 7000:
            if not self.battery_warning_active:
                self.ev3.light.on(Color.RED)
                print("Aviso: TARS está ficando sem energia...")
                self.battery_warning_active = True
        else:
            # Se a bateria for recarregada ou conectada no cabo
            if self.battery_warning_active:
                self.ev3.light.on(Color.GREEN)
                self.battery_warning_active = False

    def run(self):
        # Configuração inicial: sentar e ajustar a cabeça
        self.sit_down()
        self.adjust_head()
        
        while True:
            # Loop principal: monitora bateria, interações, lê comandos de cor e atualiza comportamento
            self.monitor_battery()
            self.monitor_counts()
            self.check_commands()
            self.behavior()
            wait(50)

# Ponto de entrada do programa
if __name__ == '__main__':
    my_puppy = Puppy()
    my_puppy.run()
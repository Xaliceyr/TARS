#!/usr/bin/env pybricks-micropython
import urandom

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor, TouchSensor
from pybricks.parameters import Port, Button, Color, Direction
from pybricks.media.ev3dev import Image, ImageFile, SoundFile
from pybricks.tools import wait, StopWatch

class Puppy:
    # Constantes de ângulo para as pernas
    HALF_UP_ANGLE = 25
    STAND_UP_ANGLE = 65
    STRETCH_ANGLE = 125

    # Constantes para a cabeça
    HEAD_UP_ANGLE = 0
    HEAD_DOWN_ANGLE = -40

    def __init__(self):
        self.ev3 = EV3Brick()

        # Configuração dos Motores das Pernas
        self.left_leg_motor = Motor(Port.D, Direction.COUNTERCLOCKWISE)
        self.right_leg_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)

        # Configuração do Motor da Cabeça com relação de engrenagens (Gears)
        # Isso ajuda o Pybricks a calcular a velocidade real na ponta do mecanismo
        self.head_motor = Motor(Port.C, Direction.COUNTERCLOCKWISE,
                                gears=[[1, 24], [12, 36]])

        self.color_sensor = ColorSensor(Port.S4)
        self.touch_sensor = TouchSensor(Port.S1)

        # Timers para comportamento
        self.pet_count_timer = StopWatch()
        self.feed_count_timer = StopWatch()
        self.count_changed_timer = StopWatch()
        self.playful_timer = StopWatch()
        
        # Timers para animação dos olhos
        self.eyes_timer_1 = StopWatch()
        self.eyes_timer_2 = StopWatch()

        self.reset()

    def adjust_head(self):
        """Ajuste manual da cabeça no início (calibração)."""
        self.ev3.screen.load_image(ImageFile.EV3_ICON)
        self.ev3.light.on(Color.ORANGE)
        print("Ajuste a cabeça com as setas e aperte o Centro.")

        while True:
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

        self.head_motor.stop()
        self.head_motor.reset_angle(0)
        self.ev3.light.on(Color.GREEN)

    def move_head(self, target):
        self.head_motor.run_target(40, target)

    def reset(self):
        """Reinicia os estados de humor do Puppy."""
        self.pet_target = urandom.randint(3, 6)
        self.feed_target = urandom.randint(2, 4)
        self.pet_count, self.feed_count = 1, 1
        
        self.pet_count_timer.reset()
        self.feed_count_timer.reset()
        self.count_changed_timer.reset()
        
        self._behavior = self.idle
        self._behavior_changed = True
        self.prev_petted = False
        self.prev_color = None

    # --- Comportamentos ---

    def idle(self):
        if self.did_behavior_change:
            self.ev3.screen.load_image(ImageFile.NEUTRAL)
            self.stand_up()
        
        self.update_behavior()
        self.update_pet_count()
        self.update_feed_count()

    def go_to_sleep(self):
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
        self.ev3.screen.load_image(ImageFile.TIRED_MIDDLE)
        self.ev3.speaker.play_file(SoundFile.DOG_WHINE)
        self.move_head(self.HEAD_UP_ANGLE)
        self.stretch()
        self.behavior = self.idle

    def act_angry(self):
        self.ev3.screen.load_image(ImageFile.ANGRY)
        self.ev3.speaker.play_file(SoundFile.DOG_GROWL)
        self.stand_up()
        wait(1000)
        self.ev3.speaker.play_file(SoundFile.DOG_BARK_1)
        self.pet_count = max(0, self.pet_count - 1)
        self.behavior = self.idle

    def go_to_bathroom(self):
        self.ev3.screen.load_image(ImageFile.CRAZY_2)
        self.stand_up()
        self.right_leg_motor.run_target(100, self.STRETCH_ANGLE)
        wait(500)
        self.ev3.speaker.play_file(SoundFile.HORN_1) # "Pum"
        wait(1000)
        self.right_leg_motor.run_target(100, self.STAND_UP_ANGLE)
        self.feed_count = 1
        self.behavior = self.idle

    # --- Movimentos Físicos ---

    def sit_down(self):
        self.left_leg_motor.run_until_stalled(-60)
        self.right_leg_motor.run_until_stalled(-60)
        self.left_leg_motor.reset_angle(0)
        self.right_leg_motor.reset_angle(0)

    def stand_up(self):
        self.left_leg_motor.run_target(100, self.STAND_UP_ANGLE, wait=False)
        self.right_leg_motor.run_target(100, self.STAND_UP_ANGLE)

    def stretch(self):
        self.left_leg_motor.run_target(100, self.STRETCH_ANGLE, wait=False)
        self.right_leg_motor.run_target(100, self.STRETCH_ANGLE)
        wait(500)
        self.stand_up()

    # --- Sistema de Lógica Interna ---

    @property
    def behavior(self):
        return self._behavior

    @behavior.setter
    def behavior(self, value):
        if self._behavior != value:
            self._behavior = value
            self._behavior_changed = True

    @property
    def did_behavior_change(self):
        if self._behavior_changed:
            self._behavior_changed = False
            return True
        return False

    def update_behavior(self):
        """Decide o que fazer com base no carinho e comida."""
        if self.pet_count >= self.pet_target and self.feed_count >= self.feed_target:
            self.behavior = self.idle # Ficaria feliz aqui
        elif self.feed_count == 0:
            # Puppy faminto
            self.ev3.screen.load_image(ImageFile.HURT)
            if self.feed_count_timer.time() > 5000:
                self.ev3.speaker.play_file(SoundFile.DOG_WHINE)
                self.feed_count_timer.reset()

    def update_pet_count(self):
        petted = self.touch_sensor.pressed()
        if petted and not self.prev_petted:
            self.pet_count += 1
            self.ev3.speaker.play_file(SoundFile.DOG_SNIFF)
            self.count_changed_timer.reset()
        self.prev_petted = petted

    def update_feed_count(self):
        color = self.color_sensor.color()
        if color in [Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW]:
            if color != self.prev_color:
                self.feed_count += 1
                self.ev3.speaker.play_file(SoundFile.CRUNCHING)
                self.count_changed_timer.reset()
                self.prev_color = color
        else:
            self.prev_color = None

    def monitor_counts(self):
        # Diminui a satisfação com o tempo (a cada 20 seg)
        if self.count_changed_timer.time() > 10000:
            self.feed_count = max(0, self.feed_count - 1)
            self.pet_count = max(0, self.pet_count - 1)
            self.count_changed_timer.reset()
        
        # Se ficar parado demais (1 min), dorme
        if self.count_changed_timer.time() > 20000:
            self.behavior = self.go_to_sleep

    def run(self):
        self.sit_down()
        self.adjust_head()
        while True:
            self.monitor_counts()
            self.behavior()
            wait(50)

if __name__ == '__main__':
    my_puppy = Puppy()
    my_puppy.run()
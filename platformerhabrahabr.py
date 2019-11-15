#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Импортируем библиотеку pygame
import pygame
from pygame import *
from player import *
from blocks import *
from generator import get_random_level
import redis
from time import time

#Объявляем переменные
WIN_WIDTH = 900  #Ширина создаваемого окна
WIN_HEIGHT = 500  # Высота
DISPLAY = (WIN_WIDTH, WIN_HEIGHT) # Группируем ширину и высоту в одну переменную
BACKGROUND_COLOR = "#004400"

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):

        self.state = self.camera_func(self.state, target.rect)

        
def camera_configure(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t = -l+WIN_WIDTH / 2, -t+WIN_HEIGHT / 2

    l = min(0, l)                           # Не движемся дальше левой границы
    l = max(-(camera.width-WIN_WIDTH), l)   # Не движемся дальше правой границы
    t = max(-(camera.height-WIN_HEIGHT), t) # Не движемся дальше нижней границы
    t = min(0, t)                           # Не движемся дальше верхней границы

    return Rect(l, t, w, h)        

def get_other_positions(name):
    keys = redis_conn.keys('player_*')
    position_dict = dict()

    for key in keys:
        key = str(key)[9:-1]
        if key != name:
            position_dict[key] = (int(str(redis_conn.hget('player_' + key, 'x'))[2:-1]),
                                  int(str(redis_conn.hget('player_' + key, 'y'))[2:-1]))
    return position_dict


def set_my_position(name, x, y):
    redis_conn.hset('player_' + name, 'x', x)
    redis_conn.hset('player_' + name, 'y', y)


def main():
    my_name = input('Enter your name: ')
    pygame.init()  # Инициация PyGame, обязательная строчка
    screen = pygame.display.set_mode(DISPLAY) # Создаем окошко
    pygame.display.set_caption("Super Mario Boy") # Пишем в шапку
    bg = Surface((WIN_WIDTH, WIN_HEIGHT)) # Создание видимой поверхности
                                         # будем использовать как фон
    bg.fill(Color(BACKGROUND_COLOR))     # Заливаем поверхность сплошным цветом
    y = 4590
    hero = Player(30, 3600, name=my_name)  # создаем героя по (x,y) координатам

    level = redis_conn.get('level')
    if not level:
        level = get_random_level(y // 32, width=40)
        redis_conn.set('level', str(level))

    else:
        level = [lev for lev in str(level)[3:-3].split(', ')]


    set_my_position(my_name, hero.rect.x, hero.rect.y)
    other_heroes = dict()


    
    #other_heroes = [Player(20 + 10*i, y) for i in range(3)]
    boost = left = right = False  # по умолчанию - стоим
    up = False
    
    entities = pygame.sprite.Group() # Все объекты
    platforms = []  # то, во что мы будем врезаться или опираться
    
    entities.add(hero)
    #[entities.add(player) for player in other_heroes]


       
    timer = pygame.time.Clock()
    x = y = 0  # координаты

    for row in level:  # вся строка
        for col in row:  # каждый символ
            if col == "-":
                pf = Platform(x, y)
                entities.add(pf)
                platforms.append(pf)

            x += PLATFORM_WIDTH  #блоки платформы ставятся на ширине блоков
        y += PLATFORM_HEIGHT     #то же самое и с высотой
        x = 0                    #на каждой новой строчке начинаем с нуля
    
    total_level_width = len(level[0])*PLATFORM_WIDTH # Высчитываем фактическую ширину уровня
    total_level_height = len(level)*PLATFORM_HEIGHT   # высоту
    
    camera = Camera(camera_configure, total_level_width, total_level_height) 
    start_time = time()

    while True: # Основной цикл программы
        timer.tick(60)

        for e in pygame.event.get(): # Обрабатываем события
            if e.type == QUIT:
                flag = True
                raise SystemExit
            if e.type == KEYDOWN and e.key == K_UP:
                up = True
            if e.type == KEYDOWN and e.key == K_LEFT:
                left = True
            if e.type == KEYDOWN and e.key == K_RIGHT:
                right = True
            if e.type == KEYDOWN and e.key == K_LSHIFT:
                boost = True

            if e.type == KEYUP and e.key == K_UP:
                up = False
            if e.type == KEYUP and e.key == K_RIGHT:
                right = False
            if e.type == KEYUP and e.key == K_LEFT:
                left = False
            if e.type == KEYUP and e.key == K_LSHIFT:
                boost = False


        screen.blit(bg, (0,0))      # Каждую итерацию необходимо всё перерисовывать 

        camera.update(hero) # центризируем камеру относительно персонажа
        hero.update(left, right, up, platforms, boost) # передвижение

        if time() - start_time > 0.2:
            other_positions = get_other_positions(my_name)

            set_my_position(my_name, hero.rect.x, hero.rect.y)
            for name in other_positions:
                if name not in other_heroes and name != my_name:
                    other_heroes[name] = Player(other_positions[name][0], other_positions[name][1], name)
                    entities.add(other_heroes[name])
                else:
                    other_heroes[name].rect.x = other_positions[name][0]
                    other_heroes[name].rect.y = other_positions[name][1]
            start_time = time()

        for e in entities:
            screen.blit(e.image, camera.apply(e))

        pygame.display.update()     # обновление и вывод всех изменений на экран
        

if __name__ == "__main__":
    main()

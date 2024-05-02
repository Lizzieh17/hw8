# Name: Lizzie Howell
# Description: Porting A5 to Python
# Date: 5/2 Spring 2024

import threading
import pygame
import time
import json

from pygame.locals import *
from time import sleep


class Sprite:
    def __init__(self, x, y, w, h, image):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = pygame.image.load(image)
        self.valid = True

    def draw(self, screen, scrollY):
        LOCATION = (self.x, self.y - scrollY)
        SIZE = (self.w, self.h)
        screen.blit(pygame.transform.scale(self.image, SIZE), LOCATION)

    def checkCollision(self, sprite2):
        if self.x + self.w < sprite2.x:
            return False
        if self.x > sprite2.x + sprite2.w:
            return False
        if self.y + self.h < sprite2.y:
            return False
        if self.y > sprite2.y + sprite2.h:
            return False
        return True

    def toString(self):
        return (
            "Sprite x,y,w,h = ("
            + str(self.x)
            + ","
            + str(self.y)
            + ","
            + str(self.w)
            + ","
            + str(self.h)
            + ")"
        )

    def isPac(self):
        return False

    def isFruit(self):
        return False

    def isWall(self):
        return False

    def isGhost(self):
        return False

    def isPellet(self):
        return False

    def isMoving(self):
        return False

    def update(self):
        return self.valid

    def shouldIWrap(self):
        if self.x >= 800:
            self.x = 4
        elif self.x <= 0:
            self.x = 775


class Wall(Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "sprite_images/wall.png")

    def isWall(self):
        return True

    def update(self):
        return True


class Pellet(Sprite):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 25, "sprite_images/pellet.png")

    def isPellet(self):
        return True

    def eatPellet(self):
        self.valid = False


class Fruit(Sprite):
    def __init__(self, x, y, dir):
        super().__init__(x, y, 25, 30, "sprite_images/fruit_images/fruit2.png")
        self.dir = dir
        self.ydir = 1
        self.xdir = 1
        self.speed = 8
        self.images = []
        self.images.append(
            pygame.image.load("sprite_images/fruit_images/fruit2.png")
        )  # img [0] strawberry
        self.images.append(
            pygame.image.load("sprite_images/fruit_images/fruit4.png")
        )  # img [1] pretzel

    def draw(self, screen, scrollY):
        LOCATION = (self.x, self.y - scrollY)
        SIZE = (self.w, self.h)
        IMAGE_NUM = self.dir
        screen.blit(pygame.transform.scale(self.images[IMAGE_NUM], SIZE), LOCATION)

    def isFruit(self):
        return True

    def isMoving(self):
        return True

    def changeDir(self):
        if self.dir == 1:
            self.ydir *= -1
        else:
            self.xdir *= -1

    def eatFruit(self):
        self.valid = False

    def update(self):
        if self.dir == 1:
            self.y += self.speed * self.ydir
        if self.dir == 0:
            self.x += self.speed * self.xdir
        return self.valid


class Ghost(Sprite):
    # Ghost Sprite Class, should always exist until hit by pacman and then enters death sequence thread
    def __init__(self, x, y):
        self.dying = False
        self.frame = 1
        super().__init__(x, y, 50, 50, "sprite_images/ghosts_images/pinky1.png")

    def deathSequence(self):
        # Using threading because that is the only source online I could find that would work for this.
        # Everything else stopped the whole program from running
        self.dying = True
        if self.frame != 1:
            exit()
        else:
            i = self.frame
            while self.dying and i <= 6:
                if i < 6:
                    self.image = pygame.image.load(
                        "sprite_images/ghosts_images/ghost{}.png".format(i)
                    )
                if i == 6:
                    self.valid = False
                    exit()
                else:
                    i += 1
                time.sleep(1)

    def isDying(self):
        return self.dying

    def isGhost(self):
        return True

    def update(self):
        return self.valid


class Pacman(Sprite):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, "sprite_images/pacman_images/pacman1.png")
        self.images = []
        self.direction = 1
        self.frame = 1
        self.MAXIMAGES = 3
        self.prevX = x
        self.prevY = y
        self.speed = 5
        # fill 0 index
        self.images.append(pygame.image.load("sprite_images/pacman_images/pacman1.png"))
        for i in range(1, 13):
            self.images.append(
                pygame.image.load("sprite_images/pacman_images/pacman{}.png".format(i))
            )

    def isPac(self):
        return True

    def isMoving(self):
        return True

    def draw(self, screen, scrollY):
        # override parent draw function so pacman can animate
        LOCATION = (self.x, self.y - scrollY)
        SIZE = (self.w, self.h)
        IMAGE_NUM = self.frame + self.direction * self.MAXIMAGES
        screen.blit(pygame.transform.scale(self.images[IMAGE_NUM], SIZE), LOCATION)

    def move(self, x, y, d):
        # move pac and save her previous position for collision fixing
        self.prevX = self.x
        self.prevY = self.y
        self.x += x
        self.y += y
        self.frame += 1
        self.direction = d
        if self.frame > self.MAXIMAGES:
            self.frame = 1

    def getOutOfWall(self):
        self.x = self.prevX
        self.y = self.prevY


class Model:
    def __init__(self):
        self.sprites = []
        self.collidingWall = False
        self.pacman = Pacman(400, 400)
        self.sprites.append(self.pacman)
        self.loadMap()

    def update(self):
        # boolean for formating in view =)
        self.collidingWall = False
        for sprite1 in self.sprites:
            if sprite1.update() == False:
                # remove is the sprite no longer exists
                self.sprites.remove(sprite1)
                continue
            if sprite1.isMoving() == False:
                # make code more efficent by checking that sprite1 is moving, aka pac/fruit
                continue
            # see if the sprite should wrap around the screen
            sprite1.shouldIWrap()
            for sprite2 in self.sprites:
                if (sprite1 != sprite2) and (sprite1.checkCollision(sprite2) == True):
                    # pac vs wall
                    if sprite1.isPac() == True and sprite2.isWall() == True:
                        self.collidingWall = True
                        sprite1.getOutOfWall()
                    # pac vs ghost
                    elif sprite1.isPac() == True and sprite2.isGhost() == True:
                        # check if the ghost is already dying or not
                        if sprite2.isDying() == False:
                            # create death sequence thread that runs paralell and keeps from the entire program stopping
                            t = threading.Thread(target=sprite2.deathSequence)
                            t.deamon = True
                            t.start()
                    # pac vs fruit
                    elif sprite1.isPac() == True and sprite2.isFruit() == True:
                        sprite2.eatFruit()
                    # pac vs pellet
                    elif sprite1.isPac() == True and sprite2.isPellet() == True:
                        sprite2.eatPellet()
                    # fruit vs wall
                    elif sprite1.isFruit() == True and sprite2.isWall() == True:
                        sprite1.changeDir()

    def loadMap(self):
        # open the json map and pull out the individual lists of sprite objects
        with open("map.json") as file:
            data = json.load(file)
            # get the list labeled as "walls" from the map.json file
            walls = data["walls"]
            pellets = data["pellets"]
            fruits = data["fruits"]
            ghosts = data["ghosts"]

        file.close()

        # for each entry inside the walls list, pull the key:value pair out and create
        # a new Wall object with (x,y,w,h)
        for entry in walls:
            self.sprites.append(Wall(entry["x"], entry["y"], entry["w"], entry["h"]))
        for entry in pellets:
            self.sprites.append(Pellet(entry["x"], entry["y"]))
        for entry in ghosts:
            self.sprites.append(Ghost(entry["x"], entry["y"]))
        for entry in fruits:
            self.sprites.append(Fruit(entry["x"], entry["y"], entry["dir"]))

    def clearScreen(self):
        # create a copy because using the original lead to a weird situation
        sprites_copy = self.sprites.copy()
        for sprite in sprites_copy:
            if sprite.isPac() == False:
                self.sprites.remove(sprite)

    def movePacman(self, x, y, d):
        self.pacman.move(x, y, d)

    def addPellet(self, pos, scrollY):
        self.sprites.append(Pellet(pos[0], pos[1] + scrollY))

    def addFruit(self, pos, d, scrollY):
        self.sprites.append(Fruit(pos[0], pos[1] + scrollY, d))

    def addGhost(self, pos, scrollY):
        self.sprites.append(Ghost(pos[0], pos[1] + scrollY))

    def getLowestWall(self):
        # returns lowest wall for better scroll functionality
        lowestY = 0
        for sprite in self.sprites:
            if sprite.isWall() == True:
                if sprite.y > lowestY:
                    lowestY = sprite.y + sprite.h
        return lowestY

    def getHighestWall(self):
        # returns highest wall for better scroll functionality
        highestY = 1000
        for sprite in self.sprites:
            if sprite.isWall() == True:
                if sprite.y < highestY:
                    highestY = sprite.y
        return highestY

    def getPacSpeed(self):
        # returns pacmans speed, using a getter for better coding practice
        return self.pacman.speed


class View:
    # View Class
    def __init__(self, model):
        screen_size = (800, 600)
        self.screen = pygame.display.set_mode(screen_size, 32)
        self.model = model
        self.scrollY = 0
        self.editing = False
        self.currentAdd = ""

    def update(self):
        # fill the background to a lighter color to signify we are in editmode
        if self.editing == True:
            self.screen.fill([40, 45, 100])
        else:
            # fill the background with black for the main game
            self.screen.fill([0, 0, 0])
        for sprite in self.model.sprites:
            # draw all the sprites
            sprite.draw(self.screen, self.scrollY)
        if self.editing == True:
            # check if we are editing and then provide a message about out edit mode for easier usage while editing
            font = pygame.font.Font("freesansbold.ttf", 32)
            text = font.render(
                "Edit Mode: Adding " + self.currentAdd,
                True,
                [10, 20, 255],
                [200, 200, 200],
            )
            self.screen.blit(text, (25, 25))
        pygame.display.flip()

    def cameraUp(self):
        # scrolling up until we hit the highest wall or stop while pac collides with a wall
        if (
            self.model.getHighestWall() < self.scrollY
            and self.model.collidingWall == False
            and self.model.pacman.y < 700
            and self.model.pacman.prevY != self.model.pacman.y
        ):
            self.scrollY -= self.model.getPacSpeed()

    def cameraDown(self):
        # scrolling down until we hit the lowest wall or stop while pac collides with a wall
        if (
            self.model.getLowestWall() > self.scrollY + 600
            and self.model.collidingWall == False
            and self.model.pacman.y > 200
            and self.model.pacman.prevY != self.model.pacman.y
        ):
            self.scrollY += self.model.getPacSpeed()


class Controller:
    # Controller class
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.keep_going = True
        self.addPellet = False
        self.addFruit = False
        self.addGhost = False
        self.editMode = False

    def update(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.keep_going = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    self.keep_going = False
            elif event.type == pygame.MOUSEBUTTONUP:
                # see if we are in edit mode
                if self.editMode == True:
                    # add pellets on click
                    if self.addPellet == True:
                        self.model.addPellet(pygame.mouse.get_pos(), self.view.scrollY)
                    # add fruit on clock
                    elif self.addFruit == True:
                        size = len(self.model.sprites)
                        num = size % 2
                        self.model.addFruit(
                            pygame.mouse.get_pos(), num, self.view.scrollY
                        )
                    # add ghost on click
                    elif self.addGhost == True:
                        self.model.addGhost(pygame.mouse.get_pos(), self.view.scrollY)
                pass
            elif event.type == pygame.KEYUP:  # this is keyReleased!
                # change editmode value and handle the adders for the sprites
                # currentAdd is information for View so we can provide a message to the user while editing
                if event.key == pygame.K_e:
                    self.editMode = not self.editMode
                    if self.editMode == True:
                        self.view.editing = True
                        self.addPellet = True
                        self.addFruit = False
                        self.addGhost = False
                        self.view.currentAdd = "pellets"
                    else:
                        self.view.editing = False
                        self.addPellets = False
                        self.addFruit = False
                        self.addGhosts = False
                if event.key == pygame.K_p:
                    self.view.currentAdd = "pellets"
                    self.addPellet = True
                    self.addFruit = False
                    self.addGhost = False
                if event.key == pygame.K_f:
                    self.view.currentAdd = "fruits"
                    self.addFruit = True
                    self.addPellet = False
                    self.addGhost = False
                if event.key == pygame.K_g:
                    self.view.currentAdd = "ghosts"
                    self.addGhost = True
                    self.addPellet = False
                    self.addFruit = False
                if event.key == pygame.K_l:
                    # clear the screen and then load all sprites, making sure pac is the only sprite in the list
                    self.model.clearScreen()
                    if len(self.model.sprites) == 1:
                        self.model.loadMap()
                if event.key == pygame.K_c:
                    self.model.clearScreen()
                pass
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.model.movePacman(-5, 0, 0)
        if keys[K_RIGHT]:
            self.model.movePacman(5, 0, 2)
        if keys[K_UP]:
            self.model.movePacman(0, -5, 1)
            self.view.cameraUp()
        if keys[K_DOWN]:
            self.model.movePacman(0, 5, 3)
            self.view.cameraDown()


print("Use the arrow keys to move. Press Esc to quit.")
pygame.init()
m = Model()
v = View(m)
c = Controller(m, v)
while c.keep_going:
    c.update()
    m.update()
    v.update()
    sleep(0.04)
print("Goodbye")

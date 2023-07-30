from pygame.locals import *
from random import randint
import pygame, glob, sys, os
import time
from sys import exit, path
sys.path.insert(0, os.getcwd())
from mygameobjects.vector2 import Vector2
pygame.init()
class Apple:
    x = 0
    y = 0
    step = 44
 
    def __init__(self,x,y):
        self.x = x * self.step
        self.y = y * self.step
 
    def draw(self, surface, image):
        surface.blit(image,(self.x, self.y)) 

class Eagle:
    x = 0
    y = 0
    TOP = 0
    RIGHT = 1
    DOWN =  2
    LEFT =  3
    UP   =  4
    speed = 200
    
    position = Vector2(400,10)
    heading  = Vector2()
    def __init__(self):
        self.x = self.position[0]
        self.y = self.position[1]
        self.ani_image = glob.glob("images/eagle/?.jpg")
        self.ani_image.sort()
        self.ani_image_pos=0
        self.image = pygame.image.load(self.ani_image[self.TOP])
        self.image.set_colorkey((1,1,1))
    
    def draw(self, surface):
        surface.blit(self.image,(self.x, self.y))
    

    def update(self,direction,surface):
       
        if direction>=0 :
          if direction == 0: #right
             self.image = pygame.image.load(self.ani_image[self.TOP])
          if direction == 1: #left
             self.image = pygame.image.load(self.ani_image[self.LEFT])
          if direction == 2: #uo
             self.image = pygame.image.load(self.ani_image[self.UP])
          if direction == 3: #uo
             self.image = pygame.image.load(self.ani_image[self.DOWN])
          self.image.set_colorkey((1,1,1))
        self.x = self.position[0] 
        self.y = self.position[1] 
        
        surface.blit(self.image,(self.x, self.y))

class Player:
    x = [0]
    y = [0]
    step = 44
    direction = 0
    length = 3
 
    updateCountMax = 2
    updateCount = 0
    
    def __init__(self, length):
       self.length = length
       for i in range(0,2000):
           self.x.append(-100)
           self.y.append(-100)
 
       # initial positions, no collision.
       self.x[1] = 1*44
       self.x[2] = 2*44
 
    def update(self):
 
        self.updateCount = self.updateCount + 1
        if self.updateCount > self.updateCountMax:
 
            # update previous positions
            for i in range(self.length-1,0,-1):
                self.x[i] = self.x[i-1]
                self.y[i] = self.y[i-1]
 
            # update position of head of snake
            if self.direction == 0:
                self.x[0] = self.x[0] + self.step
            if self.direction == 1:
                self.x[0] = self.x[0] - self.step
            if self.direction == 2:
                self.y[0] = self.y[0] - self.step
            if self.direction == 3:
                self.y[0] = self.y[0] + self.step
 
            self.updateCount = 0
 
 
    def moveRight(self):
        self.direction = 0
 
    def moveLeft(self):
        self.direction = 1
 
    def moveUp(self):
        self.direction = 2
 
    def moveDown(self):
        self.direction = 3 

    def get_direction(self):
        return self.direction

    def draw(self, surface, image):
        for i in range(0,self.length):
            surface.blit(image,(self.x[i],self.y[i])) 
 
class Game:
    def isCollision(self,x1,y1,x2,y2,bsize):
        if x1 >= x2 and x1 <= x2 + bsize:
            if y1 >= y2 and y1 <= y2 + bsize:
                return True
        return False
 
class App:
 
    windowWidth = 800
    windowHeight = 600
    player = 0
    apple = 0
    clock = pygame.time.Clock()
        
    
    def __init__(self):
        self._running = True
        self._display_surf = None
        self._image_surf = None
        self._apple_surf = None
        self.game = Game()
        self.player = Player(3) 
        self.apple = Apple(5,5)
              
        self.eagle = Eagle()
        
    def on_init(self):
        
        self._display_surf = pygame.display.set_mode((self.windowWidth,self.windowHeight), pygame.HWSURFACE)
        self._display_surf = pygame.display.set_mode((self.windowWidth,self.windowHeight), pygame.SRCALPHA,32)
        pygame.display.set_caption('Pygame Snake Game')
        self._running = True
        #self._image_surf = pygame.image.load("block.jpg").convert()
        #self._apple_surf = pygame.image.load("block.jpg").convert()
        self._image_surf = pygame.image.load("snake-angry.png").convert_alpha()
        self._apple_surf = pygame.image.load("apple.png").convert()
        #self._eagle_surf = pygame.image.load("eagle/new/eagle_0_top.jpg").convert_alpha()
    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
        
    def on_loop(self):
        self.player.update()
        time_passed = self.clock.tick()
        time_passed_seconds = time_passed / 1000.0
        
        destination = Vector2(self.player.x[0]-64,self.player.y[0]-64) - (Vector2(*self.eagle.image.get_size())/2.)
        heading = Vector2.from_points(self.eagle.position, destination)
        heading.normalize()
        distance_moved = time_passed_seconds * self.eagle.speed
        self.eagle.position += heading * distance_moved
        self.eagle.update(self.player.get_direction(), self._display_surf)
        # does snake eat apple?
        for i in range(0,self.player.length):
            if self.game.isCollision(self.apple.x,self.apple.y,self.player.x[i], self.player.y[i],44):
                self.apple.x = randint(2,9) * 44
                self.apple.y = randint(2,9) * 44
                self.player.length = self.player.length + 1
                
 
        # does snake collide with itself?
        for i in range(2,self.player.length):
            if self.game.isCollision(self.player.x[0],self.player.y[0],self.player.x[i], self.player.y[i],40):
                print("You lose! Collision: ")
                print("x[0] (" + str(self.player.x[0]) + "," + str(self.player.y[0]) + ")")
                print("x[" + str(i) + "] (" + str(self.player.x[i]) + "," + str(self.player.y[i]) + ")")
                exit(0)
 
        pass
 
    def on_render(self):
        self._display_surf.fill((0,0,0))
        self.player.draw(self._display_surf, self._image_surf)
        self.apple.draw(self._display_surf, self._apple_surf)
        self.eagle.draw(self._display_surf)
        pygame.display.flip()
 
    def on_cleanup(self):
        pygame.quit()
 	
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while( self._running ):
            pygame.event.pump()
            keys = pygame.key.get_pressed() 
 
            if (keys[K_RIGHT]):
                self.player.moveRight()
 
            if (keys[K_LEFT]):
                self.player.moveLeft()
 
            if (keys[K_UP]):
                self.player.moveUp()
 
            if (keys[K_DOWN]):
                self.player.moveDown()
 
            if (keys[K_ESCAPE]):
                self._running = False

            
            self.on_loop()
            self.on_render()
            
            
            time.sleep (50.0 / 1000.0);
            
        self.on_cleanup()
 
if __name__ == "__main__" :
    theApp = App()
    theApp.on_execute()


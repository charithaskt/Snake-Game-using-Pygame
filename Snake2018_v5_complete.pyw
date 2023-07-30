#!/usr/bin/env python
import os, pygame, sys, time, math
import pymysql, pymysql.cursors
from pygame.locals import *
import random
#=======================
from random import randint, choice
from pygame.math import Vector2
SCREEN_SIZE = (540,540)
WORLD_SCREEN_SIZE = (540, 540)
NEST_POSITION = (270, 270)
ANT_COUNT = 20
NEST_SIZE = 100

#screen = pygame.display.set_mode(SCREEN_SIZE,0,32)
pygame.init()
clock = pygame.time.Clock()


MEMFPS = 40 # frames per second, the general speed of the program
MEMWINDOWWIDTH = 200 # size of window's width in pixels
MEMWINDOWHEIGHT = 200 # size of windows' height in pixels
REVEALSPEED = 2 # speed boxes' sliding reveals and covers
BOXSIZE = 30 # size of box height & width in pixels
GAPSIZE = 3 # size of gap between boxes in pixels
BOARDWIDTH = 6 # number of columns of icons
BOARDHEIGHT = 6 # number of rows of icons
assert (BOARDWIDTH * BOARDHEIGHT) % 2 == 0, 'Board needs to have an even number of boxes for pairs of matches.'
XMARGIN = int((MEMWINDOWWIDTH - (BOARDWIDTH * (BOXSIZE + GAPSIZE))) / 2)+330
YMARGIN = int((MEMWINDOWHEIGHT - (BOARDHEIGHT * (BOXSIZE + GAPSIZE))) / 2) + 40

GRAY = (100, 100, 100)
NAVYBLUE = ( 60, 60, 100)
WHITE = (255, 255, 255)
RED= (255,0,0)
GREEN = ( 0, 255,0)
BLUE = ( 0,0, 255)
YELLOW = (255, 255,0)
ORANGE = (255, 128,0)
PURPLE = (255,0, 255)
CYAN = ( 0, 255, 255)

BGCOLOR = NAVYBLUE
LIGHTBGCOLOR = GRAY
BOXCOLOR = WHITE
HIGHLIGHTCOLOR = BLUE

DONUT = 'donut'
SQUARE = 'square'
DIAMOND = 'diamond'
LINES = 'lines'
OVAL = 'oval'

ALLCOLORS = (RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN)
ALLSHAPES = (DONUT, SQUARE, DIAMOND, LINES, OVAL)
assert len(ALLCOLORS) * len(ALLSHAPES) * 2 >= BOARDWIDTH * BOARDHEIGHT,"Board is too big for the number of shapes/colors defined."

TEXTCOLOR = WHITE 
TEXTSHADOWCOLOR = GRAY
NUMCOLOR=["1","2","3","4"]

default_font = pygame.font.get_default_font()
BIGFONT = pygame.font.SysFont(default_font, 24)
CLEARCOLOR = (180,247,125) #centiback - color
colordict = {}



class State(object):
	def __init__(self, name):
		self.name = name
	def do_actions(self):
		pass
	def check_conditions(self):
		pass
	def entry_actions(self):
		pass
	def exit_actions(self):
		pass

class StateMachine(object):
	def __init__(self):
		self.states = {}
		self.active_state = None
	def add_state(self, state):
		self.states[state.name] = state
	def think(self):
		if self.active_state is None:
			return
		self.active_state.do_actions()
		new_state_name = self.active_state.check_conditions()
		if new_state_name is not None:
			self.set_state(new_state_name)
	def set_state(self, new_state_name):
		if self.active_state is not None:
			self.active_state.exit_actions()
		self.active_state = self.states[new_state_name]
		self.active_state.entry_actions()
class World(object):
	def __init__(self):
		self.entities = {}
		self.entity_id = 0
		self.background = pygame.surface.Surface(WORLD_SCREEN_SIZE,0,32).convert()
		self.background.fill((180,247,125))
		pygame.draw.circle(self.background, (200, 255, 200), NEST_POSITION,int(NEST_SIZE))

	def add_entity(self, entity):
		self.entities[self.entity_id] = entity
		entity.id = self.entity_id
		self.entity_id += 1

	def remove_entity(self, entity):
		del self.entities[entity.id]

	def get(self, entity_id):
		if entity_id in self.entities:
			return self.entities[entity_id]
		else:
			return None
	
	def set_time_passed(self,time_passed):
		self.time_passed = time_passed
	
	def process(self, time_passed):
		time_passed_seconds = time_passed / 1000.0
		try:
			for entity in iter(self.entities.values()):
				entity.process(time_passed_seconds)
		except RuntimeError:
			return None

	def render(self, surface):
		#surface.blit(self.background, ((600-540)/2, (600-540)/2))
		surface.blit(self.background, (30, 30))
		try:
			for entity in iter(self.entities.values()):
				entity.render(surface)
		except RuntimeError:
			return None

	def get_close_entity(self, name, location, range=100.):
		location = Vector2(*location)
		try:
			for entity in iter(self.entities.values()):
				if entity.name == name:
					distance = location.distance_to(entity.location)
					if distance < range:
						return entity
			return None
		except RuntimeError:
			return None

class GameEntity(object):
	def __init__(self, world, name, image):
		self.world = world
		self.name = name
		self.image = image
		self.location = Vector2(0, 0)
		self.destination = Vector2(0, 0)
		self.speed = 0.

		self.brain = StateMachine()

		self.id = 0

	def render(self, surface):
		x, y = self.location
		w, h = self.image.get_size()
		surface.blit(self.image, (x-w/2, y-h/2))

	def process(self, time_passed):
		self.brain.think()
		if self.speed > 0. and self.location != self.destination:
			vec_to_destination = self.destination - self.location
			distance_to_destination = vec_to_destination.length()
			heading = vec_to_destination.normalize()
			travel_distance = min(distance_to_destination, time_passed * self.speed)
			self.location += travel_distance * heading

class Leaf(GameEntity):
	def __init__(self, world, image):
		GameEntity.__init__(self, world, "leaf", image)

class Spider(GameEntity):
	def __init__(self, world, image):
		GameEntity.__init__(self, world, "spider", image)
		# Make a 'dead' spider image by turning it upside down
		self.dead_image = pygame.transform.flip(image, 0, 1)
		self.health = 25
		self.speed = 50. + randint(-20, 20)

	def bitten(self):
		# Spider as been bitten
		self.health -= 1
		if self.health <= 0:
			self.speed = 0.
			self.image = self.dead_image
		self.speed = 140.

	def render(self, surface):
		GameEntity.render(self, surface)
		# Draw a health bar
		x, y = self.location
		w, h = self.image.get_size()
		bar_x = x - 12
		bar_y = y + h/2
		#fill(color,(x,y,width,height))
		surface.fill( (255, 0, 0), (bar_x, bar_y, 25, 4))
		surface.fill( (0, 255, 0), (bar_x, bar_y, self.health, 4))
	
	def process(self, time_passed):
		x, y = self.location
		if x > SCREEN_SIZE[0] + 2:
			self.world.remove_entity(self)
			return

		GameEntity.process(self, time_passed)

class Ant(GameEntity):
	def __init__(self, world, image):
		GameEntity.__init__(self, world, "ant", image)
		# State classes are defined below
		exploring_state = AntStateExploring(self)
		seeking_state = AntStateSeeking(self)
		delivering_state = AntStateDelivering(self)
		hunting_state = AntStateHunting(self)
	
		self.brain.add_state(exploring_state)
		self.brain.add_state(seeking_state)
		self.brain.add_state(delivering_state)
		self.brain.add_state(hunting_state)

		self.carry_image = None
	
	def carry(self, image):
		self.carry_image = image

	def drop(self, surface):
		if self.carry_image:
			x, y = self.location
			w, h = self.carry_image.get_size()
			surface.blit(self.carry_image, (x-w, y-h/2))
			self.carry_image = None

	def render(self, surface):
		GameEntity.render(self, surface)
		if self.carry_image:
			x, y = self.location
			w, h = self.carry_image.get_size()
			surface.blit(self.carry_image, (x-w, y-h/2))

class AntStateExploring(State):
	def __init__(self, ant):
		State.__init__(self, "exploring")
		self.ant = ant
		
	
	def random_destination(self):
		w, h = SCREEN_SIZE
		self.ant.destination = Vector2(randint(30, w), randint(30, h))
	
	def do_actions(self):
		if randint(1, 20) == 1:
			self.random_destination()
	
	def check_conditions(self):
		# If ant sees a leaf, go to the seeking state
		leaf = self.ant.world.get_close_entity("leaf", self.ant.location)
		if leaf is not None:
			self.ant.leaf_id = leaf.id
			return "seeking"
	
		# If the ant sees a spider attacking the base, go to hunting state
		spider = self.ant.world.get_close_entity("spider", NEST_POSITION, NEST_SIZE)
		if spider is not None:
			if self.ant.location.distance_to(spider.location) < 100.:
				self.ant.spider_id = spider.id
				return "hunting"
		return None

	def entry_actions(self):
		self.ant.speed = 120. + randint(-30, 30)
		self.random_destination()
	
class AntStateSeeking(State):
	def __init__(self, ant):
		State.__init__(self, "seeking")
		self.ant = ant
		self.leaf_id = None
	
	def check_conditions(self):
		# If the leaf is gone, then go back to exploring
		leaf = self.ant.world.get(self.ant.leaf_id)
		if leaf is None:
			return "exploring"
		# If we are next to the leaf, pick it up and deliver it
		if self.ant.location.distance_to(leaf.location) < 5.0:
			self.ant.carry(leaf.image)
			self.ant.world.remove_entity(leaf)
			return "delivering"
		return None

	def entry_actions(self):
		# Set the destination to the location of the leaf
		leaf = self.ant.world.get(self.ant.leaf_id)
		if leaf is not None:
			self.ant.destination = leaf.location
			self.ant.speed = 160. + randint(-20, 20)

class AntStateDelivering(State):
	def __init__(self, ant):
		State.__init__(self, "delivering")
		self.ant = ant

	def check_conditions(self):
		# If inside the nest, randomly drop the object
		if Vector2(*NEST_POSITION).distance_to(self.ant.location) < NEST_SIZE:
			if (randint(1, 10) == 1):
				self.ant.drop(self.ant.world.background)
				return "exploring"
		return None

	def entry_actions(self):
		# Move to a random point in the nest
		self.ant.speed = 60.
		random_offset = Vector2(randint(-20, 20), randint(-20, 20))
		self.ant.destination = Vector2(*NEST_POSITION) + random_offset

class AntStateHunting(State):
	def __init__(self, ant):
		State.__init__(self, "hunting")
		self.ant = ant
		self.got_kill = False

	def do_actions(self):
		spider = self.ant.world.get(self.ant.spider_id)
		if spider is None:
			return
		self.ant.destination = spider.location
		if self.ant.location.distance_to(spider.location) < 15.:
			# Give the spider a fighting chance to avoid being killed!
			if randint(1, 5) == 1:
				spider.bitten()
				# If the spider is dead, move it back to the nest
				if spider.health <= 0:
					self.ant.carry(spider.image)
					self.ant.world.remove_entity(spider)
					self.got_kill = True
	
	def check_conditions(self):
		if self.got_kill:
			return "delivering"
		spider = self.ant.world.get(self.ant.spider_id)
		# If the spider has been killed then return to exploring state
		if spider is None:
			return "exploring"
		# If the spider gets far enough away, return to exploring state
		if spider.location.distance_to(NEST_POSITION) > NEST_SIZE * 3:
			return "exploring"
		return None

	def entry_actions(self):
		self.speed = 160. + randint(0, 50)

	def exit_actions(self):
		self.got_kill = False



def calculate_new_xy(old_xy, speed, angle_in_radians):
	new_x = old_xy[0] + (speed*math.cos(angle_in_radians))
	new_y = old_xy[1] + (speed*math.sin(angle_in_radians))
	return new_x, new_y

class Rival(pygame.sprite.Sprite):
	images = []
	def __init__(self, x,y,direction,speed):
		pygame.sprite.Sprite.__init__(self)
		#self.image = pygame.Surface((16,16))
		#self.image.fill((255,0,0))
		self.image = self.images[0]
		self.rect = self.image.get_rect()
		self.rect.center = (x,y)
		self.direction = math.radians(direction)
		self.speed = speed

	def update(self):
		self.rect.center = calculate_new_xy(self.rect.center, self.speed, self.direction)
		
	def position(self):
		return self.rect.center[0], self.rect.center[1]	
		
	def change_direction(self,direction):
		self.direction = math.radians(direction)

	
			
class Eagle(pygame.sprite.Sprite):
	images = []
	def __init__(self, x,y,direction,speed):
		pygame.sprite.Sprite.__init__(self)
		self.image = self.images[0]
		self.rect = self.image.get_rect()
		self.rect.center = (x,y)
		self.direction = math.radians(direction)
		self.angle = direction
		self.speed = speed

	def update(self):
		self.rect.center = calculate_new_xy(self.rect.center, self.speed, self.direction)
		
	def position(self):
		return self.rect.center[0], self.rect.center[1]	
		
	def change_direction(self,direction):
		self.direction = math.radians(direction)
		
 
def load_image(name, colorkey=None):
    "loads an image, prepares it for play"
    fullname = os.path.join('data', name)
    try:
        surface = pygame.image.load(fullname)
    except pygame.error:
        raise (SystemExit, 'Could not load image "%s" %s'%(file, pygame.get_error()))
    if colorkey is not None:
        if colorkey is -1:
            colorkey = surface.get_at((0,0))
                    
       
        surface.set_colorkey(colorkey, RLEACCEL)
        
        #This program retuns the loaded image surface after being converted.
    else:
        surface.set_colorkey((145,204,236), RLEACCEL)
    return surface.convert()

def load_images(*files):
    imgs = []
    for file in files:
        imgs.append(load_image(file, -1))
    return imgs

def load_sound(name):
    #Every sound object should define a play method
    #This function creates sound object from the sound file (.wav)
    #found in 'data' directory.
    class NoneSound:
        def play(self): pass
    #The below command ensures that both pygame.mixer and
    #pygame.mixer.get_init() functions are loaded before
    #sound object is loaded and returned 
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join('data', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except (pygame.error, message):
        print ('Cannot load sound:', fullname)
        raise (SystemExit, message)
    return sound

def get_scores():
    high_scores =[]

    try:
        
        dbSnake = pymysql.connect(host="localhost", user="snakeadmin", passwd="admin123", db="Snake", connect_timeout=10,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
    except:
        result = Display_text('No connection - local scores only',360,175,15,(255,0,0))
        all.add(result)
        repaint_screen()
        pygame.time.delay(1000)
        glob_scores = 0
        Filepath = os.path.join('data', 'scores.dat')
        if os.path.isfile(Filepath):
            FILE = open(Filepath,"r")
            text = FILE.readline()
            high_scores = text.split('"') 
            FILE.close()
        else:
            for i in range(1,11):
                high_scores.append(str(i))
                high_scores.append('0')
                high_scores.append('Cifa')
    else:
        result = Display_text('Connection established...',360,200,15,(255,0,0))
        all.add(result)
        repaint_screen()
        pygame.time.delay(1000)
        glob_scores = 1
        cursor = dbSnake.cursor()
        cursor.execute("SELECT * FROM scores ORDER BY score DESC, record_date")
        score_data = cursor.fetchall()
        rows = len (score_data)
        for i in range (0,rows):
            high_scores.append(str(i+1))
            high_scores.append(str(score_data[i]['score']))
            high_scores.append(score_data[i]['name'])
    
        dbSnake.close()
         
    all.remove(result)
    return high_scores, glob_scores

#This function first clears the screen  by repainting background on it
#and then dirties the screen drawing  the Sprite objects from all
#group. It finally calls the display.update(dirty) function to
#update only the area that is dirtied. Update functin is a final functio
#which makes the drawn area visible. 
def repaint_screen():
  if level == 4:
    
    all.clear(screen, background) 
    #screen.fill((180,247,125))
    screen.blit(anim_screen,(0,0))
    
    #all.clear(screen, background) 
    dirty = all.draw(screen)
    pygame.display.update(dirty)
    #pygame.display.update()
  else:
    all.clear(screen, background) 
    dirty = all.draw(screen)
    pygame.display.update(dirty)
    
def save_scores(high_scores, score, name='', online=0):
    Filepath = os.path.join('data', 'scores.dat')
    # Create a file object:
    # in "write" mode
    FILE = open(Filepath,"w")
    for i in range(0,30):
        if i != 29:
            FILE.write(high_scores[i]+'"')
        else:
            FILE.write(high_scores[i])
    FILE.close()
    
    if online:
        try:
           
            dbSnake = pymysql.connect(host="localhost", user="root", passwd="", db="Snake", connect_timeout=10,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        except:
            pass
        else:
            cursor = dbSnake.cursor()

            #cursor.execute("SELECT * FROM scores WHERE score = %s",(score))
            #scores_data = cursor.fetchall()
            #position = len(scores_data)

            cursor.execute("INSERT INTO scores (score, name) VALUES (%s, %s)", (score, name))
            dbSnake.commit()
            cursor.execute("SELECT * FROM scores ORDER BY score DESC, record_date")
            scores_data = cursor.fetchall()
            rows = len(scores_data)
            if rows > 10:
                bottom = scores_data[9]['score']
                cursor.execute("DELETE FROM scores WHERE score < %s",(bottom,))
                dbSnake.commit()
            dbSnake.close()
        
        
class Food(pygame.sprite.Sprite):
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        #random.randrange(start,stop,step)
        #It is not randint hence third argument step is to be passed for integer values
        #max value is : 20*27 + 16 = 556 ( when the sprite is right or bottom 
        # its its size also have to be added. Taking it to 10 max occupied position = 566 
        self.rect[0] = (random.randrange(1,28,1)*20)+16
        self.rect[1] = (random.randrange(1,28,1)*20)+16


class Vegitable(pygame.sprite.Sprite):
    images = []
    ids = []
    #Tomanto, carrot, cucumber, onion, pumpkin, snakegourd, capsicum, bittergourd
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.imageidx = random.randrange(0,8,1)
        self.image = self.images[self.imageidx]
        

        #we are calling self.update() because setting self.image  & self.rect is a must for a Sprite object
        self.update()
        self.rect = self.image.get_rect()
        self.rect[0] = (random.randrange(1,12,1)*45) + self.imageidx
        self.rect[1] = (random.randrange(1,12,1)*45) + self.imageidx
    
    def update(self):
        
        #pumpkin
        if self.imageidx == 4:
           self.scoreincr = 10
           self.sizeincr  = 1
           
        #snake gourd
        if self.imageidx == 5:
           self.scoreincr = 10
           self.sizeincr  = 2
        #capsicum
        elif self.imageidx == 6:
           self.scoreincr = -1
           self.sizeincr  =  -1
        #bitter gourd
        elif self.imageidx == 7:
           self.scoreincr = -2
           self.sizeincr  = -1
        else:
           self.scoreincr = 2
           self.sizeincr  = 1
        
class Fruit(pygame.sprite.Sprite):
    images = []
    ids = []
    #Apple, Orange, cherry, pineapple, watermellon
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.imageidx = random.randrange(0,5,1)
        self.image = self.images[self.imageidx]
        
        #we are calling self.update() because setting self.image  & self.rect is a must for a Sprite object
        self.update()
        self.rect = self.image.get_rect()
        self.rect[0] = (random.randrange(1,9,1)*50) + self.imageidx
        self.rect[1] = (random.randrange(1,9,1)*50) + self.imageidx


    def update(self):
        #watermellon
        if self.imageidx == 4:
           self.scoreincr = 10
           self.sizeincr  =  0
        #pineapple
        if self.imageidx == 3:
           self.scoreincr = -5
           self.sizeincr  = -1
        #apple
        elif self.imageidx == 0:
           self.scoreincr = 10
           self.sizeincr  =  1
        else:
           self.scoreincr = 5
           self.sizeincr = 1


class Stone(pygame.sprite.Sprite):
    images = []
    #Diamond, pearl, stone1, stone2, stone3
    def __init__(self,id,index):
        pygame.sprite.Sprite.__init__(self)
        self.imageidx = index
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.id = id
       
        
        self.update()
        self.rect[0] = (random.randrange(1,12,1)*45)
        self.rect[1] = (random.randrange(1,12,1)*45)

    def update(self):
        if self.id == 'diamond' :
           self.scoreincr = -5
           self.sizeincr = -1
        elif self.id == 'pearl':
           self.scoreincr = -1
           self.sizeincr  = 0
           
        else:
           self.scoreincr = -1
           self.sizeincr  = -1
        if self.imageidx >=0 :
           self.image = self.images[self.imageidx]
           

class Pipe(pygame.sprite.Sprite):
    images = []
    #Red, Green, Blue, Orange
    def __init__(self,id,index):
        pygame.sprite.Sprite.__init__(self)
        self.imageidx = index
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.id = id
        self.update()
        self.rect[0] = 200
        self.rect[1] = (random.randrange(1,7,1)*40+5)
        
    def update(self):
        self.image = self.images[self.imageidx]
       
        
    def getLeftRect(self):
         leftRect = pygame.Rect(self.rect[0],self.rect[1]+self.image.get_size()[1]/2-9,3,18)
         return leftRect
         
    def getRightRect(self):
        
         rightRect = pygame.Rect(self.rect[0]+self.image.get_size()[0]-3,self.rect[1]+self.image.get_size()[1]/2-9,3,18)
         return rightRect
         
class Centipede(pygame.sprite.Sprite):
    images = []

    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        #rect object will have left,top,width,height among other 
        #properties if any in this order.
        self.rect[0] = 290
        self.rect[1] = 290
        self.speed = 0
        #1 - up ; 2 - right ; 3 - down ; 4 - left clock wise
        self.update_call = 0
        self.img_index = 0
        self.move = [0,-step]
       
    
    def update(self):
        self.update_call += 1
        #event.pump() is called one in a loop. It internally handles
        #events. It should be called when no other event methods are 
        #called. It heavily depends upon display module and it should 
        #defind using display.set_mode prior to calling this function.
        pygame.event.pump()
        #pos = [down,up,left,right] - bool values
        pos = [0,0,0,0]
        if self.rect[0]%20 == 10 and self.rect[1]%20 == 10:
            pos = [pygame.key.get_pressed()[K_DOWN],pygame.key.get_pressed()[K_UP],\
                 pygame.key.get_pressed()[K_LEFT],pygame.key.get_pressed()[K_RIGHT]]
        #In the event of only one of these keys are pressed v ^ < > 
        #update self.move list property
        if sum(pos)==1:
            # self.move[ypos] = (down_bool - up_bool)*step 
            # self.move[xpos] = (right_bool - left_bool)*step 
            #up - -ve direction and left is -ve direction
            #right and down are positive directions
            self.move[1] = (pos[0]-pos[1])*step
            self.move[0] = (pos[3]-pos[2])*step
        
        # mouth open or shut
        #After every 5 calls of this update function switch image surface
        if self.update_call == 5: 
            self.update_call = 0
            if self.img_index:
                self.img_index = 0
            else:
                self.img_index = 1

        # makes the head face in the direction of movement 
        #original head image >))) left facing. 
        #Left movement keep the original image
       
           
        if self.move[0] == -step:
             self.image = self.images[self.img_index]
             #self.chaser.set_direction(0)
             #movement is right flip the original imgae (((<    
        elif self.move[0] == step:
            #transform.flip(image_surface_object, xbool, ybool)
            self.image = pygame.transform.flip(self.images[self.img_index],1,0)
            #self.chaser.set_direction(1)
            #movement is Downward +90 angle 
        elif self.move[1] == step:
            self.image = pygame.transform.rotate(self.images[self.img_index],90)
            #self.chaser.set_direction(2)
            #movement is Upwards -90 angle
        elif self.move[1] == -step :
            self.image = pygame.transform.rotate(self.images[self.img_index],-90)
            #self.rect.move() calculates the newposition and returns the new rect object keeping
        #the original rect object intact.
        newpos = self.rect.move((self.move))
        
        #Now modify the rect object by setting it to newpos.
        self.rect = newpos
    
    #called with width of game surface and it's height 
    #the sprites can be placed in an area 30 < x < 570 and 30 < y < 570 
    def outside(self,x,y,level=1):
      if level == 1:
        if self.rect[0] < 30 or self.rect[0] > x or self.rect[1] < 30 or self.rect[1] > y:
            self.end()
            return True
        else:
            return False
      else:
        if self.rect[0] < 30 :
           self.rect[0] = 540
        elif self.rect[0] > 540 :
           self.rect[0] = 30
        elif self.rect[1] < 30 :
           self.rect[1] = 540
        elif self.rect[1] > 540 :
           self.rect[1] = 30
                
        return False 
              
    #set the image to explosion image
    #change both the x and y values of self.rect which indicated that there is a collision - a violation
    #x only movement or y only movement policy.  
    def end (self):
        self.image = self.images[2]
        self.rect = self.rect.move(-20,-20)
        
    def position(self):
        return self.rect[0], self.rect[1]

    
    def hitsStone(self,x, y):
        #here x, y are the bodies[0].rect[0] and bodies[0].rect[1]
               
        if self.rect[0] > x and self.rect[1] == y:
            #head is right side when it hit the stone
            ydirection = random.randrange(0,2,1)
            if ydirection > 0 :
                    self.rect[1] += 2 * step
            else:
                    self.rect[1] -= 2 * step
            self.rect[0] += 2 * step
        elif self.rect[0] < x and self.rect[1] == y:
            #head is left side when it hit the stone
            ydirection = random.randrange(0,2,1)
            if ydirection > 0 :
                    self.rect[1] += 2 * step
            else:
                    self.rect[1] -= 2 * step
            self.rect[0] -= 2 * step
        elif self.rect[1] < y and self.rect[0] == x:
            xdirection = random.randrange(0,2,1)
            if xdirection > 0 :
                    self.rect[0] += 2 * step
            else:
                    self.rect[0] -= 2 * step
            self.rect[1] -= 2 * step           
        elif self.rect[1] > y and self.rect[0] == x:
            xdirection = random.randrange(0,2,1)
            if xdirection > 0 :
                    self.rect[0] += 2 * step
            else:
                    self.rect[0] -= 2 * step
            self.rect[1] += 2 * step   
        self.update()

    def getLeftRect(self):
         leftRect = pygame.Rect(self.rect[0],self.rect[1]+self.image.get_size()[1]/2-5,5,10)
         return leftRect
         
    def getRightRect(self):
        
         rightRect = pygame.Rect(self.rect[0]+self.image.get_size()[0]-3,self.rect[1]+self.image.get_size()[1]/2-5,5,10)
         return rightRect        


class Body(pygame.sprite.Sprite):
    images = []
 
    def __init__(self, start):
        pygame.sprite.Sprite.__init__(self, self.containers) #call Sprite initializer
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.moves = []
        self.rect[0] = 290
        self.rect[1] = start
        for i in range (0,3):
            self.moves.append((290,start+(i*-step)))
     
    def move(self,xy):
        self.rect[0] = xy[0]
        self.rect[1] = xy[1]
        self.moves.append(xy)
        del self.moves[0]
  
class Bonus(pygame.sprite.Sprite):
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect[0] = (random.randrange(1,28,1)*20)+16
        self.rect[1] = (random.randrange(1,28,1)*20)+16
        
class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", 18)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        #we are calling self.update() because setting self.image  & self.rect is a must for a Sprite object
        self.update()
        #When Score object is created self.rect = [0,0,28,28]
        #After the move self.rect = [30,1,28,28]
        #So the 28 x 28 block is moved from right to 30 and down to 1 piexl. 
        self.rect = self.image.get_rect().move(30, 1)

    def update(self):
        if score != self.lastscore:
            self.lastscore = score
            msg = "Score: %d" % score
            #render(text,anti-aliasing,color)
            self.image = self.font.render(msg, 0, self.color)
            
class AvgScore(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", 18)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        #we are calling self.update() because setting self.image  & self.rect is a must for a Sprite object
        self.update()
        self.rect = self.image.get_rect().move(250, 580)

    def update(self):
        if avgscore != self.lastscore:
            self.lastscore = avgscore
            msg = "Avg. Score: %d" % avgscore
            #render(text,anti-aliasing,color)
            self.image = self.font.render(msg, 0, self.color)            

class SnakeLength(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", 18)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastlength = -1
        
        self.update()
        
        self.rect = self.image.get_rect().move(150, 1)

    def update(self):
        if snake_length != self.lastlength:
            self.lastlength = snake_length
            msg = "Length: %d" % snake_length
            #render(text,anti-aliasing,color)
            #The antialias argument is a boolean: if true the characters will have smooth edges. 
            #The color argument is the color of the text
            self.image = self.font.render(msg, 0, self.color)

class LevelTimeOut(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", 18)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lasttime = -1
        self.update()
        self.rect = self.image.get_rect().move(300, 1)

    def update(self):
        if level_time_out != self.lasttime:
            self.lasttime = level_time_out
            msg = "Time Left: %d" % level_time_out
            #render(text,anti-aliasing,color)
            self.image = self.font.render(msg, 0, self.color)

class Level(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", 18)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastlevel = -1
        self.update()
        self.rect = self.image.get_rect().move(460, 1)

    def update(self):
        if level != self.lastlevel:
            self.lastlevel = level
            msg = "Level: %d" % level
            #render(text,anti-aliasing,color)
            self.image = self.font.render(msg, 0, self.color)

class Text(pygame.sprite.Sprite):
    def __init__(self,status,bonus = 0):
        pygame.sprite.Sprite.__init__(self)
        if status == 1:
            text = "Ouch!!Mind the wall!"
        elif status == 0:
            text = "Ouch!!Don't bite yourself!!"
        elif status == 2:
            text = "Pause"
        elif status == 3:
            text = "Bonus %d" % bonus
        elif status == 4:
            text = "Do you want to play again? (y/n)"
        elif status == 5:
            text = "GAME OVER"
        elif status == 6:
            text = "LEVEL COMPLETED"
        elif status == 7:
            text = "LEVEL TIMEOUT"
        elif status == 8:
            text = "LEVEL CHANGED TO %d" % bonus
        elif status == 9:
            text = "YOU WON. THANKS FOR PLAYING"

        self.font = pygame.font.Font("freesansbold.ttf", 28)
        if status == 9:
            self.font = pygame.font.Font("freesansbold.ttf", 20)
        self.image = self.font.render(text, 1, (Color('maroon')))
        self.rect = self.image.get_rect(centerx = background.get_width()/2,centery = background.get_height()/2)

class Display_text(pygame.sprite.Sprite):
    def __init__(self,text,position_top,position_left,size,colour):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font("freesansbold.ttf", size)
        #font.render(text,anti_aliasing,color)
        self.image = self.font.render(text,1,colour)
        self.rect = self.image.get_rect(left = position_left,top = position_top)

    def update(self,text='',underscore='_',colour=None):
        if text != '' :
           text = text + underscore
           self.image = self.font.render(text,1,colour)

class Main_Image(pygame.sprite.Sprite):
    images=[]
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = self.images[0]
        self.rect = (30,30,540,540)

def calculate_new_xy(old_xy, speed, angle_in_radians):
	new_x = old_xy[0] + (speed*math.cos(angle_in_radians)) 
	new_y = old_xy[1] + (speed*math.sin(angle_in_radians)) 
	return new_x, new_y 
	
class Eagle(pygame.sprite.Sprite):
	images = []
	def __init__(self, x,y,direction,speed):
		pygame.sprite.Sprite.__init__(self)
		self.image = self.images[0]
		self.rect = self.image.get_rect()
		self.rect.center = (x,y)
		self.direction = math.radians(direction)
		self.angle = direction
		self.speed = speed

	def update(self):
		self.rect.midtop = calculate_new_xy(self.rect.midtop, self.speed, self.direction)
		
		
	def position(self):
		return self.rect.center[0], self.rect.center[1]	
		
	def change_direction(self,direction):
		self.direction = math.radians(direction)
	 
class MemBox(pygame.sprite.Sprite):
	images = []
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.surface.Surface((MEMWINDOWWIDTH,MEMWINDOWHEIGHT))
		self.rect = self.image.get_rect()
		self.mainBoard = getRandomizedBoard()
		self.revealedBoxes = generateRevealedBoxesData(False)
		self.updateCalled = False
		
	def update(self):
		startGameAnimation(self.mainBoard,screen)
		self.updateCalled = True
		self.image.fill(CLEARCOLOR)
		screen.blit(self.image,(330,38))
		
	
	def position(self):
		return self.rect.center[0], self.rect.center[1]	
		
def makeTextObjs(text, font, color):                        
	surf = font.render(text, True, color)
	return surf, surf.get_rect()

def generateRevealedBoxesData(val):
    revealedBoxes = []
    for i in range(BOARDWIDTH):
        revealedBoxes.append([val] * BOARDHEIGHT)
    return revealedBoxes

def getRandomizedBoard():
    # Get a list of every possible shape in every possible color.
    icons = []
    num = None
    for color in ALLCOLORS:
            for shape in ALLSHAPES:
                if color == RED :
                      num = NUMCOLOR[0] 
                if color == GREEN :
                      num = NUMCOLOR[1]
                if color == BLUE :
                      num = NUMCOLOR[2]
                if color == ORANGE :
                      num = NUMCOLOR[3]
                icons.append( (shape, color, num) )
            
    random.shuffle(icons) # randomize the order of the icons list
    numIconsUsed = int(BOARDWIDTH * BOARDHEIGHT / 2) # calculate how many icons are needed
    icons = icons[:numIconsUsed] * 2 # make two of each
    random.shuffle(icons)
    # Create the board data structure, with randomly placed icons.
    board = []
    for x in range(BOARDWIDTH):
        column = []
        for y in range(BOARDHEIGHT):
            column.append(icons[0])
            del icons[0] # remove the icons as we assign them
        board.append(column)
    return board

def leftTopCoordsOfBox(boxx, boxy):
    # Convert board coordinates to pixel coordinates
    left = boxx * (BOXSIZE + GAPSIZE) + XMARGIN
    top = boxy * (BOXSIZE + GAPSIZE) + YMARGIN
    return (left, top)

def getBoxAtPixel(x, y):
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if boxRect.collidepoint(x, y):
                return (boxx, boxy)
    return (None, None)

def drawIcon(shape, color, boxx, boxy,surface):
    quarter = int(BOXSIZE * 0.25) # syntactic sugar
    half = int(BOXSIZE * 0.5) # syntactic sugar
    left, top = leftTopCoordsOfBox(boxx, boxy) # get pixel coords from board coords
    # Draw the shapes
    if shape == DONUT:
        
        pygame.draw.circle(surface, BGCOLOR, (left + half, top + half), quarter - 5)
    elif shape == SQUARE:
        pygame.draw.rect(surface, color, (left + quarter, top + quarter, BOXSIZE - half, BOXSIZE - half))
    elif shape == DIAMOND:
        pygame.draw.polygon(surface, color, ((left + half, top), (left + BOXSIZE - 1, top + half), (left + half, top + BOXSIZE - 1), (left, top + half)))
    elif shape == LINES:
        for i in range(0, BOXSIZE, 4):
            pygame.draw.line(surface, color, (left, top + i), (left + i, top))
            pygame.draw.line(surface, color, (left + i, top + BOXSIZE - 1), (left + BOXSIZE - 1, top + i))

    elif shape == OVAL:
        pygame.draw.ellipse(surface, color, (left, top + quarter,BOXSIZE, half))

def getShapeAndColor(board, boxx, boxy):
    # shape value for x, y spot is stored in board[x][y][0]40
    # color value for x, y spot is stored in board[x][y][1]
    return board[boxx][boxy][0], board[boxx][boxy][1], board[boxx][boxy][2]

def drawBoxCovers(board, boxes, coverage,surface):
    # Draws boxes being covered/revealed. "boxes" is a list
    # of two-item lists, which have the x & y spot of the box.
    for box in boxes:
        left, top = leftTopCoordsOfBox(box[0], box[1])
        pygame.draw.rect(surface, BGCOLOR, (left, top, BOXSIZE,  BOXSIZE))
        shape, color, num = getShapeAndColor(board, box[0], box[1])
        drawIcon(shape, color, box[0], box[1],surface)
        if coverage > 0: # only draw the cover if there is an coverage
            pygame.draw.rect(surface, BOXCOLOR, (left, top, coverage,BOXSIZE))
        if color in [RED, GREEN, BLUE, ORANGE] and shape in [SQUARE, DIAMOND, OVAL]:
            numSurf, numRect = makeTextObjs(num, BIGFONT, TEXTCOLOR)
            half = int(BOXSIZE * 0.5) # syntactic sugar
            numRect.center = (left+half,top+half)
            surface.blit(numSurf,numRect)
    pygame.display.update()
    clock.tick(MEMFPS)
        
def revealBoxesAnimation(board, boxesToReveal,surface):
# Do the "box reveal" animation.
    for coverage in range(BOXSIZE, (-REVEALSPEED) - 1, - REVEALSPEED):
        drawBoxCovers(board, boxesToReveal, coverage,surface)
        
def coverBoxesAnimation(board, boxesToCover,surface):
    # Do the "box cover" animation.
    for coverage in range(0, BOXSIZE + REVEALSPEED, REVEALSPEED):
        drawBoxCovers(board, boxesToCover, coverage,surface)

def clearBoard(surface):
    # Draws all of the boxes in their covered or revealed state.
    for boxx in range(BOARDWIDTH+2):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx-1, boxy)
            pygame.draw.rect(surface, CLEARCOLOR, (left, top,BOXSIZE, BOXSIZE))
        
def drawBoard(board, revealed, surface):
    # Draws all of the boxes in their covered or revealed state.
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            if not revealed[boxx][boxy]:
                # Draw a covered box.
                pygame.draw.rect(surface, BOXCOLOR, (left, top,BOXSIZE, BOXSIZE))
            else:
                # Draw the (revealed) icon.
                shape, color, num = getShapeAndColor(board, boxx, boxy)
                drawIcon(shape, color, boxx, boxy,surface)
                numSurf, numRect = makeTextObjs(num, BIGFONT, TEXTCOLOR)
                half = int(BOXSIZE * 0.5) # syntactic sugar
                if color in [RED, GREEN, BLUE, ORANGE] and shape in [SQUARE, DIAMOND, OVAL]:
                    left, top = leftTopCoordsOfBox(boxx, boxy) # get pixel coords from board coords
                    numRect.center = (left+half,top+half)
                    surface.blit(numSurf,numRect)
                
def drawHighlightBox(boxx, boxy):
    left, top = leftTopCoordsOfBox(boxx, boxy)
    pygame.draw.rect(MEMDISPLAYSURF, HIGHLIGHTCOLOR, (left - 5, top - 5, BOXSIZE + 10, BOXSIZE + 10), 4)

def splitIntoGroupsOf(groupSize, theList):
    # splits a list into a list of lists, where the inner lists have at
    # most groupSize number of items.
    result = []
    for i in range(0, len(theList), groupSize):
        result.append(theList[i:i + groupSize])
    return result

def startGameAnimation(board, surface):
    # Randomly reveal the boxes 8 at a time.
    coveredBoxes = generateRevealedBoxesData(False)
    boxes = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
               boxes.append( (x, y) )
               random.shuffle(boxes)
               boxGroups = splitIntoGroupsOf(8, boxes)
               drawBoard(board, coveredBoxes,surface)
    for boxGroup in boxGroups:
            revealBoxesAnimation(board, boxGroup,surface)
            coverBoxesAnimation(board, boxGroup,surface)

def SnakeMenu():

	snake_menu = []
	all.empty()
	repaint_screen()
	text = 'Snake Game Menu'
	snake_menu.append(Display_text(text,90,(540-len(text))/2-30,20,(0,0,255)))
	text = ' --------------------------'
	snake_menu.append(Display_text(text,110,(540-len(text))/2-30,20,(0,0,255)))
	text = '1.  About the game'
	snake_menu.append(Display_text(text,150,(540-len(text))/2-30,20,(0,0,255)))
	text = '2.  Level 1 rules '
	snake_menu.append(Display_text(text,180,(540-len(text))/2-30,20,(0,0,255)))
	text = '3.  Level 2 rules '
	snake_menu.append(Display_text(text,210,(540-len(text))/2-30,20,(0,0,255)))
	text = '4.  Level 3 rules '
	snake_menu.append(Display_text(text,240,(540-len(text))/2-30,20,(0,0,255)))
	text = '5.  Level 4 rules '
	snake_menu.append(Display_text(text,270,(540-len(text))/2-30,20,(0,0,255)))
	text = '6.  Start the game '
	snake_menu.append(Display_text(text,300,(540-len(text))/2-30,20,(0,0,255)))
	
	text = '7.  Quit          '
	snake_menu.append(Display_text(text,330,(540-len(text))/2-30,20,(0,0,255)))
	
	text= '     Your Choice ? '
	snake_menu.append(Display_text(text,370,(540-len(text))/2-30,20,(0,0,255)))
	all.add(snake_menu)
	repaint_screen()

	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:
			sys.exit()
		if event.type == KEYDOWN:
			if event.key == K_1:
				showAbout()
				break
			elif event.key == K_2:
				showLevel1Rules()
				break
			elif event.key == K_3:
				showLevel2Rules()
				break
			elif event.key == K_4:
				showLevel3Rules()
				break
			elif event.key == K_5:
				showLevel4Rules()
				break
			elif event.key == K_6:
				return True
				
			elif event.key == K_7:
				sys.exit()
                           
	all.remove(snake_menu)
	return False
	
def showAbout():
	about = []
	all.empty()
	repaint_screen()
	text='1. About the snake game'
	about.append(Display_text(text,40,(540-len(text))/2-30,14,(0,0,255)))
	text = '  -----------------------------------'
	about.append(Display_text(text,50,(540-len(text))/2-30,14,(0,0,255)))
	
	text ='Snake is a game where the agent must maneuver a sequence of'
	about.append(Display_text(text,80,50,14,(0,0,255)))
	
	text ='rectanglular boxes forming the head and body of the snake '
	about.append(Display_text(text,100,50,14,(0,0,255)))
	text ='which growns in length each time food is touched by the head'
	about.append(Display_text(text,120,50,14,(0,0,255)))
	text ='of the snake. The food is randomly spawned inside the valid window'
	about.append(Display_text(text,140,50,14,(0,0,255)))
	text ='while checking it does not make contact with the body of the snake.'
	about.append(Display_text(text,160,50,14,(0,0,255)))
	
	text='This implementation of snake game consists of 4 levels and the general'
	about.append(Display_text(text,190,50,14,(0,0,255)))
	text='valid actions are: Up, down, left, and right movements.'
	about.append(Display_text(text,210,50,14,(0,0,255)))
	
	text='Invalid actions are :'
	about.append(Display_text(text,240,50,14,(0,0,255)))
		
	text='    It cannot turn back or move backword. It can only move forward.'
	about.append(Display_text(text,260,50,14,(0,0,255)))
	text='    If the head of the snake comes in contact with any of the walls'
	about.append(Display_text(text,280,50,14,(0,0,255)))
	
	text='    or its own body the game will end abruptly.'
	about.append(Display_text(text,300,50,14,(0,0,255)))
	
	text='Rewards:'
	about.append(Display_text(text,330,50,14,(0,0,255)))
	text='    It receives a positive reward +1 for each red square'
	about.append(Display_text(text,350,50,14,(0,0,255)))
	text='    (representing food) and other food items such as vegetables and'
	about.append(Display_text(text,370,50,14,(0,0,255)))
	text='    fruits the head comes in contact with along with an increase in '
	about.append(Display_text(text,390,50,14,(0,0,255)))
	text='    length of the body by 1 unit.'
	about.append(Display_text(text,410,50,14,(0,0,255)))
	
	
	about.append(Display_text('(Press any key to continue)',500,205,15,(255,0,0)))
	all.add(about)	
	repaint_screen()
	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:                          
			sys.exit()
		elif event.type == KEYDOWN:
			break
	all.remove(about)      
	
def showLevel2Rules():
	level_text = []
	all.empty()
	repaint_screen()
	text='3.  Level 2 rules'
	level_text.append(Display_text(text,40,(540-len(text))/2-30,14,(0,0,255)))
	text=' ----------------------'
	level_text.append(Display_text(text,50,(540-len(text))/2-30,14,(0,0,255)))
	
	text='Goal : To proceed to level 3 by maintaining the snake length >= 6 and'
	level_text.append(Display_text(text,70,50,14,(0,0,255)))
	text='getting an average score >= 15 by the end of the 2 minute time period'
	level_text.append(Display_text(text,90,50,14,(0,0,255)))
	text='assigned to second level.'
	level_text.append(Display_text(text,110,50,14,(0,0,255)))
	text='To accept the chance of proceeding directly to 4th level by entering'
	level_text.append(Display_text(text,140,50,14,(0,0,255)))
	text='appropripate pipe. Different colored pipes represent different levels'
	level_text.append(Display_text(text,160,50,14,(0,0,255)))
	text='of the game. This information is visually displayed during the course'
	level_text.append(Display_text(text,180,50,14,(0,0,255)))
	text='of the 2nd level. You get this chance only when snake length is >= 6.'
	level_text.append(Display_text(text,200,50,14,(0,0,255)))
	text='Dos:   Can make the snake move about freely in steps of 10 pixels left,'
	level_text.append(Display_text(text,240,50,14,(0,0,255)))
	text='       right, up or down using Arrow Keys or AWSD Keys.'
	level_text.append(Display_text(text,260,50,14,(0,0,255)))
	       
	text='       Eat the food by making snake head coming in contact with food item.'
	level_text.append(Display_text(text,290,50,14,(0,0,255)))
	       
	text='       Eat carrot and apple to increase the pace of the game.'
	level_text.append(Display_text(text,320,50,14,(0,0,255)))
	
	text='       Eat any other food item to come back to normal speed.'
	level_text.append(Display_text(text,350,50,14,(0,0,255)))
	       
	text='       Accept the bouns at the earliest to gain maximum'
	level_text.append(Display_text(text,380,50,14,(0,0,255)))
	text='       rewards.'
	level_text.append(Display_text(text,400,50,14,(0,0,255)))       
	text='       Enter the appropriate coloured pipe to directly proceed to 4th level'
	level_text.append(Display_text(text,420,50,14,(0,0,255)))
	text='       from 2nd level.'
	level_text.append(Display_text(text,440,50,14,(0,0,255)))
	       
	text="Don'ts :"
	level_text.append(Display_text(text,460,50,14,(0,0,255)))
	text="       Don't try to move the snake in reverse direction."
	level_text.append(Display_text(text,480,50,14,(0,0,255)))       
	text="       Don't let the snake eat pineapple or bittergourd, there will be penalty. "
	level_text.append(Display_text(text,500,50,14,(0,0,255)))       
	text="       Don't step through the stones, there will be penalty."               
	level_text.append(Display_text(text,520,50,14,(0,0,255)))

	level_text.append(Display_text('(Press any key to continue)',540,205,15,(255,0,0)))
	all.add(level_text)	
	repaint_screen()
	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:                          
			sys.exit()
		elif event.type == KEYDOWN:
			break 
	all.remove(level_text)      
      
def showLevel1Rules():
	level_text = []
	all.empty()
	repaint_screen()
	text='2.  Level 1 rules'
	level_text.append(Display_text(text,40,(540-len(text))/2-30,14,(0,0,255)))
	text=' ----------------------'
	level_text.append(Display_text(text,50,(540-len(text))/2-30,14,(0,0,255)))
	text='Goal: To proceed to level 2 by maintaining the snake length >= 6 by the '
	level_text.append(Display_text(text,80,50,14,(0,0,255)))
	text='end of 1 minute time period assigned to first level.'
	level_text.append(Display_text(text,100,50,14,(0,0,255)))
	text='Dos:  '
	level_text.append(Display_text(text,130,50,14,(0,0,255)))
	text='       Can make the snake move about freely in steps of 10 pixels left, '
	level_text.append(Display_text(text,150,50,14,(0,0,255)))
	text='       right, up or down using Arrow Keys or AWSD Keys.'
	level_text.append(Display_text(text,170,50,14,(0,0,255)))
	       
	text='       Eat the food by making snake head coming in contact with food item.'
	level_text.append(Display_text(text,200,50,14,(0,0,255)))
	                  
	text='       Accept the bouns at the eariest to gain maximum '
	level_text.append(Display_text(text,230,50,14,(0,0,255)))
	text='       rewards.' 
	level_text.append(Display_text(text,250,50,14,(0,0,255)))      
	text='       Observe carefully and remember the level numbers associated with '
	level_text.append(Display_text(text,280,50,14,(0,0,255)))
	text='       RGB and Orange Color shapes displayed during the course of the '
	level_text.append(Display_text(text,300,50,14,(0,0,255)))
	text='       game, knowledge of which will enable you to directly proceed to 4th '
	level_text.append(Display_text(text,320,50,14,(0,0,255)))
	text='       level by making the snake pass through appropriate coloured pipe.'
	level_text.append(Display_text(text,340,50,14,(0,0,255)))
	       
	text="Don'ts:"
	level_text.append(Display_text(text,380,50,14,(0,0,255)))
	text="       Don't try to move the snake in reverse direction."
	level_text.append(Display_text(text,400,50,14,(0,0,255)))
	       
	text="       Don't allow the snake to touch the walls of the game window."
	level_text.append(Display_text(text,430,50,14,(0,0,255)))
	
	level_text.append(Display_text('(Press any key to continue)',510,205,15,(255,0,0)))
	all.add(level_text)	
	repaint_screen()
	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:                          
			sys.exit()
		elif event.type == KEYDOWN:
			break 
	all.remove(level_text)	            

   
      
def showLevel3Rules():
	level_text = []
	all.empty()
	repaint_screen()
	text='4.  Level 3 rules'
	level_text.append(Display_text(text,40,(540-len(text))/2-30,14,(0,0,255)))
	text=' ----------------------'
	level_text.append(Display_text(text,50,(540-len(text))/2-30,14,(0,0,255)))

	text='Goal: To proceed to 4th level by maintaining snake length >=6 and getting'
	level_text.append(Display_text(text,80,50,14,(0,0,255)))
	text='an average score >= 10 by the end of 1 minute time period assigned to '
	level_text.append(Display_text(text,100,50,14,(0,0,255)))
	text='level 3.'
	level_text.append(Display_text(text,120,50,14,(0,0,255)))       
	text='Dos:  '
	level_text.append(Display_text(text,150,50,14,(0,0,255)))
	text='       Can make the snake move about freely in steps of 10 pixels left,'
	level_text.append(Display_text(text,170,50,14,(0,0,255)))
	text='       right, up or down using Arrow Keys or AWSD Keys.'
	level_text.append(Display_text(text,190,50,14,(0,0,255)))
	       
	text='       Eat the food by making snake head coming in contact with food item.'
	level_text.append(Display_text(text,220,50,14,(0,0,255)))
	       
	text='       Eat carrot and apple to increase the pace of the game.'
	level_text.append(Display_text(text,250,50,14,(0,0,255)))
	
	text='       Eat any other food item to come back to normal speed.'
	level_text.append(Display_text(text,280,50,14,(0,0,255)))
	       
	text='       Accept the bouns as early as possible to gain maximum'
	level_text.append(Display_text(text,310,50,14,(0,0,255)))
	text='       rewards.'
	level_text.append(Display_text(text,330,50,14,(0,0,255)))
	text="Don'ts:"
	level_text.append(Display_text(text,370,50,14,(0,0,255)))
	text="       Don't try to move the snake in reverse direction."
	level_text.append(Display_text(text,390,50,14,(0,0,255)))       
	text="       Don't let the snake eat pineapple or bittergourd, there will be "
	level_text.append(Display_text(text,420,50,14,(0,0,255)))       
	text='       penalty.'
	level_text.append(Display_text(text,440,50,14,(0,0,255)))              
	text="       Don't step through the stones, there will be penalty."
	level_text.append(Display_text(text,470,50,14,(0,0,255)))      
	
	level_text.append(Display_text('(Press any key to continue)',500,205,15,(255,0,0)))
	all.add(level_text)	
	repaint_screen()
	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:                          
			sys.exit()
		elif event.type == KEYDOWN:
			break 
	all.remove(level_text)   
        
def showLevel4Rules():
	level_text = []
	all.empty()
	repaint_screen()
	text='5.  Level 4 rules'
	level_text.append(Display_text(text,40,(540-len(text))/2-30,14,(0,0,255)))
	text=' ---------------------'
	level_text.append(Display_text(text,50,(540-len(text))/2-30,14,(0,0,255)))

	text='Goal: To win by maintaining snake length >=6 and getting an average '
	level_text.append(Display_text(text,80,50,14,(0,0,255)))
	text='score >= 10 by the end of the 1 minute time period assigned to level 4.'
	level_text.append(Display_text(text,100,50,14,(0,0,255)))       
	text='Dos:  '
	level_text.append(Display_text(text,130,50,14,(0,0,255)))
	text='       Can make the snake move about freely in steps of 10 pixels left, '
	level_text.append(Display_text(text,150,50,14,(0,0,255)))
	text='       right, up or down using Arrow Keys or AWSD Keys.'
	level_text.append(Display_text(text,170,50,14,(0,0,255)))
	       
	text='       Eat food by making snake head coming in contact with food item.'
	level_text.append(Display_text(text,200,50,14,(0,0,255)))
	           
	text='       Accept the bouns as early as possible to gain maximum'
	level_text.append(Display_text(text,230,50,14,(0,0,255)))
	text='       rewards.'
	level_text.append(Display_text(text,250,50,14,(0,0,255)))
	text="Don'ts:"
	level_text.append(Display_text(text,280,50,14,(0,0,255)))
	text="       Don't try to move the snake in reverse direction."
	level_text.append(Display_text(text,300,50,14,(0,0,255)))
	       
	text="       Don't let the snake eat pineapple or bittergourd, there will be penalty."
	level_text.append(Display_text(text,330,50,14,(0,0,255)))       
	text="       Don't step through the stones, there will be penalty."
	level_text.append(Display_text(text,360,50,14,(0,0,255)))    
	
	level_text.append(Display_text('(Press any key to continue)',500,205,15,(255,0,0)))
	all.add(level_text)	
	repaint_screen()
	pygame.event.clear()
	while 1:
		event = pygame.event.wait()
		if event.type == QUIT:                          
			sys.exit()
		elif event.type == KEYDOWN:
			break 
	all.remove(level_text) 
	
def main(start):
    

    #initialize variables
    #These variable are used in classes and functions
    #Screen is the main surface  on to which the background
    #data/centiback.gif is drawn
    #all is a list  of sprites for performing ordered updates
    #bodies is a list of Body sprites. Body is a class derived
    #from pygame.sprite.Sprite
    #Score is a value which will be displayed at the top
    #left corner

    global screen, memBoxAlive, nextlevel, pipeEntered, pipeLeftEntered, pipeRightEntered, anim_screen, background, step, score, avgscore, all, bodies, level, level_time_out, snake_length, l1_score, l2_score, l3_score, level_completed, FPS

    #this is to provide time.delay() when the game is running
    #at the end of the main while loop
    begin = 1
    #you want the snake to move step by step
    step = 10
    memBoxAlive = False
    nextlevel = None

    #initial score
    score = 0
    #At the start of the game the snake is alive and not killed
    #and member of the sprite group
    #A sprite can become member of any number of sprite groups.
    #It is deemed killed if it does not figure in any group.
    snake_alive = 1
    
    #The list of initial positions the head of the snake will
    #will move from and  occupy next. 
    #It is initially positioned upwards at (290,300) and it will
    #take the position (290,290) in one step (10) upwards
    headmoves = [(290,300),(290,290)]
    
    #To keep time for the game. The clock object is used to tick
    #at FPS (frames per second) rate. Larger this FPS faster will
    #be the game. As it creates less wating time/less amount of
    #time delay every time when it is called in a loop. 
    #It is advisable not to change the rate of this FPS to increase
    #or decrease the speed of the snake. Instead change the value of 
    #speed variable of the snake and  calulate the distance it will
    #move in the designated direction every time in a loop
    #after this wait period is completed and update its moment to that
    #position.


    #clock = pygame.time.Clock()
    FPS = 35
    #This is the list of the Body sprites. Initially they are 3 devoid of head of the snake (centiped a sprite object) 
    bodies = []
    #Collection of all the sprites which is used to update the  sprites collectively at one go.
    all = pygame.sprite.OrderedUpdates()
    all = pygame.sprite.LayeredUpdates()
    #Bonus variables given bonus or not (status), 
    #Idea is to provide only one bonus at a time. More than one bonus object is dispalyed
    #at any point of time. Bonus probability (1000) is periodically reduced and checked to see
    #the random range value generated between 1,1000 in step 1 is greater than the current probability value
    #for the player to become eligible to be awarded bonus. This will be awarded only when bonus_status is 0 and
    #within the bonus_time period before withe snake has to encounter the bonus object. Bonus_time is set to a radom
    # range value once the bonus eligibility criteria is satisfied ( bonus_staus == 0, prob = randrange(1,1000,1) > bonus_prob
    #). Bonus_probe will be decremented by one periodically. 

    bonus_status = 0
    bonus_prob = 1000
    bonus_time = 0
    
    #Amount of time the bonus text should be displayed once bonus amount (a variable depending on how quickly bonus is accepted) awarded. 
    text_time = 0
    
    #all these are Sprite objects which will be added at appropriate time to all group and get updated.
    crash_text = pygame.sprite.Sprite()
    bonus_text = pygame.sprite.Sprite()
    
    #bonus is a Sprite Object - so bonus.rect() and bonus.image() are automatically defined. 
    #bonus = Bonus() is called later when you want to display bonus on the screen
    #Bonus() is a class derived from pygame.sprite.Sprite
    bonus = pygame.sprite.Sprite()

    #get main frame
    #This is os level environment variable setting to display the game window at the center of the monitor screen. 
    os.environ['SDL_VIDEO_CENTERED'] = 'anything'

    fullname = os.path.join('data', 'Snake.gif') 
    #This is application icon displayed at the os level.
    pygame.display.set_icon(pygame.image.load(fullname))
    
    #This is to set the screen width and create a display surface object
    #referenced by screen.
    screen = pygame.display.set_mode((600,600),0,32)
    anim_screen = pygame.surface.Surface((600,600))
    #Caption displayed for the game window.
    pygame.display.set_caption('SNAKE GAME by Charitha 2018')
    
    #Background image drawn at the start of the game
    #When the player answered yes to proceed to play the game
    #at the introductory screen.
    #Here the game memu may be displayed allowing the player to
    #login or register or play as a guest and give his/her name later
    #used for the display of the result in case the player gets the
    #rank within the first 10 high scores.
    
    #This is the blank bordered screen on which the snake will be moved.           
    #540 x 540 pixels is the area of the space within which the snake
    #can be moved. 
    #Size of this window is equal to the size of the screen (660x600)
    #and blitted at (0,0) on the screen.
    
    #load_image function locates this image in the subdirectory 'data'
    #and loads this image (display surface object) on to the screen 
    #surface object.

    background = load_image('centiback.gif')
    #This command overlays background image on to the screen display
    #surface buffer at (0,0).

    screen.blit(background,(0,0))
    #The below command finally makes the display visible 
    pygame.display.flip()

    #load sounds for various events and creates sound objects
    #When snake eats the food, game crashed due to snake touches 
    #walls or its own body
    #load_sound is a user defined function

    eat_sound = load_sound('yipee.wav')
    crash_sound = load_sound('foghorn.wav')
    bonus_sound = load_sound('hey.wav')

   
    #load_images user defined function calls load_image() function for 
    #each image and passes it as an argument to load_image to create
    #the  image surface. 
    
    #Images for the head of the snake
    #First two images are shown alternatively after every 5 update calls
    #of the Centipede Sprite object to create the snake mouth open close
    #animation. The third image is to be displayed when crash occurs.
    #load_images() creates a list of image objects. But load_image()
    #returns an image object so to create a list you need [load_image()] 

    Centipede.images = load_images('centi.gif','centi2.gif','explosion1.gif')

    #-1 argument is to get the color_key from get_at(0,0)

    Food.images = [load_image('food.gif',-1)]
    Body.images = [load_image('body.gif',-1)]
    Bonus.images = [load_image('bonus.gif',-1)]

    #Bonus.images = [load_image('apple.png',-1)]

    Main_Image.images = [load_image('MainSnake1.gif')]

   
    Vegitable.images = [pygame.image.load('images/vegitables/tomato.png'),pygame.image.load('images/vegitables/carrot.png'),pygame.image.load('images/vegitables/cucumber.png'),pygame.image.load('images/vegitables/onion.png'),pygame.image.load('images/vegitables/pumpkin.png'),pygame.image.load('images/vegitables/snakegourd.png'),pygame.image.load('images/vegitables/capsicum.png'),pygame.image.load('images/vegitables/bittergourd.png')]
    Vegitable.ids = ['tomato','carrot','cucumber','onion','pumpkin','snakegourd','capsicum','bittergourd']

    Stone.images = [pygame.image.load('images/stones/diamond.png').convert_alpha(),pygame.image.load('images/stones/perl.png').convert_alpha(),pygame.image.load('images/stones/stone1.png').convert_alpha(),pygame.image.load('images/stones/stone2.png').convert_alpha(),pygame.image.load('images/stones/stone3.png').convert_alpha()]

    Pipe.images = [pygame.image.load('images/pipes/hoesred.png').convert_alpha(),pygame.image.load('images/pipes/hoesgreen.png').convert_alpha(),pygame.image.load('images/pipes/hoesblue.png').convert_alpha(),pygame.image.load('images/pipes/hoesorange.png').convert_alpha()]
    Pipe.ids = ['red','green','blue','orange']

    Fruit.images = [pygame.image.load('images/fruits/apple.png'),pygame.image.load('images/fruits/orange.png'),pygame.image.load('images/fruits/cherry.png'),pygame.image.load('images/fruits/pineapple.png'),pygame.image.load('images/fruits/watermellon.png')]
    Fruit.ids = ['apple','orange','cherry','pineapple','watermellon']
    Eagle.images = [pygame.image.load("data/eagle_1.png").convert_alpha()]    

    #This is to hide the mouse cursor from the game window.  
    pygame.mouse.set_visible(0)
    
    #30 border on all sides. Total screen width is 600
    #Game window width is 550 - but actual game object display areaa
    #is 540 x 540 pixels Display width  . Let starting with 30 and 
    #right ending at 570 pixels.

    width = screen.get_width() - 50
    height = screen.get_height() - 50

    #start screen
    #first time when the game is started the call main(0) 
    #initializes start to 0. But the pause button suspends the
    #game and restarts the game (toggle button), in which case the
    #start == 1 not 0. So welcome message is not needed in that case.
    #main introductory game image MainSnake.gif need not be shown.

    counter = 0

    if start == 0:
        start = 1
        level = 1
        level_time_out = 1000
        snake_length = 4
        l1_score = 0
        l2_score = 0
        l3_score = 0
        l4_score = 0
        avgscore = 0
        level_completed = False   
     
        #Main_Image() is a basic pygame.sprite.Sprite derived object.
        #It has a default constructor with no arguments defined.
        #Every Sprite object sould set self.image variable to the
        #loaded image surface sefe.images[0] and initialize the self.rect() 
        #In this case self.rect(30,30,540,540) 

        all.add(Main_Image())
        
        #Display_text(text_message, top,left,font_size,font_color_tuple)
        #pygame.sprite.Sprite derived object which returns surface  
        #object  by rendering
        #text in a particular font using a Font object.
        #Font used is  freesansbold.ttf. Color('maroon') is 
        #pygame method. and 'maroon' is pygame predefined color constant.

        #Display_text being a Sprite derived object has to set two
        #variables self.image  and self.rect

        all.add(Display_text('Welcome!! Press any key to start....',280,210,20,(Color('maroon'))))
        repaint_screen()
        
        #now after seeing this message the user will press a key.
        #so a wait loop has to be created to notice the keypress event.
        #Break out of the un-ending loop only when  a key is pressed or
        #the game window  closed event occurs. It then removes the
        #Welcome message Sprite object and other objects of the group 
        #added to all by emtying it.
        
        while 1:
            event = pygame.event.wait()
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN:
                break   
        all.empty()
        startGame = False
        while startGame == False:
           startGame = SnakeMenu()
        all.empty()
        repaint_screen()
    #create head...
    
    centipede = Centipede()
    centirect = centipede.rect
    Body.containers = all
    #Stone.containers = all
    #...and body...
    for i in range (3):
        #bodies = [Body(330),Body(350),Body(370)]
        bodies.append(Body(330+(i*20)))
    #...and some food
    if level == 1:
       food = Food()
    else:
       vegitable = Vegitable()
       stone      = Stone('diamond',0)
       fruit      = Fruit()
    
    stones = []

    if level != 1 :
      food = Food()
      food.kill()
      for i in range(5):
        while 1 :
            if i == 0 :   
               if centirect.colliderect(stone.rect) or pygame.sprite.spritecollide(stone,bodies,0) != []:
                    stone.kill()
                    stone = Stone('diamond',i)
                    
               else:
                    stones.append(stone)
                    break
            elif i == 1:
              stone = Stone('pearl',i)
              if centirect.colliderect(stone.rect) or pygame.sprite.spritecollide(stone,bodies,0) != [] or pygame.sprite.spritecollide(stone,stones,0) != []:
                    stone.kill()
                    stone = Stone('pearl',i)
              else:
                    stones.append(stone)
                    break
            else:
              stone = Stone('stone',i)
              if centirect.colliderect(stone.rect) or pygame.sprite.spritecollide(stone,bodies,0) != [] or pygame.sprite.spritecollide(stone,stones,0) != []:
                    stone.kill()
                    stone = Stone('stone',i)
              else:
                    stones.append(stone)
                    break
      all.add(stones)

    pipes = []
    pipeEntered = False 
    pipeLeftEntered = False
    pipeRightEntered = False
    nextlevel = None
    if level == 4:
	    w, h = WORLD_SCREEN_SIZE
	    world = World()
	    ant_image = pygame.image.load("data/ant.png").convert_alpha()
	    leaf_image = pygame.image.load("data/leaf.png").convert_alpha()
	    spider_image = pygame.image.load("data/moth.png").convert_alpha()
	
	    # Add all our ant entities

	    for ant_no in range(ANT_COUNT):
                ant = Ant(world, ant_image)
                ant.location = Vector2(randint(60, w-30), randint(60, h-30))
                ant.brain.set_state("exploring")
                world.add_entity(ant)
	    #spr = pygame.sprite.Group()
	    Rival.images = [load_image("Snake.png",-1)]
	    rival = Rival(160,120,135,10) ; all.add(rival)
	   
		

    # make sure food isn't in same place as snake
    # Until food object created is placed in a vacant allowable position loop 
    if level == 1:   
      while 1:
      
          #spritecollide(Sprite, Sprite Group, dokill<bool>) 0=don't kill body intersecting with food
          if centirect.colliderect(food.rect) or pygame.sprite.spritecollide(food,bodies,0) != [] : 
            food.kill()
            food = Food()
          else:
            break
    if level != 1: 
      while 1:
        #spritecollide(Sprite, Sprite Group, dokill<bool>) 0=don't kill body intersecting with food
      
        if centirect.colliderect(vegitable.rect) or pygame.sprite.spritecollide(vegitable,bodies,0) != [] or pygame.sprite.spritecollide(vegitable,stones,0) != []: 
            vegitable.kill()
            vegitable = Vegitable()
        else:
            break
      
      while 1:
        #spritecollide(Sprite, Sprite Group, dokill<bool>) 0=don't kill body intersecting with food
        if centirect.colliderect(fruit.rect) or pygame.sprite.spritecollide(fruit,bodies,0) != [] or pygame.sprite.spritecollide(fruit,stones,0) != [] or fruit.rect.colliderect(vegitable.rect) : 
            fruit.kill()
            fruit = Fruit()
        else:
            break  
      
    if level == 1:    
      all.add(food, centipede)
    else:
      all.add(vegitable,fruit,centipede)
      
    if level == 3 or level == 4:
      eagle = Eagle(480,60,90,3)
      all.add(eagle)
      
    
    # initialize score
    if pygame.font:
        score_instance = Score()
        all.add(score_instance)
        if avgscore > 0 and level >= 2: 
             avgscore_instance = AvgScore()
             all.add(avgscore_instance)
        snake_length_instance = SnakeLength()
        all.add(snake_length_instance)

        level_time_out_instance = LevelTimeOut()
        all.add(level_time_out_instance)

        level_instance = Level()
        all.add(level_instance)
        

    #This is to allow the score updation not to be too fast for the eye to catch and remove any keys pushed during that time    
    pygame.time.delay(400)
    #now we expect arrow keys or AWSD keys P (Pause) ESC keys pressed. If there are any pending keys in the queue clear the queue
    #before accepting any keys.
    pygame.event.clear()
    
    # main game loop - snake is alive if it is not in any Sprite Groups
    # If the snake is not alive (killed) the game is over and there is nothing to be done.
    #Initially bonus_time is set to 0 so every time the while loop is run bonus_time becomes -ve
    #Right now decrementing bonus_time and text_time has no meaning. When they are set to a positive value
    #when the player is eligible for bonus - decrementing them will reduce the time gap.
    
    while snake_alive:

        if level == 1 and counter == 550 :
             counter = 0
             random.shuffle(NUMCOLOR)
             colordict['red'] = NUMCOLOR[0]
             colordict['green'] = NUMCOLOR[1]
             colordict['blue'] = NUMCOLOR[2]
             colordict['orange'] = NUMCOLOR[3]
             
             membox = MemBox()
             all.add(membox)
             memBoxAlive = True
             all.update()
             repaint_screen()
        counter += 1

        if (level == 2 and len(pipes) <=0) and (snake_length >= 6 and level_time_out <= 1000) :
            pipe = Pipe('red',0)
            #for i in range(1):
            i = random.randrange(0,4,1)
            pipe = Pipe(Pipe.ids[i],i)
            while 1 :
               if i == 0 :   
                   if centirect.colliderect(pipe.rect) or pygame.sprite.spritecollide(pipe,bodies,0) != [] or pygame.sprite.spritecollide(pipe,stones,0) != []:
                     pipe.kill()
                     pipe = Pipe('red',i)
                    
                   else:
                     pipes.append(pipe)
                     break
               elif i == 1:
                   pipe = Pipe('green',i)
                   if centirect.colliderect(pipe.rect) or pygame.sprite.spritecollide(pipe,bodies,0) != [] or pygame.sprite.spritecollide(pipe,stones,0) != []:
                     pipe.kill()
                     pipe = Pipe('green',i)
                   else:
                     pipes.append(pipe)
                     break
               elif i == 2:
                   pipe = Pipe('blue',i)
                   if centirect.colliderect(pipe.rect) or pygame.sprite.spritecollide(pipe,bodies,0) != [] or pygame.sprite.spritecollide(pipe,stones,0) != []:
                      pipe.kill()
                      pipe = Pipe('blue',i)
                   else:
                      pipes.append(pipe)
                      break
               elif i == 3:
                   pipe = Pipe('orange',i)
                   if centirect.colliderect(pipe.rect) or pygame.sprite.spritecollide(pipe,bodies,0) != [] or pygame.sprite.spritecollide(pipe,stones,0) != []:
                      pipe.kill()
                      pipe = Pipe('orange',i)
                   else:
                      pipes.append(pipe)
                      break
        all.add(pipes)
        bonus_time -= 1
        text_time -= 1
        level_time_out -= 1
        
        #FPS - frames per second is set to 25

        if level == 4 :
            FPS = 45
        time_passed = clock.tick(FPS)

        centirect = centipede.rect
                
        
        #handles pause and exit
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()
            #key comparision is not case sensitive => K_p is same for UPPER or lower case letters
            elif event.type == KEYDOWN and event.key == K_p:
                pause = 1
                if pygame.font:
                    pause_text=Text(2)
                    all.add(pause_text)
                
                all.clear(screen, background) 
                dirty = all.draw(screen)
               
                pygame.display.update(dirty)
               
                pygame.event.clear()
                while pause:
                    event = pygame.event.wait()
                    if event.type == QUIT:
                        sys.exit()
                    if event.type == KEYDOWN and event.key == K_p:
                        pause = 0
                        pause_text.kill()
                
        #all.update()
        repaint_screen()

        if memBoxAlive == True :
           memBoxAlive = False
           all.remove(membox)
           membox.kill()
        if level == 4:
           # Add all our ant entities
	   # Add a leaf entity 1 in 20 frames
           if randint(1, 10) == 1:
                leaf = Leaf(world, leaf_image)
                leaf.location = Vector2(randint(60, w-20), randint(60, h-20))
                world.add_entity(leaf)
	
           # Add a spider entity 1 in 100 frames
           if randint(1, 100) == 1:
                spider = Spider(world, spider_image)
                #spider.location = Vector2(-50, randint(0, h))
                #spider.destination = Vector2(w+50, randint(0, h))
                spider.location = Vector2(60, randint(60, h-30))
                spider.destination = Vector2(w-30, randint(h-30, h-30))
                
                world.add_entity(spider)
	
           world.set_time_passed(time_passed)	
           world.process(time_passed)
           all.clear(screen,background)
           #screen.fill((180,247,125))
           sourceX, sourceY = (rival.position())
	
           destinationX, destinationY = (centipede.position())
           s = Vector2(sourceX,sourceY)
           d = Vector2(destinationX,destinationY)
           zero = Vector2()
           angle = zero.angle_to(d-s)
           
           all.clear(screen,background)
           #centipede.update()
           world.render(anim_screen)           
           rival.change_direction(angle)
           eagle.change_direction(angle)
	
           #all.update()
           #repaint_screen()
           #spr.draw(screen)
           
           for s in all.sprites():
             all.change_layer(s,-1)
           
        all.update()
        repaint_screen()
        
        pygame.display.flip()
        
       
        # make body move
        #creates bodies[0].moves[(290,330),(290,320),(290,310)]
        #creates bodies[1].moves[(290,350),(290,340),(290,330)]
        #creates bodies[2].moves[(290,370),(290,360),(290,350)]
        #headmoves = [(290,300),(290,290)]
        #when snake head rect moves to (290,290) lasthead = (290,300)
        #bodies[0].move(lasthead) removes (290,330) from bodies[0].moves and appends (290,300)
        #after this operation bodies[0].moves = [(290,320),(290,310),(290,300)]
        #lasthead = bodies[0].moves[0] = (290,320)
        #bodies[1].move(lasthead) removes (290,350) from bodies[1].moves and appends (290,320)
        #after this operation bodies[1].moves = [(290,340),(290,330),(290,320)]
        #lasthead = bodies[1].moves[0] = (290,340)
        #bodies[2].move(lasthead) removes (290,370) from bodies[2].moves and appends (290,340)
        #after this operation bodies[1].moves = [(290,360),(290,350),(290,340)]
        #lasthead = bodies[1].moves[0] = (290,340)

        lastmove = headmoves[0]        
        for body in bodies:
            body.move(lastmove)
            lastmove = body.moves[0]
        
        # update moves of head
        headmoves.append(centipede.position())
        del headmoves[0]
        
        # detects collision with the wall
        if centipede.outside(width,height,level) and level == 1:
            snake_alive = 0
            crash_sound.play()
            #re-create head to make sure it's last sprite in all
            #and nothing is drawn over it
            all.remove(centipede)
            all.remove(score_instance)
            if level > 1:
               all.remove(avgscore_instance)
            all.remove(level_time_out_instance)
            all.remove(snake_length_instance)
            all.remove(level_instance)
            all.remove(centipede)
            all.add(score_instance)
            if level > 1:
               all.add(avgscore_instance)
            all.add(level_time_out_instance)
            all.add(snake_length_instance)
            all.add(level_instance)
            centipede.end()
            if bonus_text.alive():
                bonus_text.kill()
            if pygame.font:
                crash_text = Text(1)
                all.add(crash_text)

                    

        # collision between head and body
        if snake_alive != 0 :
            smallcenti = centipede.rect.inflate(-15,-15)  
            for body in bodies:
                smallbody = body.rect.inflate(-15,-15)
                if smallbody.colliderect(smallcenti):
                    snake_alive = 0
                    crash_sound.play()
                    all.remove(centipede)
                    all.remove(score_instance)
                    if level > 1 :
                       all.remove(avgscore_instance)
                    all.remove(level_time_out_instance)
                    all.remove(snake_length_instance)
                    all.remove(level_instance)
                    all.add(centipede)
                    all.add(score_instance)
                    all.add(level_time_out_instance)
                    all.add(snake_length_instance)
                    all.add(level_instance)
                    if level > 1:
                       all.add(avgscore_instance)
                    centipede.end()
                    if bonus_text.alive():
                        bonus_text.kill()
                    if pygame.font:
                        crash_text = Text(0)
                        all.add(crash_text)

                               
        # repaint before you make snake grow
        # otherwise new body will show in default position
        # before being appended to snake                 
        repaint_screen()
                
        # check if food has been eaten
        # creates new food
        # makes body grow
        if level == 1 and snake_alive != 0 and centirect.colliderect(food.rect):
            food.kill()
            score = score + 1
            bonus_prob = bonus_prob - 1
            eat_sound.play()
            food = Food()
            bodies.append(Body(304))
            snake_length += 1
            while 1:
                #if bonus is visible on the screen
                if bonus.alive():
                    #argument 0 to spritecollide is a bool value - not to kill bodies if collision occurs
                    if centirect.colliderect(food.rect) or pygame.sprite.spritecollide(food,bodies,0) != [] or bonusrect.colliderect(food.rect):
                        food.kill()
                        food = Food()
                    else:
                        break
                else:
                    #check to see whether the new food created falls in vacant place 
                    if centirect.colliderect(food.rect) or pygame.sprite.spritecollide(food,bodies,0) != []:
                        food.kill()
                        food = Food()
                    else:
                        break
            all.add(food)

        #check if the snake hits a stone
        if level != 1 and snake_alive != 0 and pygame.sprite.spritecollide(centipede,stones,0) != []:
               centipede.hitsStone(bodies[0].rect[0],bodies[0].rect[1])
               for stone in stones:
                  if stone.rect.colliderect(centirect):
                     score += stone.scoreincr
                     """
                     if level == 1 :
                        avgscore = score
                     elif level == 2 :
                        avgscore = math.ceil((l1_score + score)/2)
                     elif level == 3 :
                        avgscore = math.ceil((l1_score + l2_score + score)/3)
                     elif level == 4 :
                        avgscore = math.ceil((l1_score + l2_score + l3_score + score)/4) 
                     """   
                     sizeincr = stone.sizeincr
                     
                     while sizeincr < 0 :
                         if snake_length <= 4 :
                            break
                         else:
                            bodies[-1].kill()
                            bodies = bodies[:-1]
                            snake_length -= 1
                         sizeincr += 1
                     break
        #check if the snake enteres a pipe
        if level == 2 and snake_alive != 0 and pygame.sprite.spritecollide(centipede,pipes,0) != []:
            if pipeEntered == True:
               all.remove(pipes)
               for pipe in pipes:
                   kill(pipe)
            else : 
               for pipe in pipes:
                  centiLeftRect = centipede.getLeftRect()
                  centiRightRect = centipede.getRightRect()
                  #centiRect = bodies[-1].rect
                  pipeLeftRect = pipe.getLeftRect()
                  pipeRightRect = pipe.getRightRect()
                  if (centiLeftRect.colliderect(pipeLeftRect) or centiRightRect.colliderect(pipeRightRect)):
                     if centiLeftRect.colliderect(pipeLeftRect) :
                        pipeLeftEntered = True
                  
                     elif centiRightRect.colliderect(pipeRightRect) :
                        pipeRightEntered = True    
                 
            #all.update()
            repaint_screen()
                     
        if pipeRightEntered == True and centipede.getLeftRect().colliderect(pipes[0].getLeftRect()):
                 pipeRightEntered = False
                 pipeEntered = True
                 nextlevel = colordict[pipes[0].id]
                 if nextlevel == "2" :
                     avgscore = math.ceil(l1_score/2)
                 elif nextlevel == "3" :
                     avgscore = math.ceil((l1_score + score)/3)
                 elif nextlevel == "4" :
                     avgscore = math.ceil((l1_score + score)/4)
                 snake_alive = 0
                 l2_score = score
        elif pipeLeftEntered == True and centipede.getRightRect().colliderect(pipes[0].getRightRect()):
                 pipeLeftEntered = False
                 pipeEntered = True
                 nextlevel = colordict[pipes[0].id]
                 if nextlevel == "2" :
                     avgscore = math.ceil(l1_score/2)
                 elif nextlevel == "3" :
                     avgscore = math.ceil((l1_score + score)/3)
                 elif nextlevel == "4" :
                     avgscore = math.ceil((l1_score + score)/4)
                 snake_alive = 0
                 l2_score = score
                 
        # check if vegitable has been eaten
        # creates new vegitable
        # makes body grow depending on vegitable eaten
        # increase the score depending upon the vegitable eaten
        if level != 1 and snake_alive != 0 and centirect.colliderect(vegitable.rect):
            eat_sound.play()
            score = score + vegitable.scoreincr
                       
            if vegitable.ids[vegitable.imageidx] == 'carrot' :
               FPS = 45
            elif vegitable.ids[vegitable.imageidx] != 'carrot':
               FPS = 35

            sizeincr = vegitable.sizeincr
            if sizeincr > 0 :
               for i in range(sizeincr):
                  bodies.append(Body(304))
               snake_length += sizeincr
            elif sizeincr < 0 :
               while sizeincr < 0:
                  if snake_length <= 4:
                     break
                  else:
                     bodies[-1].kill()
                     bodies = bodies[:-1]
                     snake_length -= 1
                  sizeincr += 1
            vegitable.kill()
            bonus_prob = bonus_prob - 1
            vegitable = Vegitable()
                       
            while 1:
               if bonus.alive() :
                  bonusrect = bonus.rect
                  #if bonus is visible on the screen
                  if centirect.colliderect(vegitable.rect) or pygame.sprite.spritecollide(vegitable,bodies,0) != [] or (fruit.alive() and vegitable.rect.colliderect(fruit.rect)) or pygame.sprite.spritecollide(vegitable,stones,0) != [] or (bonus.alive() and bonusrect.colliderect(vegitable.rect)):
                        vegitable.kill()
                        vegitable = Vegitable()
                  else:
                        break
               else:
                  if centirect.colliderect(vegitable.rect) or pygame.sprite.spritecollide(vegitable,bodies,0) != [] or (fruit.alive() and vegitable.rect.colliderect(fruit.rect)) or pygame.sprite.spritecollide(vegitable,stones,0) != []:
                        vegitable.kill()
                        vegitable = Vegitable()
                  else:
                        break
                 
            all.add(vegitable)
        # check if fruit has been eaten
        # creates new fruit
        # makes body grow depending on vegitable eaten
        # increase the score depending upon the vegitable eaten
        if level != 1 and snake_alive != 0 and centirect.colliderect(fruit.rect):
            eat_sound.play()
            if fruit.ids[fruit.imageidx] == 'apple' :
               FPS = 45
            elif vegitable.ids[vegitable.imageidx] != 'apple':
               FPS = 35          
            score = score + fruit.scoreincr
            sizeincr = fruit.sizeincr
            if sizeincr > 0 :
               for i in range(sizeincr):
                  bodies.append(Body(304))
               snake_length += sizeincr
            elif sizeincr < 0 :
               while sizeincr < 0:
                  if snake_length <= 4:
                     break
                  else:
                     bodies[-1].kill()
                     bodies = bodies[:-1]
                     snake_length -= 1
                  sizeincr += 1


            fruit.kill()
            
            bonus_prob = bonus_prob - 1
            
            fruit = Fruit()
            
                        
            while 1:
                if bonus.alive():
                   bonusrect = bonus.rect
                   #if bonus is visible on the screen
                   if centirect.colliderect(fruit.rect) or pygame.sprite.spritecollide(fruit,bodies,0) != [] or (vegitable.alive() and fruit.rect.colliderect(vegitable.rect)) or pygame.sprite.spritecollide(fruit,stones,0) != [] or (bonus.alive() and bonusrect.colliderect(fruit.rect)):
                        fruit.kill()
                        fruit = Fruit()
                   else:
                        break
                else:
                  if centirect.colliderect(fruit.rect) or pygame.sprite.spritecollide(fruit,bodies,0) != [] or (vegitable.alive() and fruit.rect.colliderect(vegitable.rect)) or pygame.sprite.spritecollide(fruit,stones,0) != []:
                        fruit.kill()
                        fruit = Fruit()
                  else:
                        break
            all.add(fruit)

        # display new bonus(only one at a time) 
        #bonus_status tells whether the bonus Object is displaced on the screen
        if bonus_status == 0 and random.randrange(1,1000,1) > bonus_prob:
            bonus_status = 1
            bonus = Bonus()
            bonusrect = bonus.rect
            bonus_time = random.randrange(40,100,1)
            #Keep generating and destroying the bonus object untill the object generated is placed in a vacant place.
            if level != 1 :
              while 1:
                if  bonusrect.colliderect(centipede.rect) or pygame.sprite.spritecollide(bonus,bodies, 0) != [] or pygame.sprite.spritecollide(bonus,stones, 0) != [] or (vegitable.alive and bonusrect.colliderect(vegitable.rect)) or (fruit.alive and bonusrect.colliderect(fruit.rect)):
                    bonus.kill()
                    bonus = Bonus()
                    bonusrect = bonus.rect
                else:
                    break
            else :
                if bonusrect.colliderect(food.rect) or bonusrect.colliderect(centipede.rect) or pygame.sprite.spritecollide(bonus,bodies, 0) != [] :
                    bonus.kill()
                    bonus = Bonus()
                    bonusrect = bonus.rect

            all.add(bonus)
        
        # kill bonus when time is up
        #bonus_time will be either -ve or a +ve value 40 <= bonus_time < 100
        #if bonus_time == 0 it means it was set to a positive value  and time ran out
        #before being accepted
        if bonus_time == 0:
            bonus.kill()
            bonus_status = 0
            
        # kill bonus text
        #text_time will be either -ve or a +ve value 25 ( it is set to 25 when bonus is accepted
        #If bonus is taken bonus is added to score and 'Bonus Amount ' text is displayed for a
        #maximum of 1 second since text_time = 35 and FPS=35. In one second text_time 35 will be
        #decremented in steps of 1 to 0.
        #if bonus_time == 0 it means it was set to a positive value  and time ran out
        #before being accepted
        if text_time == 0:
            bonus_text.kill()

        # check if bonus has been eaten
        # snake also grows with bonus 
        if bonus.alive() and snake_alive != 0:
            if bonusrect.colliderect(centipede.rect):
                bonus.kill()
                bonus_status = 0
                bonus_prob = 1000
                if bonus_text.alive():
                    bonus_text.kill()
                bonus_points = round(bonus_time/5+2)
                score = score + bonus_points
                               
                bonus_sound.play()
                bonus_text = Text(3,bonus_points)
                text_time = 25
                all.add(bonus_text)
                bodies.append(Body(304))
                snake_length += 1
                bonus_time = 0
        if level >= 3 :
                
                sourceX, sourceY = (eagle.position())
                destinationX, destinationY = (centipede.position())
                s = pygame.math.Vector2(sourceX,sourceY)
                d = pygame.math.Vector2(destinationX,destinationY)
                zero = pygame.math.Vector2()
                angle = zero.angle_to(d-s)
	
                #centipede.update()
                eagle.change_direction(angle)
                eagle.update()
                
        promt = ''       
        if level_time_out <= 0 and snake_alive != 0:
            all.empty()
            
            all.add(score_instance)
            if level > 1 :
                all.add(avgscore_instance)
            all.add(level_time_out_instance)
            all.add(snake_length_instance)
            all.add(level_instance)
             
            if level == 1:
               if snake_length >= 6:
                  l1_score = score
                  level_completed = True
                  avgscore = math.ceil(l1_score/2)
                  promt = Display_text('(Congrats! level 1 completed.)',350,205,15,(255,0,0))
               else:
                  promt = Display_text('(Sorry Time Out!! level 1 not completed.)',350,205,15,(255,0,0))
                  level_completed = False
               
            elif level == 2:
               if snake_length >= 6 and (l1_score + score)/2 > 15:
                  l2_score = score
                  level_completed = True
                  avgscore = math.ceil((l1_score + l2_score )/3)
                  promt = Display_text('(Congrats! level 2 completed.)',350,205,15,(255,0,0))
               else:
                  promt = Display_text('(Sorry Time Out!! level 2 not completed.)',350,205,15,(255,0,0))
            elif level == 3:
                  if snake_length >= 6 and (l1_score + l2_score + score) /3 > 10:
                        l3_score = score
                        level_completed = True
                        avgscore = math.ceil((l1_score + l2_score + l3_score )/4)
                        promt = Display_text('(Congrats! level 3 completed.)',350,205,15,(255,0,0))
                  else:
                        promt = Display_text('(Sorry Time Out!! level 3 not completed.)',350,205,15,(255,0,0))
                        level_completed = False
            elif level == 4:
                  if snake_length >= 6 and (l1_score + l2_score + l3_score + score) /4 > 10:
                        l4_score = score
                        level_completed = True
                        avgscore = math.ceil((l1_score + l2_score + l3_score + l4_score)/4)
                        promt = Display_text('(Congrats! You Won.)',350,205,15,(255,0,0))
                  else:
                        promt = Display_text('(Sorry Time Out!! level 4 not completed.)',350,205,15,(255,0,0))
                        level_completed = False
         

        if promt != '':
           if level == 4:
              all.clear(screen,background)
              pygame.display.flip()
              
           all.add(promt) 
           repaint_screen()
           pygame.time.delay(1000)
           all.remove(promt)    
                 
        
        # game over
        #If the snake is killed (removed from the scene for whatever may be the reason
        #the game is over.
        #Whenever collision occurs between snake and walls and snake and its body snake_alive
        #is set to 0. When the snake is present on the screen it is set to 1
        if snake_alive == 0 or level_time_out <= 0 or pipeEntered == True:
            if pipeEntered == True:
               pipeEntered = False
               game_over = Text(8,int(nextlevel))
               level_completed = True
               level = 2
            elif snake_alive == 0:
               pygame.time.delay(1000)
               crash_text.kill()
               game_over = Text(5)
            else:
               if level_completed == True:
                  if level == 4:
                     game_over = Text(9)               
                  else:
                    game_over = Text(6)
               else:
                   game_over = Text(7)
            #level_time_out = 1000
            promt = Display_text('(Press any key to continue)',350,205,15,(255,0,0))
            all.add(game_over,promt)
            repaint_screen()
            
            #remove any keys remaining from the event queue so that event.wait() does wait for a key
            pygame.event.clear()
            while 1:
                    event = pygame.event.wait()
                    if event.type == QUIT:
                           sys.exit()
                    if event.type == KEYDOWN:
                           break
            
            all.remove(game_over, promt)
            all.remove(centipede)
            if level == 1 and food.alive():
                   all.remove(food)
            for pipe in pipes:
                 pipe.kill()
                 all.remove(pipes)
            for body in bodies:
                body.kill()
            if bonus.alive():
                all.remove(bonus)
            if level != 1:
               if vegitable.alive():
                  vegitable.kill()
                  all.remove(vegitable)
               if fruit.alive():
                  fruit.kill()
                  all.remove(fruit)
               for stone in stones:
                  stone.kill()
                  all.remove(stone)
            if level == 3 or level == 4:
               eagle.kill()
               all.remove(eagle)
                                    	
            # create high scores
            info = Display_text('Trying to connect to global High Scores',300,130,18,(255,0,0))
            all.add(info)
            repaint_screen()
            pygame.time.delay(1000)
            high_scores, glob_scores = get_scores()
            all.remove(info)
            
            place = 0
            #From each row of data from the scores table 3 elements are stored in high_scores
            #1 - place (rank/position)  2- Score  3. Name
            #This way for 10 rows of data there will be 30 elements stored in the high_scores
            #So the last score stored is at the index 28 in the high_scores.
            #As the scores are stored in the descending order of score, least score will be at index 28
            if score > int(high_scores[28]):
                #verify score with 9th row and below row by row 
                #i ranges from 25,22,19,...,-2
                #place ranges from 30,27,24,...,3
                for i in range(25,-3,-3):
                    if i < 0:
                        high_scores[1] = str(score)
                        high_scores[2] = "_"
                        place = 3
                        break
                    if score > int(high_scores[i]):
                        high_scores[i+3] = high_scores[i]
                        high_scores[i+4] = high_scores[i+1]
                    else:
                        high_scores[i+3] = str(score)
                        high_scores[i+4] = "_"
                        place = i+5
                        break
            score_text = []
            if glob_scores:
                #score heading vertical position 80, horizontal position 110  
                score_text.append(Display_text('HIGH SCORES (ONLINE TABLE)',80,110,28,(0,0,255)))
            else:
                score_text.append(Display_text('HIGH SCORES (LOCAL  TABLE)',80,110,28,(0,0,255)))
            place_pos = 190
            #i ranges from 0,3,6,...,27
            #place ranges from 3,6,...25,30
            for i in range (0,30,3):
                if place - 3 == i:
                    colour = (255,0,0)
                else:
                    colour = (0,0,255)
                if i == 27:
                    place_pos = 180
                point = high_scores[i+1].find('.')
                #hide the fractional part of the scores and show only integer part
                #in case average score is used as score in which case it can be real value
                if point > 0:
                    high_scores[i+1] = high_scores[i+1] [0:point]
                #The newly inserted line is displayed in RED and all other lines in BLUE color.
                #The last line has Row number 10 a two digit number (rest single digit) so xpos = 180 instead of 190
                #int(high_scores[i]) is 1 for i == 0. So the data rows will be displayed from ypos 135, incremented by 35.
               
                score_text.append(Display_text(high_scores[i],int(high_scores[i])*35+100,place_pos,20,colour))
                #to align scores to xpos 300 - right justified
                score_text.append(Display_text(high_scores[i+1],int(high_scores[i])*35+100,300-(len(high_scores[i+1])*12),20,colour))

                #Player names are left justified. The start at xpos 340

                score_text.append(Display_text(high_scores[i+2],int(high_scores[i])*35+100,340,20,colour))
            if place > 0:
                score_text.append(Display_text('(Congratulations!! Enter your name.)',500,180,15,(255,0,0)))
            else:
                score_text.append(Display_text('(Press any key to continue)',500,205,15,(255,0,0)))
            
            all.add(score_text)
            all.update()
            repaint_screen()
            #line xpos = 110 to 520; ypos 120
            line = pygame.draw.line(screen,(0,0,255),(110,120),(520,120),3)
            #Display a heading line Rank     Score       Name
            pygame.display.update(line)
            #First data line is the 3rd Display_text object so place = 3 
            if place > 0:
                current_string = ''
                while 1:
                    event = pygame.event.wait()
                    if event.type == QUIT:
                        sys.exit()
                    if event.type != KEYDOWN:
                        continue
                    if event.key == K_BACKSPACE:
                        #remove last char
                        current_string = current_string[:-1]
                    elif event.key == K_RETURN:
                        if len(current_string) == 0:
                            current_string = 'Player 1'
                        #score_text[heading_text, row_0_rank, row_0_score, row_0_name, row_1_rank,.....]
                        #if place == 3 you will be point to name of the player with score_text[place] 
                        #call the update method of Display_text(pygame.sprite.Sprite) object
                        score_text[place].update(current_string,'',(255,0,0))
                        #score_text last index is 30  
                        #score_text[31] was 'Congratualtions!! Enter your name.' so replace it with 'Svaing...' 
                        score_text[31].update('Saving........ Please wait.......','',(255,0,0))
                        repaint_screen()
                        #independently drawn - not a sprite and not added to all so that all.upate() is called. 
                        line = pygame.draw.line(screen,(0,0,255),(110,120),(520,120),3)
                        pygame.display.update(line) 
                        break
                    elif event.unicode:
                        if len(current_string) <= 15:
                            if event.unicode !='"':
                                current_string += event.unicode
                    #if enter key is not pressed prepend the name '_' string with the name typed.
                    score_text[place].update(current_string,'_',(255,0,0))
                    repaint_screen()
                    #draw agin line in the  same place after every update
                    line = pygame.draw.line(screen,(0,0,255),(110,120),(530,120),3)
                    pygame.display.update(line) 
                    
                high_scores[place-1] = current_string
                save_scores(high_scores, score, current_string, glob_scores)
            
                score_text[31].update(' Saved! Press any key to continue. ','',(255,0,0))
                repaint_screen()
                line = pygame.draw.line(screen,(0,0,255),(110,120),(520,120),3)
                pygame.display.update(line)
            else:
                # update your local scores with global
                if glob_scores:
                    save_scores(high_scores, score)
            
            while 1:
                event = pygame.event.wait()
                if event.type == QUIT:
                    sys.exit()
                if event.type == KEYDOWN:
                    break
            all.remove(score_text)
            
            if level == 4 and level_completed == True:
              all.remove(game_over, promt)
              all.remove(centipede)
              if level == 1 and food.alive():
                   all.remove(food)
              for pipe in pipes:
                 pipe.kill()
                 all.remove(pipes)
              for body in bodies:
                body.kill()
              if bonus.alive():
                all.remove(bonus)
              if vegitable.alive():
                vegitable.kill()
                all.remove(vegitable)
              if fruit.alive():
                fruit.kill()
                all.remove(fruit)
              for stone in stones:
                stone.kill()
                all.remove(stone)
              eagle.kill()
              all.remove(eagle)
              all.empty()
              repaint_screen()
              score_summary_text = []
              score_summary_text.append(Display_text('Scores Summary',90,212,20,(0,0,255)))
            
              text = 'Level-1 Score   : %03d' % l1_score
              score_summary_text.append(Display_text(text,150,210,18,(0,0,255)))
            
              text = 'Level-2 Score   : %03d' % l2_score
              score_summary_text.append(Display_text(text,170,210,18,(0,0,255)))
            
              text = 'Level-3 Score   : %03d' % l3_score
              score_summary_text.append(Display_text(text,190,210,18,(0,0,255)))
            
              text = 'Level-4 Score   : %03d' % l4_score
              score_summary_text.append(Display_text(text,210,210,18,(0,0,255)))
            
              text = '-----------------------------'
              score_summary_text.append(Display_text(text,230,210,18,(0,0,255)))
            
              total_score = l1_score + l2_score + l3_score + l4_score
              text = 'Total Score       : %03d' % total_score
              score_summary_text.append(Display_text(text,250,210,18,(0,0,255)))
              avg_score = math.ceil(total_score / 4)
              text = 'Average Score : %03d' % avg_score
              score_summary_text.append(Display_text(text,270,210,18,(0,0,255)))
            
              status = 'Game Status : Winner **** Keep it up *****'
              score_summary_text.append(Display_text(status,330,110,20,(212,37,210)))
              
              score_summary_text.append(Display_text('(Press any key to continue)',500,205,15,(255,0,0)))
              
             
              all.add(score_summary_text)
              repaint_screen()
              line = pygame.draw.line(screen,(0,0,255),(110,80),(520,80),3)
              pygame.display.update(line)
            
              #remove any keys remaining from the event queue so that event.wait() does wait for a key
              pygame.event.clear()
              while 1:
                    event = pygame.event.wait()
                    if event.type == QUIT:
                           sys.exit()
                    if event.type == KEYDOWN:
                           break
              all.remove(score_summary_text)
                        
                       
            #all.empty()
            all.add(Main_Image())
            
            if level_completed == True and level == 4:
                all.add(Display_text('Hi Winner! Want to play again? (y/n)',280,230,18,(Color('maroon'))))
                
            elif level_completed == True:
                all.add(Display_text('Proceed to next level? (y/n)',280,230,20,(Color('maroon'))))
               
            else:
                all.add(Display_text('Do you want to play again? (y/n)',280,230,20,(Color('maroon'))))
                
            score = 0
            snake_length = 4
            snake_alive = 0
            level_time_out = 1000
            
            if level_completed == True or nextlevel != None:
               if level == 2 and nextlevel != None:
                  level = int(nextlevel)
                  nextlevel = None
               else:
                  level = level + 1
               if level == 5:
                  level = 1
               level_completed = False
            if level == 2 :
              level_time_out = 2000
            repaint_screen()
                    
        if begin == 1:
            begin = 0
            pygame.time.delay(1000)

# start game when loaded first time              
if __name__ == '__main__': main(0)

# handles 'play again' situation
#This is allow calling main with start = 1 to skip Welcome messsage
#and reloading Main_image()

end = 1
while end:
    event = pygame.event.wait()
    if event.type == QUIT:
        end = 0
    if event.type != KEYDOWN:
        continue
    if event.key == K_ESCAPE:
        end = 0
    elif event.key == K_n:
        end = 0
    elif event.key == K_y:
        main(1)


import pyray as rl
import raylib as ray
import math
import time
import re
import random
import discordrpc
import os
import sys
import webbrowser
import socket
import json
#import cv2
import ctypes

#set path correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))
version = "version 0.1"

#notes for self
'''
interactables are COMPLETELY FUCKED
FIX THEM PLS TY POOKIE
ALSO MAKE A SOUND ENGINE :3
fix the dynamically swinging weapons, claws should not damage, also swords do too much dmg
do websockets
make inventory
make armor
'''

#helper functions

def createconnection(METHOD,HOST="0.0.0.0",PORT="52555",):
    global sock
    match METHOD:
        case _:
            #set ip and port
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.bind((HOST, PORT))
            sock.listen()
            sock.setblocking(False)

def sendpacket(CONTENT):
    global sock
    sock.send(CONTENT)

def recievemessage():
    global sock
    

3
def raritytocolour(rarity):
    #enter a rarity, give back a colour switch case statement
    match rarity:
        case "trash":
            return rl.BROWN
        case "common":
            return rl.BLACK
        case "rare":
            return rl.BLUE
        case "unique":
            return rl.PURPLE
        case "legendary":
            return rl.ORANGE
        case "mythic":
            return rl.YELLOW

def drawcursor():
    #need to draw the cursor onto the screen
    global vcursor, xscale, gamestate
    #check if the cursor is down to choose which one to draw
    if rl.is_mouse_button_down(CLICK):
        rl.draw_texture_ex(texturecache["cursordown.png"],vcursor,0,xscale,rl.WHITE)
    else:
        rl.draw_texture_ex(texturecache["cursor.png"],vcursor,0,xscale,rl.WHITE)
    #check for currently player
    if gamestate == "ingame":
        if players[currentplayer].reloading == True:
            #get the cursor offset
            cursorringoffset = rl.Vector2(
                (texturecache["cursor.png"].width-2) * xscale / 2,
                (texturecache["cursor.png"].height-4) * xscale / 2
            )
            #calculate the current reload percentage
            currentplayerreloadpercent = ((
                players[currentplayer].reloadtimer/weapondata[players[currentplayer].weapon.weaponname]["reloadtime"]
            )*100)
            #draw a ring around the cursor using the offset and percentage
            rl.draw_ring(rl.vector2_add(vcursor,cursorringoffset),27*xscale,31*xscale,-90,(currentplayerreloadpercent*3.6)-90,32,rl.BLACK)
        

def old_angle_between_vectors(v1, v2):
    #grab the difference between the 2 vectors
    dx = v2.x - v1.x
    dy = v2.y - v1.y
    #get the angle using atan and convert radians to degrees
    angle_deg = math.degrees(math.atan2(dy, dx))
    #offset it by 90 and keep it within 360 degrees
    angle_deg = (angle_deg + 90) % 360
    #return the angle
    return angle_deg

def angle_between_vectors(v1, v2):
    #get the angle between 2 vectors, apended by 90, clamped into 360 and in degrees
    return (-math.degrees(rl.vector2_line_angle(v2 ,v1)) -90) % 360

def old_step(vector2, direction, distance):#
    #dont use this like ever
    direction = direction+90
    output = rl.vector2_add(vector2, rl.Vector2(math.cos(math.radians(direction)) * distance, math.sin(math.radians(direction)) * distance))
    return output

def step(vector1, direction, distance):
    #get the direction by convering the direction into radians and offsetting by -270
    direction = math.radians(direction-270)
    #get the sin of the change in y
    changeiny = math.sin(direction) * distance
    #change in x
    changeinx = math.cos(direction) * distance
    #turn it into a vector
    vector2 = rl.Vector2(changeinx,changeiny)
    #turn it into a output
    output = rl.vector2_add(vector1,vector2)
    #output
    return output

def texturefiltering(filteringtype):
    #texture filter it
    global texturecache
    #go through every texture and apply a filter type to it (usually use point tho)
    for texture in texturecache:
        rl.set_texture_filter(texturecache[texture], filteringtype)

#close the game
def close_game():
    #close audio devices
    rl.close_audio_device()
    #close the window
    rl.close_window()
    #close the discord rpc
    if 'rpc' in globals():
        try:
            rpc.disconnect()
        except:
            pass
    #quit env
    quit()

def doui():
    #go through every item in the ui list and draw them + do logic
    for uiitem in ui:
        if isinstance(uiitem,button):
            uiitem.draw_button()
            uiitem.check_click()
        if isinstance(uiitem,slider):
            uiitem.draw_slider()

def playmusic(songtoplay):
    if not rl.is_music_stream_playing(soundcache[songtoplay]):
        rl.play_music_stream(soundcache[songtoplay])
    rl.update_music_stream(soundcache[songtoplay])

def addquanititableitem(list,item,appendammount):
    if item in list:
        list[item] += appendammount
    else:
        list[item] = appendammount
    
class animation():
    def __init__(self,frames,animtype):
        self.frames = frames
        self.animtype = animtype
    def givetexture(self,number=0):
        # frames may be filenames (str) or texture objects; return a texture object
        def _get_texture(frame):
            if isinstance(frame, str):
                return texturecache[frame]
            return frame
        match self.animtype:
            case "random":
                frame = random.choice(self.frames)
                return _get_texture(frame)
            case "order":
                frame = self.frames[number % len(self.frames)]
                return _get_texture(frame)
                #just gives them in order so yeah
            case "time":
                index = int(rl.get_time() * 12) % len(self.frames)
                frame = self.frames[index]
                return _get_texture(frame)
                #time gives them at 12fps; cycles through frames and wraps around
            case _:
                frame = self.frames[0]
                return _get_texture(frame)


class wall():
    def __init__(self,walltype,wallhitbox):
        self.walltype = walltype
        self.hitbox = wallhitbox

class projectile():
    def __init__(self,type,position,direction,team):
        pass
        self.type = type
        self.alive = True
        self.position = position
        self.direction = direction
        self.team = team
        self.texture = texturecache[projectiledata[type]["texture"]]
        self.speed = projectiledata[type]["speed"]
        self.damage = projectiledata[type]["damage"]
        self.lifetime = projectiledata[type]["lifetime"]
        self.size = projectiledata[type]["size"]
        self.ability = projectiledata[type]["ability"]
        self.creationtime = time.time()
        self.starttime = time.time()
        match type:
            #none of this is technically needed, just looks better
            case "slash":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "claw":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "bullet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "bluelaser":
                self.position = step(self.position,self.direction-90,35) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "pellet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "stuffed_pellet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "extra_stuffed_pellet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "nano_pellet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "light_bullet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "heavy_bullet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "corrosive_round":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "ricochet_bullet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.bounces = 5
            case "explosive_bullet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the player
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
            case "arrow":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
            case "volt":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
            case "mikuvolt":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
            case "rip_and_tear_pellet":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
            case "dart":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
            case "hurtspell":
                self.position = step(self.position,self.direction+90,40) #so it spawns in front of the enemy
                self.position = step(self.position,self.direction,40) #so it spawns in front of the weapon
                self.direction = self.direction - random.randint(1,4)
                pass

    def movement(self):
        self.position = step(self.position,self.direction,self.speed * rl.get_frame_time() * 100)
        if rl.vector2_distance(self.position,vspawn) > 50000:
            self.alive = False
        if (time.time() - self.starttime) > self.lifetime:
            self.alive = False
        for wall in walls:
            if wall.walltype == "rectangle":
                if rl.check_collision_circle_rec(self.position,self.size,wall.hitbox):
                    if self.ability == "bounce":
                        self.bounces = self.bounces - 1
                        match random.randint(0,1):
                            case 0:
                                self.direction = self.direction + random.randint(-110,-70)
                            case 1:
                                self.direction = self.direction + random.randint(70,110)
                    else:
                        self.alive = False
            if wall.walltype == "circle":
                if rl.check_collision_circles(self.position,self.size,wall.hitbox,100):
                    if self.ability == "bounce":
                        self.bounces = self.bounces - 1
                        match random.randint(0,1):
                            case 0:
                                self.direction = self.direction + random.randint(-110,-70)
                                self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
                            case 1:
                                self.direction = self.direction + random.randint(70,110)
                                self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
                    else:
                        self.alive = False

class item():
    def __init__(self,weaponname):
        self.weaponname = weaponname
        self.texture = texturecache[weapondata[weaponname]["texture"]]
        self.damage = weapondata[weaponname]["damage"]
        self.position = rl.Vector2(0,0)
        self.magazine = weapondata[weaponname]["capacity"]
        self.ammo = self.magazine
        self.repositiononreload = weapondata[weaponname]["reloadreposition"]
        pass
    def movement(self,player):
        self.position = player.position
        self.position = step(self.position,player.direction,weapondata[self.weaponname]["offset"].x)
        self.position = step(self.position,player.direction+90,weapondata[self.weaponname]["offset"].y)
        if weapondata[self.weaponname]["swingable"] == True:
            if player.isswinging == True:
                self.position = step(self.position,player.direction,weapondata[self.weaponname]["offsetonuse"].x)
                self.position = step(self.position,player.direction+90,weapondata[self.weaponname]["offsetonuse"].y)
        '''
        match self.weaponname:
            case "katana":
                self.position = step(player.position,player.direction+90,30)
                self.position = step(self.position,player.direction,20)
                if weapondata[self.weaponname]["swingable"] == True:
                    if player.isswinging == True:
                        self.position = step(self.position,player.direction,weapondata[self.weaponname]["offsetonuse"].x)
                        self.position = step(self.position,player.direction+90,weapondata[self.weaponname]["offsetonuse"].y)
            case "automatic_rifle":
                self.position = step(player.position,player.direction+90,40)
                self.position = step(self.position,player.direction,40)
            case "shotgun":
                self.position = step(player.position,player.direction+90,40)
                self.position = step(self.position,player.direction,40)
            case "blue_phantom":
                self.position = step(player.position,player.direction+90,40)
                self.position = step(self.position,player.direction,40)
            case "pistol":
                self.position = step(player.position,player.direction+90,38)
                self.position = step(self.position,player.direction,35)
            case "mechanical_firearm":
                self.position = step(player.position,player.direction+90,38)
                self.position = step(self.position,player.direction,35)
            case "dualies":
                pass
                self.position = step(player.position,player.direction,35)
            case "sniper":
                self.position = step(player.position,player.direction+90,40)
                self.position = step(self.position,player.direction,35)
    '''
    def reloadmovement(self,player):
        self.position = step(self.position,player.direction,weapondata[self.weaponname]["reloadoffset"].x)
        self.position = step(self.position,player.direction+90,weapondata[self.weaponname]["reloadoffset"].y)

class player():
    def __init__(self,character):
        self.team = "player"
        self.position = vspawn #cords 0,0 in world space
        self.direction = 0
        self.character = character
        self.maxhealth = characterdata[character]["health"]
        self.speed = characterdata[character]["speed"]
        self.texture = texturecache[characterdata[character]["texture"]]
        self.inventory = {}
        #self.inventory.append(characterdata[character]["default_weapon"])
        addquanititableitem(self.inventory,characterdata[character]["default_weapon"],1)
        self.weapon = item(characterdata[character]["default_weapon"])
        self.jumpheight = 0
        self.weaponcooldown = 0
        self.health = self.maxhealth
        self.staminamax = 10
        self.stamina = self.staminamax
        self.reloading = False
        self.alternate = 0
        self.xvelocity = 0
        self.yvelocity = 0
        self.defence = 5
        self.isswinging = False
        self.swingindex = 0
        self.inventoryopen = False
        self.changeindirection = 0
        self.previousdirection = None
        self.lasttimeplayerswingingpolled = 0
        # whether this swing has already dealt damage
        self.doswingdamage = 0
        # short window (seconds) after swing press during which hits register
        self.swing_timer = 0

    def updateweaponinfo(self):
        self.weapon.texture = texturecache[weapondata[self.weapon.weaponname]["texture"]]
        self.weapon.damage = weapondata[self.weapon.weaponname]["damage"]

    def updateplayerinfo(self):
        self.maxhealth = characterdata[self.character]["health"]
        self.speed = characterdata[self.character]["speed"]
        self.texture = texturecache[characterdata[self.character]["texture"]]


    def moveindir(self, direction, distance): 
        self.position = step(self.position, direction, distance)
    ###
    '''
    def movement(self):
        oldposition = self.position
        if rl.is_key_down(SPRINT) and self.stamina > 0:
            self.speed = characterdata[self.character]["speed"] * 1.6
            self.stamina = self.stamina - (10 * rl.get_frame_time())
        else:
            self.speed = characterdata[self.character]["speed"]
            self.stamina += (3 * rl.get_frame_time())

        self.stamina = rl.clamp(self.stamina,0,self.staminamax)
        if rl.is_key_down(UP):
            self.position = rl.vector2_add(self.position, rl.Vector2(0, (self.speed*rl.get_frame_time()*100*-1)))
        if rl.is_key_down(DOWN):
            self.position = rl.vector2_add(self.position, rl.Vector2(0, (self.speed*rl.get_frame_time()*100)))
        for wall in walls:
            if wall.walltype == "rectangle":
                if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                    self.position = oldposition
            if wall.walltype == "circle":
                if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                    self.position = oldposition
        oldposition = self.position
        if rl.is_key_down(LEFT):
            self.position = rl.vector2_add(self.position, rl.Vector2((self.speed*rl.get_frame_time()*100*-1), 0))
        if rl.is_key_down(RIGHT):
            self.position = rl.vector2_add(self.position, rl.Vector2((self.speed*rl.get_frame_time()*100), 0))
        if rl.is_key_down(JUMP):
            self.jumpheight = self.jumpheight + 1
        for wall in walls:
            if wall.walltype == "rectangle":
                if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                    self.position = oldposition
            if wall.walltype == "circle":
                if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                    self.position = oldposition
        self.jumpheight = self.jumpheight * 0.8
        pass
    '''
    def movement(self):
        # decrement swing window timer
        if self.swing_timer > 0:
            self.swing_timer -= rl.get_frame_time()
            if self.swing_timer <= 0:
                self.swing_timer = 0
                # swing ended
                self.isswinging = False
                self.doswingdamage = 0
        if self.previousdirection == None:
            self.previousdirection = self.direction
        #stamina and sprint
        if rl.is_key_down(SPRINT) and self.stamina > 0:
            self.speed = characterdata[self.character]["speed"] * 1.6
            self.stamina = self.stamina - (10 * rl.get_frame_time())
        else:
            self.speed = characterdata[self.character]["speed"]
            self.stamina += (3 * rl.get_frame_time())
        self.stamina = rl.clamp(self.stamina,0,self.staminamax)
        oldposition = self.position
        #movement check if diag
        if (rl.is_key_down(UP) or rl.is_key_down(DOWN)) and (rl.is_key_down(LEFT) or rl.is_key_down(RIGHT)):
            self.speed = self.speed * 0.7071
        #y
        if rl.is_key_down(UP):
            self.yvelocity = self.yvelocity - (self.speed*rl.get_frame_time()*25)
        if rl.is_key_down(DOWN):
            self.yvelocity = self.yvelocity + (self.speed*rl.get_frame_time()*25)
        self.position = rl.vector2_add(self.position, rl.Vector2(0, self.yvelocity))
        for wall in walls:
            if wall.walltype == "rectangle":
                if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                    self.position = oldposition
            if wall.walltype == "circle":
                if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                    self.position = oldposition
        oldposition = self.position
        #x
        if rl.is_key_down(LEFT):
            self.xvelocity = self.xvelocity - (self.speed*rl.get_frame_time()*25)
        if rl.is_key_down(RIGHT):
            self.xvelocity = self.xvelocity + (self.speed*rl.get_frame_time()*25)
        self.position = rl.vector2_add(self.position, rl.Vector2(self.xvelocity, 0))
        for wall in walls:
            if wall.walltype == "rectangle":
                if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                    self.position = oldposition
            if wall.walltype == "circle":
                if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                    self.position = oldposition
        self.xvelocity = self.xvelocity * 0.8
        self.yvelocity = self.yvelocity * 0.8
        #get swing ammount
        if self.lasttimeplayerswingingpolled < 0.33:
            self.lasttimeplayerswingingpolled += rl.get_frame_time()
        else:
            self.changeindirection = abs(self.direction - self.previousdirection) / rl.get_frame_time()
            if self.changeindirection < 20:
                self.changeindirection = 0
            #print(self.changeindirection)
            self.previousdirection = self.direction
        pass
    

    def pointtomouse(self):
        mouseposition = rl.get_screen_to_world_2d(rl.Vector2(rl.get_mouse_x(), rl.get_mouse_y()), camera)
        self.direction = angle_between_vectors(mouseposition, self.position)
        

    def damage(self):
        global players, projectiles
        for projectile in projectiles:
            if projectile.team != self.team:
                if rl.check_collision_circles(self.position,40,projectile.position,projectile.size):
                    self.health = self.health - rl.clamp(projectile.damage - self.defence,1,float('inf'))
                    numberpopups.append(numberpopup(self.position,projectile.damage - self.defence))
                    projectile.alive = False

    def doinventory(self):
        global INVENTORY
        # first should it be open or close
        if self.inventoryopen == False:
            if rl.is_key_pressed(INVENTORY):
                self.inventoryopen = True
        elif self.inventoryopen == True:
            if rl.is_key_pressed(INVENTORY):
                self.inventoryopen = False

    def drawinventory(self):
        #draw inventory if open and suspend mouse interaction with the world
        if self.inventoryopen == True:
            pass
            #write the draw function
            for item in self.inventory:
                #backdrop for inv if open
                rl.draw_rectangle_rounded(rl.Rectangle(50*xscale,50*yscale,500*xscale,700*yscale),0.1,16,(53,56,57,150))
                rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(50*xscale,50*yscale,500*xscale,700*yscale),0.1,16,5*xscale,rl.BLACK)
                pass
                #draw each item in the inventory
    def attack(self):
        global projectiles
        self.weaponcooldown += rl.get_frame_time()
        if self.weaponcooldown >= weapondata[self.weapon.weaponname]["firerate"] and self.weapon.ammo > 0 and not self.reloading:
            # default to not swinging; will be set on press
            # Use mouse press for swings so each click reliably starts a swing
            if weapondata[self.weapon.weaponname]["swingable"]:
                    match weapondata[self.weapon.weaponname]["requirenewclick"]:
                                case False:
                                    if rl.is_mouse_button_down(CLICK):
                                        self.isswinging = True
                                        self.swing_timer = 0.2
                                        self.doswingdamage = 0
                                        # advance swing index and cooldown
                                        self.swingindex = (self.swingindex + 1) % 2
                                        self.weaponcooldown = 0
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction,self.team))
                                        self.weapon.ammo -=1
                                        self.swingindex = (self.swingindex + 1) % 2
                                        self.weaponcooldown = 0
                                case True:
                                    if rl.is_mouse_button_pressed(CLICK):
                                        self.isswinging = True
                                        self.swing_timer = 0.2
                                        self.doswingdamage = 0
                                        # advance swing index and cooldown
                                        self.swingindex = (self.swingindex + 1) % 2
                                        self.weaponcooldown = 0
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction,self.team))
                                        self.weapon.ammo -=1
                                        self.swingindex = (self.swingindex + 1) % 2
                                        self.weaponcooldown = 0
            else:
                match weapondata[self.weapon.weaponname]["ability"]:
                    case "alternate":
                        # alternate abilities still fire on press
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0

                    case "altalternate":
                        # alternate abilities still fire on press but inverse
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction+90,70),self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction+90,70),self.direction+random.randint(-7,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0

                    case "widealternate":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,14),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-14,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,14),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-14,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                                    
                    case "spray":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    for _ in range(0,random.randint(5,10)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    for _ in range(0,random.randint(5,10)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                    case "minispray":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    for _ in range(0,random.randint(2,5)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    for _ in range(0,random.randint(2,5)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.weaponcooldown = 0
                    case "widealternate":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,14),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-14,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    if self.alternate == 0:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction+random.randint(-7,14),self.team))
                                        self.alternate = 1
                                    else:
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],step(self.position,self.direction-90,70),self.direction+random.randint(-14,7),self.team))
                                        self.alternate = 0
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                    case "spray":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    for _ in range(0,random.randint(5,10)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    for _ in range(0,random.randint(5,10)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                    case "minispray":
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    for _ in range(0,random.randint(2,5)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    for _ in range(0,random.randint(2,5)):
                                        projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction + random.randint(-15,15),self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                    case _:
                        match weapondata[self.weapon.weaponname]["requirenewclick"]:
                            case False:
                                if rl.is_mouse_button_down(CLICK):
                                    projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction,self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                            case True:
                                if rl.is_mouse_button_pressed(CLICK):
                                    projectiles.append(projectile(weapondata[self.weapon.weaponname]["projectile"],self.position,self.direction,self.team))
                                    self.weapon.ammo -=1
                                    self.swingindex = (self.swingindex + 1) % 2
                                    self.weaponcooldown = 0
                                
                                
        if rl.is_key_pressed(RELOAD) and not self.weapon.ammo == self.weapon.magazine and not self.reloading:
            self.reloading = True
            self.reloadtimer = 0
        if self.reloading:
            self.reloadtimer += rl.get_frame_time()
            if self.reloadtimer >= weapondata[self.weapon.weaponname]["reloadtime"]:
                self.reloading = False
                self.weapon.ammo = self.weapon.magazine
                                
class enemy():
    def __init__(self,type,pos):
        self.team = "enemy"
        self.type = type
        self.position = pos
        self.texture = texturecache[enemydata[type]["texture"]]
        self.speed = enemydata[type]["speed"]
        self.maxhealth = enemydata[type]["health"]
        self.health = self.maxhealth   
        self.direction = 0
        self.attack_cooldown = enemydata[self.type]["attackcooldown"]
        self.passedspawncheck = False
        while not self.passedspawncheck:
            self.passedspawncheck = True
            for wall in walls:
                    if wall.walltype == "rectangle":
                        if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                            self.position = rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))
                            self.passedspawncheck = False
                    if wall.walltype == "circle":
                        if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                            self.position = rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))
                            self.passedspawncheck = False
            for enemy in enemies:
                if enemy != self:
                    if rl.check_collision_circles(self.position,40,enemy.position,40):
                        self.position = rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))
                        self.passedspawncheck = False
            if rl.check_collision_circles(self.position,40,vspawn,600):
                            self.position = rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))
                            self.passedspawncheck = False
    def ai(self):
        global players
        smallestdistance = float('inf') 
        playertotarget = None            
        for indexofplayerforenemy, player in enumerate(players):
            self.distance = rl.vector2_distance(player.position, self.position)
            if self.distance < smallestdistance:
                smallestdistance = self.distance
                playertotarget = indexofplayerforenemy
                self.target = players[playertotarget]
        if rl.vector2_distance(self.target.position,self.position) < enemydata[self.type]["detectionrange"]:
            #self.direction = angle_between_vectors(players[playertotarget].position,self.position)
            self.direction += ((angle_between_vectors(players[playertotarget].position,self.position) - self.direction + 180) % 360 - 180) * 0.1
            oldposition = self.position
            match enemydata[self.type]["aitype"]:
                case "standard":
                    self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
                case "dumb":
                    self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
                case "spin":
                    if self.distance < 500:
                        self.position = step(self.position,self.direction+90,(self.speed * rl.get_frame_time() * 100))
                    else:
                        self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
            for wall in walls:
                if wall.walltype == "rectangle":
                    if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                        self.position = oldposition
                if wall.walltype == "circle":
                    if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                        self.position = oldposition
            for enemy in enemies:
                if enemy != self:
                    if rl.check_collision_circles(self.position,40,enemy.position,40):
                        self.position = oldposition
        else:
            oldposition = self.position
            match enemydata[self.type]["aitype"]:
                case "dumb":
                    self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
                    for wall in walls:
                        if wall.walltype == "rectangle":
                            if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                                self.position = oldposition
                        if wall.walltype == "circle":
                            if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                                self.position = oldposition
                    for enemy in enemies:
                        if enemy != self:
                            if rl.check_collision_circles(self.position,40,enemy.position,40):
                                self.position = oldposition
                
    
    def distance_to_self(self,enemy):
        #return rl.vector2_distance_sqr(enemy.position, self.position)
        return rl.vector2_distance(enemy.position, self.position)


    def damage(self):
        global players, projectiles, numberpopups, enemies, particles
        for cprojectile in projectiles:
            if cprojectile.team != self.team:
                if rl.check_collision_circles(self.position,40,cprojectile.position,cprojectile.size):
                    match cprojectile.ability:
                        case "duplicate":
                            projectiles.append(projectile("pellet",step(cprojectile.position,cprojectile.direction-180,150),random.randint(0,360),cprojectile.team))
                    
                            self.health = self.health - cprojectile.damage
                            numberpopups.append(numberpopup(self.position,cprojectile.damage))
                            cprojectile.alive = False

                        case "voltchain":
                            if len(enemies) >= 2:
                                #make a sorted list of their distances
                                enemiesclone = sorted(enemies,key=self.distance_to_self)
                                #make each of them take damage
                                #value 0 is self so skip
                                for i in range(1,int(rl.clamp(len(enemies),0,4))):
                                    #do the damage
                                    if rl.vector2_distance_sqr(self.position,enemiesclone[i].position) < 90000:
                                    
                                        enemiesclone[i].health -= cprojectile.damage
                                        numberpopups.append(numberpopup(enemiesclone[i].position,cprojectile.damage))
                                        #particle trail
                                        particles.append(particle(texturecache["volt.png"],enemiesclone[i].position,random.randint(0,360),0,0.1,4))
                                self.health = self.health - cprojectile.damage
                                numberpopups.append(numberpopup(self.position,cprojectile.damage))
                                particles.append(particle(cprojectile.texture,self.position,random.randint(0,360),0,0.1,4))
                                cprojectile.alive = False
                            else:
                                self.health = self.health - cprojectile.damage
                                numberpopups.append(numberpopup(self.position,cprojectile.damage))
                                particles.append(particle(cprojectile.texture,self.position,random.randint(0,360),0,0.1,4))
                                cprojectile.alive = False

                        case "mikuvoltchain":
                            if len(enemies) >= 2:
                                #make a sorted list of their distances
                                enemiesclone = sorted(enemies,key=self.distance_to_self)
                                #make each of them take damage
                                #value 0 is self so skip
                                for i in range(1,int(rl.clamp(len(enemies),0,7))):
                                    #do the damage
                                    if rl.vector2_distance_sqr(self.position,enemiesclone[i].position) < 90000:
                                    
                                        enemiesclone[i].health -= cprojectile.damage
                                        numberpopups.append(numberpopup(enemiesclone[i].position,cprojectile.damage))
                                        #particle trail
                                        particles.append(particle(texturecache["mikuvolt.png"],enemiesclone[i].position,random.randint(0,360),0,0.1,4))
                                self.health = self.health - cprojectile.damage
                                numberpopups.append(numberpopup(self.position,cprojectile.damage))
                                particles.append(particle(cprojectile.texture,self.position,random.randint(0,360),0,0.1,4))
                                cprojectile.alive = False
                            else:
                                self.health = self.health - cprojectile.damage
                                numberpopups.append(numberpopup(self.position,cprojectile.damage))
                                particles.append(particle(cprojectile.texture,self.position,random.randint(0,360),0,0.1,4))
                                cprojectile.alive = False
                        
                        case "knockback":
                            self.health = self.health - cprojectile.damage
                            numberpopups.append(numberpopup(self.position,cprojectile.damage))
                            oldposition = self.position
                            self.position = step(self.position,cprojectile.direction,100)
                            for wall in walls:
                                if wall.walltype == "rectangle":
                                    if rl.check_collision_circle_rec(self.position,40,wall.hitbox):
                                        self.position = oldposition
                                if wall.walltype == "circle":
                                    if rl.check_collision_circles(self.position,40,wall.hitbox,100):
                                        self.position = oldposition
                            for enemy in enemies:
                                if enemy != self:
                                    if rl.check_collision_circles(self.position,40,enemy.position,40):
                                        self.position = oldposition
                            cprojectile.alive = False

                        case _:
                            self.health = self.health - cprojectile.damage
                            numberpopups.append(numberpopup(self.position,cprojectile.damage))
                            cprojectile.alive = False
        '''
        for player in players:
            if weapondata[player.weapon.weaponname]["swingable"]:
                if player.changeindirection > 50:
                    if rl.check_collision_circles(self.position,25,step(player.position,player.direction,20),100):
                        self.health = self.health - weapondata[player.weapon.weaponname]["damage"]
                        numberpopups.append(numberpopup(self.position,weapondata[player.weapon.weaponname]["damage"]))
        '''
        
                        

                


    def attack(self):
        global players, projectiles, particles
        if self.attack_cooldown > enemydata[self.type]["attackcooldown"]:
            match enemydata[self.type]["attacktype"]:
                case "arrow":
                    pass
                    if rl.vector2_distance(self.target.position,self.position) < enemydata[self.type]["attackrange"]:
                        projectiles.append(projectile("arrow",self.position,self.direction,self.team))
                        self.attack_cooldown = 0
                case "dart":
                    pass
                    if rl.vector2_distance(self.target.position,self.position) < enemydata[self.type]["attackrange"]:
                        projectiles.append(projectile("dart",self.position,self.direction,self.team))
                        self.attack_cooldown = 0
                case "melee":
                    for player in players:
                        if rl.vector2_distance(self.position,player.position) < enemydata[self.type]["attackrange"]:
                            player.health = player.health - rl.clamp(enemydata[self.type]["attackdamage"]-player.defence,1,float('inf'))
                            numberpopups.append(numberpopup(self.position,int(rl.clamp(enemydata[self.type]["attackdamage"]-player.defence,1,float('inf')))))
                            particles.append(particle(texturecache["slash.png"],self.position,self.direction,5,0.2,1))
                            self.attack_cooldown = 0
                case _:
                    pass
                    if rl.vector2_distance(self.target.position,self.position) < enemydata[self.type]["attackrange"]:
                        projectiles.append(projectile(enemydata[self.type]["attacktype"],self.position,self.direction,self.team))
                        self.attack_cooldown = 0
        
        self.attack_cooldown += rl.get_frame_time()
            
class particle():
    def __init__(self,texture,position,direction,speed,lifetime,scale):
        self.position = position
        self.texture = texture
        self.direction = direction
        self.speed = speed
        self.lifetime = lifetime
        self.scale = scale
        self.starttime = time.time()
        self.alive = True
    def movement(self):
        self.position = step(self.position,self.direction,(self.speed * rl.get_frame_time() * 100))
        if (time.time() - self.starttime) > self.lifetime:
            self.alive = False
    
class numberpopup():
    def __init__(self,position,value):
        self.position = position
        self.value = value
        self.timeleft = 0.2
        self.alive = True
    
    def updatelifetime(self):
        self.timeleft -= rl.get_frame_time()
        if self.timeleft < 0:
            self.alive = False

class interactable():
    def __init__(self,name,position):
        self.position = position
        self.name = name
        self.texture = texturecache[interactabledata[self.name]["texture"]]
        self.cooldown = 0
        self.scale = 1
        self.alive = True
    
    def touchingplayer(self):
        self.cooldown -= rl.get_frame_time()
        for player in players:
            if not rl.check_collision_circles(player.position,100,self.position,100):
                pass
            else:
                if rl.is_key_pressed(INTERACT) and self.cooldown <= 0:
                    self.cooldown = interactabledata[self.name]["cooldown"]
                    addquanititableitem(player.inventory,interactabledata[self.name]["drops"],random.randint(interactabledata[self.name]["quantity"].x,interactabledata[self.name]["quantity"].y))                 
        
class uielement():
    def __init__(self):
        pass
    
class button(uielement):
    def __init__(self,identity,rectangle,content):
        self.identity = identity
        self.content = content
        self.rectangle = rectangle
    
    def is_hovered(self):
        self.drawrectangle = self.rectangle
        self.drawrectangle = rl.Rectangle(self.drawrectangle.x*xscale,self.drawrectangle.y*yscale,self.drawrectangle.width*xscale,self.drawrectangle.height*yscale)
        if rl.check_collision_point_rec(vcursor,self.drawrectangle):
            return True
        else:
            return False
        
    def draw_button(self):
        global xscale, yscale
        self.drawrectangle = self.rectangle
        self.drawrectangle = rl.Rectangle(self.drawrectangle.x*xscale,self.drawrectangle.y*yscale,self.drawrectangle.width*xscale,self.drawrectangle.height*yscale)
        if self.is_hovered():
            #make button bigger when hovered
            self.drawrectangle = rl.Rectangle((self.drawrectangle.x-4),(self.drawrectangle.y-4),(self.drawrectangle.width+8),(self.drawrectangle.height+8))
            self.sizetodrawtext = 56
        else:
            self.sizetodrawtext = 50
        if self.is_hovered():
            rl.draw_rectangle_rounded(self.drawrectangle,0.3,1,(73,76,77,150))
        else:
            rl.draw_rectangle_rounded(self.drawrectangle,0.3,1,(53,56,57,150))
        rl.draw_rectangle_rounded_lines_ex(self.drawrectangle,0.3,1,5*xscale,rl.BLACK)
        #draw centered text in button (complex)
        self.drawedtextsize = rl.measure_text_ex(gamefont,self.content,self.sizetodrawtext*xscale,0)
        #have flashing text when typing in the type ip button/ when it is selected
        global typingip
        if self.identity == "typeip" and typingip:
            rl.draw_text_ex(
                gamefont,
                self.content,
                rl.Vector2((self.drawrectangle.x+(self.drawrectangle.width/2)-(self.drawedtextsize.x/2)),(self.drawrectangle.y+(self.drawrectangle.height/2))-(self.drawedtextsize.y/2)),
                self.sizetodrawtext*xscale,
                0,
                (0,0,0,int(rl.clamp(math.sin(time.time()*4)*127+128,150,255)))
                )
        else:
            rl.draw_text_ex(
            gamefont,
            self.content,
            rl.Vector2((self.drawrectangle.x+(self.drawrectangle.width/2)-(self.drawedtextsize.x/2)),(self.drawrectangle.y+(self.drawrectangle.height/2))-(self.drawedtextsize.y/2)),
            self.sizetodrawtext*xscale,
            0,
            rl.BLACK
            )
    def check_click(self):
        #actions
        global gamestate, typingip
        if self.is_hovered():
            if rl.is_mouse_button_pressed(CLICK):
                match self.identity:
                    case "play":
                        pass
                        print("hello world")
                        gamestate = "gamesetup"
                    case "continue":
                        reset()
                        gamestate = "ingame"
                    case "settings":
                        pass
                        gamestate = "settings"
                    case "credits":
                        gamestate = "swaptocredits"
                        pass
                    case "exit":
                        global rpc
                        pass
                        close_game()
                    case "back":
                        gamestate = "applysettings"
                    case "fullscreen":
                        if gamesettings["fullscreen"] == "on":
                            gamesettings["fullscreen"] = "off"
                        else:
                            gamesettings["fullscreen"] = "on"
                    case "graphics":
                        match gamesettings["graphics"]:
                            case "low":
                                gamesettings["graphics"] = "medium"
                            case "medium":
                                gamesettings["graphics"] = "high"
                            case "high":
                                gamesettings["graphics"] = "low"
                    case "volume":
                        match gamesettings["volume"]:
                            case "mute":
                                gamesettings["volume"] = "max"
                            case "max":
                                gamesettings["volume"] = "mute"
                    case "vsync":
                        match gamesettings["vsync"]:
                            case "off":
                                gamesettings["vsync"] = "on"
                            case "on":
                                gamesettings["vsync"] = "off"
                    case "mode":
                        match gamesettings["mode"]:
                            case "host":
                                gamesettings["mode"] = "client"
                            case "client":
                                gamesettings["mode"] = "host"
                    case "help":
                        webbrowser.open_new_tab("https://ionslayerr.github.io")
                    case "respawn":
                        reset()
                        gamestate = "mainmenu"
                    case "menu":
                        gamestate = "applysettings"
                    case "join":
                        reset()
                        gamestate = "ingame"
                    case "host":
                        reset()
                        gamestate = "ingame"
                    case "typeip":
                        if not typingip:
                            typingip = True
                    case _:
                        pass
                        gamestate = "error"
        
class slider(uielement):
    def __init__(self,identity,rectangle,content,value,minvalue,maxvalue):
        self.identity = identity
        self.content = content
        self.rectangle = rectangle
        self.value = value
        self.minvalue = minvalue
        self.maxvalue = maxvalue
    
    def is_hovered(self):
        self.drawrectangle = self.rectangle
        self.drawrectangle = rl.Rectangle(self.drawrectangle.x*xscale,self.drawrectangle.y*yscale,self.drawrectangle.width*xscale,self.drawrectangle.height*yscale)
        if rl.check_collision_point_rec(vcursor,self.drawrectangle):
            return True
        else:
            return False
        
    def draw_slider(self):
        global xscale, yscale
        self.drawrectangle = self.rectangle
        self.drawrectangle = rl.Rectangle(self.drawrectangle.x*xscale,self.drawrectangle.y*yscale,self.drawrectangle.width*xscale,self.drawrectangle.height*yscale)
        rl.draw_rectangle_rounded(self.drawrectangle,0.3,1,(53,56,57,150))
        rl.draw_rectangle_rounded_lines_ex(self.drawrectangle,0.3,1,5*xscale,rl.BLACK)
        self.sizetodrawtext = 50
        #draw text centered horizontally, 25% down vertically in the rect
        self.drawedtextsize = rl.measure_text_ex(gamefont,self.content,self.sizetodrawtext*xscale,0)
        rl.draw_text_ex(
            gamefont,
            self.content,
            rl.Vector2((self.drawrectangle.x+(self.drawrectangle.width/2)-(self.drawedtextsize.x/2)),(self.drawrectangle.y+(self.drawrectangle.height/4))-(self.drawedtextsize.y/4)),
            self.sizetodrawtext*xscale,
            0,
            rl.BLACK
            )
        #first find the space in the rectangle to draw the slider part
        self.drawspace = self.drawrectangle(self.drawrectanglex+20*xscale,self.drawrectangle.y+(self.drawrectangle.height/2)-10*yscale,self.drawrectangle.width-40*xscale,20*yscale)
        #sliders arent actually dragable, just click on a certain point to set value
    def check_click(self):
        pass
    def is_hovered(self):
        pass


def setup():
    global typingip, writtenip, showpause, camerazoom, debugmode, wheel, gamequality, glbtime, invopen, itemdata, interactables, interactabledata, sounddata,tracklist, rpc, vectorscale, selectedcharacter, numberpopups, uidata, creditsscrolltimer, ui, buttons, selectedcharacter, armourdata, graphicsoptions, gamesettings, particles, screencapture, soundcache, gamefont, titlescreenparticles, projectiledata, texturefilteringtype,fakefps, vspawn, vcursorfordragbox, vcursor, usefollowingcamera, walls, camera,enemydata, characterdata, weapondata,  screen_width, screen_height, gamestate, texturecache, virtual_width, virtual_height, currentplayer, players, projectiles, enemies, worldmap, camera, accum_48hz, accum_24hz
    accum_48hz = 0.0
    accum_24hz = 0.0
    debugmode = False
    writtenip = ""
    typingip = False
    #game data
    characterdata = {
        "ninja" : {
            "texture":"ninja.png",
            "health":90,
            "speed":7,
            "default_weapon":"katana",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Ninja",
            "bonustextures":[]
            },
        "wizard" : {
            "texture":"wizard.png",
            "health":105,
            "speed":5,
            "default_weapon":"wand",
            "script": "default",
            "badgetexture":"wizardbadge.png",
            "displayname":"Wizard",
            "bonustextures":[]
            },
        "wolfknight" : {
            "texture":"wolfknight.png",
            "health":140,
            "speed":6,
            "default_weapon":"claws",
            "script": "default",
            "badgetexture":"wolfknightbadge.png",
            "displayname":"Wolf Knight",
            "bonustextures":[]
            },
        "sakura" : {
            "texture":"sakura.png",
            "health":165,
            "speed":5,
            "default_weapon":"katana",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Sakura",
            "bonustextures":[]
            },
        "hitman" : {
            "texture":"hitman.png",
            "health":100,
            "speed":4,
            "default_weapon":"sniper",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Hitman",
            "bonustextures":[]
            },
        "rin" : {
            "texture":"rin.png",
            "health":100,
            "speed":4,
            "default_weapon":"fireworks",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Rin",
            "bonustextures":[]
            },
        "seraph" : {
            "texture":"seraph.png",
            "health":100,
            "speed":5,
            "default_weapon":"staff",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Seraph",
            "bonustextures":[]
            },
        "noxen" : {
            "texture":"noxen.png",
            "health":100,
            "speed":4,
            "default_weapon":"knife",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Noxen",
            "bonustextures":[]
            },
        "hunter" : {
            "texture":"hunter.png",
            "health":100,
            "speed":4,
            "default_weapon":"axe",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Hunter",
            "bonustextures":[]
            },
        "heath" : {
            "texture":"heath.png",
            "health":100,
            "speed":4,
            "default_weapon":"bolt_action_rifle",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Heath",
            "bonustextures":[]
            },
        "hostage" : {
            "texture":"hostage.png",
            "health":100,
            "speed":4,
            "default_weapon":"automatic_shotgun",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Hostage",
            "bonustextures":[]
            },
        "boxer" : {
            "texture":"boxer.png",
            "health":100,
            "speed":4,
            "default_weapon":"boxing_gloves",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Boxer",
            "bonustextures":[]
            },
        "engineer" : {
            "texture":"engineer.png",
            "health":100,
            "speed":4,
            "default_weapon":"taser",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Engineer",
            "bonustextures":[]
            },
        "raider" : {
            "texture":"raider.png",
            "health":100,
            "speed":4,
            "default_weapon":"negative_dagger",
            "script": "default",
            "badgetexture":"raiderbadge.png",
            "displayname":"Raider",
            "bonustextures":[]
            },
        "angel" : {
            "texture":"angel.png",
            "health":45,
            "speed":8,
            "default_weapon":"staff",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Angel",
            "bonustextures":[]
            },
        "demon" : {
            "texture":"demon.png",
            "health":55,
            "speed":7,
            "default_weapon":"fork",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Demon",
            "bonustextures":[]
            },
        "robot" : {
            "texture":"robot.png",
            "health":250,
            "speed":3,
            "default_weapon":"blaster",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Robot",
            "bonustextures":[]
            },
        "richu" : {
            "texture":"richu.png",
            "health":100,
            "speed":4,
            "default_weapon":"dualies",
            "script": "default",
            "badgetexture":"richubadge.png",
            "displayname":"Richu",
            "bonustextures":[]
            },
        "michi" : {
            "texture":"michi.png",
            "health":85,
            "speed":5,
            "default_weapon":"pistol",
            "script": "default",
            "badgetexture":"michibadge.png",
            "displayname":"Michi",
            "bonustextures":[]
            },
        "rosalyn" : {
            "texture":"rosalyn.png",
            "health":85,
            "speed":5,
            "default_weapon":"pistol",
            "script": "default",
            "badgetexture":"rosalynbadge.png",
            "displayname":"Rosalyn",
            "bonustextures":[]
            },
        "slayer" : {
            "texture":"slayer.png",
            "health":100,
            "speed":5,
            "default_weapon":"automatic_shotgun",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Slayer",
            "bonustextures":[]
            },
        "piglord" : {
            "texture":"piglord.png",
            "health":150,
            "speed":6,
            "default_weapon":"broadsword",
            "script": "default",
            "badgetexture":"piglordbadge.png",
            "displayname":"Pig Lord",
            "bonustextures":[]
            },
    } # nameoftexture is always 0, the its just stats
    """
        "hatsune_miku" : {
            "texture":"hatsune_miku.png",
            "health":100,
            "speed":5,
            "default_weapon":"miku_miku_beam",
            "script": "default",
            "badgetexture":"ninjabadge.png",
            "displayname":"Hatsune Miku",
            "bonustextures":[]
            },
        "doomguy" : {
            "texture":"doomguy.png",
            "health":700,
            "speed":12,
            "default_weapon":"super_shotgun",
            "script": "default",
            "badgetexture":"doomguybadge.png",
            "displayname":"Doomguy",
            "bonustextures":[]
            },
    """
    weapondata = {
        "katana" : {
            "texture":"katana.png",
            "damage":10,
            "firerate":0.3,
            "projectile":"slash",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "fork" : {
            "texture":"fork.png",
            "damage":10,
            "firerate":0.5,
            "projectile":"lunge",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(40,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "staff" : {
            "texture":"staff.png",
            "damage":10,
            "firerate":0.3,
            "projectile":"lunge",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(10,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "dagger" : {
            "texture":"dagger.png",
            "damage":5,
            "firerate":0.1,
            "projectile":"slash",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(5,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "knife" : {
            "texture":"knife.png",
            "damage":5,
            "firerate":0.1,
            "projectile":"slash",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(20,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(15,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "negative_dagger" : {
            "texture":"negative_dagger.png",
            "damage":5,
            "firerate":0.05,
            "projectile":"inverted_dagger",
            "speed":15,
            "capacity": 7,
            "reloadtime":1.8,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(30,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "broadsword" : {
            "texture":"broadsword.png",
            "damage":12,
            "firerate":0.2,
            "projectile":"slash",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(40,33),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": True,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "wand" : {
            "texture":"wand.png",
            "damage":10,
            "firerate":0.3,
            "projectile":"hurtspell",
            "speed":15,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(20,40),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "automatic_shotgun" : {
            "texture":"automatic_shotgun.png",
            "damage":8,
            "firerate":0.6,
            "projectile":"pellet",
            "speed":15,
            "capacity": 6,
            "reloadtime":2.3,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-5,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": "spray",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "double_barrel_shotgun" : {
            "texture":"double_barrel_shotgun.png",
            "damage":8,
            "firerate":0.4,
            "projectile":"extra_stuffed_pellet",
            "speed":20,
            "capacity": 2,
            "reloadtime":1.8,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-5,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": "minispray",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "pump_shotgun" : {
            "texture":"pump_shotgun.png",
            "damage":8,
            "firerate":0.6,
            "projectile":"stuffed_pellet",
            "speed":15,
            "capacity": 5,
            "reloadtime":2.3,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-5,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": "spray",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "super_shotgun" : {
            "texture":"super_shotgun.png",
            "damage":8,
            "firerate":0.4,
            "projectile":"rip_and_tear_pellet",
            "speed":40,
            "capacity": float("inf"),
            "reloadtime":0.1,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-5,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": "spray",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "mini_shotgun" : {
            "texture":"mini_shotgun.png",
            "damage":8,
            "firerate":0.3,
            "projectile":"nano_pellet",
            "speed":7,
            "capacity": 4,
            "reloadtime":1.1,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-5,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": "mini_spray",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "automatic_rifle" : {
            "texture":"automatic_rifle.png",
            "damage":10,
            "firerate":0.2,
            "projectile":"bullet",
            "speed":15,
            "capacity":30,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-2,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "miku_miku_beam" : {
            "texture":"miku_miku_beam.png",
            "damage":10,
            "firerate":0.05,
            "projectile":"mikuvolt",
            "speed":80,
            "capacity":120,
            "reloadtime":8,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(35,35),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "blue_phantom" : {
            "texture":"blue_phantom.png",
            "damage":8,
            "firerate":0.1,
            "projectile":"bullet",
            "speed":25,
            "capacity":40,
            "reloadtime":3,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-2,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "red_drift" : {
            "texture":"red_drift.png",
            "damage":6,
            "firerate":0.3,
            "projectile":"bullet",
            "speed":20,
            "capacity":25,
            "reloadtime":0.5,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,40),
            "reloadoffset": rl.Vector2(-2,-25),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "pistol" : {
            "texture":"pistol.png",
            "damage":5,
            "firerate":0.2,
            "projectile":"light_bullet",
            "speed":9,
            "capacity":8,
            "reloadtime":1.5,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : False,
            "offset" : rl.Vector2(38,35),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "blaster" : {
            "texture":"blaster.png",
            "damage":15,
            "firerate":0.1,
            "projectile":"bluelaser",
            "speed":15,
            "capacity":20,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : False,
            "offset" : rl.Vector2(30,-35),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "dual_blasters" : {
            "texture":"dual_blasters.png",
            "damage":5,
            "firerate":0.1,
            "projectile":"bluelaser",
            "speed":9,
            "capacity":18,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : False,
            "offset" : rl.Vector2(30,0),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": "altalternate",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "mechanical_firearm" : {
            "texture":"mechanical_firearm.png",
            "damage":15,
            "firerate":0.9,
            "projectile":"heavy_bullet",
            "speed":13,
            "capacity":5,
            "reloadtime":1,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : False,
            "offset" : rl.Vector2(38,35),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "taser" : {
            "texture":"taser.png",
            "damage":5,
            "firerate":0.4,
            "projectile":"volt",
            "speed":9,
            "capacity":10,
            "reloadtime":1.8,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : False,
            "offset" : rl.Vector2(38,35),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "dualies" : {
            "texture":"dualies.png",
            "damage":5,
            "firerate":0.2,
            "projectile":"light_bullet",
            "speed":9,
            "capacity":18,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : False,
            "offset" : rl.Vector2(25,0),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": "alternate",
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": False
        },
        "claws" : {
            "texture":"claws.png",
            "damage":5,
            "firerate":0.1,
            "projectile":"claw",
            "speed":4,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : True,
            "offset" : rl.Vector2(30,0),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(10,0),
            "swingable": True,
            "ability": "widealternate",
            "bonustextures":["clawsl.png","clawsr.png"],
            "animproperty": animation(["clawsl.png","clawsr.png"],"time"),
            "requirenewclick": True
        },
        "boxing_gloves" : {
            "texture":"boxing_gloves.png",
            "damage":5,
            "firerate":0.2,
            "projectile":"glove",
            "speed":4,
            "capacity": float('inf'),
            "reloadtime":0,
            "script": "default",
            "takerecoil" : False,
            "reloadreposition" : True,
            "offset" : rl.Vector2(30,0),
            "reloadoffset": rl.Vector2(0,0),
            "offsetonuse": rl.Vector2(0,0),
            "swingable": True,
            "ability": "widealternate",
            "bonustextures":["boxing_glovesl.png","boxing_glovesr.png"],
            "animproperty": animation(["boxing_glovesr.png","boxing_glovesl.png",],"time"),
            "requirenewclick": True
        },
        "sniper" : {
            "texture":"sniper.png",
            "damage":10,
            "firerate":0.7,
            "projectile":"heavy_bullet",
            "speed":15,
            "capacity":3,
            "reloadtime":3,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,35),
            "reloadoffset": rl.Vector2(5,-25),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "terror_tracker" : {
            "texture":"terror_tracker.png",
            "damage":10,
            "firerate":0.4,
            "projectile":"heavy_bullet",
            "speed":15,
            "capacity":5,
            "reloadtime":4,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,35),
            "reloadoffset": rl.Vector2(5,-25),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "bolt_action_rifle" : {
            "texture":"bolt_action_rifle.png",
            "damage":15,
            "firerate":0.4,
            "projectile":"bullet",
            "speed":15,
            "capacity":5,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,35),
            "reloadoffset": rl.Vector2(5,-25),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },
        "calibre_corrode" : {
            "texture":"calibre_corrode.png",
            "damage":10,
            "firerate":0.3,
            "projectile":"corrosive_round",
            "speed":60,
            "capacity":2,
            "reloadtime":2,
            "script": "default",
            "takerecoil" : True,
            "reloadreposition" : True,
            "offset" : rl.Vector2(40,35),
            "reloadoffset": rl.Vector2(5,-25),
            "offsetonuse": rl.Vector2(20,0),
            "swingable": False,
            "ability": None,
            "bonustextures":[],
            "animproperty": None,
            "requirenewclick": True
        },

    }
    enemydata = {
        "zombie_male" : {
            "texture":"zombie_male.png",
            "health":60,
            "speed":1,
            "attackcooldown":1,
            "attacktype":"melee",
            "attackdamage":16,
            "attackrange":100,
            "script": "default",
            "aitype": "dumb",
            "detectionrange": 1000,
            "bonustextures":[]
        },
        "zombie_female" : {
            "texture":"zombie_female.png",
            "health":50,
            "speed":1.25,
            "attackcooldown":0.8,
            "attacktype":"melee",
            "attackdamage":14,
            "attackrange":100,
            "script": "default",
            "aitype": "dumb",
            "detectionrange": 800,
            "bonustextures":[]
        },
        "dart_zombie" : {
            "texture":"dart_zombie.png",
            "health":24,
            "speed":0.8,
            "attackcooldown":0.3,
            "attacktype":"dart",
            "attackdamage":14,
            "attackrange":700,
            "script": "default",
            "aitype": "spin",
            "detectionrange": 1000,
            "bonustextures":[]
        },
        "skeleton" : {
            "texture":"skeleton.png",
            "health":12,
            "speed":2.5,
            "attackcooldown":1,
            "attacktype":"melee",
            "attackdamage":18,
            "attackrange":100,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 3000,
            "bonustextures":[]
        },
        "skeleton_archer" : {
            "texture":"skeleton_archer.png",
            "health":14,
            "speed":2,
            "attackcooldown":1,
            "attacktype":"arrow",
            "attackdamage":0,
            "attackrange":1000,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 2000,
            "bonustextures":[]
        },
        "butcherer" : {
            "texture":"butcherer.png",
            "health":55,
            "speed":1.7,
            "attackcooldown":1.5,
            "attacktype":"melee",
            "attackdamage":27,
            "attackrange":100,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 3000,
            "bonustextures":[]
        },
        "brute" : {
            "texture":"brute.png",
            "health":140,
            "speed":0.8,
            "attackcooldown":3,
            "attacktype":"melee",
            "attackdamage":65,
            "attackrange":100,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 3000,
            "bonustextures":[]
        },
        "titan" : {
            "texture":"titan.png",
            "health":300,
            "speed":0.6,
            "attackcooldown":5,
            "attacktype":"melee",
            "attackdamage":95,
            "attackrange":100,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 1400,
            "bonustextures":[]
        },
        "slime" : {
            "texture":"slime.png",
            "health":45,
            "speed":1.7,
            "attackcooldown":1,
            "attacktype":"melee",
            "attackdamage":15,
            "attackrange":100,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 2500,
            "bonustextures":[]
        },
        "lumberjack" : {
            "texture":"lumberjack.png",
            "health":60,
            "speed":1.6,
            "attackcooldown":3,
            "attacktype":"melee",
            "attackdamage":40,
            "attackrange":50,
            "script": "default",
            "aitype": "standard",
            "detectionrange": 2000,
            "bonustextures":[]
        }

    }
    projectiledata = {
        "slash" : {
            "texture":"slash.png",
            "damage":25,
            "speed":70,
            "lifetime":0.01,
            "size":100,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "lunge" : {
            "texture":"slash.png",
            "damage":37,
            "speed":70,
            "lifetime":0.01,
            "size":100,
            "projectiletracking":False,
            "script": "default",
            "ability": "knockback",
            "bonustextures":[]
        },
        "claw" : {
            "texture":"claw.png",
            "damage":45,
            "speed":10,
            "lifetime":0.02,
            "size":100,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "glove" : {
            "texture":"glove.png",
            "damage":30,
            "speed":20,
            "lifetime":0.02,
            "size":100,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "arrow" : {
            "texture":"arrow.png",
            "damage":25,
            "speed":9,
            "lifetime":float('inf'),
            "size":10,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "dart" : {
            "texture":"dart.png",
            "damage":4,
            "speed":16,
            "lifetime":float('inf'),
            "size":4,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "inverted_dagger" : {
            "texture":"inverted_dagger.png",
            "damage":32,
            "speed":4,
            "lifetime":5,
            "size":30,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "bullet" : {
            "texture":"bullet.png",
            "damage":35,
            "speed":25,
            "lifetime": float('inf'),
            "size":15,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "bluelaser" : {
            "texture":"bluelaser.png",
            "damage":15,
            "speed":30,
            "lifetime": float('inf'),
            "size":15,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "pellet" : {
            "texture":"pellet.png",
            "damage":4,
            "speed":30,
            "lifetime": float('inf'),
            "size":15,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "stuffed_pellet" : {
            "texture":"pellet.png",
            "damage":8,
            "speed":30,
            "lifetime": float('inf'),
            "size":15,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "extra_stuffed_pellet" : {
            "texture":"pellet.png",
            "damage":13,
            "speed":40,
            "lifetime": float('inf'),
            "size":15,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "rip_and_tear_pellet" : {
            "texture":"rip_and_tear_pellet.png",
            "damage":36,
            "speed":60,
            "lifetime": float('inf'),
            "size":30,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "nano_pellet" : {
            "texture":"nano_pellet.png",
            "damage":2,
            "speed":70,
            "lifetime": 3,
            "size":3,
            "projectiletracking":False,
            "script": "default",
            "ability": "duplicate",
            "bonustextures":[]
        },
        "volt" : {
            "texture":"volt.png",
            "damage":4,
            "speed":15,
            "lifetime": 2,
            "size":3,
            "projectiletracking":False,
            "script": "default",
            "ability": "voltchain",
            "bonustextures":[]
        },
        "mikuvolt" : {
            "texture":"mikuvolt.png",
            "damage":11,
            "speed":30,
            "lifetime": 4,
            "size":6,
            "projectiletracking":False,
            "script": "default",
            "ability": "mikuvoltchain",
            "bonustextures":[]
        },
        "voltspawn" : {
            "texture":"volt.png",
            "damage":5,
            "speed":70,
            "lifetime": 2,
            "size":3,
            "projectiletracking":False,
            "script": "default",
            "ability": "chain",
            "bonustextures":[]
        },
        "hurtspell" : {
            "texture":"hurtspell.png",
            "damage":33,
            "speed":10,
            "lifetime": 4,
            "size":10,
            "projectiletracking":False,
            "script": "default",
            "ability": "None",
            "bonustextures":[]
        },
        "windspell" : {
            "texture":"windspell.png",
            "damage":33,
            "speed":10,
            "lifetime": 4,
            "size":10,
            "projectiletracking":False,
            "script": "default",
            "ability": "knockback",
            "bonustextures":[]
        },
        "heavy_bullet" : {
            "texture":"heavy_bullet.png",
            "damage":100,
            "speed":25,
            "lifetime":float('inf'),
            "size":20,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "corrosive_round" : {
            "texture":"corrosive_round.png",
            "damage":200,
            "speed":15,
            "lifetime":float('inf'),
            "size":3,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "light_bullet" : {
            "texture":"light_bullet.png",
            "damage":20,
            "speed":30,
            "lifetime": float('inf'),
            "size":10,
            "projectiletracking":False,
            "script": "default",
            "ability": "none",
            "bonustextures":[]
        },
        "ricochet_bullet" : {
            "texture":"ricochet_bullet.png",
            "damage":50,
            "speed":10,
            "lifetime":float('inf'),
            "size":20,
            "projectiletracking":False,
            "script": "default",
            "ability": "bounce",
            "bonustextures":[]
        },
        "explosive_bullet" : {
            "texture":"explosive_bullet.png",
            "damage":5,
            "speed":25,
            "lifetime":float('inf'),
            "size":30,
            "projectiletracking":False,
            "script": "default",
            "ability": "explode",
            "bonustextures":[]
        }
    }
    armourdata = {
        "wood" : {
            "defence" : 3,
            "effects" : None
        },
        "cactus" : {
            "defence" : 5,
            "effects" : "thorns"
        },
    }
    uidata = {
        "cursor" : {
            "texture" : "cursor.png",
            "data" : None
        },
        "cursordown" : {
            "texture" : "cursordown.png",
            "data" : None
        },
        "world_map" : {
            "texture" : "world_map.png",
            "data" : None
        },
        "background" : {
            "texture" : "background.png",
            "data" : None
        },
        "main_icon" : {
            "texture" : "main_icon.png",
            "data" : None
        },
        "title_screen_logo" : {
            "texture" : "title_screen_logo.png",
            "data" : None
        },
        "crown" : {
            "texture" : "crown.png",
            "data" : None
        },
            
    }
    sounddata = {
        "awaken.mp3" : {
            "content" : "awaken.mp3"
        },
        "thunderbolt.mp3" : {
            "content" : "thunderbolt.mp3"
        },
        "4nn1h1l4t3.mp3" : {
            "content" : "4nn1h1l4t3.mp3"
        },
        "ampere.mp3" : {
            "content" : "ampere.mp3"
        },
        "cry_about_death.mp3" : {
            "content" : "cry_about_death.mp3"
        },
        "rampage_engine.mp3" : {
            "content" : "rampage_engine.mp3"
        },
        "tear_the_tears.mp3" : {
            "content" : "tear_the_tears.mp3"
        },
        "the_first_stronghold_in_centuries.mp3" : {
            "content" : "the_first_stronghold_in_centuries.mp3"
        },
        "tyrants_leave_bones.mp3" : {
            "content" : "tyrants_leave_bones.mp3"
        },
    }
    interactabledata = {
        "tree" : {
            "texture" : "tree.png",
            "type" : "rescources",
            "drops" : "wood",
            "quantity" : rl.Vector2(2,5),
            "cooldown" : 5,
            "destroyonuse" : False
        },
        "rock" : {
            "texture" : "rock.png",
            "type" : "rescources",
            "drops" : "stone",
            "quantity" : rl.Vector2(3,8),
            "cooldown" : 10,
            "destroyonuse" : False
        },
        "iron_ore" : {
            "texture" : "iron_ore.png",
            "type" : "rescources",
            "drops" : "iron",
            "quantity" : rl.Vector2(1,3),
            "cooldown" : 15,
            "destroyonuse" : False
        },
        "gold_ore" : {
            "texture" : "gold_ore.png",
            "type" : "rescources",
            "drops" : "gold",
            "quantity" : rl.Vector2(5,7),
            "cooldown" : 15,
            "destroyonuse" : False
        },
    }
    itemdata = {
        
    }


    #important stuff
    players = []
    projectiles = []
    enemies = []
    worldmap = []
    walls = []
    particles = []
    buttons = []
    interactables = []
    numberpopups = []
    ui = []
    tracklist = []
    assetroot = "lib/"
    gamestate = "loadinggame"
    screen_width = 1280
    screen_height = 720
    virtual_width = 1920   
    virtual_height = 1080
    xscale = rl.get_screen_width() / virtual_width
    yscale = rl.get_screen_height() / virtual_height
    vectorscale = rl.Vector2(xscale,yscale)
    vcursorfordragbox = rl.Vector2(0,0)
    vspawn = rl.Vector2(16000,16000)
    fakefps = 1
    texturefilteringtype = ray.TEXTURE_FILTER_POINT
    wheel = 1

    #load game settings so they save
    if os.path.exists("settings.strongdata"):
        with open("settings.strongdata", "r") as file:
            gamesettings = json.load(file)
    else:
        with open("settings.strongdata", "w") as file:
            gamesettings = {
                "fullscreen":"off",
                "graphics":"low",
                "volume":"max",
                "vsync":"off",
                "mode":"host"
            }
            json.dump(gamesettings, file, indent=4)

        

    #gamesettings = {
    #    "fullscreen":"off",
    #    "graphics":"low",
    #    "volume":"max",
    #    "vsync":"off"
    #}
    graphicsoptions = ["low","medium","high"]
    creditsscrolltimer = 0
    selectedcharacter = list(characterdata)[0]
    print(selectedcharacter)
    #keybinds
    global UP, DOWN, LEFT, RIGHT, JUMP, SPRINT, RELOAD, CLICK, INTERACT, INVENTORY
    UP = rl.KEY_W
    DOWN = rl.KEY_S
    LEFT = rl.KEY_A
    RIGHT = rl.KEY_D
    JUMP = rl.KEY_SPACE
    SPRINT = rl.KEY_LEFT_SHIFT
    RELOAD = rl.KEY_R
    CLICK = rl.MOUSE_LEFT_BUTTON
    INTERACT = rl.KEY_E
    INVENTORY = rl.KEY_TAB
    #making window
    rl.set_config_flags(rl.FLAG_WINDOW_RESIZABLE)
    rl.set_config_flags(rl.FLAG_MSAA_4X_HINT)
    rl.init_window(screen_width, screen_height, "Strongholds v0.1")
    rl.init_audio_device()
    rl.set_window_icon(rl.load_image("icon.png"))
    rl.set_target_fps(0)
    rl.hide_cursor()
    rl.set_exit_key(rl.KEY_F10)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SoftDecay.Strongholds")
    glbtime = 0
    #loading textures
    texturecache = {}
    soundcache = {}
    #old texture loading
    #ui asets
    '''
    texturecache.update({("background.png") : rl.load_texture((assetroot + "background.png"))})
    texturecache.update({("main_icon.png") : rl.load_texture((assetroot + "main_icon.png"))})
    texturecache.update({("title_screen_logo.png") : rl.load_texture((assetroot + "title_screen_logo.png"))})
    '''
    #characters
    '''
    texturecache.update({("ninja.png") : rl.load_texture((assetroot + "ninja.png"))})
    texturecache.update({("wizard.png") : rl.load_texture((assetroot + "wizard.png"))})
    texturecache.update({("wolfknight.png") : rl.load_texture((assetroot + "wolfknight.png"))})
    texturecache.update({("sakura.png") : rl.load_texture((assetroot + "sakura.png"))})
    texturecache.update({("hitman.png") : rl.load_texture((assetroot + "hitman.png"))})
    texturecache.update({("raider.png") : rl.load_texture((assetroot + "raider.png"))})
    texturecache.update({("angel.png") : rl.load_texture((assetroot + "angel.png"))})
    texturecache.update({("richu.png") : rl.load_texture((assetroot + "richu.png"))})
    '''
    #weapons
    '''
    texturecache.update({("katana.png") : rl.load_texture((assetroot + "katana.png"))})
    texturecache.update({("automatic_rifle.png") : rl.load_texture((assetroot + "automatic_rifle.png"))})
    texturecache.update({("pistol.png") : rl.load_texture((assetroot + "pistol.png"))})
    texturecache.update({("staff.png") : rl.load_texture((assetroot + "staff.png"))})
    texturecache.update({("sniper.png") : rl.load_texture((assetroot + "sniper.png"))})
    texturecache.update({("dualies.png") : rl.load_texture((assetroot + "dualies.png"))})
    texturecache.update({("blue_phantom.png") : rl.load_texture((assetroot + "blue_phantom.png"))})
    texturecache.update({("shotgun.png") : rl.load_texture((assetroot + "shotgun.png"))})
    '''
    #enemies
    '''
    texturecache.update({("zombie_male.png") : rl.load_texture((assetroot + "zombie_male.png"))})
    texturecache.update({("zombie_female.png") : rl.load_texture((assetroot + "zombie_female.png"))})
    texturecache.update({("skeleton.png") : rl.load_texture((assetroot + "skeleton.png"))})
    texturecache.update({("skeleton_archer.png") : rl.load_texture((assetroot + "skeleton_archer.png"))})
    texturecache.update({("butcherer.png") : rl.load_texture((assetroot + "butcherer.png"))})
    texturecache.update({("brute.png") : rl.load_texture((assetroot + "brute.png"))})
    texturecache.update({("titan.png") : rl.load_texture((assetroot + "titan.png"))})
    texturecache.update({("slime.png") : rl.load_texture((assetroot + "slime.png"))})
    texturecache.update({("lumberjack.png") : rl.load_texture((assetroot + "lumberjack.png"))})
    '''
    #buttons
    '''
    texturecache.update({("play_button.png") : rl.load_texture((assetroot + "play_button.png"))})
    texturecache.update({("settings_button.png") : rl.load_texture((assetroot + "settings_button.png"))})
    texturecache.update({("exit_button.png") : rl.load_texture((assetroot + "exit_button.png"))})
    texturecache.update({("credits_button.png"): rl.load_texture((assetroot + "credits_button.png"))})
    texturecache.update({("fullscreen_on.png") : rl.load_texture((assetroot + "fullscreen_on.png"))})
    texturecache.update({("fullscreen_off.png") : rl.load_texture((assetroot + "fullscreen_off.png"))})
    texturecache.update({("graphics_low.png") : rl.load_texture((assetroot + "graphics_low.png"))})
    texturecache.update({("graphics_medium.png") : rl.load_texture((assetroot + "graphics_medium.png"))})
    texturecache.update({("graphics_high.png") : rl.load_texture((assetroot + "graphics_high.png"))})
    texturecache.update({("back_button.png") : rl.load_texture((assetroot + "back_button.png"))})
    '''
    #projectiles
    '''
    texturecache.update({("slash.png") : rl.load_texture((assetroot + "slash.png"))})
    texturecache.update({("bullet.png") : rl.load_texture((assetroot + "bullet.png"))})
    texturecache.update({("heavy_bullet.png") : rl.load_texture((assetroot + "heavy_bullet.png"))})
    texturecache.update({("light_bullet.png") : rl.load_texture((assetroot + "light_bullet.png"))})
    texturecache.update({("ricochet_bullet.png") : rl.load_texture((assetroot + "ricochet_bullet.png"))})
    texturecache.update({("arrow.png") : rl.load_texture((assetroot + "arrow.png"))})
    texturecache.update({("pellet.png") : rl.load_texture((assetroot + "pellet.png"))})
    '''
    #map
    '''
    texturecache.update({("world_map.png") : rl.load_texture((assetroot + "world_map.png"))})
    '''
    #mouse
    '''
    texturecache.update({("cursor.png") : rl.load_texture((assetroot + "cursor.png"))})
    texturecache.update({("cursordown.png") : rl.load_texture((assetroot + "cursordown.png"))})
    '''
    #load textures based off dict data now instead
    #new texture loading
    try:
        t_start = time.time()
        #load character textures
        for sprite in characterdata:
            filenameoftexture = characterdata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        for sprite in characterdata:
            filenameoftexture = characterdata[sprite]['badgetexture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        for sprite in characterdata:
            listofbonustextures = characterdata[sprite]['bonustextures']
            print(listofbonustextures)
            for texturetotake in listofbonustextures:
                filenameoftexture = texturetotake
                texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        #load weapon textures
        for sprite in weapondata:
            filenameoftexture = weapondata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        for sprite in weapondata:
            listofbonustextures = weapondata[sprite]['bonustextures']
            print(listofbonustextures)
            for texturetotake in listofbonustextures:
                filenameoftexture = texturetotake
                texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        #load enemy textures
        for sprite in enemydata:
            filenameoftexture = enemydata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        for sprite in enemydata:
            listofbonustextures = enemydata[sprite]['bonustextures']
            print(listofbonustextures)
            for texturetotake in listofbonustextures:
                filenameoftexture = texturetotake
                texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        #load projectile textures
        for sprite in projectiledata:
            filenameoftexture = projectiledata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})
        for sprite in projectiledata:
            listofbonustextures = projectiledata[sprite]['bonustextures']
            print(listofbonustextures)
            for texturetotake in listofbonustextures:
                filenameoftexture = texturetotake
                texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})

        for sprite in uidata:
            filenameoftexture = uidata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})

        for sprite in interactabledata:
            filenameoftexture = interactabledata[sprite]['texture']
            print(filenameoftexture)
            texturecache.update({(filenameoftexture) : rl.load_texture((assetroot + filenameoftexture))})

        t_end = time.time()
        print(f"Loaded {len(texturecache)} textures in {t_end-t_start:.2f}s")
    except Exception as e:
        print("failed to load textures", e)

    texturefiltering(rl.TEXTURE_FILTER_POINT)
    

    #load music and sounds
    try:
        s_start = time.time()
        for sound in sounddata:
            filenameoftexture = sounddata[sound]['content']
            print(filenameoftexture)
            soundcache.update({(filenameoftexture) : rl.load_music_stream((assetroot + filenameoftexture))})
        s_end = time.time()
        print(f"Loaded {len(soundcache)} music/sounds in {s_end-s_start:.2f}s")
    except Exception as e:
        print("failed to load sounds", e)

    for texture in texturecache:
        rl.set_texture_filter(texturecache[texture], rl.TEXTURE_FILTER_TRILINEAR)
    #font
    gamefont = rl.load_font_ex(assetroot+"calibri-bold.ttf",512,None,0)
    rl.gui_set_font(gamefont)
    #apply texture filtering
    texturefiltering(texturefilteringtype)
    #screencapture
    screencapture = rl.load_render_texture(virtual_width, virtual_height)
    currentplayer = 0 # this is probably gonna get fucked up when multiplayer is added
    players.append(player(selectedcharacter))
    #buttons
    buttons = {}
    #camera
    camera = rl.Camera2D()
    camera.offset = rl.Vector2(screen_width/2,screen_height/2)
    camera.target = players[currentplayer].position
    camera.rotation = 0.0
    camera.zoom = 1.0
    usefollowingcamera = False
    #discord setup
    try:
        # don't re-create RPC if it already exists (can block intermittently)
        if not ("rpc" in globals() and rpc is not None):
            rpc = discordrpc.RPC(app_id=1377364367724646551)
            rpc.set_activity(
                state= "Playing Strongholds!",
                details= "version 0.1",
                large_image="Main icon3",
                large_text="Strongholds",
                small_image="Main icon3",
                small_text="Strongholds"
            )
    except Exception:
        pass
    #titlescreenparticles :p
    titlescreenparticles = []

def reset():
    global typingip, writtenip, showpause, camerazoom, debugmode, wheel, gamequality, glbtime, invopen, itemdata, interactables, interactabledata, sounddata, tracklist, rpc, vectorscale, selectedcharacter, numberpopups, uidata,creditsscrolltimer, ui, buttons,armourdata, graphicsoptions, gamesettings, particles, screencapture, soundcache, gamefont, titlescreenparticles, projectiledata, texturefilteringtype,fakefps, vspawn, vcursorfordragbox, vcursor, usefollowingcamera, walls, camera,enemydata, characterdata, weapondata,  screen_width, screen_height, gamestate, texturecache, virtual_width, virtual_height, currentplayer, players, projectiles, enemies, worldmap, camera, accum_48hz, accum_24hz
    #game data
    
    #important stuff
    players = []
    projectiles = []
    enemies = []
    worldmap = []
    walls = []
    particles = []
    buttons = []
    interactables = []
    ui = []
    tracklist = []
    tracklist.append(random.choice(list(sounddata.keys())))
    numberpopups = []
    invopen = False
    showpause = False
    writtenip = ""
    typingip = False
    #keybinds
    global UP, DOWN, LEFT, RIGHT, JUMP, SPRINT, RELOAD, CLICK, INTERACT, INVENTORY

    #setup the player
    currentplayer = 0 # this is probably gonna get fucked up when multiplayer is added
    players.append(player(selectedcharacter))
    #players.append(player("ninja"))
    #add walls (this will be long)
    #top left test square
    walls.append(wall("rectangle",rl.Rectangle(100,100,200,200)))
    #dungeon 1
    walls.append(wall('rectangle',rl.Rectangle(19665.814453125,13283.24609375,1129.34765625,390.8212890625)))
    walls.append(wall('rectangle',rl.Rectangle(20794.54296875,13285.0224609375,140.89453125,388.7802734375)))
    walls.append(wall('rectangle',rl.Rectangle(20794.357421875,13674.5478515625,141.556640625,884.013671875)))
    walls.append(wall('rectangle',rl.Rectangle(20428.90625,14092.0908203125,361.3984375,146.134765625)))
    walls.append(wall('rectangle',rl.Rectangle(19666.35546875,14580.4423828125,392.658203125,677.59375)))
    walls.append(wall('rectangle',rl.Rectangle(20056.03125,15257.3818359375,718.5859375,245.1708984375)))
    walls.append(wall('rectangle',rl.Rectangle(19662.162109375,15256.3515625,393.234375,245.10546875)))
    walls.append(wall('rectangle',rl.Rectangle(19663.36328125,15501.763671875,396.564453125,892.89453125)))
    walls.append(wall('rectangle',rl.Rectangle(19663.93359375,16394.173828125,191.7890625,391.919921875)))
    walls.append(wall('rectangle',rl.Rectangle(19851.830078125,16398.349609375,399.25,747.642578125)))
    walls.append(wall('rectangle',rl.Rectangle(20250.8515625,16397.259765625,322.9375,749.44921875)))
    walls.append(wall('rectangle',rl.Rectangle(19855.26171875,17146.759765625,393.130859375,224.5546875)))
    walls.append(wall('rectangle',rl.Rectangle(20935.62109375,13284.5107421875,2099.1640625,388.166015625)))
    walls.append(wall('rectangle',rl.Rectangle(23031.4765625,13283.59765625,112.71484375,391.056640625)))
    walls.append(wall('rectangle',rl.Rectangle(23142.869140625,13281.994140625,819.203125,392.1162109375)))
    walls.append(wall('rectangle',rl.Rectangle(23037.734375,13675.7666015625,103.572265625,923.6064453125)))
    walls.append(wall('rectangle',rl.Rectangle(23573.2578125,13677.642578125,393.98828125,3078.669921875)))
    walls.append(wall('rectangle',rl.Rectangle(22359.53125,16394.6484375,1214.59375,360.6796875)))
    walls.append(wall('rectangle',rl.Rectangle(21500.21484375,15669.0185546875,1139.1875,232.103515625)))
    walls.append(wall('rectangle',rl.Rectangle(21500.37109375,15900.66015625,249.330078125,500.0703125)))
    walls.append(wall('rectangle',rl.Rectangle(20573.005859375,16396.712890625,1177.201171875,1435.51171875)))
    walls.append(wall('rectangle',rl.Rectangle(19871.947265625,17366.203125,367.2109375,1759.669921875)))
    walls.append(wall('rectangle',rl.Rectangle(20249.34765625,18756.146484375,573.705078125,372.904296875)))
    walls.append(wall('rectangle',rl.Rectangle(19244.0078125,18292.66796875,625.873046875,227.552734375)))
    walls.append(wall('rectangle',rl.Rectangle(16410.296875,17372.521484375,3458.755859375,152.2109375)))
    walls.append(wall('rectangle',rl.Rectangle(16409.099609375,17523.984375,356.671875,2389.076171875)))
    walls.append(wall('rectangle',rl.Rectangle(16411.9921875,19911.232421875,353.853515625,338.14453125)))
    walls.append(wall('rectangle',rl.Rectangle(16764.841796875,19908.94140625,3091.568359375,340.861328125)))
    walls.append(wall('rectangle',rl.Rectangle(20224.658203125,19868.76171875,1128.431640625,390.7421875)))
    walls.append(wall('rectangle',rl.Rectangle(20035.169921875,19891.068359375,189.482421875,366.77734375)))
    walls.append(wall('rectangle',rl.Rectangle(19857.12890625,19907.82421875,177.302734375,346.9921875)))
    walls.append(wall('rectangle',rl.Rectangle(17120.896484375,19101.658203125,107.767578125,810.20703125)))
    walls.append(wall('rectangle',rl.Rectangle(21324.888671875,18277.091796875,406.26953125,1587.224609375)))
    walls.append(wall('rectangle',rl.Rectangle(22308.2734375,18298.623046875,356.779296875,219.529296875)))
    walls.append(wall('rectangle',rl.Rectangle(22667.484375,18518.677734375,499.1953125,1345.427734375)))
    walls.append(wall('rectangle',rl.Rectangle(22661.91015625,18299.38671875,502.8203125,216.724609375)))
    walls.append(wall('rectangle',rl.Rectangle(21326.828125,19863.828125,2827.087890625,394.232421875)))
    walls.append(wall('rectangle',rl.Rectangle(23763.818359375,17842.03125,389.345703125,2016.751953125)))
    walls.append(wall('rectangle',rl.Rectangle(22363.423828125,16754.51953125,1789.6015625,1084.853515625)))
    #plains walls
    walls.append(wall('rectangle',rl.Rectangle(17952.7890625,15378.2119140625,642.3515625,388.373046875)))
    walls.append(wall('rectangle',rl.Rectangle(18204.205078125,15765.00390625,391.177734375,860.63671875)))
    walls.append(wall('rectangle',rl.Rectangle(17950.005859375,16230.4130859375,271.380859375,396.5595703125)))
    walls.append(wall('rectangle',rl.Rectangle(16420.978515625,16009.740234375,1035.115234375,522.58203125)))
    walls.append(wall('rectangle',rl.Rectangle(14016.30859375,14910.958984375,1528.0830078125,767.6474609375)))
    walls.append(wall('rectangle',rl.Rectangle(14690.0166015625,16219.40625,439.4892578125,971.162109375)))
    walls.append(wall('rectangle',rl.Rectangle(13397.6630859375,16397.05859375,472.0048828125,788.9375)))
    walls.append(wall('rectangle',rl.Rectangle(12818.533203125,16707.1796875,598.7470703125,477.48828125)))
    walls.append(wall('rectangle',rl.Rectangle(12343.5146484375,16396.197265625,476.8076171875,786.708984375)))
    walls.append(wall('rectangle',rl.Rectangle(11186.212890625,17324.763671875,646.298828125,392.345703125)))
    walls.append(wall('rectangle',rl.Rectangle(11183.1357421875,17716.4765625,396.892578125,463.173828125)))
    walls.append(wall('rectangle',rl.Rectangle(11182.5888671875,18177.87890625,651.5126953125,396.734375)))
    walls.append(wall('rectangle',rl.Rectangle(12330.9287109375,17955.775390625,1029.8505859375,523.498046875)))
    walls.append(wall('rectangle',rl.Rectangle(12289.587890625,14814.0654296875,906.4794921875,945.4990234375)))
    walls.append(wall('rectangle',rl.Rectangle(13312.72265625,12936.25390625,440.3388671875,969.5556640625)))
    walls.append(wall('rectangle',rl.Rectangle(12018.892578125,13111.7685546875,476.466796875,788.7197265625)))
    walls.append(wall('rectangle',rl.Rectangle(11441.8330078125,13424.0068359375,590.3037109375,476.744140625)))
    walls.append(wall('rectangle',rl.Rectangle(10968.1064453125,13111.3212890625,473.80078125,790.6689453125)))
    walls.append(wall('rectangle',rl.Rectangle(10914.724609375,11528.48046875,908.99609375,950.775390625)))
    walls.append(wall('rectangle',rl.Rectangle(12639.6787109375,11629.40234375,1525.0576171875,763.423828125)))
    walls.append(wall('rectangle',rl.Rectangle(15135.208984375,11050.2939453125,911.51953125,950.0029296875)))
    walls.append(wall('rectangle',rl.Rectangle(16863.39453125,11148.96875,1525.421875,766.2744140625)))
    walls.append(wall('rectangle',rl.Rectangle(17536.845703125,12454.8359375,440.056640625,971.609375)))
    walls.append(wall('rectangle',rl.Rectangle(16244.11328125,12631.7236328125,474.34765625,788.9755859375)))
    walls.append(wall('rectangle',rl.Rectangle(15666.708984375,12941.6943359375,574.0029296875,478.7529296875)))
    walls.append(wall('rectangle',rl.Rectangle(15190.6611328125,12630.7119140625,475.8056640625,789.6796875)))
    walls.append(wall('rectangle',rl.Rectangle(16111.9013671875,10067.51953125,650.4541015625,393.822265625)))
    walls.append(wall('rectangle',rl.Rectangle(16367.322265625,9605.6484375,392.580078125,459.7998046875)))
    walls.append(wall('rectangle',rl.Rectangle(16110.099609375,9213.875,649.68359375,390.314453125)))
    walls.append(wall('rectangle',rl.Rectangle(14575.30859375,9843.705078125,1040.3896484375,523.486328125)))
    walls.append(wall('rectangle',rl.Rectangle(12385.4072265625,8384.0751953125,1527.1455078125,764.025390625)))
    walls.append(wall('rectangle',rl.Rectangle(10659.197265625,8283.234375,908.8115234375,951.6201171875)))
    walls.append(wall('rectangle',rl.Rectangle(11769.337890625,9866.041015625,472.13671875,790.35546875)))
    walls.append(wall('rectangle',rl.Rectangle(11189.408203125,10180.6767578125,579.126953125,474.4619140625)))
    walls.append(wall('rectangle',rl.Rectangle(10715.6298828125,9868.392578125,472.1201171875,786.69140625)))
    walls.append(wall('rectangle',rl.Rectangle(8523.7861328125,10268.23828125,649.693359375,395.322265625)))
    walls.append(wall('rectangle',rl.Rectangle(8780.5654296875,9805.658203125,391.787109375,458.60546875)))
    walls.append(wall('rectangle',rl.Rectangle(8523.9541015625,9410.970703125,648.8828125,393.478515625)))
    walls.append(wall('rectangle',rl.Rectangle(6996.9755859375,10043.0712890625,1033.544921875,522.8544921875)))
    walls.append(wall('rectangle',rl.Rectangle(4675.1640625,12806.8232421875,1035.48681640625,528.1279296875)))
    walls.append(wall('rectangle',rl.Rectangle(3533.328125,12175.2607421875,649.8369140625,393.3876953125)))
    walls.append(wall('rectangle',rl.Rectangle(3531.767578125,12567.72265625,391.161865234375,463.0078125)))
    walls.append(wall('rectangle',rl.Rectangle(3533.71875,13031.234375,649.0146484375,397.2041015625)))
    walls.append(wall('rectangle',rl.Rectangle(13365.599609375,19204.3515625,1028.271484375,523.451171875)))
    walls.append(wall('rectangle',rl.Rectangle(14894.2744140625,19428.2734375,650.0908203125,395.197265625)))
    walls.append(wall('rectangle',rl.Rectangle(15145.107421875,18969.380859375,394.986328125,455.072265625)))
    walls.append(wall('rectangle',rl.Rectangle(14892.640625,18575.390625,641.640625,388.2890625)))
    walls.append(wall('rectangle',rl.Rectangle(9616.185546875,19809.60546875,648.5234375,395.78125)))
    walls.append(wall('rectangle',rl.Rectangle(9866.5908203125,19349.9296875,394.373046875,452.7265625)))
    walls.append(wall('rectangle',rl.Rectangle(9616.650390625,18954.228515625,641.310546875,391.224609375)))
    walls.append(wall('rectangle',rl.Rectangle(8087.427734375,19586.4140625,1032.849609375,529.9765625)))
    walls.append(wall('rectangle',rl.Rectangle(19644.849609375,12101.1962890625,1034.228515625,522.7060546875)))
    walls.append(wall('rectangle',rl.Rectangle(21172.49609375,12323.814453125,650.146484375,394.59375)))
    walls.append(wall('rectangle',rl.Rectangle(21427.466796875,11862.341796875,394.376953125,460.58984375)))
    walls.append(wall('rectangle',rl.Rectangle(21172.021484375,11466.0068359375,648.525390625,394.8896484375)))
    walls.append(wall('rectangle',rl.Rectangle(18000.365234375,8590.2216796875,1034.65234375,525.33203125)))
    walls.append(wall('rectangle',rl.Rectangle(19526.060546875,7957.83935546875,651.24609375,396.80322265625)))
    walls.append(wall('rectangle',rl.Rectangle(19528.140625,8816.6943359375,650.697265625,392.4443359375)))
    walls.append(wall('rectangle',rl.Rectangle(19783.900390625,8352.5498046875,394.333984375,462.85546875)))
    walls.append(wall('rectangle',rl.Rectangle(13062.171875,9692.7763671875,438.6953125,969.6064453125)))
    #dungeon 2
    walls.append(wall('rectangle',rl.Rectangle(8866.3955078125,13172.0595703125,667.533203125,230.771484375)))
    walls.append(wall('rectangle',rl.Rectangle(9490.3505859375,12563.8828125,382.880859375,812.5234375)))
    walls.append(wall('rectangle',rl.Rectangle(9532.9404296875,13375.9453125,338.6435546875,32.6455078125)))
    walls.append(wall('rectangle',rl.Rectangle(9535.3671875,13407.75,340.8359375,4755.162109375)))
    walls.append(wall('rectangle',rl.Rectangle(4455.14404296875,17805.947265625,5086.59716796875,356.697265625)))
    walls.append(wall('rectangle',rl.Rectangle(4116.52734375,14323.970703125,336.22802734375,3837.2109375)))
    walls.append(wall('rectangle',rl.Rectangle(4453.119140625,17346.904296875,808.74365234375,109.294921875)))
    walls.append(wall('rectangle',rl.Rectangle(5848.52490234375,14707.61328125,223.00732421875,622.0244140625)))
    walls.append(wall('rectangle',rl.Rectangle(5236.27783203125,14324.2783203125,1606.55029296875,382.8408203125)))
    walls.append(wall('rectangle',rl.Rectangle(6036.9501953125,11441.7998046875,353.17333984375,340.8232421875)))
    walls.append(wall('rectangle',rl.Rectangle(6743.39697265625,11785.46875,106.97412109375,806.1220703125)))
    walls.append(wall('rectangle',rl.Rectangle(6035.04833984375,11783.390625,354.7275390625,2388.265625)))
    walls.append(wall('rectangle',rl.Rectangle(6033.9052734375,14168.9658203125,807.7451171875,153.9873046875)))
    walls.append(wall('rectangle',rl.Rectangle(6390.3916015625,11443.232421875,3483.064453125,338.9296875)))
    walls.append(wall('rectangle',rl.Rectangle(8726.2626953125,17347.587890625,808.5380859375,108.59765625)))
    walls.append(wall('rectangle',rl.Rectangle(6839.53369140625,14170.5,306.291015625,1717.2255859375)))
    walls.append(wall('rectangle',rl.Rectangle(7144.35791015625,14171.861328125,1609.97509765625,535.318359375)))
    walls.append(wall('rectangle',rl.Rectangle(7914.18603515625,14708.1640625,232.14990234375,622.0517578125)))
    walls.append(wall('rectangle',rl.Rectangle(6844.63916015625,16291.3173828125,303.08203125,1124.8115234375)))
    #sandtomb
    walls.append(wall('rectangle',rl.Rectangle(23130.78515625,10152.7314453125,459.388671875,286.3671875)))
    walls.append(wall('rectangle',rl.Rectangle(23915.890625,8538.986328125,550.810546875,786.0380859375)))
    walls.append(wall('rectangle',rl.Rectangle(23123.740234375,8056.67236328125,469.576171875,1293.83251953125)))
    walls.append(wall('rectangle',rl.Rectangle(22042.3515625,5163.49072265625,437.541015625,385.2099609375)))
    walls.append(wall('rectangle',rl.Rectangle(22041.775390625,5548.26806640625,440.763671875,2117.13134765625)))
    walls.append(wall('rectangle',rl.Rectangle(22476.900390625,5163.62109375,2940.60546875,375.2216796875)))
    walls.append(wall('rectangle',rl.Rectangle(25414.32421875,5161.6494140625,487.982421875,2752.359375)))
    walls.append(wall('rectangle',rl.Rectangle(25425.32421875,7914.48291015625,1113.935546875,387.74169921875)))
    walls.append(wall('rectangle',rl.Rectangle(26537.53515625,7915.6328125,442.24609375,2883.6025390625)))
    walls.append(wall('rectangle',rl.Rectangle(26540.46484375,10797.2998046875,1915.56640625,383.48046875)))
    walls.append(wall('rectangle',rl.Rectangle(28451.634765625,10797.6943359375,438.455078125,2884.505859375)))
    walls.append(wall('rectangle',rl.Rectangle(25522.48046875,13311.1328125,2929.953125,372.2734375)))
    walls.append(wall('rectangle',rl.Rectangle(25049.322265625,10801.8251953125,471.962890625,2881.69921875)))
    walls.append(wall('rectangle',rl.Rectangle(23132.3359375,10435.5576171875,2378.0703125,363.09375)))
    walls.append(wall('rectangle',rl.Rectangle(25562.984375,9048.8251953125,678.158203125,783.3203125)))
    walls.append(wall('rectangle',rl.Rectangle(22045.525390625,7663.75390625,1081.416015625,391.53955078125)))
    walls.append(wall('rectangle',rl.Rectangle(23126.83984375,7675.12109375,465.21484375,380.87451171875)))
    walls.append(wall('rectangle',rl.Rectangle(23591.537109375,7675.541015625,871.427734375,620.8037109375)))
    walls.append(wall('rectangle',rl.Rectangle(24555.271484375,5784.8759765625,551.146484375,784.185546875)))
    walls.append(wall('rectangle',rl.Rectangle(22779.994140625,6290.52197265625,680.814453125,785.92724609375)))
    walls.append(wall('rectangle',rl.Rectangle(25837.486328125,12280.267578125,548.6328125,785.701171875)))
    walls.append(wall('rectangle',rl.Rectangle(27482.728515625,11772.7626953125,680.29296875,782.361328125)))
    
    
    #walls are just an array of rectangle objects lol
    #add enemies (measure time to create, can spike on reset)
    enemy_start = time.time()
    enemies.append(enemy("zombie_male",vspawn))
    for _ in range(random.randint(10,20)):
        tempenemychoicelist = [
            "zombie_male",
            "zombie_female",
            "skeleton",
            "skeleton_archer",
            "brute",
            "titan",
            "dart_zombie",
            "butcherer",
            "lumberjack",
            "slime",
        ]
        enemies.append(enemy(random.choice(tempenemychoicelist),rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))))
    enemy_end = time.time()
    print(f"Created {len(enemies)} enemies in {enemy_end-enemy_start:.2f}s")
    
    #add the single tree
    #interactables.append(interactable("tree",vspawn))

    #camera
    camera = rl.Camera2D()
    camera.offset = rl.Vector2(screen_width/2,screen_height/2)
    camera.target = players[currentplayer].position
    camera.rotation = 0.0
    camera.zoom = 1.25
    camerazoom = 1.00
    usefollowingcamera = False
    #discord setup - only init if missing to avoid blocking reinitialisation
    try:
        if not ("rpc" in globals() and rpc is not None):
            rpc = discordrpc.RPC(app_id=1377364367724646551)
            rpc.set_activity(
                state= "Playing Strongholds!",
                details= "version 0.1",
                large_image="Main icon3",
                large_text="Strongholds",
                small_image="Main icon3",
                small_text="Strongholds"
            )
    except Exception:
        pass
    #titlescreenparticles :p
    titlescreenparticles = []

def main():
    global typingip, writtenip, showpause, debugmode, wheel, gamequality, glbtime, invopen, itemdata, interactables, interactabledata, sounddata, tracklist, rpc, vectorscale, selectedcharacter, numberpopups, uidata, camerazoom, creditsscrolltimer, ui, buttons, deathscreencounter, graphicsoptions, gamesettings, particles, screencapture, soundcache, gamefont, titlescreenparticles, projectiledata, texturefilteringtype,fakefps, vspawn, vcursorfordragbox, xscale, yscale, vcursor, usefollowingcamera, walls, camera, enemydata,characterdata, gamestate, virtual_height, virtual_width, texturecache, currentplayer, camera, players, projectiles, enemies, worldmap, accum_48hz, accum_24hz
    global UP, DOWN, LEFT, RIGHT, JUMP, SPRINT, RELOAD, CLICK, INTERACT, INVENTORY
    buttons.clear()
    ui.clear()
    #window sizing
    xcursor = rl.get_mouse_x()
    ycursor = rl.get_mouse_y()
    vcursor = rl.Vector2(xcursor, ycursor)
    virtual_width = 1920
    virtual_height = 1080
    screen_height = rl.get_screen_height()
    screen_width = rl.get_screen_width()
    #keep it within normalish aspect ratio
    if not (1.55 <= (screen_width/screen_height) <= 1.75):
        rl.set_window_size(screen_width, int(screen_width/1.66))
        pass

    xscale = rl.get_screen_width() / virtual_width
    yscale = rl.get_screen_height() / virtual_height
    vectorscale = rl.Vector2(xscale,yscale)
    
    
    #do texture filtering
    #for texture in texturecache:
    #    rl.set_texture_filter(texturecache[texture], rl.TEXTURE_FILTER_TRILINEAR)
    match gamestate:
        case "ingame":
            playmusic(tracklist[0])
            
            #scripts
            if False:
                for vplayer in players:
                    if characterdata[vplayer.character]["script"] == "default":
                        pass
                    else:
                        try:
                            exec(characterdata[vplayer.character]["script"])
                        except:
                            print(f"Error executing script for character {vplayer.character}")
                    if weapondata[vplayer.weapon.weaponname]["script"] == "default":
                        pass
                    else:
                        try:
                            exec(weapondata[vplayer.weapon.weaponname]["script"])
                        except:
                            print(f"Error executing script for weapon {vplayer.weapon.weaponname}")
                for venemy in enemies:
                    if enemydata[venemy.type]["script"] == "default":
                        pass
                    else:
                        try:
                            exec(characterdata[venemy.type]["script"])
                        except:
                            print(f"Error executing script for character {venemy.type}")
                for vprojectile in projectiles:
                    if projectiledata[vprojectile.type]["script"] == "default":
                        pass
                    else:
                        try:
                            exec(projectiledata[vprojectile.type]["script"])
                        except:
                            print(f"Error executing script for projectile {vprojectile.type}")
                    
            #24hz accum
            accum_24hz += rl.get_frame_time()
            while accum_24hz >= (1.0 / 24.0):
                if random.randint(0,24) == 0:
                    if len(enemies) < 30:
                        tempenemychoicelist = [
                        "zombie_male",
                        "zombie_female",
                        "skeleton",
                        "skeleton_archer",
                        "brute",
                        "titan",
                        "dart_zombie",
                        "butcherer",
                        "lumberjack",
                        "slime",
                        ]
                        #spawn bonus enemies in :3
                        enemies.append(enemy(random.choice(tempenemychoicelist),rl.vector2_add(vspawn,rl.Vector2(random.randint(-4000,4000),random.randint(-4000,4000)))))
                accum_24hz -= (1.0 / 24.0)

            #handle pause menu
            if rl.is_key_pressed(rl.KEY_ESCAPE):
                showpause = not showpause

            #do all the enemy stuff
            for venemy in enemies:
                venemy.ai()
                venemy.damage()
                venemy.attack()
                if venemy.health <= 0:
                    enemies.remove(venemy)
            
            for vparticle in particles:
                vparticle.movement()
                if vparticle.alive == False:
                    particles.remove(vparticle)

            for vinteractable in interactables:
                vinteractable.touchingplayer()
            
            #player stuff
            players[currentplayer].doinventory()
            players[currentplayer].pointtomouse()
            if players[currentplayer].inventoryopen == False:
                players[currentplayer].movement()
                players[currentplayer].attack()
            for vplayer in players:
                vplayer.damage()
                vplayer.weapon.movement(vplayer)
                vplayer.updateweaponinfo()
                vplayer.updateplayerinfo()
                if vplayer.health <= 0:
                    gamestate = "deathscreen"
                    deathscreencounter = 0
            #projectile stuff
            for vprojectile in projectiles:
                vprojectile.movement()
                if vprojectile.alive == False:
                    projectiles.remove(vprojectile)

            for vnumberpopup in numberpopups:
                vnumberpopup.updatelifetime()
            for vnumberpopup in numberpopups:
                if vnumberpopup.alive == False:
                    numberpopups.remove(vnumberpopup)

            camera.offset = rl.Vector2(screen_width/2,screen_height/2)
            match gamequality:
                case "low":
                    usefollowingcamera = False
                case "medium":
                    usefollowingcamera = False
                case "high":
                    usefollowingcamera = True
            if usefollowingcamera:
                camera.target = rl.vector2_lerp(camera.target,players[currentplayer].position,(0.05*(rl.get_frame_time()*100)))
            else:
                camera.target = players[currentplayer].position
            camera.rotation = 0.0

            wheel = rl.get_mouse_wheel_move()

            if wheel != 0:
                camerazoom += wheel * 0.2   # zoom sensitivity

            camerazoom = rl.clamp(camerazoom, 0.5, 1.5)
            camera.zoom = camerazoom * xscale
            
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.begin_mode_2d(camera)
            rl.draw_texture_ex(texturecache["world_map.png"], rl.Vector2(0,0), 0, 4, rl.WHITE)
            for vprojectile in projectiles:
                rl.draw_texture_pro(
                    vprojectile.texture,
                    rl.Rectangle(0,0, vprojectile.texture.width, vprojectile.texture.height),
                    rl.Rectangle(vprojectile.position.x,vprojectile.position.y, vprojectile.texture.width,vprojectile.texture.height),
                    rl.Vector2(vprojectile.texture.width/2,vprojectile.texture.height/2),
                    vprojectile.direction+90 if not gamesettings["graphics"] == "low" else round((vprojectile.direction+90) / 22.5) * 22.5,
                    rl.WHITE
                )
            for venemy in enemies:
                rl.draw_texture_pro(
                    venemy.texture,
                    rl.Rectangle(0,0, venemy.texture.width, venemy.texture.height),
                    rl.Rectangle(venemy.position.x,venemy.position.y, venemy.texture.width,venemy.texture.height),
                    rl.Vector2(venemy.texture.width/2,venemy.texture.height/2),
                    venemy.direction+90 if not gamesettings["graphics"] == "low" else round((venemy.direction+90) / 22.5) * 22.5,
                    rl.WHITE
                )
            #draw the player stuff (complex)
            for player in players:
                #draw weapons
                if weapondata[player.weapon.weaponname]["reloadreposition"] == True and player.reloading == True:
                    player.weapon.reloadmovement(player)
                    if weapondata[player.weapon.weaponname]["animproperty"] == None:
                        rl.draw_texture_pro(
                            player.weapon.texture,
                            rl.Rectangle(0,0, player.weapon.texture.width, player.weapon.texture.height),
                            rl.Rectangle(player.weapon.position.x,player.weapon.position.y, player.weapon.texture.width,player.weapon.texture.height),
                            rl.Vector2(player.weapon.texture.width/2,player.weapon.texture.height/2),
                            player.direction+45 if not gamesettings["graphics"] == "low" else round((player.direction+45) / 22.5) * 22.5,
                            rl.WHITE
                            )
                    else:
                        rl.draw_texture_pro(
                        weapondata[player.weapon.weaponname]["animproperty"].givetexture(),
                        rl.Rectangle(0,0, player.weapon.texture.width, player.weapon.texture.height),
                        rl.Rectangle(player.weapon.position.x,player.weapon.position.y, player.weapon.texture.width,player.weapon.texture.height),
                        rl.Vector2(player.weapon.texture.width/2,player.weapon.texture.height/2),
                        player.direction+45 if not gamesettings["graphics"] == "low" else round((player.direction+45) / 22.5) * 22.5,
                        rl.WHITE
                        )
                elif weapondata[player.weapon.weaponname]["takerecoil"] == True:
                    if rl.is_mouse_button_down(CLICK) and not weapondata[player.weapon.weaponname]["requirenewclick"]:
                        rl.draw_texture_pro(
                        player.weapon.texture,
                        rl.Rectangle(0,0, player.weapon.texture.width, player.weapon.texture.height),
                        rl.Rectangle(player.weapon.position.x,player.weapon.position.y, player.weapon.texture.width,player.weapon.texture.height),
                        rl.Vector2((player.weapon.texture.width/2)+random.randint(-1,1),(player.weapon.texture.height/2)+random.randint(-1,1)),
                        player.direction+ 90 if not gamesettings["graphics"] == "low" else round((player.direction+90) / 22.5) * 22.5,
                        rl.WHITE
                        )
                    elif rl.is_mouse_button_pressed(CLICK) and weapondata[player.weapon.weaponname]["requirenewclick"]:
                        rl.draw_texture_pro(
                        player.weapon.texture,
                        rl.Rectangle(0,0, player.weapon.texture.width, player.weapon.texture.height),
                        rl.Rectangle(player.weapon.position.x,player.weapon.position.y, player.weapon.texture.width,player.weapon.texture.height),
                        rl.Vector2((player.weapon.texture.width/2)+random.randint(-1,1),(player.weapon.texture.height/2)+random.randint(-1,1)),
                        player.direction+ 90 if not gamesettings["graphics"] == "low" else round((player.direction+90) / 22.5) * 22.5,
                        rl.WHITE
                        )
                    else:
                        rl.draw_texture_pro(
                        player.weapon.texture,
                        rl.Rectangle(0,0, player.weapon.texture.width, player.weapon.texture.height),
                        rl.Rectangle(player.weapon.position.x,player.weapon.position.y, player.weapon.texture.width,player.weapon.texture.height),
                        rl.Vector2(player.weapon.texture.width/2,player.weapon.texture.height/2),
                        player.direction+ 90 if not gamesettings["graphics"] == "low" else round((player.direction+90) / 22.5) * 22.5,
                        rl.WHITE
                        )
                else:
                    # choose texture: use animproperty while swinging if available
                    anim = weapondata[player.weapon.weaponname]["animproperty"]
                    texturetodraw = player.weapon.texture
                    if weapondata[player.weapon.weaponname]["swingable"] and player.isswinging and anim is not None:
                        # if the animation is 'order' use the per-swing index so it flips each swing
                        if getattr(anim, "animtype", None) == "order":
                            texturetodraw = anim.givetexture(player.swingindex)
                        else:
                            texturetodraw = anim.givetexture()
                    rl.draw_texture_pro(
                        texturetodraw,
                        rl.Rectangle(0,0, texturetodraw.width, texturetodraw.height),
                        rl.Rectangle(player.weapon.position.x,player.weapon.position.y, texturetodraw.width,texturetodraw.height),
                        rl.Vector2(texturetodraw.width/2,texturetodraw.height/2),
                        player.direction+90,
                        rl.WHITE
                    )

            #draw players
            for player in players:
                rl.draw_texture_pro(
                    player.texture,
                    rl.Rectangle(0,0, player.texture.width, player.texture.height),
                    rl.Rectangle(player.position.x,player.position.y, player.texture.width,player.texture.height),
                    rl.Vector2(player.texture.width/2,player.texture.height/2),
                    player.direction+ 90 if not gamesettings["graphics"] == "low" else round((player.direction+90) / 22.5) * 22.5,
                    rl.WHITE if player.health > player.maxhealth/5 else (255, 255-int((math.sin(rl.get_time()*5) * 0.5 + 0.5) * 255), 255-int((math.sin(rl.get_time()*5) * 0.5 + 0.5) * 255), 255)
                )
                #draw text above player to show character name if mouse cursor nearby and fade based on distance
                #if rl.check_collision_point_circle(rl.get_screen_to_world_2d(vcursor,camera),player.position,100):
                #    rl.draw_text_ex(gamefont,(player.character).capitalize(),rl.Vector2(player.position.x - (rl.measure_text_ex(gamefont,player.character,30,2).x*0.5),player.position.y - 75),30,2,rl.RAYWHITE)
                if rl.check_collision_point_circle(rl.get_screen_to_world_2d(vcursor,camera),player.position,100):
                    distance = rl.vector2_distance(rl.get_screen_to_world_2d(vcursor,camera),player.position)
                    alpha = int(255 - (distance / 100) * 255)
                    rl.draw_text_ex(gamefont,(player.character).capitalize(),rl.Vector2(player.position.x - (rl.measure_text_ex(gamefont,player.character,30,2).x*0.5),player.position.y - 75),30,2,(255,255,255,alpha))
            
            if debugmode:
                for wall in walls:
                    rl.draw_rectangle_lines_ex(wall.hitbox,15*xscale,rl.RED)

            for interactable in interactables:
                rl.draw_texture_pro(
                    interactable.texture,
                    rl.Rectangle(0,0, interactable.texture.width, interactable.texture.height),
                    rl.Rectangle(interactable.position.x,interactable.position.y, interactable.texture.width*interactable.scale,interactable.texture.height*interactable.scale),
                    rl.Vector2((interactable.texture.width*interactable.scale)/2,(interactable.texture.height*interactable.scale)/2),
                    0,
                    rl.WHITE
                )

            for interactable in interactables:
                rl.draw_texture_pro(
                    interactable.texture,
                    rl.Rectangle(0,0, interactable.texture.width, interactable.texture.height),
                    rl.Rectangle(interactable.position.x,interactable.position.y, interactable.texture.width*interactable.scale,interactable.texture.height*interactable.scale),
                    rl.Vector2((interactable.texture.width*interactable.scale)/2,(interactable.texture.height*interactable.scale)/2),
                    0,
                    rl.WHITE
                )

            for particle in particles:
                rl.draw_texture_pro(
                    particle.texture,
                    rl.Rectangle(0,0, particle.texture.width, particle.texture.height),
                    rl.Rectangle(particle.position.x,particle.position.y, particle.texture.width*particle.scale,particle.texture.height*particle.scale),
                    rl.Vector2((particle.texture.width*particle.scale)/2,(particle.texture.height*particle.scale)/2),
                    particle.direction+ 90 if not gamesettings["graphics"] == "low" else round((particle.direction+90) / 22.5) * 22.5,
                    rl.WHITE
                )
            for numberpopup in numberpopups:
                rl.draw_text_ex(gamefont,str(numberpopup.value),numberpopup.position,45,0,(240,0,0,150))

            rl.end_mode_2d()
            #rl.draw_text(str(f"Ingame: {str(rl.get_screen_to_world_2d(vcursor,camera).x)} {str(rl.get_screen_to_world_2d(vcursor,camera).y)} "), 20, 20, 40, rl.RAYWHITE)
            #rl.draw_text(f"{str((rl.get_fps()*(fakefps)))} fps", 20, 70, 40, rl.RAYWHITE)
            #rl.draw_text(f"Health: {str(players[currentplayer].health)}/{str(players[currentplayer].maxhealth)}", 20, 120, 40, rl.RAYWHITE)
            #rl.draw_text(f"Stamina: {str(int(players[currentplayer].stamina))}/10", 20, 170, 40, rl.RAYWHITE)
            #rl.draw_text(f"Weapon: {str(players[currentplayer].weapon.weaponname)}", 20, 220, 40, rl.RAYWHITE)
            #rl.draw_text(f"Ammo: {str(players[currentplayer].weapon.ammo)}/{str(players[currentplayer].weapon.magazine)}", 20, 270, 40, rl.RAYWHITE)
            #'''
            if debugmode:
                rl.draw_text_ex(gamefont,f"Strongholds Test {version}",rl.Vector2(20,20),40,2,rl.RAYWHITE)
                rl.draw_text_ex(gamefont,f"Ingame: {str(round(rl.get_screen_to_world_2d(vcursor,camera).x))} {str(round(rl.get_screen_to_world_2d(vcursor,camera).y))} ", rl.Vector2(20,70),40,2,rl.RAYWHITE)
                rl.draw_text_ex(gamefont,f"Username: amu", rl.Vector2(20,120),40,2,rl.RAYWHITE)
                rl.draw_text_ex(gamefont,f"{str((rl.get_fps()*(fakefps)))} fps", rl.Vector2(20,170),40,2,rl.RAYWHITE)
            
            #'''
            #rl.draw_text_ex(gamefont,f"Health: {str(players[currentplayer].health)}/{str(players[currentplayer].maxhealth)}", rl.Vector2(20,170),40,2,rl.RAYWHITE)
            #rl.draw_text_ex(gamefont,f"Stamina: {str(int(players[currentplayer].stamina))}/10", rl.Vector2(20,220),40,2,rl.RAYWHITE)
            #rl.draw_text_ex(gamefont,f"Weapon: {str(players[currentplayer].weapon.weaponname)}", rl.Vector2(20,270),40,2,rl.RAYWHITE)
            
            #rl.draw_text_ex(gamefont,f"Ammo: {str(players[currentplayer].weapon.ammo)}/{str(players[currentplayer].weapon.magazine)}", rl.Vector2(20,320),40,2,rl.RAYWHITE)
            #draw bottom left hud
            
            rl.draw_rectangle_rounded(rl.Rectangle(50*xscale,800*yscale,(500)*xscale,250*yscale),0.2,16,(73,76,77,150))
            rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(50*xscale,800*yscale,(500)*xscale,250*yscale),0.2,16,5*xscale,rl.BLACK)
            #rl.draw_circle_v(rl.Vector2(100*xscale,850*yscale),45*xscale,rl.BLACK)
            #rl.draw_circle_v(rl.Vector2(100*xscale,850*yscale),40*xscale,(73,76,77,150))
            #draw player ico on hud
            rl.draw_ring(rl.Vector2(100*xscale, 850*yscale),40*xscale,45*xscale,0,360,32,rl.BLACK)
            #rl.draw_texture_ex(players[currentplayer].texture,rl.Vector2(77.5*xscale,827.5*yscale),0,0.6*xscale,rl.WHITE)
            shtxt = players[currentplayer].texture #shorten down the name of the text variable for the next line
            rl.draw_texture_ex(players[currentplayer].texture,rl.Vector2(100*xscale-(shtxt.width*0.6)*xscale/2,850*yscale-(shtxt.height*0.6)/2*yscale),0,0.6*xscale,rl.WHITE)
            #draw weapon icon in hud
            shtxt = players[currentplayer].weapon.texture #shorten down the name of the text variable for the next line
            rl.draw_texture_ex(players[currentplayer].weapon.texture,rl.Vector2(100*xscale-(shtxt.width*0.6)*xscale/2,940*yscale-(shtxt.height*0.6)/2*yscale),0,0.6*xscale,rl.WHITE)
            #draw ring for weapon icon
            rl.draw_ring(rl.Vector2(100*xscale, 940*yscale),40*xscale,45*xscale,0,360,32,rl.BLACK)
            #draw player name
            rl.draw_text_ex(gamefont,f"{(characterdata[(players[currentplayer].character)]['displayname'])} [{int(players[currentplayer].health)}/{players[currentplayer].maxhealth}]", rl.Vector2(160*xscale,(850*yscale-(rl.measure_text_ex(gamefont,"meow",int(30*yscale),2).y/2))),30*xscale,2,rl.BLACK)
            #draw weapon name, omit ammo if inf
            if not players[currentplayer].weapon.ammo == float("inf"):
                rl.draw_text_ex(gamefont,f"{(players[currentplayer].weapon.weaponname.capitalize().replace('_',' '))} [{players[currentplayer].weapon.ammo}/{players[currentplayer].weapon.magazine}]", rl.Vector2(160*xscale,(940*yscale-(rl.measure_text_ex(gamefont,"meow",int(30*yscale),2).y/2))),30*xscale,2,rl.BLACK)
            else:
                rl.draw_text_ex(gamefont,f"{(players[currentplayer].weapon.weaponname.capitalize().replace('_',' '))}", rl.Vector2(160*xscale,(940*yscale-(rl.measure_text_ex(gamefont,"meow",int(30*yscale),2).y/2))),30*xscale,2,rl.BLACK)
            #draw all the stats (REPLACE WITH BARSz``)
            #bars

            '''
            if (players[currentplayer].maxhealth) * 0.2 < players[currentplayer].health:
                rl.draw_text_ex(gamefont,f"HP: {str(int(players[currentplayer].health))}/{str(players[currentplayer].maxhealth)}", rl.Vector2(170*xscale,860*yscale),30*xscale,2,rl.BLACK)
            else:
                rl.draw_text_ex(gamefont,f"HP: {str(int(players[currentplayer].health))}/{str(players[currentplayer].maxhealth)}", rl.Vector2(170*xscale,860*yscale),30*xscale,2,(240,0,0,255))
            if int(players[currentplayer].stamina) < 2:
                rl.draw_text_ex(gamefont,f"STA: {str(int(players[currentplayer].stamina))}/10", rl.Vector2(170*xscale,900*yscale),30*xscale,2,(175,115,10,255))
            else:
                rl.draw_text_ex(gamefont,f"STA: {str(int(players[currentplayer].stamina))}/10", rl.Vector2(170*xscale,900*yscale),30*xscale,2,rl.BLACK)
            rl.draw_text_ex(gamefont,f"WPN: {players[currentplayer].weapon.weaponname.capitalize().replace('_',' ')}", rl.Vector2(170*xscale,940*yscale),30*xscale,2,rl.BLACK)
            if not players[currentplayer].weapon.magazine == float('inf'):
                if not players[currentplayer].weapon.ammo == 0:
                    rl.draw_text_ex(gamefont,f"AMMO: {str(players[currentplayer].weapon.ammo)}/{str(players[currentplayer].weapon.magazine)}", rl.Vector2(170*xscale,980*yscale),30*xscale,2,rl.BLACK)
                else:
                    rl.draw_text_ex(gamefont,f"AMMO: {str(players[currentplayer].weapon.ammo)}/{str(players[currentplayer].weapon.magazine)}", rl.Vector2(170*xscale,980*yscale),30*xscale,2,(240,0,0,255))
            '''

            if showpause:
                rl.draw_rectangle_rounded(rl.Rectangle(1600*xscale,20*yscale,300*xscale,1040*yscale),0.1,1,(53,56,57,150))
                rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(1600*xscale,20*yscale,300*xscale,1040*yscale),0.1,1,5*xscale,rl.BLACK)
                ui.append(button("menu",rl.Rectangle((1620),(930),(260),(100)),"Back"))
                doui()
            players[currentplayer].drawinventory()
            drawcursor()
            rl.end_drawing()
            # this runs at only 48hz (game fps is uncapped)
            accum_48hz += rl.get_frame_time()
            while accum_48hz >= (1.0 / 48.0):
                #do networking
                accum_48hz -= (1.0 / 48.0)
            

        case "loadinggame":
            playmusic("thunderbolt.mp3")
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.draw_texture_ex(texturecache["background.png"], rl.Vector2(0,0), 0, (2*xscale), rl.WHITE)
            rl.draw_texture_ex(texturecache["main_icon.png"], rl.Vector2((50*xscale),(50*xscale)), 0, (0.4*xscale), rl.WHITE)
            drawcursor()
            rl.end_drawing()
            gamestate = "applysettings"

        case "gamesetup":
            global writtenip, typingip
            #add networking setup buttons, choose between HOST and JOIN
            #essentially the text box for ip input is just a button, once clicked it takes control of keyboard input and saves to writtenip variable
            ui.append(button("typeip",rl.Rectangle((75),(900),(500),(100)),writtenip if not writtenip == "" else "Enter IP or Code"))
            #join game only works if writtenip is valid
            ui.append(button("join",rl.Rectangle((600),(900),(350),(100)),"Join Game"))
            #hosting doesnt require entering an ip
            ui.append(button("host",rl.Rectangle((975),(900),(350),(100)),"Host Game"))
            #start game to be removed once hosting and joining fully works
            ui.append(button("continue",rl.Rectangle((1350),(900),(495),(100)),"Singleplayer"))
            #ui.append(slider("test",rl.Rectangle((20),(20),(350),(200)),"test",50,0,100))
            if rl.is_key_pressed(rl.KEY_ENTER) and typingip:
                typingip = False
            if rl.is_key_pressed(rl.KEY_ESCAPE) and typingip:
                typingip = False
            if rl.is_key_pressed(rl.KEY_BACKSPACE) and typingip:
                writtenip = writtenip[:-1]
            for i in range(32,127):
                if rl.is_key_pressed(i) and typingip:
                    writtenip += chr(i)
            playmusic("thunderbolt.mp3")
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.draw_texture_ex(texturecache["background.png"], rl.Vector2(0,0), 0, (2*xscale), rl.WHITE)
            rl.draw_rectangle_rounded(rl.Rectangle(50*xscale,50*yscale,1820*xscale,980*yscale),0.05,16,(53,56,57,150))
            rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(50*xscale,50*yscale,1820*xscale,980*yscale),0.05,16,5*xscale,rl.BLACK)
            doui()
            drawcursor()
            rl.end_drawing()

        case "mainmenu":
            playmusic("thunderbolt.mp3")
            rl.begin_drawing()
            rl.clear_background(rl.RAYWHITE)
            rl.draw_texture_ex(texturecache["background.png"], rl.Vector2(0,0), 0, (2*xscale), rl.WHITE)
            rl.draw_texture_ex(texturecache["title_screen_logo.png"], rl.Vector2((50*xscale),(50*xscale)), 0, (1.5*xscale), rl.WHITE)
            '''
            playbuttonhitbox = rl.Rectangle((50*xscale),(500*yscale),(350*xscale),(100*yscale))
            if rl.check_collision_point_rec(vcursor, playbuttonhitbox):
                rl.draw_texture_pro(texturecache["play_button.png"],rl.Rectangle(0,0,texturecache["play_button.png"].width,texturecache["play_button.png"].height),playbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                if rl.is_mouse_button_pressed(CLICK):
                    gamestate = "ingame"
            else:
                rl.draw_texture_pro(texturecache["play_button.png"],rl.Rectangle(0,0,texturecache["play_button.png"].width,texturecache["play_button.png"].height),playbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            
            
            settingsbuttonhitbox = rl.Rectangle((50*xscale),(620*yscale),(350*xscale),(100*yscale))
            if rl.check_collision_point_rec(vcursor, settingsbuttonhitbox):
                rl.draw_texture_pro(texturecache["settings_button.png"],rl.Rectangle(0,0,texturecache["settings_button.png"].width,texturecache["settings_button.png"].height),settingsbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                if rl.is_mouse_button_pressed(CLICK):
                    gamestate = "settings"
            else:
                rl.draw_texture_pro(texturecache["settings_button.png"],rl.Rectangle(0,0,texturecache["settings_button.png"].width,texturecache["settings_button.png"].height),settingsbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            
            creditsbuttonhitbox = rl.Rectangle((50*xscale),(740*yscale),(350*xscale),(100*yscale))
            if rl.check_collision_point_rec(vcursor, creditsbuttonhitbox):
                rl.draw_texture_pro(texturecache["credits_button.png"],rl.Rectangle(0,0,texturecache["credits_button.png"].width,texturecache["credits_button.png"].height),creditsbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                if rl.is_mouse_button_pressed(CLICK):
                    gamestate = "credits"
                    
            else:
                rl.draw_texture_pro(texturecache["credits_button.png"],rl.Rectangle(0,0,texturecache["credits_button.png"].width,texturecache["credits_button.png"].height),creditsbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))

            exitbuttonhitbox = rl.Rectangle((50*xscale),(860*yscale),(350*xscale),(100*yscale))
            if rl.check_collision_point_rec(vcursor, exitbuttonhitbox):
                rl.draw_texture_pro(texturecache["exit_button.png"],rl.Rectangle(0,0,texturecache["exit_button.png"].width,texturecache["exit_button.png"].height),exitbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                if rl.is_mouse_button_pressed(CLICK):
                    rl.close_window()
                    rl.close_audio_device()
                    quit()
            else:
                rl.draw_texture_pro(texturecache["exit_button.png"],rl.Rectangle(0,0,texturecache["exit_button.png"].width,texturecache["exit_button.png"].height),exitbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))

            #rl.draw_rectangle_rec(playbuttonhitbox, rl.DARKGRAY)
            #rl.draw_rectangle_rec(settingsbuttonhitbox, rl.DARKGRAY)
            #experimental draw drag box
            if not rl.is_mouse_button_down(CLICK):
                vcursorfordragbox = vcursor
            else:
                rl.draw_rectangle_v(vcursorfordragbox,(rl.vector2_subtract(vcursor,vcursorfordragbox)),(30,30,30,100))
            '''
            
            ui.append(button("play",rl.Rectangle((50),(500),(350),(100)),"Play"))
            ui.append(button("settings",rl.Rectangle((50),(620),(350),(100)),"Settings"))
            ui.append(button("credits",rl.Rectangle((50),(740),(350),(100)),"Credits"))
            ui.append(button("exit",rl.Rectangle((50),(860),(350),(100)),"Exit"))
            #ui.append(button("error",rl.Rectangle((50),(50),(350),(100)),"error"))
            #buttons.append(button("settings",rl.Rectangle(50,50,100,100),"hello"))
            #buttons.append(button("settings",rl.Rectangle(50,50,100,100),"hello"))

            #character select
            rl.draw_rectangle_rounded(rl.Rectangle(440*xscale,500*yscale,1430*xscale,540*yscale),0.05,1,(53,56,57,150)) 
            rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(440*xscale,500*yscale,1430*xscale,540*yscale),0.05,1,5*xscale,rl.BLACK)
            #draw the characters
            rl.draw_text_ex(gamefont,"Character Select:",rl.vector2_multiply(rl.Vector2(460,520),vectorscale),50*xscale,0,rl.BLACK)
            #make a grid with all the positions
            ''' old and inefficient (its actually awful)
            positionstodrawcharacters = [
                rl.Vector2(460,575),
                rl.Vector2(560,575),
                rl.Vector2(660,575),
                rl.Vector2(760,575),
                rl.Vector2(860,575),
                rl.Vector2(960,575),
                rl.Vector2(1060,575),
                rl.Vector2(1160,575),
                rl.Vector2(1260,575),
                rl.Vector2(1360,575),
                rl.Vector2(1460,575),
                rl.Vector2(460,675),
                rl.Vector2(560,675),
                rl.Vector2(660,675),
                rl.Vector2(760,675),
                rl.Vector2(860,675),
                rl.Vector2(960,675),
                rl.Vector2(1060,675),
                rl.Vector2(1160,675),
                rl.Vector2(1260,675),
                rl.Vector2(1360,675),
                rl.Vector2(1460,675),
                rl.Vector2(460,775),
                rl.Vector2(560,775),
                rl.Vector2(660,775),
                rl.Vector2(760,775),
                rl.Vector2(860,775),
                rl.Vector2(960,775),
                rl.Vector2(1060,775),
                rl.Vector2(1160,775),
                rl.Vector2(1260,775),
                rl.Vector2(1360,775),
                rl.Vector2(1360,775),
            ]
            '''
            #less jank, make a list with all the positions to draw the characters at
            positionstodrawcharacters = []
            for y in (575, 675, 775,875):
                for x in range(460, 1461, 100):
                    positionstodrawcharacters.append(rl.Vector2(x, y))

            #draw a character at each one of those positions in the grid
            for name, drawpos in zip(characterdata,positionstodrawcharacters):

                #center texture into the 100x100 grid
                texture = texturecache[characterdata[name]['texture']]
                offset = rl.Vector2(((100-texture.width)/2)*xscale,((100-texture.height)/2)*yscale)
                rl.draw_texture_ex(texturecache[characterdata[name]['texture']],rl.vector2_add(rl.vector2_multiply(drawpos,rl.Vector2(xscale,yscale)),offset),0,1*xscale,rl.WHITE)
                if rl.check_collision_point_rec(vcursor,rl.Rectangle(drawpos.x*xscale,drawpos.y*yscale,100*xscale,100*yscale)):
                    if rl.is_mouse_button_pressed(CLICK):
                        selectedcharacter = name
                if name == selectedcharacter:
                    #draw a crown point down that appears above the character in the colour gold using draw pos which is the top left of the current char (unscaled)
                    rl.draw_texture_pro(
                        texturecache["crown.png"],
                        rl.Rectangle(0,0,68,50),
                        rl.Rectangle(drawpos.x*xscale+(33*xscale),drawpos.y*yscale-(15*yscale),34*xscale,25*yscale),
                        rl.Vector2(0,0),
                        0,
                        rl.WHITE
                    )
                    #rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(drawpos.x*xscale,drawpos.y*yscale,100*xscale,100*yscale),0.05,1,5*xscale,(150,140,65,255))
            #draw the badge icon of each character to the right of the grid
            rl.draw_texture_pro(
                texturecache[characterdata[selectedcharacter]["badgetexture"]],
                rl.Rectangle(1,1,511,511), #basically 512 but gotta clip a bit of the edge off
                rl.Rectangle(1580*xscale,550*yscale,256*xscale,256*yscale), #drawn always at 256x
                rl.Vector2(0,0),
                0,
                rl.WHITE
            )
            #draw a sleek frame around the badge pure black
            rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(1580*xscale,550*yscale,256*xscale,256*yscale),0.1,1,10*xscale,rl.BLACK)
            #draw the name of the character below centered below the badge
            rl.draw_text_ex(
                gamefont,
                characterdata[selectedcharacter]["displayname"],
                rl.Vector2(int(1580*xscale+(128*xscale)-int(rl.measure_text_ex(gamefont,selectedcharacter.capitalize().replace('_',' '),40*xscale,0).x/2)),int(830*yscale)),40*xscale,2,
                rl.BLACK
            )
            #do the ui
            doui()
            #draw the cursor
            drawcursor()
            rl.end_drawing()

        case "swaptocredits":
            playmusic("thunderbolt.mp3")
            creditsscrolltimer = 0
            gamestate = "credits"

        case "credits":
            playmusic("thunderbolt.mp3")
            if rl.is_key_pressed(rl.KEY_ESCAPE):
                gamestate = "mainmenu"
            pass
            ui.append(button("back",rl.Rectangle((50),(50),(200),(75)),"Back"))
            doui()
            creditsscrolltimer += rl.get_frame_time()
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.draw_text_ex(gamefont,f"Credits:",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Credits:",80*xscale,0).x/2),(900-creditsscrolltimer*50)),80*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Development: Ammunimium",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Development: Ammunimium",40*xscale,0).x/2),(1080-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Development: LaptopAbuser",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Development: LaptopAbuser",40*xscale,0).x/2),(1150-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Music: SaraBassCringe",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Music: SaraBassCringe",40*xscale,0).x/2),(1220-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Music: PeacefulBuilda",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Music: PeacefulBuilda",40*xscale,0).x/2),(1290-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Music: Ammunimium",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Music: Ammunimium",40*xscale,0).x/2),(1360-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Art: Ammunimium",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Art: Ammunimium",40*xscale,0).x/2),(1430-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Planning: Bankett",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Planning: Bankett",40*xscale,0).x/2),(1500-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"Networking: Blank",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"Networking: Blank",40*xscale,0).x/2),(1570-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            rl.draw_text_ex(gamefont,f"End Of Credits",rl.Vector2(int(1920/2*xscale)-int(rl.measure_text_ex(gamefont,"End Of Credits",40*xscale,0).x/2),(1640-creditsscrolltimer*50)),40*xscale,2,rl.RAYWHITE)
            drawcursor()
            rl.end_drawing()

        case "settings":
            playmusic("thunderbolt.mp3")
            if rl.is_key_pressed(rl.KEY_ENTER):
                gamestate = "applysettings"
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.draw_texture_ex(texturecache["background.png"], rl.Vector2(0,0), 0, (2*xscale), rl.WHITE)
            #rl.draw_text("Settings", 20, 20, 40, rl.DARKGRAY)
            #back button hitbox
            '''
            backbuttonhitbox = rl.Rectangle((18*xscale),(32*yscale),(520*xscale),(100*yscale))
            if rl.check_collision_point_rec(vcursor, backbuttonhitbox):
                    rl.draw_texture_pro(texturecache["back_button.png"],rl.Rectangle(0,0,texturecache["back_button.png"].width,texturecache["back_button.png"].height),backbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                    if rl.is_mouse_button_pressed(CLICK):
                        gamestate = "applysettings"
            else:
                rl.draw_texture_pro(texturecache["back_button.png"],rl.Rectangle(0,0,texturecache["back_button.png"].width,texturecache["back_button.png"].height),backbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            #fullscreen button hitbox
            fullscreenbuttonhitbox = rl.Rectangle((18*xscale),(152*yscale),(520*xscale),(100*yscale))
            #drawing state on
            if gamesettings["fullscreen"] == "on":
                if rl.check_collision_point_rec(vcursor, fullscreenbuttonhitbox):
                    rl.draw_texture_pro(texturecache["fullscreen_on.png"],rl.Rectangle(0,0,texturecache["fullscreen_on.png"].width,texturecache["fullscreen_on.png"].height),fullscreenbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                    if rl.is_mouse_button_pressed(CLICK):
                        gamesettings["fullscreen"] = "off"
                else:
                    rl.draw_texture_pro(texturecache["fullscreen_on.png"],rl.Rectangle(0,0,texturecache["fullscreen_on.png"].width,texturecache["fullscreen_on.png"].height),fullscreenbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            #drawing state off
            elif gamesettings["fullscreen"] == "off":
                if rl.check_collision_point_rec(vcursor, fullscreenbuttonhitbox):
                    rl.draw_texture_pro(texturecache["fullscreen_off.png"],rl.Rectangle(0,0,texturecache["fullscreen_off.png"].width,texturecache["fullscreen_off.png"].height),fullscreenbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                    if rl.is_mouse_button_pressed(CLICK):
                        gamesettings["fullscreen"] = "on"
                else:
                    rl.draw_texture_pro(texturecache["fullscreen_off.png"],rl.Rectangle(0,0,texturecache["fullscreen_off.png"].width,texturecache["fullscreen_off.png"].height),fullscreenbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            #draw graphics option buttons
            graphicsbuttonhitbox =  rl.Rectangle((18*xscale),(272*yscale),(520*xscale),(100*yscale))
            match gamesettings["graphics"]:
                case "low":
                    if rl.check_collision_point_rec(vcursor, graphicsbuttonhitbox):
                        rl.draw_texture_pro(texturecache["graphics_low.png"],rl.Rectangle(0,0,texturecache["graphics_low.png"].width,texturecache["graphics_low.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                        if rl.is_mouse_button_pressed(CLICK):
                            gamesettings["graphics"] = "medium"
                    else:
                        rl.draw_texture_pro(texturecache["graphics_low.png"],rl.Rectangle(0,0,texturecache["graphics_low.png"].width,texturecache["graphics_low.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
                case "medium":
                    if rl.check_collision_point_rec(vcursor, graphicsbuttonhitbox):
                        rl.draw_texture_pro(texturecache["graphics_medium.png"],rl.Rectangle(0,0,texturecache["graphics_medium.png"].width,texturecache["graphics_medium.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                        if rl.is_mouse_button_pressed(CLICK):
                            gamesettings["graphics"] = "high"
                    else:
                        rl.draw_texture_pro(texturecache["graphics_medium.png"],rl.Rectangle(0,0,texturecache["graphics_medium.png"].width,texturecache["graphics_medium.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
                case "high":
                    if rl.check_collision_point_rec(vcursor, graphicsbuttonhitbox):
                        rl.draw_texture_pro(texturecache["graphics_high.png"],rl.Rectangle(0,0,texturecache["graphics_high.png"].width,texturecache["graphics_high.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(255,255,255,255))
                        if rl.is_mouse_button_pressed(CLICK):
                            gamesettings["graphics"] = "low"
                    else:
                        rl.draw_texture_pro(texturecache["graphics_high.png"],rl.Rectangle(0,0,texturecache["graphics_high.png"].width,texturecache["graphics_high.png"].height),graphicsbuttonhitbox,rl.Vector2(0,0),0,(210,210,210,255))
            '''
            ui.append(button("back",rl.Rectangle((50),(50),(500),(100)),"Back (Saves Settings)"))
            ui.append(button("graphics",rl.Rectangle((50),(170),(500),(100)),f"Graphics: {gamesettings['graphics'].capitalize()}"))
            ui.append(button("fullscreen",rl.Rectangle((50),(290),(500),(100)),f"Fullscreen: {gamesettings['fullscreen'].capitalize()}"))
            ui.append(button("vsync",rl.Rectangle((50),(410),(500),(100)),f"Vsync: {gamesettings['vsync'].capitalize()}"))
            ui.append(button("volume",rl.Rectangle((50),(530),(500),(100)),f"Volume: {gamesettings['volume'].capitalize()}"))
            ui.append(button("help",rl.Rectangle((50),(930),(500),(100)),"Help?"))
            
            #buttons.append(button("settings",rl.Rectangle(50,50,100,100),"hello"))
            #buttons.append(button("settings",rl.Rectangle(50,50,100,100),"hello"))
            rl.draw_rectangle_rounded(rl.Rectangle(570*xscale,50*yscale,1330*xscale,980*yscale),0.05,1,(53,56,57,150))
            rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(570*xscale,50*yscale,1330*xscale,980*yscale),0.05,1,5*xscale,rl.BLACK)

            doui()
            drawcursor()
            rl.end_drawing()
        
        case "applysettings":
            with open("settings.strongdata", "w") as file:
                json.dump(gamesettings, file, indent=4)
            match gamesettings["fullscreen"]:
                case "on":
                    if rl.is_window_fullscreen() == True:
                        pass
                    else:
                        rl.toggle_fullscreen()
                        rl.set_window_size(rl.get_monitor_width(0),rl.get_monitor_height(0))
                case "off":
                    if rl.is_window_fullscreen() == False:
                        pass
                    else:
                        rl.toggle_fullscreen()

            match gamesettings["graphics"]:
                case "low":
                    texturefiltering(rl.TEXTURE_FILTER_POINT)
                    gamequality = "low"
                case "medium":
                    texturefiltering(rl.TEXTURE_FILTER_POINT)
                    gamequality = "medium"
                case "high":
                    texturefiltering(rl.TEXTURE_FILTER_POINT)
                    gamequality = "high"
            if gamesettings["vsync"] == "on":
                rl.set_window_state(rl.FLAG_VSYNC_HINT)
            else:
                rl.clear_window_state(rl.FLAG_VSYNC_HINT)
            if gamesettings["volume"] == "mute":
                rl.set_master_volume(0)
            if gamesettings["volume"] == "max":
                rl.set_master_volume(100)
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            rl.draw_texture_ex(texturecache["background.png"], rl.Vector2(0,0), 0, (2*xscale), rl.WHITE)
            rl.draw_text("Saving.", 20, 20, 40, rl.DARKGRAY)
            drawcursor()
            rl.end_drawing()
                

            gamestate = "mainmenu"



        case "deathscreen":
            deathscreencounter += rl.get_frame_time()
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            ui.append(button("respawn",rl.Rectangle((710),(690),(500),(100)),"Confirm"))
            doui()
            measureyoudiedtext = rl.measure_text_ex(gamefont,f"You Died!",80,2)
            rl.draw_text_ex(gamefont,f"You Died!",rl.Vector2((1920/2*xscale)-(measureyoudiedtext.x/2),(1080/2*yscale)-(measureyoudiedtext.y/2)),80,2,rl.RED)
            #rl.draw_text_ex(gamefont,f"You Died!", rl.Vector2(1920/2*xscale,1080/2*yscale),40,2,rl.RAYWHITE)
            drawcursor()
            rl.end_drawing()

            if deathscreencounter > 30:
                reset()
                gamestate = "mainmenu"

        case "error":
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)
            #draw error text centered in one line
            ui.append(button("back",rl.Rectangle((0),(50),(200),(75)),"Back"))
            doui()
            rl.end_drawing()


    

    

            

if __name__ == "__main__":
    setup()
    while not rl.window_should_close():
        #mainloop
        main()
        #additional debug thingy
        #toggle debugmode with keybind
        if rl.is_key_pressed(ray.KEY_F3):
            debugmode = not debugmode
        if debugmode and gamestate == "ingame":
            global value1, value2
            if rl.is_key_pressed(ray.KEY_C):
                value1 = rl.get_screen_to_world_2d(vcursor,camera)
            if rl.is_key_pressed(ray.KEY_V):
                value2 = rl.get_screen_to_world_2d(vcursor,camera)
            if rl.is_key_pressed(ray.KEY_B):
                walls.append(wall("rectangle",rl.Rectangle(value1.x,value1.y,value2.x-value1.x,value2.y-value1.y)))
                print(f"walls.append(wall('rectangle',rl.Rectangle({value1.x},{value1.y},{value2.x-value1.x},{value2.y-value1.y})))")
    close_game()



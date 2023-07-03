import pygame,math,random,sys,os,copy,requests,threading
import PyUI as pyui
pygame.init()
screenw = 800
screenh = 600
screen = pygame.display.set_mode((screenw, screenh),pygame.RESIZABLE)
pygame.display.set_caption('btb')
pygame.scrap.init()
ui = pyui.UI()
done = False
clock = pygame.time.Clock()
ui.defaultcol = (16,163,127)
ui.defaulttextcol = (255,255,255)
ui.defaultanimationspeed = 20

def sectostr(sec):
    h = int(sec//3600)
    m = str(int(sec%3600//60))
    s = str(int(sec%60))
    ms = sec%1
    if len(s) == 1: s = '0'+s
    if h == 0:
        return f'{m}:{s}'
    else:
        return f'{h}:{m}:{s}'

def makefileable(name):
    special = '\/:*?"<>|'
    for a in special:
        name = name.replace(a,'')
    return name

def loadimage(url,name):
    path = pyui.resourcepath(f'data\\images\\{name}.png')
    if not os.path.isfile(path):
        img_data = requests.get(url).content
        with open(path, 'wb') as handler:
            handler.write(img_data)
    return path

def songdatapull(data):
    info = {}
    info['album'] = data['album']['name']
    info['name'] = data['name']
    artists = [a['name'] for a in data['artists']]
    artist = ''
    for a in artists:
        artist = artist+a+','
    artist = artist.removesuffix(',')
    info['artist'] = artist
    info['length'] = data['duration_ms']/1000
    info['image_url'] = data['album']['images'][0]['url']
    return info

def spotifyplaylistpull(link):
    try:
        import spotipy
    except:
        return 0
    from spotipy.oauth2 import SpotifyClientCredentials
    client_id = 'bbafafb36cc04da98d011939cf935c33'
    client_secret = '4864d4b57ec44d20b4ef67607e810e51'
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    try:
        data = sp.playlist(link)
    except:
        print('invalid link')
        return 0
    songdata = []
    for a in data['tracks']['items']:
        songdata.append(songdatapull(a['track']))
    files = []
    for a in songdata:
        files.append(makedat(a))
    return [[readdat(a)['path'] for a in files],data['name']]

def makedat(info,overwrite=False):
    if 'name' in info: name = makefileable(info['name'])
    else: name = 'unknown'
    if 'artist' in info: artist = makefileable(info['artist'])
    else: artist = 'unknown'
    if 'album' in info: album = makefileable(info['album'])
    else: album = 'unknown'
    if 'length' in info: length = info['length']
    else: length = 0
    if 'image_url' in info: image_url = info['image_url']
    else: image_url = 'none'
    if 'image_path' in info: image_path = info['image_path']
    else:
        if image_url == 'none':image_path = 'none'
        else:
            image_path = loadimage(image_url,album)
    if 'path' in info: path = info['path']
    else: path = pyui.resourcepath('data\\mp3\\'+name+'-'+artist+'.mp3')
    if 'downloaded' in info: downloaded = info['downloaded']
    else: downloaded = False
    if path == 'none':file = f'data\\songs\\{name}-{artist}.dat'                                
    else:
        n = path.split('\\')[-1].removesuffix('.mp3')
        file = pyui.resourcepath('data\\songs\\'+n+'.dat')
    if not(os.path.isfile(file)) or overwrite:
        with open(file,'w') as f:
            f.write(f'name:{name}\n')
            f.write(f'artist:{artist}\n')
            f.write(f'album:{album}\n')
            f.write(f'length:{length}\n')
            f.write(f'image_path:{image_path}\n')
            f.write(f'image_url:{image_url}\n')
            f.write(f'path:{path}\n')
            f.write(f'downloaded:{downloaded}\n')
    return file

def readdat(path):
    with open(path,'r') as f:
        data = f.readlines()
    info = {}
    for b in data:
        b = b.removesuffix('\n')
        split = b.split(':',1)
        if split[1] == 'False': split[1] = False
        elif split[1] == 'True': split[1] = True
        info[split[0]] = split[1]
    return info

def makeplst(pl):
    path = pyui.resourcepath(f'data\\playlists\\{pl[1]}.plst')
    with open(path,'w') as f:
        for a in pl[0]:
            f.write(f'{a}\n')
def readplst(title='',path=''):
    if path == '':
        path = pyui.resourcepath(f'data\\playlists\\{title}.plst')
    if title == '':
        title = path.split('\\')[-1].removesuffix('.plst')
    pl = []
    with open(path,'r') as f:
        data = f.readlines()
    for a in data:
        pl.append(a.removesuffix('\n'))
    return [pl,title]
    

class funcercm:
    def __init__(self,param,music):
        self.func = lambda: music.controlmenu(param)
class funcerpl:
    def __init__(self,param,music):
        self.func = lambda: music.moveplaylist(param)
class funceram:
    def __init__(self,param,music):
        self.func = lambda: music.addtoplaylist(param)
        
class MUSIC:
    def __init__(self):
        self.shuffle = False
        self.playing = False
        self.storevolume = 1
        self.songlength = 1
        self.awaitinginput = False
        
        self.initfiles()
        self.loadmusic()
        self.loadplaylists()
        self.activeplaylist = 0
        self.activesong = -1
        self.generatequeue()
        self.songhistory = []
        self.nextsong()

        self.makegui()

    def initfiles(self):
        if not os.path.isdir(pyui.resourcepath('data')):
            os.mkdir(pyui.resourcepath('data'))
        if not os.path.isdir(pyui.resourcepath('data\\songs')):
            os.mkdir(pyui.resourcepath('data\\songs'))
        if not os.path.isdir(pyui.resourcepath('data\\mp3s')):
            os.mkdir(pyui.resourcepath('data\\mp3s'))
        if not os.path.isdir(pyui.resourcepath('data\\playlists')):
            os.mkdir(pyui.resourcepath('data\\playlists'))
        if not os.path.isdir(pyui.resourcepath('data\\images')):
            os.mkdir(pyui.resourcepath('data\\images'))
    def scanmp3s(self):
        files = [pyui.resourcepath('data\\mp3s\\'+f) for f in os.listdir(pyui.resourcepath('data\\mp3s')) if f[len(f)-4:]=='.mp3']
        for a in files:
            fl = a.split('\\')[-1].removesuffix('.mp3')
            name = fl
            fl = pyui.resourcepath(fl+'.dat')
            if not os.path.isfile(fl):
                songmp3 = pygame.mixer.Sound(a)
                length = round(songmp3.get_length())
                makedat({'name':name,'length':length,'path':a,'downloaded':True})
    def loadmusic(self):
        self.scanmp3s()
        files = [pyui.resourcepath('data\\songs\\'+f) for f in os.listdir(pyui.resourcepath('data\\songs')) if f[len(f)-4:]=='.dat']
        self.songdata = []
        self.allsongs = []
        for file in files:
            self.songdata.append(readdat(file))
        for a in self.songdata:
            self.allsongs.append(a['path'])
    def loadplaylists(self):
        self.playlists = []
        self.playlists.append([[self.allsongs[a] for a in range(len(self.allsongs))],'All Music'])
        files = [pyui.resourcepath('data\\playlists\\'+f) for f in os.listdir(pyui.resourcepath('data\\playlists')) if f[len(f)-5:]=='.plst']
        for a in files:
            self.playlists.append(readplst(path=a))
    def generatequeue(self):
        if not self.shuffle:
            if self.activesong == -1:
                self.queue = copy.copy(self.playlists[self.activeplaylist][0])
            else:
                self.queue = [self.playlists[self.activeplaylist][0][a] for a in range(self.playlists[self.activeplaylist][0].index(self.activesong),len(self.playlists[self.activeplaylist][0]))]
    def nextsong(self):
        pygame.mixer.music.unload()
        self.missedtime = 0
        self.realtime = 0
        if self.activesong != -1:
            self.songhistory.append(self.activesong)
        if len(self.queue)!=0:
            self.activesong = self.queue[0]
            del self.queue[0]
            while len(self.queue)>0 and not(self.songdata[self.allsongs.index(self.activesong)]['downloaded']):
                self.activesong = self.queue[0]
                del self.queue[0]
            if self.songdata[self.allsongs.index(self.activesong)]['downloaded']:
                pygame.mixer.music.load(self.activesong)
                songmp3 = pygame.mixer.Sound(self.activesong)
                self.songlength = round(songmp3.get_length())
                self.refreshsongdisplays()
                pygame.mixer.music.set_endevent(pygame.USEREVENT)
                pygame.mixer.music.play()
                if not self.playing:
                    pygame.mixer.music.pause()
            else:
                self.activesong = -1
        else:
            self.activesong = -1
    def prevsong(self):
        self.queue.insert(0,0)
             
    def update(self):
        if self.awaitinginput:
            if self.input != []:
                self.importplaylist2()
        if self.activesong!=-1:
            self.realtime = round(pygame.mixer.music.get_pos()/1000)+self.missedtime
            if sectostr(self.realtime)!=ui.IDs['songtime'].text:
                if not ui.IDs['song duration button'].holding:
                    ui.IDs['song duration'].slider = self.realtime
                ui.IDs['songtime'].text = sectostr(self.realtime)
                ui.IDs['songtime'].refresh(ui)
                ui.IDs['songtime'].resetcords(ui)
    def refreshsongdisplays(self):
        if self.activesong != -1 and 'song duration' in ui.IDs:
            ui.IDs['song duration'].maxp = self.songlength
            ui.IDs['songlength'].text = sectostr(self.songlength)
            ui.IDs['songlength'].refresh(ui)
            ui.IDs['songlength'].resetcords(ui)
            ui.IDs['song title'].text = self.songdata[self.allsongs.index(self.activesong)]['name']
            ui.IDs['song title'].refresh(ui)
            ui.IDs['song title'].resetcords(ui)
            ui.IDs['artist name'].text = self.songdata[self.allsongs.index(self.activesong)]['artist']
            ui.IDs['artist name'].refresh(ui)
            ui.IDs['artist name'].resetcords(ui)
            if self.songdata[self.allsongs.index(self.activesong)]['image_path'] != 'none':
                ui.IDs['song img'].img = pygame.image.load(self.songdata[self.allsongs.index(self.activesong)]['image_path'])
            else:
                ui.IDs['song img'].img = pyui.loadinganimation(12)
            ui.IDs['song img'].refresh(ui)
            ui.IDs['song img'].resetcords(ui)
            
    def makegui(self):
        self.songbarwidth = 0.4
        ## main 3 buttons
        ui.makerect(0,0,screenw,93,col=(32,33,35),anchor=(0,'h-93'),layer=4,scalesize=False,ID='controlbar')
        ui.makebutton(0,0,'{pause rounded=0.1}',30,anchor=('w/2','h-60'),toggletext='{play rounded=0.05}',toggleable=True,togglecol=(16,163,127),center=True,width=49,height=49,roundedcorners=100,scalesize=False,clickdownsize=2,command=self.playpause,toggle=self.playing,ID='playpause button',layer=5)
        ui.makebutton(0,0,'{skip rounded=0.05 left}',22,anchor=('w/2-55','h-60'),center=True,width=45,height=45,roundedcorners=100,scalesize=False,clickdownsize=2,layer=5)
        ui.makebutton(0,0,'{skip rounded=0.05}',22,anchor=('w/2+55','h-60'),center=True,width=45,height=45,roundedcorners=100,scalesize=False,clickdownsize=2,command=self.nextsong,layer=5)

        ## song progress slider
        ui.makeslider(0,0,screenw*self.songbarwidth,12,maxp=self.songlength,anchor=('w/2','h-19'),center=True,border=1,roundedcorners=4,button=ui.makebutton(0,0,'',width=20,height=20,clickdownsize=0,borderdraw=False,backingdraw=False,runcommandat=1,command=self.setsongtime,ID='song duration button'),movetoclick=True,scalesize=False,col=(131,243,216),backingcol=(16,163,127),ID='song duration',layer=5)
        ui.maketext(0,0,sectostr(0),20,backingcol=(32,33,35),anchor=('w*'+str((1-self.songbarwidth)/2)+'-8','h-19'),objanchor=('w','h/2'),scalesize=False,ID='songtime',layer=5)
        ui.maketext(0,0,sectostr(self.songlength),20,backingcol=(32,33,35),anchor=('w*'+str((1+self.songbarwidth)/2)+'+8','h-19'),objanchor=('0','h/2'),scalesize=False,ID='songlength',layer=5)

        ## volume control
        ui.makeslider(0,0,100,12,maxp=1,anchor=('w-10','h-46'),objanchor=('w','h/2'),border=1,roundedcorners=4,button=ui.makebutton(0,0,'',width=20,height=20,clickdownsize=0,borderdraw=False,backingdraw=False,runcommandat=1,command=self.setvolume,ID='volume button'),movetoclick=True,scalesize=False,col=(131,243,216),backingcol=(16,163,127),startp=self.storevolume,ID='volume',layer=5)
        ui.makebutton(0,0,'{speaker}',20,anchor=('w-120','h-46'),objanchor=('w','h/2'),roundedcorners=10,scalesize=False,clickdownsize=2,spacing=4,toggleable=True,togglecol=(16,163,127),toggletext='{mute}',command=self.mutetoggle,ID='mute button',layer=5)

        ## song title/image
        ui.maketext(0,0,'',70,anchor=('50','h-46'),center=True,scalesize=False,img=pyui.loadinganimation(12),ID='song img',layer=5)
        ui.maketext(0,0,'Song',20,anchor=('90','h-45'),objanchor=(0,'h'),backingcol=(32,33,35),maxwidth=200,textcenter=False,scalesize=False,ID='song title',layer=5)
        ui.maketext(0,0,'Artist',15,anchor=('90','h-45'),backingcol=(32,33,35),maxwidth=200,textcol=(220,220,220),scalesize=False,ID='artist name',layer=5)  
        
        ## playlist
        titles = [ui.maketext(0,0,'Image',30,textcenter=True,col=(62,63,75)),
                  ui.maketext(0,0,'Song',30,textcenter=True,col=(62,63,75)),
                  ui.maketext(0,0,'Album',30,textcenter=True,col=(62,63,75)),
                  ui.maketext(0,0,'Length',30,textcenter=True,col=(62,63,75)),'']
        wid = int((screenw-315-12)/3)
        ui.maketable(160,100,[],titles,ID='playlist',boxwidth=[70,wid,wid,wid,70],boxheight=[40],backingdraw=True,textsize=20,verticalspacing=4,textcenter=False,col=(62,63,75),scalesize=False,scalex=False,scaley=False,roundedcorners=4,clickablerect=pygame.Rect(160,100,2000,screenh-193))
        self.refreshsongtable()
        ui.makerect(156,0,2000,100,col=(62,63,75),scalesize=False,scalex=False,scaley=False,layer=2,ID='title backing')
        ui.maketext(0,5,self.playlists[self.activeplaylist][1],80,anchor=('(w-175)/2+160',0),center=True,centery=False,scalesize=False,scalex=False,scaley=False,ID='playlist name',layer=3)
        ui.maketext(0,65,str(len(self.playlists[self.activeplaylist][0]))+' songs',30,anchor=('(w-175)/2+160',0),center=True,centery=False,scalesize=False,scalex=False,scaley=False,ID='playlist info',layer=3)
        ui.makescroller(0,0,screenh-193,self.shiftsongtable,maxp=ui.IDs['playlist'].height,pageheight=screenh-200,anchor=('w',100),objanchor=('w',0),ID='scroller',scalesize=False,scalex=False,scaley=False,runcommandat=1)
            
        ## side bar
        ui.makerect(150,0,4,1000,layer=2,scalesize=False,scalex=False,scaley=False,ID='playlists spliter')
        ui.maketext(75,30,'Playlists',40,center=True,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(12,50,'+',55,roundedcorners=30,width=35,height=35,textoffsety=-3,scalesize=False,scalex=False,scaley=False,command=self.makeplaylist,clickdownsize=2)
        ui.makebutton(50,50,'Import',32,roundedcorners=30,height=35,scalesize=False,scalex=False,scaley=False,command=self.importplaylist,clickdownsize=2)
        ui.maketable(5,95,[['']],roundedcorners=4,textsize=20,boxwidth=140,scalesize=False,scalex=False,scaley=False,verticalspacing=3,ID='playlist table')
        self.refreshplaylisttable()
        
        ## control menu
        ui.makewindowedmenu(0,0,100,230,'control','main',col=(52,53,65),scalesize=False,scalex=False,scaley=False,roundedcorners=10,ID='controlmenu')
        ui.makebutton(5,5,'Play',30,col=(62,63,75),textcol=(240,240,240),roundedcorners=8,width=90,height=40,menu='control',command=self.playselected,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(5,50,'Queue',30,col=(62,63,75),textcol=(240,240,240),roundedcorners=8,width=90,height=40,menu='control',command=self.queueselected,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(5,95,'Info',30,col=(62,63,75),textcol=(240,240,240),roundedcorners=8,width=90,height=40,menu='control',command=self.infomenu,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(5,140,'Add',30,col=(62,63,75),textcol=(240,240,240),roundedcorners=8,width=90,height=40,menu='control',command=self.addmenu,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(5,185,'Remove',30,col=(62,63,75),textcol=(240,240,240),roundedcorners=8,width=90,height=40,menu='control',command=self.removesong,scalesize=False,scalex=False,scaley=False)

        ## add menu
        ui.makewindowedmenu(160,20,200,255,'add menu','main',col=(52,53,65),scalesize=False,scalex=False,scaley=False,roundedcorners=10,colorkey=(2,2,2),ID='add menu')
        ui.maketable(5,5,[],['Playlist'],menu='add menu',roundedcorners=4,boxwidth=190,textsize=30,scalesize=False,scalex=False,scaley=False,verticalspacing=3,col=(62,63,75),ID='playlist add')
        
        ## info editor
        ui.makewindowedmenu(160,20,600,255,'song info','main',col=(52,53,65),scalesize=False,scalex=False,scaley=False,roundedcorners=10,colorkey=(2,2,2))
        ui.maketable(5,5,[['Name',ui.maketextbox(0,0,'',400,10,height=50,roundedcorners=2,textsize=30,col=(62,63,75),ID='inputinfo name',linelimit=10)],
                          ['Artist',ui.maketextbox(0,0,'',400,10,height=50,roundedcorners=2,textsize=30,col=(62,63,75),ID='inputinfo artist',linelimit=10)],
                          ['Album',ui.maketextbox(0,0,'',400,10,height=50,roundedcorners=2,textsize=30,col=(62,63,75),ID='inputinfo album',linelimit=10)],
                          ['Image',ui.maketextbox(0,0,'',400,10,height=50,roundedcorners=2,textsize=30,col=(62,63,75),ID='inputinfo image',linelimit=10)]],boxwidth=[-1,500],boxheight=50,menu='song info',roundedcorners=4,textsize=30,scalesize=False,scalex=False,scaley=False,verticalspacing=3,col=(62,63,75))
        ui.makebutton(300,220,'Save',30,self.saveinfo,'song info',roundedcorners=8,spacing=2,horizontalspacing=14,center=True,centery=False,clickdownsize=2,scalesize=False,scalex=False,scaley=False)
        self.refreshsongdisplays()

        ## playlist editor
        ui.makebutton(0,0,'{pencil}',25,self.plsteditmenu,anchor=('w-5',5),objanchor=('w',0),roundedcorners=10,width=40,height=40,textoffsety=-1,scalesize=False,scalex=False,scaley=False,layer=3,clickdownsize=2)
        ui.makewindowedmenu(160,20,600,99,'plstedit menu','main',col=(52,53,65),scalesize=False,scalex=False,scaley=False,roundedcorners=10,colorkey=(2,2,2),ID='plstedit menu')
        ui.maketable(5,5,[['Name',ui.maketextbox(0,0,'',400,10,height=50,roundedcorners=2,textsize=30,col=(62,63,75),ID='inputinfo plstname',linelimit=10,verticalspacing=2)]],menu='plstedit menu',roundedcorners=4,boxwidth=[84,500],boxheight=50,textsize=30,scalesize=False,scalex=False,scaley=False,verticalspacing=3,col=(62,63,75),ID='plstedit table')
        ui.makebutton(300,64,'Save',30,self.saveplstinfo,'plstedit menu',roundedcorners=8,spacing=2,horizontalspacing=14,center=True,centery=False,clickdownsize=2,scalesize=False,scalex=False,scaley=False)
        ui.makebutton(595,94,'Delete',30,self.deleteplst,'plstedit menu',roundedcorners=8,spacing=2,horizontalspacing=14,objanchor=('w','h'),clickdownsize=2,scalesize=False,scalex=False,scaley=False,col=(180,60,60))
        
        
    def setsongtime(self):
        if ui.IDs['song duration button'].clickedon == 2 and self.activesong!=-1:
            self.missedtime = ui.IDs['song duration'].slider-pygame.mixer.music.get_pos()/1000
            pygame.mixer.music.set_pos(ui.IDs['song duration'].slider)
    def setvolume(self):
        pygame.mixer.music.set_volume(ui.IDs['volume'].slider)
        if ui.IDs['volume'].slider == 0:
            ui.IDs['mute button'].toggle = False
        else:
            ui.IDs['mute button'].toggle = True
    def mutetoggle(self):
        if not ui.IDs['mute button'].toggle:
            self.storevolume = ui.IDs['volume'].slider
            ui.IDs['volume'].slider = 0
        else:
            ui.IDs['volume'].slider = self.storevolume
        self.setvolume()
            
    def playpause(self):
        self.playing = ui.IDs['playpause button'].toggle
        if self.playing:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
    def shiftsongtable(self):
        ui.IDs['playlist'].y = 100-ui.IDs['scroller'].scroll
        ui.IDs['playlist'].refreshcords(ui)
    def refreshsongtable(self):
        ui.IDs['playlist'].wipe(ui,False)
        data = []
        for a in self.playlists[self.activeplaylist][0]:
            func = funcercm(a,self)
            obj = ui.makebutton(0,0,'{dots}',20,command=func.func,col=(62,63,75),clickdownsize=1,roundedcorners=4)
            dat = self.songdata[self.allsongs.index(a)]
            if dat['image_path'] == 'none': img = '-'
            else: img = ui.maketext(0,0,'',64,img=pygame.image.load(dat['image_path']),col=(62,63,75),roundedcorners=4,textcenter=True,scalesize=False)
            data.append([img,dat['name']+'\n- '+dat['artist'],dat['album'],sectostr(float(dat['length'])),obj])
        ui.IDs['playlist'].data = data
        ui.IDs['playlist'].refresh(ui)
        ui.IDs['playlist'].refreshcords(ui)
    def refreshplaylisttable(self):
        ui.IDs['playlist table'].wipe(ui)
        data = []
        for a in self.playlists:
            name = a[1].removesuffix('.plst')
            if name[len(name)-5:] != '%del%':
                func = funcerpl(self.playlists.index(a),self)
                data.append([ui.makebutton(0,0,a[1],25,clickdownsize=1,roundedcorners=4,verticalspacing=4,command=func.func,maxwidth=130)])
        ui.IDs['playlist table'].data = data
        ui.IDs['playlist table'].refresh(ui)
        ui.IDs['playlist table'].refreshcords(ui)
    def importplaylist(self):
        self.thread = threading.Thread(target=self.getinput)
        self.input = []
        self.awaitinginput = True
        self.thread.start()
    def importplaylist2(self):
        self.awaitinginput = False
        link = self.input
        pl = spotifyplaylistpull(link)
        if pl != 0:
            self.loadmusic()
            self.playlists.append(pl)
            makeplst(pl)
            self.moveplaylist(len(self.playlists)-1)
            self.refreshplaylisttable()
    def getinput(self):
        self.input = input('Enter your spotify link: ')
    def makeplaylist(self):
        self.playlists.append([[],'New Playlist '+str(len(self.playlists)+1)])
        makeplst([[],'New Playlist '+str(len(self.playlists))])
        self.moveplaylist(len(self.playlists)-1)
        self.refreshplaylisttable()
    def moveplaylist(self,playlist):
        ui.IDs['scroller'].scroll = 0
        self.shiftsongtable()
        self.activeplaylist = playlist
        self.refreshsongtable()
        self.refreshplaylistdisplay()
        ui.IDs['scroller'].scroller = 0
        ui.IDs['scroller'].maxp = ui.IDs['playlist'].height
        ui.IDs['scroller'].refresh(ui)
    def refreshplaylistdisplay(self):
        ui.IDs['playlist name'].text = self.playlists[self.activeplaylist][1]
        ui.IDs['playlist name'].refresh(ui)
        ui.IDs['playlist name'].resetcords(ui)
        ui.IDs['playlist info'].text = str(len(self.playlists[self.activeplaylist][0]))+' songs'
        ui.IDs['playlist info'].refresh(ui)
        ui.IDs['playlist info'].resetcords(ui)
    def addtoplaylist(self,playlist):
        self.playlists[[a[1] for a in self.playlists].index(playlist)][0].append(self.selected)
        makeplst(self.playlists[[a[1] for a in self.playlists].index(playlist)])
        ui.menuback()
    def removesong(self):
        ui.menuback()
        if self.activeplaylist != 0:
            self.playlists[self.activeplaylist][0].remove(self.selected)
            makeplst(self.playlists[self.activeplaylist])
            self.refreshsongtable()
    def controlmenu(self,song):
        self.selected = song
        mpos = pygame.mouse.get_pos()
        if screenw-mpos[0]<ui.IDs['controlmenu'].width: wid = ui.IDs['controlmenu'].width
        else: wid = 0
        if screenh-mpos[1]-100<ui.IDs['controlmenu'].height: hei = ui.IDs['controlmenu'].height
        else: hei = 0
        ui.IDs['controlmenu'].x = mpos[0]-wid
        ui.IDs['controlmenu'].y = mpos[1]-hei
        ui.IDs['controlmenu'].startanchor = mpos
        ui.movemenu('control','down')
    def infomenu(self):
        dat = self.songdata[self.allsongs.index(self.selected)]
        ui.IDs['inputinfo name'].text = dat['name']
        ui.IDs['inputinfo artist'].text = dat['artist']
        ui.IDs['inputinfo album'].text = dat['album']
        ui.IDs['inputinfo image'].text = dat['image_path']
        ui.IDs['inputinfo name'].refresh(ui)
        ui.IDs['inputinfo artist'].refresh(ui)
        ui.IDs['inputinfo album'].refresh(ui)
        ui.IDs['inputinfo image'].refresh(ui)
        ui.movemenu('song info','down')
    def addmenu(self):
        data = []
        for a in range(1,len(self.playlists)):
            func = funceram(self.playlists[a][1],self)
            data.append([ui.makebutton(0,0,self.playlists[a][1],25,clickdownsize=1,roundedcorners=4,verticalspacing=4,command=func.func)])
        ui.IDs['playlist add'].data = data
        ui.IDs['playlist add'].refresh(ui)
        ui.IDs['playlist add'].refreshcords(ui)
        ui.IDs['add menu'].height = ui.IDs['playlist add'].height+10
        ui.movemenu('add menu','down')
    def plsteditmenu(self):
        if self.activeplaylist!=0:
            ui.IDs['inputinfo plstname'].text = self.playlists[self.activeplaylist][1]
            ui.IDs['inputinfo plstname'].refresh(ui)
            ui.movemenu('plstedit menu','down')
    def deleteplst(self):
        ui.IDs['inputinfo plstname'].text = self.playlists[self.activeplaylist][1]+'%del%'
        self.saveplstinfo()
        self.moveplaylist(0)
    def saveplstinfo(self):
        name = ui.IDs['inputinfo plstname'].text
        old = self.playlists[self.activeplaylist][1]
        self.playlists[self.activeplaylist][1] = name
        os.rename(pyui.resourcepath(f'data\\playlists\\{old}.plst'),pyui.resourcepath(f'data\\playlists\\{name}.plst'))
        self.refreshplaylisttable()
        self.refreshplaylistdisplay()
        ui.menuback()
    def saveinfo(self):
        name = ui.IDs['inputinfo name'].text
        artist = ui.IDs['inputinfo artist'].text
        album = ui.IDs['inputinfo album'].text
        image = ui.IDs['inputinfo image'].text
        if len(image.split('\\')) == 1:
            image = pyui.resourcepath(f'data\\images\\{image}')
        self.songdata[self.allsongs.index(self.selected)]['name'] = name
        self.songdata[self.allsongs.index(self.selected)]['artist'] = artist
        self.songdata[self.allsongs.index(self.selected)]['album'] = album
        if os.path.isfile(image):
            self.songdata[self.allsongs.index(self.selected)]['image_path'] = image
        length = self.songdata[self.allsongs.index(self.selected)]['length']
        fl = self.selected.removesuffix('.mp3')
        fl+='.dat'
        makedat(self.songdata[self.allsongs.index(self.selected)],True)
        self.refreshsongtable()
        ui.menuback()
        
    def playselected(self):
        self.activesong = self.selected
        self.generatequeue()
        ui.menuback()
        self.nextsong()
        if not self.playing:
            ui.IDs['playpause button'].toggle = True
            self.playpause()
    def queueselected(self):
        self.queue.insert(0,self.selected)
        ui.menuback()

    

music = MUSIC()

while not done:
    pygameeventget = ui.loadtickdata()
    for event in pygameeventget:
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.VIDEORESIZE:
            screenw = event.w
            screenh = event.h
            ui.IDs['controlbar'].width = screenw
            ui.IDs['playlists spliter'].height = screenh
            ui.IDs['title backing'].width = screenw
            ui.IDs['song duration'].width = event.w*music.songbarwidth
            ui.IDs['song duration'].resetcords(ui)
            ui.IDs['scroller'].height = screenh-193
            ui.IDs['scroller'].pageheight = screenh-200
            ui.IDs['scroller'].refresh(ui)
            wid = int((screenw-315-12)/3)
            ui.IDs['playlist'].boxwidth = [70,wid,wid,wid,70]
            ui.IDs['playlist'].clickablerect = pygame.Rect(160,100,2000,screenh-193)
            ui.IDs['playlist'].refresh(ui)
            ui.IDs['playlist'].refreshcords(ui)
        if event.type == pygame.mixer.music.get_endevent():
            music.nextsong()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and ui.activemenu == 'main':
                if ui.IDs['playpause button'].toggle: ui.IDs['playpause button'].toggle = False
                else: ui.IDs['playpause button'].toggle = True
                music.playpause()
    
    screen.fill((62,63,75))
    music.update()
    ui.rendergui(screen)
    pygame.display.flip()
    clock.tick(60)
pygame.mixer.music.stop()
pygame.quit()

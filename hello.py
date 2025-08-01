import pygame, sys, math
# ── CONFIG ───────────────────────────────────────────────────────────
W, H           = 800, 600
MAX_DIST       = 400                 # px
PX_PER_CM      = 4                   # 4 px ≈ 1 cm
FOV_DEG        = 24
TURN_DEG       = 3                   # sensor rotation speed
MOVE_PX        = 4                   # sensor translation speed

# wave parameters (slowed for visibility)
CREST_GAP      = 40
PING_PERIOD_MS = 800
WAVE_SPEED_PXMS= 0.8                 # pixels per millisecond

# physics constants
V_SOUND_MPS    = 343                 # speed of sound in air
V_SOUND_CMMS   = 34.3                # cm per millisecond

# palette
BG        =(18,18,22) ; SENSOR_C=(80,160,255) ; OBJ_C=(255,140,40)
PING_C    =(40,220,100); ECHO_C=(235,115,45)
RAY_C     =(200,200, 0); HIT_C =(255, 50,50); SEL_C =(0,255,0)
TXT_C     =(235,235,235)

pygame.init()
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Ultrasonic Sensor – physics overlay")
clock =pygame.time.Clock()
font  =pygame.font.SysFont(None,22)

# ── WORLD ────────────────────────────────────────────────────────────
sensor=[100,H//2] ; heading=0
SZ=60
obstacles=[pygame.Rect(500,100,SZ,SZ),pygame.Rect(650,300,SZ,SZ),
           pygame.Rect(400,450,SZ,SZ),pygame.Rect(250,250,SZ,SZ)]
TAU=math.tau
ping=None ; last_launch=pygame.time.get_ticks()

# ── MATH HELPERS ─────────────────────────────────────────────────────
def unit(deg): r=math.radians(deg); return math.cos(r),math.sin(r)

def ray_aabb(o,d,rect,lim):
    ox,oy=o; dx,dy=d; eps=1e-9
    # slabs in X
    if abs(dx)<eps:
        if ox<rect.left or ox>rect.right: return None
        tx_min,tx_max=-math.inf,math.inf
    else:
        tx1,tx2=(rect.left-ox)/dx,(rect.right-ox)/dx
        tx_min,tx_max=min(tx1,tx2),max(tx1,tx2)
    # slabs in Y
    if abs(dy)<eps:
        if oy<rect.top or oy>rect.bottom:return None
        ty_min,ty_max=-math.inf,math.inf
    else:
        ty1,ty2=(rect.top-oy)/dy,(rect.bottom-oy)/dy
        ty_min,ty_max=min(ty1,ty2),max(ty1,ty2)
    t0=max(tx_min,ty_min); t1=min(tx_max,ty_max)
    if t1<0 or t0>t1 or t0>lim: return None
    return max(t0,0.0)

def first_hit(o,d,lim):
    best=pt=idx=None
    for i,rect in enumerate(obstacles):
        t=ray_aabb(o,d,rect,lim)
        if t is not None and (best is None or t<best):
            best,idx=t,i
            pt=(o[0]+d[0]*t,o[1]+d[1]*t)
    return best,pt,idx

def draw_fan(surf,centre,det_angle,prog,col):
    arc_angle=(-det_angle)%TAU           # convert to Pygame arc
    half=math.radians(FOV_DEG/2)
    for k in range(7):
        r=prog-k*CREST_GAP
        if r<=0: continue
        alpha=max(0,220-k*35)
        pygame.draw.arc(
            surf,(*col,alpha),
            pygame.Rect(centre[0]-r,centre[1]-r,r*2,r*2),
            arc_angle-half,arc_angle+half,2)

# ── MAIN LOOP ────────────────────────────────────────────────────────
while True:
    dt=clock.tick(60)                      # ms since last frame

    # input
    for e in pygame.event.get():
        if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
            pygame.quit();sys.exit()
    k=pygame.key.get_pressed()
    if k[pygame.K_LEFT]:  sensor[0]-=MOVE_PX
    if k[pygame.K_RIGHT]: sensor[0]+=MOVE_PX
    if k[pygame.K_UP]:    sensor[1]-=MOVE_PX
    if k[pygame.K_DOWN]:  sensor[1]+=MOVE_PX
    if k[pygame.K_a]:     heading=(heading+TURN_DEG)%360
    if k[pygame.K_d]:     heading=(heading-TURN_DEG)%360
    sensor[0]=max(0,min(W,sensor[0])); sensor[1]=max(0,min(H,sensor[1]))
    spos=tuple(sensor)

    # sensing
    dvec=unit(heading)
    hit_d,hit_pt,hit_idx=first_hit(spos,dvec,MAX_DIST)
    seen=hit_d is not None
    dist_cm=hit_d/PX_PER_CM if seen else None
    tof_ms=(2*dist_cm)/V_SOUND_CMMS if seen else None   # physics ToF

    # ping timing
    now=pygame.time.get_ticks()
    if ping is None and now-last_launch>=PING_PERIOD_MS:
        ping=dict(origin=spos,dir_det=math.radians(heading),
                  tgt_d=hit_d or MAX_DIST,has_hit=seen,hit_pt=hit_pt,
                  out=0.0,echo=None,echo_det=None)
        last_launch=now
    if ping:
        step=WAVE_SPEED_PXMS*dt; ping["out"]+=step
        if ping["echo"] is None and ping["out"]>=ping["tgt_d"]:
            if ping["has_hit"]:
                ping["echo"]=0.0
                sx,sy=spos; hx,hy=ping["hit_pt"]
                ping["echo_det"]=math.atan2(sy-hy,sx-hx)
            else: ping=None
        if ping and ping["echo"] is not None:
            ping["echo"]+=step
            if ping["echo"]>=ping["tgt_d"]: ping=None

    # draw ----------------------------------------------------------------
    screen.fill(BG)
    ray_end=(spos[0]+dvec[0]*MAX_DIST,spos[1]+dvec[1]*MAX_DIST)
    pygame.draw.line(screen,RAY_C,spos,ray_end,1)

    for i,rect in enumerate(obstacles):
        pygame.draw.rect(screen,OBJ_C,rect,0)
        if i==hit_idx: pygame.draw.rect(screen,SEL_C,rect,3)
    if seen: pygame.draw.circle(screen,HIT_C,(int(hit_pt[0]),int(hit_pt[1])),4)

    layer=pygame.Surface((W,H),pygame.SRCALPHA)
    if ping:
        draw_fan(layer,ping["origin"],ping["dir_det"],ping["out"],PING_C)
        if ping["echo"] is not None:
            draw_fan(layer,ping["hit_pt"],ping["echo_det"],ping["echo"],ECHO_C)
    screen.blit(layer,(0,0))

    pygame.draw.circle(screen,SENSOR_C,(int(spos[0]),int(spos[1])),12)

    # physics overlay  ----------------------------------------------------
    overlay_lines=[
        "Ultrasonic ranging:",
        "d = (v · t) / 2",
        f"v = {V_SOUND_MPS} m/s",
    ]
    if seen:
        overlay_lines.append(f"t = {tof_ms:6.2f} ms")
        overlay_lines.append(f"d = {dist_cm:6.1f} cm")
    else:
        overlay_lines.append("t = —")
        overlay_lines.append("d = —")
    for i,line in enumerate(overlay_lines):
        txt=font.render(line,True,TXT_C)
        screen.blit(txt,(10,10+i*20))

    pygame.display.flip()
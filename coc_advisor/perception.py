"""Local scene anchors and explicit, confidence-bearing observations.

Initial validated UI slice: English TH2-style army with Barbarians/Archers.
Other inventories/layouts remain unsupported until real fixtures validate them.
"""
from dataclasses import dataclass,field
from pathlib import Path
import re
import time
import cv2
import numpy as np
from PIL import Image

ASSETS=Path(__file__).parent/'assets'
ANCHORS={
 'home_battle':(13,431,113,529), 'edit_army':(44,492,183,535),
 'find_match':(109,365,326,434),'army_title':(436,44,524,67),
 'army_attack':(760,464,938,501),'result_home':(419,438,542,493),
 'damage_100':(460,77,502,97),'three_stars':(325,33,635,182),
 'locked_hero':(25,145,260,475),'locked_spells':(415,310,610,330),
 'scout_next':(798,350,953,423),'end_battle':(15,385,126,425),'reload_game':(251,307,342,326)}


@dataclass
class Observation:
    scene: str
    frame: object
    confidence: float=0
    buttons: dict=field(default_factory=dict)
    inventory: list=field(default_factory=list)
    result: dict | None=None
    layout: dict | None=None
    hud: dict=field(default_factory=dict)
    unknown: list=field(default_factory=list)
    elapsed_ms: float=0


class GeometryGuard:
    def __init__(self,image):
        self.orb=cv2.ORB_create(nfeatures=600)
        self.points,self.descriptors=self.orb.detectAndCompute(self.crop(image),None)
    @staticmethod
    def crop(image):
        im=np.array(image.resize((960,540)).convert('L'))
        return im[60:420,140:850]
    def matches(self,image):
        points,descriptors=self.orb.detectAndCompute(self.crop(image),None)
        if self.descriptors is None or descriptors is None:return False
        pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(self.descriptors,descriptors,k=2)
        good=[a for pair in pairs if len(pair)==2 for a,b in [pair] if a.distance<.7*b.distance]
        if len(good)<12:return False
        src=np.float32([self.points[m.queryIdx].pt for m in good]); dst=np.float32([points[m.trainIdx].pt for m in good])
        transform,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=2)
        if transform is None or int(inliers.sum())<10:return False
        scale=float(np.hypot(transform[0,0],transform[0,1]))
        return .99<scale<1.01 and np.max(np.abs(transform[:,2]))<5 and abs(transform[0,1])<.01


class Perception:
    def __init__(self):
        self.templates={p.stem:np.array(Image.open(p).convert('RGB')) for p in ASSETS.glob('*.png')}
        self.ocr=None
        self.profile_cache=None

    @staticmethod
    def canonical(image): return np.array(image.resize((960,540),Image.Resampling.BILINEAR))

    def score(self,image,name):
        if name not in self.templates or name not in ANCHORS:return 0.
        x1,y1,x2,y2=ANCHORS[name]; pad=5
        roi=image[max(0,y1-pad):min(540,y2+pad),max(0,x1-pad):min(960,x2+pad)]
        template=self.templates[name]
        if roi.shape[0]<template.shape[0] or roi.shape[1]<template.shape[1]:return 0.
        matches=cv2.matchTemplate(roi,template,cv2.TM_CCOEFF_NORMED)
        _,score,_,(x,y)=cv2.minMaxLoc(matches)
        patch=roi[y:y+template.shape[0],x:x+template.shape[1]]
        if np.abs(patch.astype(float)-template.astype(float)).mean()>25:return 0.
        return float(score)

    def scene(self,image):
        im=self.canonical(image)
        if self.score(im,'reload_game')>.9:return 'disconnected',.99
        center=im[201:343,230:730].astype(float)
        grey=(np.abs(center[:,:,0]-center[:,:,1])<6)&(np.abs(center[:,:,1]-center[:,:,2])<6)&(center.mean(axis=2)>35)&(center.mean(axis=2)<130)
        if grey.mean()>.45:return 'unknown',0.
        for name,scene in [('army_title','army'),('result_home','result'),('edit_army','match'),('home_battle','home')]:
            score=self.score(im,name)
            if score>.88:return scene,score
        # Scout/battle anchors are learned only from independently inspected real UI.
        for name,scene in [('scout_next','scout'),('battle_surrender','battle')]:
            if name in self.templates:
                score=self.score(im,name)
                if score>.88:return scene,score
        red=im[387:421,17:122]
        if ((red[:,:,0]>160)&(red[:,:,1]<100)&(red[:,:,2]<100)).mean()>.2 and im[450:535].mean()<140:
            return 'battle',.9
        if im.mean()<8 or (im.mean()>235 and im.std()<25):return 'loading',.9
        return 'unknown',0.

    def recognize_lines(self,crops):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1)
        result,_=self.ocr.text_rec([np.ascontiguousarray(x[:,:,::-1]) for x in crops])
        return result

    @staticmethod
    def number(text):
        match=re.fullmatch(r'[xX]?\s*(\d{1,3})',text.strip())
        return int(match.group(1)) if match else None

    def army(self,im):
        # Detect actual card borders; never infer inventory from camp occupants.
        roi=im[138:225,276:940]
        r,g,b=cv2.split(roi)
        mask=((b.astype(float)>r.astype(float)*1.18)&(b>150)&(g>100)).astype('uint8')*255
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        boxes=sorted([(x+276,y+138,w,h) for c in contours for x,y,w,h in [cv2.boundingRect(c)] if 45<w<95 and 45<h<90])
        inventory=[]; unknown=[]; crops=[]
        for x,y,w,h in boxes:
            portrait=im[y+22:y+h-18,x+6:x+w-6]
            scores={}
            for name in ('barbarian','archer'):
                template=cv2.resize(self.templates[name+'_portrait'],(portrait.shape[1],portrait.shape[0]))
                scores[name]=float(cv2.matchTemplate(portrait,template,cv2.TM_CCOEFF_NORMED)[0,0])
            name=max(scores,key=scores.get)
            if scores[name]<.75:unknown.append('Unrecognized troop card'); continue
            crops.extend([im[y:y+20,x:x+37],im[y+h-23:y+h-2,x:x+25]])
            inventory.append(dict(name=name,count=None,level=None,confidence=scores[name],slot=len(inventory),box=(x,y,w,h)))
        if crops:
            lines=self.recognize_lines(crops+[im[112:134,300:356]])
            for i,troop in enumerate(inventory):
                for offset,key in [(0,'count'),(1,'level')]:
                    text,score=lines[i*2+offset]; value=self.number(text)
                    if key=='level':
                        x,y,w,h=troop['box']; badge=im[y+h-22:y+h,x:x+25]
                        score1=max(float(cv2.matchTemplate(badge,self.templates[key],cv2.TM_CCOEFF_NORMED).max()) for key in ('level_1','level_1_archer'))
                        if score1>.92:value=1; score=score1
                    if score>=.65 and value is not None and value>0:troop[key]=value
                    else:unknown.append('Unreadable troop '+key)
            capacity,score=lines[-1]; match=re.fullmatch(r'(\d+)/(\d+)',capacity.replace(' ',''))
            if not match or score<.7 or sum(t['count'] or 0 for t in inventory)!=int(match.group(1)):
                unknown.append('Inventory does not match observed army capacity')
        if self.score(im,'locked_hero')<.9 or self.score(im,'locked_spells')<.9:
            unknown.append('Hero/spell capabilities are not yet validated')
        if not inventory:unknown.append('No supported army cards')
        return inventory,unknown

    def layout(self,im):
        hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
        mask=(((hsv[:,:,0]<9)|(hsv[:,:,0]>170))&(hsv[:,:,1]>120)&(hsv[:,:,2]>120)).astype('uint8')
        mask[:45]=0; mask[430:]=0; mask[:,:140]=0; mask[:,880:]=0
        points=cv2.findNonZero(mask)
        if points is None or len(points)<200:return None
        hull=cv2.convexHull(points)
        if cv2.contourArea(hull)<10000:return None
        field=im[40:380,140:880]; template=self.templates.get('cannon_scout')
        if template is None:return None
        scores=cv2.matchTemplate(field,template,cv2.TM_CCOEFF_NORMED)
        _,score,_,point=cv2.minMaxLoc(scores)
        if score<.72:return None
        cannon=(point[0]+140+template.shape[1]/2,point[1]+40+template.shape[0]/2)
        m=cv2.moments(hull); center=(m['m10']/m['m00'],m['m01']/m['m00']); candidates=[]
        for angle in np.linspace(0,2*np.pi,16,endpoint=False):
            for radius in range(20,600,4):
                x=center[0]+np.cos(angle)*radius; y=center[1]+np.sin(angle)*radius
                if not 150<x<865 or not 65<y<410:break
                if cv2.pointPolygonTest(hull,(float(x),float(y)),True)<-18:
                    candidates.append((float(x),float(y))); break
        if not candidates:return None
        entry=min(candidates,key=lambda p:(p[0]-cannon[0])**2+(p[1]-cannon[1])**2)
        return dict(entry=(entry[0]/960,entry[1]/540),known_cannon=(cannon[0]/960,cannon[1]/540),
                    method='red-zone hull and matched cannon; uncalibrated tactic',unclassified_defences=True)

    def troop_counts(self,im):
        boxes=[]
        for slot in range(8):
            x=83+slot*72
            if x+70>=960:break
            # Active/inactive troop card has a solid rectangular border, unlike empty dashed slots.
            patch=im[449:534,x:x+68]
            if patch.shape[1]<68:break
            edge=patch[:,0:3].mean()
            if slot>=2:break  # Only the two validated basic troop slots are currently supported.
            boxes.append(im[446:470,x+18:x+68])
        lines=self.recognize_lines(boxes)
        return [self.number(text) if score>=.65 else None for text,score in lines]

    def observe(self,frame,previous_state=None):
        start=time.monotonic(); scene,confidence=self.scene(frame.image); im=self.canonical(frame.image)
        o=Observation(scene,frame,confidence)
        for name in ('home_battle','edit_army','find_match','army_attack','result_home','reload_game'):
            if self.score(im,name)>.88:
                x1,y1,x2,y2=ANCHORS[name]; o.buttons[name]=((x1+x2)/1920,(y1+y2)/1080)
        if scene=='army':o.inventory,o.unknown=self.army(im)
        if scene=='match':
            lines=self.recognize_lines([im[398:430,194:228]])
            text,score=lines[0]; cost=self.number(text)
            if score>.8 and cost is not None:o.hud['match_cost']=cost
        if scene=='home':
            template=self.templates.get('townhall_2')
            if template is not None:
                field=im[90:420,150:820]; scores=cv2.matchTemplate(field,template,cv2.TM_CCOEFF_NORMED)
                _,score,_,(x,y)=cv2.minMaxLoc(scores)
                if score>.65:o.layout={'townhall_candidate':((150+x+template.shape[1]/2)/960,(90+y+template.shape[0]/2)/540)}
            profile=im[343:376,210:720]
            key=profile.tobytes()
            # Reuse text only for identical pixels, including unsuccessful reads.
            if self.profile_cache is None or self.profile_cache[0]!=key:
                self.profile_cache=(key,self.recognize_lines([profile])[0])
            text,score=self.profile_cache[1]; normalized=re.sub('[^a-z0-9]','',text.lower())
            match=re.fullmatch(r'townhalllevel(\d{1,2})',normalized)
            if match and score>.8:o.hud['own_th']=int(match.group(1))
        if scene=='result':
            if self.score(im,'damage_100')>.96 and self.score(im,'three_stars')>.96:
                o.result=dict(destruction=100,stars=3,verified=False,method='validated-template')
            else:o.unknown.append('Result digits/stars not independently validated')
        if scene in ('scout','battle'):
            o.hud['remaining']=self.troop_counts(im)
            if scene=='scout':o.layout=self.layout(im)
        o.elapsed_ms=(time.monotonic()-start)*1000
        return o

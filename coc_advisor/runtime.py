"""Resident local diagnostic controller; no chat/API round trips during play."""
import hashlib
from pathlib import Path
import threading
import time
from .controller import Controller
from .device import DeviceError
from .experience import ExperienceStore
from .perception import Perception, GeometryGuard
from .prediction import predict
from .training import LearningCoordinator

ROOT=Path(__file__).resolve().parents[1]


class ResultVerifier:
    def __init__(self):self.key=None; self.first_pts=None
    def consider(self,o):
        if o.result is None:return None
        key=(o.result.get('destruction'),o.result.get('stars'))
        pts=getattr(o.frame,'source_pts_us',None)
        if pts is None:return None
        if key!=self.key:self.key=key; self.first_pts=pts; return None
        if pts-self.first_pts<200000:return None
        return dict(o.result,verified=True)


class AttackRuntime:
    def __init__(self,client,stream,stop=None,on_status=None,max_inputs=40,store=None,learning=None):
        self.client=client; self.stream=stream; self.stop=stop or threading.Event()
        self.on_status=on_status or (lambda text:None)
        self.controller=Controller(); self.reader=Perception(); self.verifier=ResultVerifier()
        self.owns_store=store is None; self.owns_learning=learning is None
        self.store=store or ExperienceStore(ROOT/'recordings/experience')
        self.learning=learning or LearningCoordinator(self.store,ROOT/'recordings/models')
        self.battle_id=None; self.result=None; self.actions=0; self.last_observation=None
        self.model=None; self.deadline=None
        self.max_inputs=max_inputs; self.matchmaking_actions=0
        self.predicted=False
        self.geometry=None

    def context(self,o):
        army=self.controller.army
        names='+'.join(sorted(t['name'] for t in army))
        features={'own_th':self.controller.own_th,'enemy_th':None,
                  'domain':f'{self.controller.own_th}:{names}' if self.controller.own_th else None,
                  'barbarians':sum(t['count'] for t in army if t['name']=='barbarian'),
                  'archers':sum(t['count'] for t in army if t['name']=='archer')}
        if self.controller.entry:features.update(entry_x=self.controller.entry[0],entry_y=self.controller.entry[1])
        layout=o.layout or {}
        if layout.get('known_cannon'):
            features.update(cannon_x=layout['known_cannon'][0],cannon_y=layout['known_cannon'][1])
        return dict(schema_version=1,features=features,army=army,observed_at=time.monotonic(),
                    controller_version='basic-v1',unsupported=['Enemy TH and unclassified defences remain unknown'])

    def run(self,timeout=360):
        started=time.monotonic(); last_sequence=None; last_status=0; result_seen=0
        try:
            self.learning.set_battle_active(True)
            # Warm recognition before gameplay; this is not performed per battle frame.
            self.reader.recognize_lines([self.reader.canonical(self.stream.latest().image)[0:30,0:100]])
            while not self.stop.is_set() and time.monotonic()-started<timeout:
                frame=self.stream.latest()
                if frame is None or frame.sequence==last_sequence:self.stop.wait(.01);continue
                last_sequence=frame.sequence
                observation=self.reader.observe(frame); self.last_observation=observation
                if observation.scene in ('scout','battle') and self.controller.army:
                    observation.hud['remaining']=observation.hud.get('remaining',[])[:len(self.controller.army)]
                if observation.scene=='scout' and observation.layout:
                    if self.battle_id:self.store.append_event(self.battle_id,'layout',observation.layout)
                    if self.controller.entry is None:
                        self.controller.entry=tuple(observation.layout['entry']); self.geometry=GeometryGuard(frame.image)
                if observation.scene=='battle' and self.controller.entry is None:
                    layout=self.reader.layout(self.reader.canonical(frame.image))
                    if layout:self.controller.entry=tuple(layout['entry']); self.geometry=GeometryGuard(frame.image)
                if observation.scene in ('scout','battle') and self.battle_id and self.controller.entry and not self.predicted:
                    context=self.context(observation); self.store.update_context(self.battle_id,context)
                    forecast=predict(context['features'],self.model)
                    forecast.update(predicted_at=time.monotonic(),challengers=self.learning.shadow(context['features']))
                    self.store.record_prediction(self.battle_id,forecast); self.predicted=True
                if observation.scene=='result':
                    result_seen+=1
                    verified=self.verifier.consider(observation)
                    if self.battle_id and self.result is None:
                        if verified is None and result_seen<5:self.stop.wait(.2);continue
                        result=verified or dict(destruction=None,stars=None,verified=False,reason='Unreadable terminal result')
                        evidence=ROOT/'recordings/experience'/f'{self.battle_id}-result.png'
                        frame.image.save(evidence); result['evidence']=str(evidence)
                        self.store.finish_battle(self.battle_id,result); self.result=result
                        self.learning.set_battle_active(False); self.learning.schedule(self.battle_id)
                intents=self.controller.tick(observation)
                if observation.scene=='home' and self.controller.finished:
                    self.on_status('Returned home. Result: '+str(self.result or 'previous battle not labeled'))
                    return self.result
                for intent in intents:
                    if self.actions>=self.max_inputs:
                        self.on_status('Input cap reached; diagnostic stopped'); return self.result
                    if intent.label=='army_attack' and self.matchmaking_actions>=1:
                        self.on_status('One-match cap reached; diagnostic stopped'); return self.result
                    if intent.label=='army_attack' and self.battle_id is None:
                        context=self.context(observation); self.battle_id=self.store.begin_battle(context)
                        self.model=self.learning.snapshot()
                        self.learning.set_battle_active(True)
                    def valid(new):
                        scene=self.reader.scene(new.image)[0]
                        allowed=scene==intent.scene or (scene in ('scout','battle') and intent.scene in ('scout','battle'))
                        if intent.label in ('home_battle','edit_army','army_attack','result_home','reload_game'):
                            allowed=allowed and self.reader.score(self.reader.canonical(new.image),intent.label)>.92
                        if intent.kind=='hold':
                            if self.geometry is None or not self.geometry.matches(new.image):
                                self.controller.entry=None; self.controller.wait_count=None; self.geometry=None
                                self.controller.reason='Camera geometry changed; deployment paused'
                                return False
                        return allowed
                    try:
                        used=self.client.tap_latest(self.stream,intent.x,intent.y,self.stop,valid,intent.hold_ms)
                        self.actions+=1; self.controller.ack(intent,True)
                        if intent.label=='army_attack':self.matchmaking_actions+=1
                        if self.battle_id:self.store.append_event(self.battle_id,'action',dict(label=intent.label,
                            kind=intent.kind,x=intent.x,y=intent.y,hold_ms=intent.hold_ms,source_pts_us=used.source_pts_us,
                            source_bound=used.requested_at,submitted_at=time.monotonic()))
                    except DeviceError as exc:
                        self.controller.ack(intent,False)
                        if self.stop.is_set():break
                        self.on_status('Input withheld: '+str(exc))
                if time.monotonic()-last_status>1:
                    self.on_status(f'{observation.scene} · {self.controller.reason} · {self.actions} inputs · perception {observation.elapsed_ms:.0f}ms')
                    last_status=time.monotonic()
                self.stop.wait(.15)
            self.on_status('Stopped' if self.stop.is_set() else 'Diagnostic timeout; episode kept incomplete')
            return self.result
        finally:
            self.controller.stop(); self.learning.set_battle_active(False)
            if self.owns_learning:self.learning.close(wait=20)
            if self.owns_store:self.store.close()

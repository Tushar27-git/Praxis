"""Bounded local baseline controller. Unsupported observations pause explicitly."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ActionIntent:
    kind: str
    x: float
    y: float
    scene: str
    label: str
    hold_ms: int=0


class Controller:
    def __init__(self):
        self.army=[]; self.entry=None; self.pending=None; self.last_navigation=None
        self.selected=None; self.wait_count=None; self.reason='Ready'; self.stopped=False
        self.prepared=False; self.finished=False
        self.own_th=None; self.profile_attempted=False; self.match_cost=None

    def stop(self):self.stopped=True; self.pending=None; self.reason='Stopped'

    def tick(self,o):
        if self.stopped or self.pending:return []
        if o.scene=='home' and not self.finished and self.own_th is None:
            value=o.hud.get('own_th')
            if type(value) is int and 1<=value<=30:self.own_th=value
            else:
                target=(o.layout or {}).get('townhall_candidate')
                if target and not self.profile_attempted:
                    self.pending=ActionIntent('tap',*target,'home','inspect_town_hall');return [self.pending]
                self.reason='Paused: own Town Hall level not verified';return []
        if o.scene in ('home','match','army','result','disconnected'):
            if o.scene=='home' and self.finished:return []
            label={'home':'home_battle','match':'edit_army','army':'army_attack','result':'result_home','disconnected':'reload_game'}[o.scene]
            if o.scene=='army':
                if o.unknown or not o.inventory:
                    self.reason='Paused: '+', '.join(o.unknown or ['Army unreadable']);return []
                if any(t['name'] not in ('barbarian','archer') or not t['count'] or not t['level'] for t in o.inventory):
                    self.reason='Paused: unsupported army';return []
                self.army=[dict(t) for t in o.inventory]; self.prepared=True
            if o.scene=='result':self.finished=True
            key=(o.scene,label)
            if o.scene=='match':self.match_cost=o.hud.get('match_cost')
            if o.scene=='army' and (self.own_th!=2 or self.match_cost!=10):
                self.reason='Paused: diagnostic requires verified TH2 and10gold matchmaking cost';return []
            if key==self.last_navigation or label not in o.buttons:return []
            x,y=o.buttons[label]; self.pending=ActionIntent('tap',x,y,o.scene,label)
            return [self.pending]
        if o.scene not in ('scout','battle') or not self.army:return []
        if self.entry is None:
            if not o.layout or not o.layout.get('entry'):
                self.reason='Paused: deployment geometry unknown';return []
            self.entry=tuple(o.layout['entry'])
        remaining=o.hud.get('remaining')
        if not remaining or len(remaining)!=len(self.army) or any(type(n) is not int or n<0 for n in remaining):
            self.reason='Waiting for verified troop counts';return []
        if self.wait_count is not None:
            if (self.selected is None or remaining[self.selected]>=self.wait_count[self.selected]
                    or any(n>before for n,before in zip(remaining,self.wait_count))):
                self.reason='Waiting for deployment count feedback';return []
        self.wait_count=None
        slot=next((i for i,n in enumerate(remaining) if n>0),None)
        if slot is None:self.reason='All troops deployed; observing result';return []
        if self.selected!=slot:
            self.pending=ActionIntent('tap',.12+.075*slot,.91,o.scene,f'select_{slot}')
        else:
            self.pending=ActionIntent('hold',*self.entry,o.scene,f'deploy_{slot}',400)
            self._before_count=tuple(remaining)
        return [self.pending]

    def ack(self,intent,success):
        self.pending=None
        if not success:return
        if intent.label.startswith('select_'):self.selected=int(intent.label.split('_')[1])
        elif intent.label.startswith('deploy_'):self.wait_count=self._before_count
        elif intent.label=='inspect_town_hall':self.profile_attempted=True
        else:self.last_navigation=(intent.scene,intent.label)
        self.reason='Executed '+intent.label

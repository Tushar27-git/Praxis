import unittest
from types import SimpleNamespace
from coc_advisor.controller import Controller


def obs(scene,**kwargs):
    base=dict(scene=scene,buttons={},inventory=[],unknown=[],layout=None,hud={},result=None,
              frame=SimpleNamespace(sequence=1,requested_at=1))
    base.update(kwargs); return SimpleNamespace(**base)


class ControllerTests(unittest.TestCase):
    def test_navigation_does_not_duplicate_pending_actions(self):
        c=Controller(); c.own_th=2; o=obs('home',buttons={'home_battle':(.06,.89)})
        a=c.tick(o)[0]; self.assertEqual(a.kind,'tap'); self.assertEqual(c.tick(o),[])
        c.ack(a,True); self.assertEqual(c.tick(o),[])
        self.assertEqual(c.tick(obs('match',buttons={'edit_army':(.12,.95)}))[0].label,'edit_army')
    def test_unknown_army_blocks_matchmaking(self):
        c=Controller(); self.assertEqual(c.tick(obs('army',unknown=['unknown troop'])),[])
        self.assertIn('unknown troop',c.reason)
    def test_deployment_requires_count_feedback(self):
        c=Controller(); c.army=[dict(name='barbarian',count=20,level=1)]; c.entry=(.8,.2)
        o=obs('battle',hud={'remaining':[20]})
        select=c.tick(o)[0]; self.assertEqual(select.label,'select_0'); c.ack(select,True)
        hold=c.tick(o)[0]; self.assertEqual(hold.kind,'hold'); c.ack(hold,True)
        self.assertEqual(c.tick(o),[])
        o.hud['remaining']=[17]
        self.assertEqual(c.tick(o)[0].kind,'hold')
    def test_stop_cancels_future_actions(self):
        c=Controller(); c.stop()
        self.assertEqual(c.tick(obs('home',buttons={'home_battle':(.06,.89)})),[])
    def test_deployment_feedback_requires_selected_count_to_decrease(self):
        c=Controller(); c.army=[dict(name='barbarian',count=20,level=1),dict(name='archer',count=10,level=1)]
        c.entry=(.8,.2)
        o=obs('battle',hud={'remaining':[20,10]})
        select=c.tick(o)[0]; c.ack(select,True)
        hold=c.tick(o)[0]; c.ack(hold,True)
        for counts in ([21,10],[20,9],[19,11]):
            o.hud['remaining']=counts
            self.assertEqual(c.tick(o),[],str(counts))
        o.hud['remaining']=[18,10]
        self.assertEqual(c.tick(o)[0].label,'deploy_0')
    def test_unknown_own_townhall_requires_profile_before_matchmaking(self):
        c=Controller(); self.assertEqual(c.tick(obs('home',buttons={'home_battle':(.06,.89)})),[])
        action=c.tick(obs('home',buttons={'home_battle':(.06,.89)},layout={'townhall_candidate':(.5,.4)}))[0]
        self.assertEqual(action.label,'inspect_town_hall')
    def test_starting_on_army_cannot_bypass_townhall_and_cost_gate(self):
        c=Controller(); army=[dict(name='barbarian',count=20,level=1)]
        self.assertEqual(c.tick(obs('army',inventory=army,buttons={'army_attack':(.88,.89)})),[])
        c.own_th=13; c.match_cost=10
        self.assertEqual(c.tick(obs('army',inventory=army,buttons={'army_attack':(.88,.89)})),[])
    def test_remaining_counts_cannot_exceed_observed_army(self):
        c=Controller(); c.army=[dict(name='barbarian',count=20,level=1),dict(name='archer',count=10,level=1)]
        c.entry=(.8,.2)
        for counts in ([21,10],[20,11],[True,10],[-1,10],[None,10]):
            self.assertEqual(c.tick(obs('battle',hud={'remaining':counts})),[],str(counts))
        self.assertEqual(c.tick(obs('battle',hud={'remaining':[20,10]}))[0].label,'select_0')

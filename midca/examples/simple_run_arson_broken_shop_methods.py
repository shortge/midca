#!/usr/bin/env python
import midca
from midca.modules.perceive import PerfectObserver
from midca.modules.plan import PyHopPlannerBroken
from midca.modules.intend import SimpleIntend
from midca.modules.act import SimpleAct
from midca.modules.interpret import ADistanceAnomalyNoter, TFStack, TFFire, UserGoalInput
from midca.modules.evaluate import SimpleEval
from midca.modules import simulator
from midca.metamodules import monitor, interpret, metaeval, metaintend, plan, control
from midca.worldsim import domainread, stateread
from midca.domains.blocksworld import blockstate, scene, util
from midca.domains.blocksworld.plan import methods_broken, operators
from midca import base
import inspect, os

def asqiiDisplay(world):
    blocks = blockstate.get_block_list(world)
    print(str(scene.Scene(blocks)))


thisDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

MIDCA_ROOT = thisDir + "/../"

### Domain Specific Variables
DOMAIN_ROOT = MIDCA_ROOT + "domains/blocksworld/"
DOMAIN_FILE = DOMAIN_ROOT + "arsonist.sim"
STATE_FILE = DOMAIN_ROOT + "states/defstate_fire_pyhop_inducing_bug.sim"
DISPLAY_FUNC = util.asqiiDisplay
DECLARE_METHODS_FUNC = methods_broken.declare_methods
DECLARE_OPERATORS_FUNC = operators.declare_ops
GOAL_GRAPH_CMP_FUNC = util.preferFire

world = domainread.load_domain(DOMAIN_FILE)
stateread.apply_state_file(world, STATE_FILE)
myMidca = base.PhaseManager(world, verbose=1, display = asqiiDisplay, metaEnabled=True)

# add cognitive layer phases
for phase in ["Simulate", "Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]:
    myMidca.append_phase(phase)

# add cognitive layer modules
myMidca.append_module("Simulate", simulator.MidcaActionSimulator())
myMidca.append_module("Simulate", simulator.ASCIIWorldViewer(DISPLAY_FUNC))
myMidca.append_module("Perceive", PerfectObserver.PerfectObserver())
myMidca.append_module("Interpret", ADistanceAnomalyNoter.ADistanceAnomalyNoter())
myMidca.append_module("Interpret", UserGoalInput.UserGoalInput())
myMidca.append_module("Eval", SimpleEval.SimpleEval())
myMidca.append_module("Intend", SimpleIntend.SimpleIntend())
myMidca.append_module("Plan", PyHopPlannerBroken.PyHopPlannerBroken(util.pyhop_state_from_world,
                                                                util.pyhop_tasks_from_goals,
                                                                DECLARE_METHODS_FUNC,
                                                                DECLARE_OPERATORS_FUNC,
                                                                extinguishers=False))
myMidca.append_module("Act", SimpleAct.SimpleAct())

# add meta layer phases
#for phase in ["Monitor", "Interpret", "Eval", "Intend", "Plan", "Control"]:
for phase in ["Monitor", "Interpret", "Intend", "Plan", "Control"]:
    myMidca.append_meta_phase(phase)

# add meta layer modules
myMidca.append_meta_module("Monitor", monitor.MRSimpleMonitor())
myMidca.append_meta_module("Interpret", interpret.MRSimpleDetectOld())
myMidca.append_meta_module("Interpret", interpret.MRSimpleGoalGen())
myMidca.append_meta_module("Intend", metaintend.MRSimpleIntend())
myMidca.append_meta_module("Plan", plan.MRSimplePlanner())
myMidca.append_meta_module("Control", control.MRSimpleControl())

#myMidca.mem.enableTracing(myMidca.trace)

myMidca.insert_module('Simulate', simulator.ArsonSimulator(arsonChance = 0.3, arsonStart = 2), 1)
#myMidca.insert_module('Interpret', guide.TFStack(), 1)
myMidca.insert_module('Interpret', TFFire.TFFire(), 2)

def preferFire(goal1, goal2):
    if 'predicate' not in goal1 or 'predicate' not in goal2:
        return 0
    elif goal1['predicate'] == 'onfire' and goal2['predicate'] != 'onfire':
        return -1
    elif goal1['predicate'] != 'onfire' and goal2['predicate'] == 'onfire':
        return 1
    return 0

#tells the PhaseManager to copy and store MIDCA states so they can be accessed later.
myMidca.storeHistory = True
myMidca.initGoalGraph(cmpFunc = preferFire)
myMidca.init()
myMidca.run()

'''
The code below would print out MIDCA's goal set for the first 20 phases of the run above. Note that any memory values can be accessed in this way, assuming that the storeHistory value was set to True during the run. This code is left as an example, but commented out because it will throw an error if fewer than 20 cycles were simulated.

for i in range(20):
    print myMidca.history[i].mem.get(myMidca.midca.mem.CURRENT_GOALS)

'''

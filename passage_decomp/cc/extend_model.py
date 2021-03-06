from pm4py.objects.petri.petrinet import PetriNet, Marking
from pccip.passage_decomp.algorithm.constants import ARTIFICIAL_START, ARTIFICIAL_END
from pm4py.objects.petri import utils
from typing import Tuple


class NoInitialMarking(Exception):
    pass


class NoFinalMarking(Exception):
    pass


def extend_model(net: PetriNet,
                 initial_marking: Marking,
                 final_marking: Marking) -> Tuple[PetriNet, Marking, Marking]:
    """This function extends the given petri net with an Bot and Top transition

    Args:
        net (PetriNet): Input Petri Net
        initial_marking (Marking): Input Initial Marking
        final_marking (Marking): Input Final Marking

    Raises:
        NoInitialMarking: No initial marking is given
        NoFinalMarking: No final marking is given

    Returns:
        Tuple[PetriNet, Marking, Marking]: Return petri net with extended transition
    """
    if not initial_marking:
        raise NoInitialMarking("No initial marking defined")

    if not final_marking:
        raise NoFinalMarking("No final marking defined")

    t_bot = PetriNet.Transition(ARTIFICIAL_END, ARTIFICIAL_END)
    t_top = PetriNet.Transition(ARTIFICIAL_START, ARTIFICIAL_START)
    net.transitions.add(t_bot)
    net.transitions.add(t_top)
    for currentSource in initial_marking:
        utils.add_arc_from_to(t_top, currentSource, net)

    for currentSink in final_marking:
        utils.add_arc_from_to(currentSink, t_bot, net)

    return (net, initial_marking, final_marking)


def remove_extension(net: PetriNet, im: Marking, fm: Marking):
    """Remove the petri net extension when it is no longer required.

    Args:
        net (PetriNet): Input Petri Net
        im (Marking): Input Initial Marking
        fm (Marking): Input Final Marking
    """
    for i in im:
        utils.remove_transition(net, next(iter(i.in_arcs)).source)
    for f in fm:
        utils.remove_transition(net, next(iter(f.out_arcs)).target)

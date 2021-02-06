from typing import Set, List, Tuple
from pm4py.objects.log.log import EventLog, Trace
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pm4py.statistics.start_activities.log.get import get_start_activities
from pm4py.statistics.end_activities.log.get import get_end_activities
from pm4py.objects.petri.utils import remove_place, remove_transition
from pm4py.objects.petri.utils import remove_arc, add_arc_from_to
from pccip.bin.pd.p_variants import Variants


def split_log(sublog: EventLog):
    if not isinstance(sublog, EventLog):
        raise TypeError('Invalid Event Log Type')
    start_activities = set(get_start_activities(sublog).keys())
    end_activities = set(get_end_activities(sublog).keys())
    split_log = EventLog()

    for trace in sublog:
        last_loop = 0
        prev_event = None
        for index, event in enumerate(trace):
            curr_event = event['concept:name']
            if index < len(trace) - 1:
                next_event = trace[index+1]['concept:name']
            else:
                next_event = None
            # if event is a starting activity, not at the start of the trace
            # and the previous event was not a starting event (parallel),
            # split the log
            if curr_event in start_activities \
                and index > last_loop \
                    and prev_event not in start_activities:
                split_log.append(Trace(trace[last_loop:index]))
                last_loop = index
            # if event is a ending activity, not at the end of the trace
            # and the next event is not a ending event (parallel),
            # split the log
            elif curr_event in end_activities \
                and index < len(trace) - 1 \
                    and next_event not in end_activities:
                split_log.append(Trace(trace[last_loop:index+1]))
                last_loop = index + 1
            prev_event = curr_event
        # add the rest of the trace as a trace
        split_log.append(Trace(trace[last_loop:]))

    return split_log


def create_fragment(sublog: EventLog,
                    parameters: dict = None,
                    variant: str = 'DEFAULT_VARIANT') -> PetriNet:
    if not isinstance(sublog, EventLog):
        raise TypeError('Invalid Event Log Type')

    variant = getattr(Variants, variant.upper(), None)
    if variant is None:
        raise TypeError('Invalid input variant (p_algo)')

    if parameters is None:
        parameters = {}

    # create new log by splitting the input sublog
    new_log = split_log(sublog)
    # use the p-algo to create a new fragment
    net, im, fm = variant(sublog=new_log, parameters=parameters)

    initial_marking = Marking()
    final_marking = Marking()
    im_place = next(iter(im.keys()))
    fm_place = next(iter(fm.keys()))

    # Create new Marking if fragment is the start fragment
    # and remove artificial start
    if len(im_place.out_arcs) == 1:
        im_transition = next(iter(im_place.out_arcs)).target
        if im_transition.label == 'Artificial:Start':
            new_im_place = next(iter(im_transition.out_arcs)).target
            remove_place(net, im_place)
            remove_transition(net, im_transition)
            initial_marking = Marking({new_im_place: 1})

    # Create new Marking if fragment is the end fragment
    # and remove artificial end
    if len(fm_place.in_arcs) == 1:
        fm_transition = next(iter(fm_place.in_arcs)).source
        if fm_transition.label == 'Artificial:End':
            new_fm_place = next(iter(fm_transition.in_arcs)).source
            remove_place(net, fm_place)
            remove_transition(net, fm_transition)
            final_marking = Marking({new_fm_place: 1})

    # if not at end, remove the generated start and/or end place
    if not len(initial_marking):
        # remove all silent border transitions
        out_arcs = im_place.out_arcs.copy()
        for arc in out_arcs:
            if arc.target.label is None:
                # remove all places, only connected to silent transition
                to_remove_places = {p.target for p in arc.target.out_arcs
                                    if len(p.target.in_arcs) == 1}
                for place in to_remove_places:
                    remove_place(net, place)
                remove_transition(net, arc.target)
        # finally remove the initial place
        remove_place(net, im_place)
    if not len(final_marking):
        # remove all silent border transitions
        in_arcs = fm_place.in_arcs.copy()
        for arc in in_arcs:
            if arc.source.label is None:
                # remove all places, only connected to silent transition
                to_remove_places = {p.source for p in arc.source.in_arcs
                                    if len(p.source.out_arcs) == 1}
                for place in to_remove_places:
                    remove_place(net, place)
                remove_transition(net, arc.source)
        # finally remove the final place
        remove_place(net, fm_place)

    return net, initial_marking, final_marking


def merge_fragments(fragments: List[
                               Tuple[PetriNet, Marking, Marking]]) -> PetriNet:
    if not isinstance(fragments[0], tuple):
        raise TypeError('Please use a List[Tuple[PetriNet, Marking, Marking]]')
    if not isinstance(fragments[0][0], PetriNet) \
       or not isinstance(fragments[0][1], Marking) \
       or not isinstance(fragments[0][2], Marking):
        raise TypeError('Please use Tuple[PetriNet, Marking, Marking]')

    merged_net = fragments[0][0]
    transitions = {tran.label: tran for tran in merged_net.transitions}
    net_list = [net[0] for net in fragments[1:]]
    # for each fragment in the list
    for net in net_list:
        # for each transition in the fragment
        for transition in net.transitions:
            in_arcs_src = {arc.source for arc in transition.in_arcs}
            out_arcs_tar = {arc.target for arc in transition.out_arcs}
            # if transition has already been added, alter edges
            if transition.label in transitions:
                # if transition comes after the merge transition
                for place in in_arcs_src:
                    remove_arc_set(net, transition.in_arcs)
                    merged_net.places.add(place)
                    add_arc_from_to(place,
                                    transitions[transition.label],
                                    merged_net)
                # if trannsition comes before the merge transition
                for place in out_arcs_tar:
                    remove_arc_set(net, transition.out_arcs)
                    merged_net.places.add(place)
                    add_arc_from_to(transitions[transition.label],
                                    place,
                                    merged_net)
            else:
                # if transition does not yet exist, simply add
                merged_net.transitions.add(transition)
                transitions[transition.label] = transition
        # add all the arcs and places from the current fragment to the merge
        merged_net.places.update(net.places)
        merged_net.arcs.update(net.arcs)

    # collect all of the non-empty initial and final marking
    initial_marking_set = {im[1] for im in fragments if not len(im[1]) == 0}
    final_marking_set = {im[2] for im in fragments if not len(im[2]) == 0}

    initial_marking = Marking()
    final_marking = Marking()

    # add all the initial and final markings from the fragments
    if initial_marking_set:
        for marking in initial_marking_set:
            initial_marking = initial_marking + marking
    if final_marking_set:
        for marking in final_marking_set:
            final_marking = final_marking + marking

    return merged_net, initial_marking, final_marking


def remove_arc_set(net: PetriNet, arc_set: Set[PetriNet.Arc]) -> None:
    for arc in arc_set.copy():
        remove_arc(net, arc)

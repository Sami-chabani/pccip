from typing import Tuple, Set
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pm4py.objects.log.log import EventLog
from pccip.passage_decomp.pd.import_log import import_log
from pccip.passage_decomp.pd.extend_log import extend_log
from pccip.passage_decomp.pd.causal_structure import create_causal_structure
from pccip.passage_decomp.pd.causal_structure import create_custom_causal_structure
from pccip.passage_decomp.passages.min_passages import min_passages
from pccip.passage_decomp.cc.log_decomp import efficient_log_decomp
from pccip.passage_decomp.pd.net_fragments import create_fragment, merge_fragments


def passage_process_discovery(xes: EventLog,
                              c_algo: str = 'DEFAULT_VARIANT',
                              c_params: dict = None,
                              p_algo: str = 'DEFAULT_VARIANT',
                              p_params: dict = None,
                              c_custom: Set[Tuple[str, str]] = None) \
        -> Tuple[PetriNet, Marking, Marking]:
    """Algorithm that executes decomposed process discovery using passages.

    Args:
        xes (EventLog): already imported EventLog or file location to .xes
        c_algo (str, optional): Causal algorithm to create causal structure.
                                Variants available: 'ALPHA', 'HEURISTIC'.
                                Defaults to 'DEFAULT_VARIANT'.
        c_params (dict, optional): Parameters for the causal algorithm.
                                   Defaults to None.
        p_algo (str, optional): Process discovery algorithm to create net
                                fragments from sublogs.
                                Variants available: 'ALPHA', 'INDUCTIVE'.
                                Defaults to 'DEFAULT_VARIANT'.
        p_params (dict, optional): Parameters for the discovery algorithm.
                                   Defaults to None.
        c_custom (Set[Tuple[str, str]], optional): Set of edges to manually
                                                   define the causal structure.

    Returns:
        Tuple[PetriNet, Marking, Marking]: Complete petri net of the whole log.
    """
    # import event log (through file path or already imported xes)
    log = import_log(xes)

    # extend the event log
    ext_log = extend_log(log)

    # generate causal structure of the event log
    if c_custom is None:
        causal = create_causal_structure(ext_log, c_algo, c_params)
    else:
        causal = create_custom_causal_structure(c_custom, log)

    # generate passages using the causal structure
    passage_set = min_passages(causal)

    # generate sublogs based off of each passage
    sublogs = efficient_log_decomp(ext_log, passage_set)

    # generate fragments based off of each sublog
    fragments = []
    for log in sublogs:
        fragments.append(create_fragment(log, p_algo, p_params))

    # merge the fragments to create the final petri net
    result_net, result_im, result_fm = merge_fragments(fragments)

    return result_net, result_im, result_fm

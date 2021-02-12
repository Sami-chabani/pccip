import os
import pytest
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments import algorithm as alignments
from pm4py.objects.petri.importer import importer as pnml_importer
from pccip.passage_decomp.cc import adapted_cost


@pytest.mark.parametrize(('tupl, result'),
                         [(('a', 'b'), None),
                         (('a', '>>'), 'a'),
                         (('a', None), None)])
def test_Get_Acti(tupl, result):
    assert adapted_cost.get_acti(tupl) == result


@pytest.fixture
def net_frag():
    currentDir = os.path.dirname(os.path.realpath(__file__))
    pathToFile_1 = os.path.join(currentDir, 'figure8_mod_orig.xes')
    pathToFile_2 = os.path.join(currentDir, 'figure8_mod.xes')
    log_1 = xes_importer.apply(pathToFile_1)
    log_2 = xes_importer.apply(pathToFile_2)
    net, initial_marking, final_marking = inductive_miner.apply(log_1)
    aligned_transition = alignments.apply_log(
                log_2,
                net, initial_marking, final_marking
                )
    return aligned_transition


def test_get_misaligned(net_frag):
    result = adapted_cost.get_misaligned_trans(net_frag)
    assert result[0] == {'Artificial:Start', 'b', 'a'}


@pytest.fixture
def nnfreg():
    currentDir = os.path.dirname(os.path.realpath(__file__))
    pathToLog = os.path.join(currentDir, 'figure8_mod.xes')
    log = xes_importer.apply(pathToLog)
    pathToFile_1 = os.path.join(currentDir, 'f1.pnml')
    pathToFile_2 = os.path.join(currentDir, 'f2.pnml')
    pathToFile_3 = os.path.join(currentDir, 'f3.pnml')
    pathToFile_4 = os.path.join(currentDir, 'f4.pnml')
    pathToFile_5 = os.path.join(currentDir, 'f5.pnml')
    fragments_1, im_1, fm_1 = pnml_importer.apply(pathToFile_1)
    fragments_2, im_2, fm_2 = pnml_importer.apply(pathToFile_2)
    fragments_3, im_3, fm_3 = pnml_importer.apply(pathToFile_3)
    fragments_4, im_4, fm_4 = pnml_importer.apply(pathToFile_4)
    fragments_5, im_5, fm_5 = pnml_importer.apply(pathToFile_5)
    list_frag = [(fragments_1, im_1, fm_1),
                 (fragments_2, im_2, fm_2),
                 (fragments_3, im_3, fm_3),
                 (fragments_4, im_4, fm_4),
                 (fragments_5, im_5, fm_5)]

    return log, list_frag


def test_adapted_cost_fun(nnfreg):
    align_trace = adapted_cost.adapted_cost_func(nnfreg[0], nnfreg[1])
    assert align_trace[0][0]['cost'] == 0
    assert align_trace[1][0]['cost'] == 10000


def test_fragment_fitness(nnfreg):
    align_trace = adapted_cost.adapted_cost_func(nnfreg[0], nnfreg[1])
    fragment_fitness = adapted_cost.fragment_fitness(align_trace)
    assert fragment_fitness[0]['averageFitness'] == 1.0
    assert round(fragment_fitness[1]['averageFitness'], 3) == 0.844


def test_overall_fit(nnfreg):
    align_trace = adapted_cost.adapted_cost_func(nnfreg[0], nnfreg[1])
    assert adapted_cost.overall_fitness(nnfreg[0], align_trace) == 0
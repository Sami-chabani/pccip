from pytest import fixture
import pm4py
from os import path
from pm4py.objects.log.importer.xes import importer as log_importer
from pccip.passage_decomp.algorithm.conformance_checking import passage_conformance_checking


class Test_conformance_passages:
    @fixture
    def alpha_model(self):
        currentDir = path.dirname(path.realpath(__file__))
        logPath = "logs/roadtraffic50traces.xes"
        pathToLog = path.join(currentDir, logPath)

        # net, init, final = import_petri_net(pathToModel)
        log = log_importer.apply(pathToLog)
        net, init, final = pm4py.discover_petri_net_inductive(log)

        return net, init, final, log

    def test_alpha_model(self, alpha_model):
        print("Give Path to PNML Model")
        net = alpha_model[0]
        init_marking = alpha_model[1]
        final_marking = alpha_model[2]
        log = alpha_model[3]
        _, global_fitness = passage_conformance_checking(
            net, init_marking, final_marking, log)

        assert global_fitness == 1
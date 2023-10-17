import re

import penman
from amr_utils.amr_readers import Matedata_Parser, TreePenmanModel
from util import node_name_to_reference_graph_string

import random

from amrbank_analysis.vulcan_pickle_builder import VulcanPickleBuilder


def main():
    amrs, graph_id2_reentrant_triples = load("../external_resources/amrs/split/concatenated/test.txt")
    print(len(amrs))
    print(len(graph_id2_reentrant_triples))

    r = random.Random(5803)  # seed generated by random.org
    r.shuffle(amrs)

    vulcan_pickle_builder = VulcanPickleBuilder()
    with open("../corpus/reentrancies.tsv", "w") as f:
        for graph in amrs:
            reentrant_triples = graph_id2_reentrant_triples[graph.metadata['id']]
            if len(reentrant_triples) > 0:
                for source, role, target in reentrant_triples:
                    vulcan_pickle_builder.add_graph(graph)
                    vulcan_pickle_builder.add_graph_highlight([source, target])
                    f.write(f"{graph.metadata['id']}\t{node_name_to_reference_graph_string(source, graph)}"
                            f"\t{role}\t{node_name_to_reference_graph_string(target, graph)}\n")

    vulcan_pickle_builder.save_pickle("outputs/reentrancies.pickle")


def check_brackets_and_raise_exception_if_fail(amr_string):
    if not amr_string.startswith('(') or not amr_string.endswith(')'):
        raise Exception('Could not parse AMR from: ', amr_string)


def load(amr_file_name):
    print('[amr]', 'Loading AMRs from file:', amr_file_name)
    amrs = []
    metadata_parser = Matedata_Parser()
    graph_id2_reentrant_triples = dict()

    with open(amr_file_name, 'r', encoding='utf8') as f:
        sents = f.read().replace('\r', '').split('\n\n')
        no_tokens = False
        if all(sent.strip().startswith('(') for sent in sents):
            no_tokens = True

        for sent in sents:
            metadata = get_metadata(metadata_parser, no_tokens, sent)
            amr_string = get_amr_string(no_tokens, sent)
            if not amr_string:
                continue
            check_brackets_and_raise_exception_if_fail(amr_string)
            reentrant_triples = get_reentrant_triples(amr_string)
            graph_id2_reentrant_triples[metadata['id']] = reentrant_triples

            amr = penman.decode(sent)
            amrs.append(amr)

    return amrs, graph_id2_reentrant_triples


def get_reentrant_triples(amr_string):
    g = penman.decode(amr_string, model=TreePenmanModel())
    triples = g.triples() if callable(g.triples) else g.triples
    node_labels = set()
    reentrant_triples = []
    for s, r, t in triples:
        if r == ":instance":
            node_labels.add(s)
        elif t in node_labels:
            reentrant_triples.append((s, r, t))
    return reentrant_triples


def get_metadata(metadata_parser, no_tokens, sent):
    prefix_lines = [line for i, line in enumerate(sent.split('\n')) if
                    line.strip().startswith('#') or (i == 0 and not no_tokens)]
    prefix = '\n'.join(prefix_lines)
    metadata, graph_metadata = metadata_parser.readlines(prefix)
    return metadata


def get_amr_string(no_tokens, sent):
    amr_string_lines = [line for i, line in enumerate(sent.split('\n'))
                        if not line.strip().startswith('#') and (i > 0 or no_tokens)]
    amr_string = ''.join(amr_string_lines).strip()
    amr_string = re.sub(' +', ' ', amr_string)
    return amr_string


if __name__ == '__main__':
    main()

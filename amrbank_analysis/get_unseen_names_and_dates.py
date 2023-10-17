import random

from penman import Graph

from amrbank_analysis.find_rare_node_labels import load_corpus_from_folder
from amrbank_analysis.vulcan_pickle_builder import VulcanPickleBuilder


def main():
    training_corpus = load_corpus_from_folder("../../../data/Edinburgh/amr3.0/data/amrs/split/training/")
    print(len(training_corpus))
    test_corpus = load_corpus_from_folder("../../../data/Edinburgh/amr3.0/data/amrs/split/test/")
    print(len(test_corpus))

    r = random.Random(391)  # seed generated by random.org
    r.shuffle(test_corpus)

    seen_dates = set()
    seen_names = set()

    for graph in training_corpus:
        for instance in graph.instances():
            if instance.target == "date-entity":
                date_string = get_date_string_for_date_instance(graph, instance)
                seen_dates.add(date_string)
            elif instance.target == "name":
                name_string = get_name_string_for_name_instance(graph, instance)
                seen_names.add(name_string)

    vpb_unseen_dates = VulcanPickleBuilder()
    vpb_unseen_names = VulcanPickleBuilder()
    vpb_seen_dates = VulcanPickleBuilder()
    vpb_seen_names = VulcanPickleBuilder()

    with open("outputs/unseen_dates.txt", "w") as f:
        with open("../corpus/unseen_dates.tsv", "w") as g:
            with open("outputs/unseen_names.txt", "w") as f2:
                with open("../corpus/unseen_names.tsv", "w") as g2:
                    with open("../corpus/seen_dates.tsv", "w") as h:
                        with open("../corpus/seen_names.tsv", "w") as h2:
                            for graph in test_corpus:
                                for instance in graph.instances():
                                    if instance.target == "date-entity":
                                        date_string = get_date_string_for_date_instance(graph, instance)
                                        if date_string not in seen_dates:
                                            f.write(date_string + "\n")
                                            g.write(f"{graph.metadata['id']}\t{date_string}\n")
                                            vpb_unseen_dates.add_graph(graph)
                                            vpb_unseen_dates.add_graph_highlight([instance.source])
                                        else:
                                            h.write(f"{graph.metadata['id']}\t{date_string}\n")
                                            vpb_seen_dates.add_graph(graph)
                                            vpb_seen_dates.add_graph_highlight([instance.source])
                                    elif is_name_node(graph, instance):
                                        name_string = get_name_string_for_name_instance(graph, instance)
                                        if name_string not in seen_names:
                                            f2.write(name_string + "\n")
                                            g2.write(f"{graph.metadata['id']}\t{name_string}\n")
                                            vpb_unseen_names.add_graph(graph)
                                            vpb_unseen_names.add_graph_highlight([instance.source])
                                        else:
                                            h2.write(f"{graph.metadata['id']}\t{name_string}\n")
                                            vpb_seen_names.add_graph(graph)
                                            vpb_seen_names.add_graph_highlight([instance.source])

    vpb_unseen_dates.save_pickle("outputs/unseen_dates.pickle")
    vpb_unseen_names.save_pickle("outputs/unseen_names.pickle")
    vpb_seen_dates.save_pickle("outputs/seen_dates.pickle")
    vpb_seen_names.save_pickle("outputs/seen_names.pickle")


def is_name_node(graph: Graph, instance):
    if not instance.target == "name":
        return False
    incoming_name_edges = [edge for edge in graph.edges(target=instance.source, role=":name")]
    if len(incoming_name_edges) == 0:
        return False
    name_attributes = [attribute for attribute in graph.attributes(source=instance.source)
                       if attribute.role.startswith(":op")]
    return len(name_attributes) > 0


def get_name_string_for_name_instance(graph, instance):
    """
    given a graph and an instance in it, returns the " ".join of its sorted target labels
    used only when instance is a name, so the targets are op_i. Sorting them gives the parts of the name in order.
    :param graph:
    :param instance:
    :return: str: e.g. "Capitol Hill"
    """
    name_dict = []
    for attribute in graph.attributes(source=instance.source):
        name_dict.append((attribute.role, attribute.target))
    name_dict.sort()  # in opi order
    name_string = " ".join([t[1] for t in name_dict]).replace("\"", "")
    return name_string


def get_date_string_for_date_instance(graph, instance):
    date_dict = []
    for attribute in graph.attributes(source=instance.source):
        date_dict.append((attribute.role, attribute.target))
    date_dict.sort()
    date_string = " ".join([f"{t[0]} {t[1]}" for t in date_dict])
    return date_string


if __name__ == "__main__":
    main()

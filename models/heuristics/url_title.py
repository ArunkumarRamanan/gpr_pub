import os
import urllib

from .coref import Coref
from .stanford_base import StanfordModel
from .utils import parse_tree_to_graph, get_syntactical_distance_from_graph

class StanfordURLTitleModel(Coref, StanfordModel):
    def __init__(self, model, debug=False):
        self.model = model
        self.debug = debug
    
    def predict(self, text, a, b, pronoun_offset, a_offset, b_offset, url, id, debug=False, **kwargs):
        doc, tokens, pronoun_offset, a_offset, b_offset, a_span, b_span, pronoun_token, a_tokens, b_tokens = self.tokenize(text, 
                                                                                                        a, 
                                                                                                        b, 
                                                                                                        pronoun_offset, 
                                                                                                        a_offset, 
                                                                                                        b_offset, 
                                                                                                        **kwargs)

        clusters = []

        title = os.path.basename(urllib.parse.unquote(url)).replace('_', ' ')
        title = [token for token in self.model.tokenize(title)]
        
        try:
            trees = self.model.parse_text(text)
            graph = parse_tree_to_graph(trees, doc)

            for token in a_tokens:
                token.syn_dist = get_syntactical_distance_from_graph(graph, token, pronoun_token)
                
            for token in b_tokens:
                token.syn_dist = get_syntactical_distance_from_graph(graph, token, pronoun_token)
                
            candidate_a = sorted(filter(lambda token: token.text in title, a_tokens), key=lambda token: token.syn_dist)
            candidate_b = sorted(filter(lambda token: token.text in title, b_tokens), key=lambda token: token.syn_dist)
            
            if len(candidate_a) and len(candidate_b) and candidate_a[0].syn_dist == candidate_b[0].syn_dist:
                if debug: 
                    print('{}, Both mentions have the same syntactic distance'.format(id))
            else:
                candidates = sorted(candidate_a + candidate_b, key=lambda token: token.syn_dist)
                if len(candidates):
                    candidate = candidates[0]
                    clusters.append([[pronoun_offset, pronoun_offset], [candidate.i, candidate.i]])
                
        except Exception as e:
            print('{}, {}'.format(id, e))

        return tokens, clusters, pronoun_offset, a_span, b_span
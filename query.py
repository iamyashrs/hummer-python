import fingerprint
import library

freq_num = 40
max_match_tol = 0.9


class QueryClient:
    '''A class designed to handle all functionality related to filtering
       the music database and finding a song match based on a sample'''

    def __init__(self, hash_table):
        '''Initializes object by storing provided hash table in
           a field within the object.

           @param dict hash table associated with library for search
           @return QueryClient'''
        self.database_hash = hash_table

    def query(self, sample_audio, mode="sample"):
        '''Different settings based on whether a recording or a songs snippet.
           Returns matching song if one is found, else 'no match was found'
           and the closely related songs

           @param string location of sample file
           @param string used to determine which search mode to use
                  (for internal use only)
           @return tuple'''
        global freq_num
        global max_match
        if mode == "record":
            freq_num = 100
            max_match_tol = 0.9
        else:
            freq_num = 40
            max_match_tol = 0.9
        '''initiates search algo specified in paper'''
        sample_fp = fingerprint.Fingerprint(sample_audio)
        filt_list = self._filter_library(sample_fp)
        match = self._best_match(filt_list, sample_fp)
        if match:
            if match[0] is None:
                return ("No match was found", ["No close matches"])
            else:
                # return (match[0].split("/")[1].strip(), match[1])
                return match[0].strip(), match[1]
        else:
            return "No match was found", ["No close matches"]

    def _filter_library(self, sample_fprint):
        '''Helper function that determines candidate list.

           @param Fingerprint fingerprint of sample audio used in search
           @return Fingerprint list'''
        random_tokens = sample_fprint.hash_list()[:freq_num]
        return self._table_lookup(random_tokens)

    def _table_lookup(self, token_list):
        '''Takes in a list of tokens and returns the fingerprints that contain
           all those tokens in its hash.

           @param (tuple list) tokens that will be looked up in hash table
           @return Fingerprint list'''
        result = []
        for token in token_list:
            try:
                for fingerprint in self.database_hash[token[0]]:
                    if fingerprint not in result:
                        result.append(fingerprint)
            except:
                pass
        return result

    def _best_match(self, candidate_list, sample_fprint):
        '''Finds sample-audio track pair that match the best.
           iterates over all items in list using hist. Also finds
           close matches.

           @param (Fingerprint list) Fingerprint
           @result tuple'''
        match_coeff = []
        for candidate in candidate_list:
            comparison = fingerprint.compare(sample_fprint, candidate)
            if comparison != None:
                match_coeff.append(comparison)
        if match_coeff == []:
            return None

        # find best match and close matches according to weighting algorithm
        close_matches = zip(*sorted(match_coeff))[1][-5:]
        match_list = zip(*match_coeff)[0]
        max_match = max(match_list)
        max_match = (max_match, match_list.index(max_match))
        close_maxs = [(a - 1000 * (int(a / 1000)), match_list.index(a), a)
                      for a in match_list if (a > (max_match_tol * max_match[0]))]
        if len(close_maxs) > 1:
            close_maxs = sorted(close_maxs, reverse=True, key=lambda x: (x[2]))
            mode_list = zip(*close_maxs)
            highest_mode_index = mode_list[0].index(max(mode_list[0]))
            best_match = match_coeff[mode_list[1][highest_mode_index]][1]
            close_matches = tuple(x for x in close_matches if x != best_match)
            return (best_match, close_matches)
        else:
            best_match = match_coeff[max_match[1]][1]
            close_matches = tuple(x for x in close_matches if x != best_match)
            return (best_match, close_matches)

from collections import namedtuple

from fuzzysearch.common import Match


Candidate = namedtuple('Candidate', ['start', 'subseq_index', 'dist'])


def _prepare_init_candidates_dict(subsequence, max_l_dist):
    return dict((
        (char, index)
        for (index, char) in enumerate(subsequence[:max_l_dist + 1])
        if char not in subsequence[:index]
    ))

def find_near_matches_customized_levenshtein(subsequence, sequence, max_l_dist):
    if not subsequence:
        raise ValueError('Given subsequence is empty!')

    # optimization: prepare some often used things in advance
    _init_candidates_dict = _prepare_init_candidates_dict(subsequence, max_l_dist)
    _subseq_len = len(subsequence)

    candidates = []
    for index, char in enumerate(sequence):
        new_candidates = []

        idx_in_subseq = _init_candidates_dict.get(char, None)
        if idx_in_subseq is not None:
            if idx_in_subseq + 1 == _subseq_len:
                yield Match(index, index + 1, idx_in_subseq)
            else:
                new_candidates.append(Candidate(index, idx_in_subseq + 1, idx_in_subseq))

        for cand in candidates:
            # if this sequence char is the candidate's next expected char
            if subsequence[cand.subseq_index] == char:
                # if reached the end of the subsequence, return a match
                if cand.subseq_index + 1 == _subseq_len:
                    yield Match(cand.start, index + 1, cand.dist)
                # otherwise, update the candidate's subseq_index and keep it
                else:
                    new_candidates.append(cand._replace(
                        subseq_index=cand.subseq_index + 1,
                    ))

            # if this sequence char is *not* the candidate's next expected char
            else:
                # we can try skipping a sequence or sub-sequence char (or both),
                # unless this candidate has already skipped the maximum allowed
                # number of characters
                if cand.dist == max_l_dist:
                    continue

                # add a candidate skipping a sequence char
                new_candidates.append(cand._replace(dist=cand.dist + 1))

                if index + 1 < len(sequence) and cand.subseq_index + 1 < _subseq_len:
                    # add a candidate skipping both a sequence char and a
                    # subsequence char
                    new_candidates.append(cand._replace(
                        dist=cand.dist + 1,
                        subseq_index=cand.subseq_index + 1,
                    ))

                # try skipping subsequence chars
                for n_skipped in xrange(1, max_l_dist - cand.dist + 1):
                    # if skipping n_skipped sub-sequence chars reaches the end
                    # of the sub-sequence, yield a match
                    if cand.subseq_index + n_skipped == _subseq_len:
                        yield Match(cand.start, index + 1, cand.dist + n_skipped)
                        break
                    # otherwise, if skipping n_skipped sub-sequence chars
                    # reaches a sub-sequence char identical to this sequence
                    # char, add a candidate skipping n_skipped sub-sequence
                    # chars
                    elif subsequence[cand.subseq_index + n_skipped] == char:
                        # if this is the last char of the sub-sequence, yield
                        # a match
                        if cand.subseq_index + n_skipped + 1 == _subseq_len:
                            yield Match(cand.start, index + 1,
                                        cand.dist + n_skipped)
                        # otherwise add a candidate skipping n_skipped
                        # subsequence chars
                        else:
                            new_candidates.append(cand._replace(
                                dist=cand.dist + n_skipped,
                                subseq_index=cand.subseq_index + 1 + n_skipped,
                            ))
                        break
                # note: if the above loop ends without a break, that means that
                # no candidate could be added / yielded by skipping sub-sequence
                # chars

        candidates = new_candidates

    for cand in candidates:
        dist = cand.dist + _subseq_len - cand.subseq_index
        if dist <= max_l_dist:
            yield Match(cand.start, len(sequence), dist)